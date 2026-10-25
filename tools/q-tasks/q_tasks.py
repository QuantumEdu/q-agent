#!/usr/bin/env python3
"""Durable local tasks and commit-bound verification (Python stdlib, POSIX)."""
import argparse
from process_guard import workload, identity, launch_args, surviving
from workflow import Workflow, schema as workflow_schema, PHASES
from operations import Operations, schema as operation_schema
from snapshots import backup, restore
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
from runtime_support import (MIB, BoundedOutput, capture_command, diagnostic,
                             prune_logs, resources, runner_active)
from capabilities import BACKENDS, CAPABILITIES, inspect_backend, require_capabilities


def now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def command_signals():
    """Defer cancellation until Popen has returned an owned process handle."""
    received = []
    previous = {}
    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            previous[signum] = signal.signal(signum, lambda number, frame: received.append(number))
        yield received
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


class Tasks:
    timestamp = staticmethod(now)

    def __init__(self, project):
        self.root = Path(subprocess.check_output(
            ["git", "-C", str(project), "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
        self.directory = self.root / ".cache" / "q-agent-tasks"
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        # A project must exclude runtime state before verification can be clean.
        self.db = sqlite3.connect(self.directory / "tasks.sqlite3", timeout=10)
        self.db.row_factory = sqlite3.Row
        if self.db.execute("PRAGMA user_version").fetchone()[0] > 1:
            self.db.close()
            raise ValueError("Unsupported task schema version; refuse downgrade")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL,
                retry_reason TEXT);
            CREATE TABLE IF NOT EXISTS attempts (
                request_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, operation TEXT NOT NULL,
                command TEXT NOT NULL, timeout REAL NOT NULL, state TEXT NOT NULL,
                commit_sha TEXT NOT NULL, started_at TEXT NOT NULL, finished_at TEXT,
                exit_code INTEGER, child_pid INTEGER, checkout_matches INTEGER,
                error TEXT, log_path TEXT NOT NULL);
        """)
        columns = {name: 'INTEGER' for name in ('min_free_bytes', 'max_log_bytes', 'output_bytes', 'output_truncated')}
        columns['required_capabilities'] = 'TEXT'
        columns.update(process_identity='TEXT', launch_guard='TEXT', process_closed='INTEGER', replay_policy='TEXT')
        for column, kind in columns.items():
            if column not in {row[1] for row in self.db.execute('PRAGMA table_info(attempts)')}:
                try:
                    self.db.execute(f'ALTER TABLE attempts ADD COLUMN {column} {kind}')
                except sqlite3.OperationalError:
                    if column not in {row[1] for row in self.db.execute('PRAGMA table_info(attempts)')}:
                        raise

        with self.db:
            workflow_schema(self.db)
            operation_schema(self.db)
            self.db.execute('CREATE TABLE IF NOT EXISTS store_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            self.db.execute("INSERT OR IGNORE INTO store_meta VALUES ('project', ?)", (str(self.root),))
            if self.db.execute("SELECT value FROM store_meta WHERE key='project'").fetchone()[0] != str(self.root):
                raise ValueError('Ledger belongs to another project path; explicit migration required')
            self.db.execute("PRAGMA user_version=1")
        self.workflow = Workflow(self)
        self.operations = Operations(self)

    def checkout(self):
        def git(*args):
            return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()
        return git("rev-parse", "HEAD"), not git("status", "--porcelain", "--untracked-files=all")

    @contextmanager
    def lock(self):
        with (self.directory / "runner.lock").open("a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError("A local task command is active; inspect it before retrying") from None
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def task(self, task_id):
        row = self.db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown task")
        return dict(row)

    def recover(self):
        # Only the holder of the runner lock may conclude an earlier runner exited.
        with self.db:
            self.db.execute("UPDATE tasks SET state='uncertain' WHERE state='running'")
            self.db.execute("UPDATE attempts SET state='uncertain', error='runner_lost', "
                            "finished_at=? WHERE state='running'", (now(),))

    def add(self, task_id, title):
        with self.lock(), self.db:
            row = self.db.execute("SELECT title FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row and row[0] != title:
                raise ValueError("Task ID already belongs to a different title")
            self.db.execute("INSERT OR IGNORE INTO tasks VALUES (?, ?, 'pending', NULL)", (task_id, title))
        return self.task(task_id)

    def retry(self, task_id, reason):
        if not reason.strip():
            raise ValueError("Record the inspection and retry authorization")
        with self.lock():
            self.recover()
            if self.task(task_id)["state"] not in {"failed", "uncertain", "awaiting_verification", "verified"}:
                raise ValueError("Task does not require a retry")
            if self.task(task_id)['state'] == 'uncertain':
                last = self.db.execute('SELECT * FROM attempts WHERE task_id=? ORDER BY rowid DESC LIMIT 1', (task_id,)).fetchone()
                if last and (last['replay_policy'] or 'inspect') != 'repeatable':
                    raise ValueError('Uncertain command requires task reconcile with observed outcome first')
            with workload(self.directory, self.db), self.db:
                self.db.execute("UPDATE tasks SET state='pending', retry_reason=? WHERE id=?", (reason, task_id))
        return self.task(task_id)

    def resume(self):
        active = False
        try:
            with self.lock():
                self.recover()
        except ValueError:
            active = True
        head, clean = self.checkout()
        tasks = []
        for row in self.db.execute("SELECT * FROM tasks ORDER BY id"):
            task = dict(row)
            proof = self.db.execute("SELECT * FROM attempts WHERE task_id=? ORDER BY rowid DESC LIMIT 1",
                                    (task["id"],)).fetchone()
            stale = task["state"] == "verified" and (not clean or not proof or proof["commit_sha"] != head)
            task["workflow"] = self.workflow.get(task["id"])
            task["outstanding_effects"] = self.db.execute(
                "SELECT count(*) FROM effects WHERE task_id=? AND state NOT IN ('completed', 'no_effect')", (task['id'],)).fetchone()[0]
            task["evidence_stale"] = stale
            task["next_action"] = ("verify_current_checkout" if stale else {
                "pending": "dispatch_when_authorized", "running": "observe_active_command",
                "uncertain": "inspect_effects_before_retry", "failed": "inspect_failure_before_retry",
                "awaiting_verification": "commit_then_verify", "verified": "review_acceptance_criteria",
            }[task["state"]])
            tasks.append(task)
        blocked = None
        if not active:
            try:
                with workload(self.directory, self.db):
                    pass
            except (OSError, ValueError) as exc:
                blocked = str(exc)
        return {"runner_active": active, "commit_sha": head, "checkout_clean": clean,
                "dispatch_blocked": active or blocked is not None, "recovery_blocked_reason": blocked, "tasks": tasks}

    def history(self, task_id):
        self.task(task_id)
        return {"attempts": [dict(row) for row in self.db.execute(
            "SELECT * FROM attempts WHERE task_id=? ORDER BY rowid", (task_id,))],
            "workflow_events": [dict(row) for row in self.db.execute(
                "SELECT * FROM workflow_events WHERE task_id=? ORDER BY rowid", (task_id,))],
            "effect_events": [dict(row) for row in self.db.execute(
                'SELECT e.* FROM effect_events e JOIN effects f ON e.effect_id=f.id WHERE f.task_id=? ORDER BY e.rowid', (task_id,))],
            "effects": [dict(row) for row in self.db.execute('SELECT * FROM effects WHERE task_id=?', (task_id,))],
            "reconciliations": [dict(row) for row in self.db.execute(
                'SELECT r.* FROM reconciliations r JOIN attempts a USING (request_id) WHERE a.task_id=?', (task_id,))]}

    def preflight(self, minimum=256 * MIB):
        return {'resources': resources(self.root, minimum), 'runner_active': runner_active(self.directory)}

    def execute(self, operation, task_id, request_id, command, timeout,
                min_free_mib=256, max_log_mib=8, required=(), replay_policy='inspect'):
        if not command or not request_id or not math.isfinite(timeout) or not 0 < timeout <= 900:
            raise ValueError("Supply a command, request ID and timeout in (0, 900] seconds")
        if not 0 <= min_free_mib < 2**43 or not 1 <= max_log_mib <= 64:
            raise ValueError('Require nonnegative disk reserve and a log limit of 1..64 MiB')
        encoded = json.dumps(command)
        required = sorted(set(required))
        with self.lock():
            self.recover()
            task = self.task(task_id)
            old = self.db.execute("SELECT * FROM attempts WHERE request_id=?", (request_id,)).fetchone()
            if old:
                if (old["task_id"], old["operation"], old["command"], old["timeout"]) != (task_id, operation, encoded, timeout):
                    raise ValueError("Request ID conflicts with an existing operation")
                if ((old['min_free_bytes'] is not None and old['min_free_bytes'] != min_free_mib * MIB)
                        or (old['max_log_bytes'] is not None and old['max_log_bytes'] != max_log_mib * MIB)):
                    raise ValueError('Request ID conflicts with existing resource/output settings')
                if (old['required_capabilities'] or '[]') != json.dumps(required):
                    raise ValueError('Request ID conflicts with existing capability requirements')
                if (old['replay_policy'] or 'inspect') != replay_policy:
                    raise ValueError('Request ID conflicts with recovery policy')
                return dict(old)
            if task["state"] in {"failed", "uncertain"} or (operation == "run" and task["state"] != "pending"):
                raise ValueError("Inspect existing effects and use retry explicitly before dispatch")
            with workload(self.directory, self.db) as lease_fd:
                return self._execute(operation, task_id, request_id, command, timeout,
                                     min_free_mib, max_log_mib, required, encoded, lease_fd, replay_policy)

    def _execute(self, operation, task_id, request_id, command, timeout,
                 min_free_mib, max_log_mib, required, encoded, lease_fd, replay_policy):
        head, clean = self.checkout()
        if operation == "verify" and not clean:
            raise ValueError("Commit changes and exclude .cache/ before commit-bound verification")
        admission = resources(self.root, min_free_mib * MIB)
        if not admission['admitted']:
            raise ValueError('Resource admission rejected: ' + admission['reason'])
        require_capabilities(required)
        # Random log names never interpret request IDs as paths.
        import uuid
        log = self.directory / (uuid.uuid4().hex + ".log")
        with self.db:
            self.workflow.prepare(task_id, request_id, operation)
            self.db.execute("INSERT INTO attempts (request_id,task_id,operation,command,timeout,state,"
                            "commit_sha,started_at,log_path,min_free_bytes,max_log_bytes,required_capabilities) VALUES (?,?,?,?,?,'running',?,?,?,?,?,?)",
                            (request_id, task_id, operation, encoded, timeout, head, now(), str(log),
                             min_free_mib * MIB, max_log_mib * MIB, json.dumps(required)))
            self.db.execute("UPDATE attempts SET launch_guard='prepared', replay_policy=? WHERE request_id=?", (replay_policy, request_id))
            self.db.execute("UPDATE tasks SET state='running' WHERE id=?", (task_id,))
        child = None
        gate_write = None
        exit_code, error = None, None
        capture = None
        with command_signals() as received:
            try:
                prune_logs(self.directory, [row[0] for row in self.db.execute(
                    'SELECT log_path FROM attempts ORDER BY rowid DESC')])
                with log.open("x+b") as output:
                    os.chmod(log, 0o600)
                    capture = BoundedOutput(output, max_log_mib * MIB)
                    token = uuid.uuid4().hex
                    receipt = self.directory / (token + '.completion.json')
                    gate_read, gate_write = os.pipe()
                    try:
                        child = subprocess.Popen(launch_args(command, gate_read, lease_fd, receipt, token),
                            cwd=self.root, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, start_new_session=True,
                            pass_fds=(gate_read, lease_fd))
                    finally:
                        os.close(gate_read)
                    with self.db:
                        self.db.execute("UPDATE attempts SET child_pid=?, process_identity=?, launch_guard='dispatched' WHERE request_id=?",
                                        (child.pid, json.dumps(identity(child.pid, token, receipt)), request_id))
                    os.write(gate_write, b'1')
                    os.close(gate_write)
                    gate_write = None
                    error = capture_command(child, timeout, received, capture)
            except OSError:
                error = "launch_or_log_failed"
            finally:
                if gate_write is not None:
                    os.close(gate_write)
                if child is not None:
                    if child.poll() is None:
                        try:
                            os.killpg(child.pid, signal.SIGTERM)
                        except ProcessLookupError:
                            pass
                        try:
                            child.wait(timeout=2)
                        except subprocess.TimeoutExpired:
                            os.killpg(child.pid, signal.SIGKILL)
                            child.wait()
                    exit_code = child.wait()
                    child.stdout.close()
        process_closed = child is None
        if child is not None:
            saved = self.db.execute('SELECT process_identity FROM attempts WHERE request_id=?', (request_id,)).fetchone()[0]
            try:
                process_closed = bool(saved) and not surviving(saved)
                if not process_closed:
                    error = error or 'descendants_alive'
            except (OSError, ValueError):
                error = error or 'supervisor_completion_unavailable'
        end_head, end_clean = self.checkout()
        matches = clean and end_clean and head == end_head
        state = ("uncertain" if error else "failed" if exit_code != 0 else
                 "awaiting_verification" if operation == "run" else "verified" if matches else "uncertain")
        with self.db:
            state = self.workflow.finish(task_id, request_id, operation, state)
            total = capture.total if capture else 0
            self.db.execute("UPDATE attempts SET state=?, finished_at=?, exit_code=?, checkout_matches=?, error=?, "
                            "output_bytes=?, output_truncated=?, process_closed=? WHERE request_id=?",
                            (state, now(), exit_code, int(matches), error, total, int(total > max_log_mib * MIB), int(process_closed), request_id))
            self.db.execute("UPDATE tasks SET state=? WHERE id=?", (state, task_id))
        result = dict(self.db.execute("SELECT * FROM attempts WHERE request_id=?", (request_id,)).fetchone())
        try:
            diagnostic(self.directory, result)
        except OSError:
            result['diagnostics_recorded'] = False  # Never invalidate durable work for best-effort diagnostics.
        return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("task")
    add.add_argument("title")
    sub.add_parser("resume")
    sub.add_parser('preflight')
    capabilities = sub.add_parser('capabilities')
    capabilities.add_argument('--backend', choices=BACKENDS, default='local')
    history = sub.add_parser("history")
    history.add_argument("task")
    retry = sub.add_parser("retry")
    retry.add_argument("task")
    retry.add_argument("--reason", required=True)
    for name in ("run", "verify"):
        execute = sub.add_parser(name)
        execute.add_argument("task")
        execute.add_argument("--request-id", required=True)
        execute.add_argument("--timeout", type=float, default=300)
        execute.add_argument('--replay-policy', choices=['inspect', 'repeatable'], default='inspect')
        execute.add_argument('--min-free-mib', type=int, default=256)
        execute.add_argument('--max-log-mib', type=int, default=8)
        execute.add_argument('--require-capability', action='append', choices=CAPABILITIES, default=[])
    sub.add_parser('backup').add_argument('path', type=Path)
    sub.add_parser('restore').add_argument('path', type=Path)
    reconcile = sub.add_parser('reconcile')
    reconcile.add_argument('task')
    reconcile.add_argument('--attempt', required=True)
    reconcile.add_argument('--outcome', choices=['completed', 'failed', 'no_effect'], required=True)
    reconcile.add_argument('--evidence', required=True)
    effects = sub.add_parser('effect').add_subparsers(dest='effect_action', required=True)
    prepare = effects.add_parser('prepare')
    prepare.add_argument('effect')
    prepare.add_argument('--task', required=True)
    prepare.add_argument('--payload', type=Path, required=True)
    approve = effects.add_parser('approve')
    approve.add_argument('effect')
    approve.add_argument('--evidence', required=True)
    effects.add_parser('claim').add_argument('effect')
    effects.add_parser('show').add_argument('effect')
    settle = effects.add_parser('settle')
    settle.add_argument('effect')
    settle.add_argument('--outcome', choices=['completed', 'failed', 'no_effect'], required=True)
    settle.add_argument('--external-receipt', required=True)
    settle.add_argument('--evidence', required=True)
    wf = sub.add_parser('workflow')
    commands = wf.add_subparsers(dest='workflow_action', required=True)
    start = commands.add_parser('start')
    start.add_argument('task')
    start.add_argument('--request-id', required=True)
    start.add_argument('--source', nargs='+', required=True)
    start.add_argument('--tests', nargs='+', required=True)
    start.add_argument('--max-corrections', type=int, default=2)
    start.add_argument('--definition', required=True)
    start.add_argument('--backend', default='host')
    start.add_argument('--model', default='unknown')
    start.add_argument('--harness', nargs='*', default=['.q-agent.json'])
    advance = commands.add_parser('advance')
    advance.add_argument('task')
    advance.add_argument('--request-id', required=True)
    advance.add_argument('--sequence', type=int, required=True)
    advance.add_argument('--phase', choices=PHASES, required=True)
    advance.add_argument('--evidence', required=True)
    review = commands.add_parser('review')
    review.add_argument('task')
    review.add_argument('--request-id', required=True)
    review.add_argument('--sequence', type=int, required=True)
    review.add_argument('--verdict', choices=['APPROVED', 'REJECTED'], required=True)
    review.add_argument('--reviewer', required=True)
    review.add_argument('--evidence', required=True)
    commands.add_parser('show').add_argument('task')
    # Split explicitly: argparse REMAINDER would swallow options after task ID.
    argv = sys.argv[1:]
    separator = argv.index("--") if "--" in argv else len(argv)
    args = parser.parse_args(argv[:separator])
    if args.action == 'capabilities':
        print(json.dumps(inspect_backend(args.backend)))
        return 0
    store = None
    try:
        store = Tasks(args.project)
        if args.action == 'backup':
            result = backup(store, args.path)
        elif args.action == 'restore':
            result = restore(store, args.path)
        elif args.action == 'reconcile':
            result = store.operations.reconcile(args.task, args.attempt, args.outcome, args.evidence)
        elif args.action == 'effect':
            if args.effect_action == 'prepare':
                result = store.operations.prepare(args.effect, args.task, json.loads(args.payload.read_text()))
            elif args.effect_action == 'approve':
                result = store.operations.approve(args.effect, args.evidence)
            elif args.effect_action == 'claim':
                result = store.operations.claim(args.effect)
            elif args.effect_action == 'settle':
                result = store.operations.settle(args.effect, args.outcome, args.external_receipt, args.evidence)
            else:
                result = store.operations.get(args.effect)
        elif args.action == 'workflow':
            if args.workflow_action == 'start':
                result = store.workflow.start(args.task, args.request_id, args.source, args.tests,
                    args.max_corrections, args.definition, args.backend, args.model, args.harness)
            elif args.workflow_action == 'advance':
                result = store.workflow.advance(args.task, args.request_id, args.sequence,
                                                args.phase, args.evidence)
            elif args.workflow_action == 'review':
                result = store.workflow.review(args.task, args.request_id, args.sequence,
                                              args.verdict, args.reviewer, args.evidence)
            else:
                result = store.workflow.get(args.task)
                if result is None:
                    raise ValueError('Workflow not registered')
        elif args.action == "add":
            result = store.add(args.task, args.title)
        elif args.action == "resume":
            result = store.resume()
        elif args.action == "history":
            result = store.history(args.task)
        elif args.action == 'preflight':
            result = store.preflight()
        elif args.action == "retry":
            result = store.retry(args.task, args.reason)
        else:
            result = store.execute(args.action, args.task, args.request_id, argv[separator + 1:], args.timeout,
                                   args.min_free_mib, args.max_log_mib, args.require_capability, args.replay_policy)
        print(json.dumps(result, ensure_ascii=False))
        if args.action == 'effect' and args.effect_action == 'claim':
            return 0
        return 1 if result.get("state") in {"failed", "uncertain"} else 0
    except (ValueError, OSError, sqlite3.Error, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    finally:
        if store is not None:
            store.db.close()


if __name__ == "__main__":
    raise SystemExit(main())
