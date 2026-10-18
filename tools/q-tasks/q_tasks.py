#!/usr/bin/env python3
"""Durable local tasks and commit-bound verification (Python stdlib, POSIX)."""
import argparse
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
    def __init__(self, project):
        self.root = Path(subprocess.check_output(
            ["git", "-C", str(project), "rev-parse", "--show-toplevel"], text=True).strip()).resolve()
        self.directory = self.root / ".cache" / "q-agent-tasks"
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        # A project must exclude runtime state before verification can be clean.
        self.db = sqlite3.connect(self.directory / "tasks.sqlite3", timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA busy_timeout=5000")
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
        for column in ('min_free_bytes', 'max_log_bytes', 'output_bytes', 'output_truncated'):
            if column not in {row[1] for row in self.db.execute('PRAGMA table_info(attempts)')}:
                try:
                    self.db.execute(f'ALTER TABLE attempts ADD COLUMN {column} INTEGER')
                except sqlite3.OperationalError:
                    if column not in {row[1] for row in self.db.execute('PRAGMA table_info(attempts)')}:
                        raise

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
            with self.db:
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
            task["evidence_stale"] = stale
            task["next_action"] = ("verify_current_checkout" if stale else {
                "pending": "dispatch_when_authorized", "running": "observe_active_command",
                "uncertain": "inspect_effects_before_retry", "failed": "inspect_failure_before_retry",
                "awaiting_verification": "commit_then_verify", "verified": "review_acceptance_criteria",
            }[task["state"]])
            tasks.append(task)
        return {"runner_active": active, "commit_sha": head, "checkout_clean": clean, "tasks": tasks}

    def history(self, task_id):
        self.task(task_id)
        return {"attempts": [dict(row) for row in self.db.execute(
            "SELECT * FROM attempts WHERE task_id=? ORDER BY rowid", (task_id,))]}

    def preflight(self, minimum=256 * MIB):
        return {'resources': resources(self.root, minimum), 'runner_active': runner_active(self.directory)}

    def execute(self, operation, task_id, request_id, command, timeout,
                min_free_mib=256, max_log_mib=8):
        if not command or not request_id or not math.isfinite(timeout) or not 0 < timeout <= 900:
            raise ValueError("Supply a command, request ID and timeout in (0, 900] seconds")
        if min_free_mib < 0 or not 1 <= max_log_mib <= 64:
            raise ValueError('Require nonnegative disk reserve and a log limit of 1..64 MiB')
        encoded = json.dumps(command)
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
                return dict(old)
            if task["state"] in {"failed", "uncertain"} or (operation == "run" and task["state"] != "pending"):
                raise ValueError("Inspect existing effects and use retry explicitly before dispatch")
            head, clean = self.checkout()
            if operation == "verify" and not clean:
                raise ValueError("Commit changes and exclude .cache/ before commit-bound verification")
            admission = resources(self.root, min_free_mib * MIB)
            if not admission['admitted']:
                raise ValueError('Resource admission rejected: ' + admission['reason'])
            # Random log names never interpret request IDs as paths.
            import uuid
            log = self.directory / (uuid.uuid4().hex + ".log")
            with self.db:
                self.db.execute("INSERT INTO attempts (request_id,task_id,operation,command,timeout,state,"
                                "commit_sha,started_at,log_path,min_free_bytes,max_log_bytes) VALUES (?,?,?,?,?,'running',?,?,?,?,?)",
                                (request_id, task_id, operation, encoded, timeout, head, now(), str(log),
                                 min_free_mib * MIB, max_log_mib * MIB))
                self.db.execute("UPDATE tasks SET state='running' WHERE id=?", (task_id,))
            child = None
            exit_code, error = None, None
            capture = None
            with command_signals() as received:
                try:
                    prune_logs(self.directory, [row[0] for row in self.db.execute(
                        'SELECT log_path FROM attempts ORDER BY rowid DESC')])
                    with log.open("x+b") as output:
                        os.chmod(log, 0o600)
                        capture = BoundedOutput(output, max_log_mib * MIB)
                        child = subprocess.Popen(command, cwd=self.root, stdin=subprocess.DEVNULL,
                                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, start_new_session=True)
                        with self.db:
                            self.db.execute("UPDATE attempts SET child_pid=? WHERE request_id=?", (child.pid, request_id))
                        error = capture_command(child, timeout, received, capture)
                except OSError:
                    error = "launch_or_log_failed"
                finally:
                    if child is not None:
                        # Only this freshly spawned group is ours; never act on saved PIDs.
                        try:
                            os.killpg(child.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        exit_code = child.wait()
                        child.stdout.close()
            end_head, end_clean = self.checkout()
            matches = clean and end_clean and head == end_head
            state = ("uncertain" if error else "failed" if exit_code != 0 else
                     "awaiting_verification" if operation == "run" else "verified" if matches else "uncertain")
            with self.db:
                total = capture.total if capture else 0
                self.db.execute("UPDATE attempts SET state=?, finished_at=?, exit_code=?, checkout_matches=?, error=?, "
                                "output_bytes=?, output_truncated=? WHERE request_id=?",
                                (state, now(), exit_code, int(matches), error, total, int(total > max_log_mib * MIB), request_id))
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
        execute.add_argument('--min-free-mib', type=int, default=256)
        execute.add_argument('--max-log-mib', type=int, default=8)
    # Split explicitly: argparse REMAINDER would swallow options after task ID.
    argv = sys.argv[1:]
    separator = argv.index("--") if "--" in argv else len(argv)
    args = parser.parse_args(argv[:separator])
    store = None
    try:
        store = Tasks(args.project)
        if args.action == "add":
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
                                   args.min_free_mib, args.max_log_mib)
        print(json.dumps(result, ensure_ascii=False))
        return 1 if result.get("state") in {"failed", "uncertain"} else 0
    except (ValueError, OSError, sqlite3.Error, subprocess.CalledProcessError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    finally:
        if store is not None:
            store.db.close()


if __name__ == "__main__":
    raise SystemExit(main())
