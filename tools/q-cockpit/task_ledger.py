"""Read-only, bounded task projection; never dispatch or recover from HTTP GET."""
from contextlib import closing
import fcntl
from pathlib import Path
import sqlite3
import subprocess


def ledger_snapshot(project: Path, limit: int = 200) -> dict:
    root = Path(project).resolve()
    directory = root / ".cache/q-agent-tasks"
    database = directory / "tasks.sqlite3"
    empty = {"status": "absent", "tasks": [], "total": 0, "truncated": False}
    if not database.exists():
        return empty
    try:
        if not database.resolve().is_relative_to(root):
            raise ValueError("Ledger escapes project")
        active = False
        lock = directory / "runner.lock"
        if lock.exists():
            with lock.open("r") as handle:
                try:
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    fcntl.flock(handle, fcntl.LOCK_UN)
                except BlockingIOError:
                    active = True
        def git(*args):
            return subprocess.check_output(["git", "-C", str(root), *args], text=True,
                                           stderr=subprocess.DEVNULL, timeout=3).strip()
        head = git("rev-parse", "HEAD")
        clean = not git("status", "--porcelain", "--untracked-files=all")
        with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=.2)) as db:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA query_only=ON")
            db.execute("BEGIN")
            total = db.execute("SELECT count(*) FROM tasks").fetchone()[0]
            rows = db.execute("""SELECT t.id, t.title, t.state, a.commit_sha, a.exit_code,
                a.started_at, a.finished_at FROM tasks t LEFT JOIN attempts a ON a.rowid =
                (SELECT max(rowid) FROM attempts WHERE task_id=t.id)
                ORDER BY t.rowid DESC LIMIT ?""", (limit,)).fetchall()
        tasks = []
        for row in rows:
            task = dict(row)
            task["recorded_state"] = task["state"]
            if task["state"] == "running" and not active:
                task["state"] = "uncertain"
            task["evidence_stale"] = task["state"] == "verified" and (not clean or task["commit_sha"] != head)
            tasks.append(task)
        return {"status": "available", "tasks": tasks, "total": total,
                "truncated": total > limit, "runner_active": active}
    except (OSError, ValueError, sqlite3.Error, subprocess.SubprocessError):
        return {**empty, "status": "unavailable"}
