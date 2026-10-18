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


def now():
    return datetime.now(timezone.utc).isoformat()


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

    def execute(self, operation, task_id, request_id, command, timeout):
        if not command or not request_id or not math.isfinite(timeout) or not 0 < timeout <= 900:
            raise ValueError("Supply a command, request ID and timeout in (0, 900] seconds")
        encoded = json.dumps(command)
        with self.lock():
            self.recover()
            task = self.task(task_id)
            old = self.db.execute("SELECT * FROM attempts WHERE request_id=?", (request_id,)).fetchone()
            if old:
                if (old["task_id"], old["operation"], old["command"], old["timeout"]) != (task_id, operation, encoded, timeout):
                    raise ValueError("Request ID conflicts with an existing operation")
                return dict(old)
            if task["state"] in {"failed", "uncertain"} or (operation == "run" and task["state"] != "pending"):
                raise ValueError("Inspect existing effects and use retry explicitly before dispatch")
            head, clean = self.checkout()
            if operation == "verify" and not clean:
                raise ValueError("Commit changes and exclude .cache/ before commit-bound verification")
            # Random log names never interpret request IDs as paths.
            import uuid
            log = self.directory / (uuid.uuid4().hex + ".log")
            with self.db:
                self.db.execute("INSERT INTO attempts (request_id,task_id,operation,command,timeout,state,"
                                "commit_sha,started_at,log_path) VALUES (?,?,?,?,?,'running',?,?,?)",
                                (request_id, task_id, operation, encoded, timeout, head, now(), str(log)))
                self.db.execute("UPDATE tasks SET state='running' WHERE id=?", (task_id,))
            child = None
            exit_code, error = None, None
            try:
                with log.open("xb") as output:
                    os.chmod(log, 0o600)
                    child = subprocess.Popen(command, cwd=self.root, stdin=subprocess.DEVNULL,
                                             stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                    with self.db:
                        self.db.execute("UPDATE attempts SET child_pid=? WHERE request_id=?", (child.pid, request_id))
                    exit_code = child.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                error = "timeout"
            except KeyboardInterrupt:
                error = "interrupted"
            except OSError:
                error = "launch_or_log_failed"
            finally:
                if child is not None:
                    # Only this freshly spawned group is ours; never act on saved PIDs.
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
            end_head, end_clean = self.checkout()
            matches = clean and end_clean and head == end_head
            state = ("uncertain" if error else "failed" if exit_code != 0 else
                     "awaiting_verification" if operation == "run" else "verified" if matches else "uncertain")
            with self.db:
                self.db.execute("UPDATE attempts SET state=?, finished_at=?, exit_code=?, checkout_matches=?, error=? "
                                "WHERE request_id=?", (state, now(), exit_code, int(matches), error, request_id))
                self.db.execute("UPDATE tasks SET state=? WHERE id=?", (state, task_id))
            return dict(self.db.execute("SELECT * FROM attempts WHERE request_id=?", (request_id,)).fetchone())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="action", required=True)
    add = sub.add_parser("add")
    add.add_argument("task")
    add.add_argument("title")
    sub.add_parser("resume")
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
        elif args.action == "retry":
            result = store.retry(args.task, args.reason)
        else:
            result = store.execute(args.action, args.task, args.request_id, argv[separator + 1:], args.timeout)
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
