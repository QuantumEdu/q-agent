"""Read-only dashboard checks against a real ledger and HTTP server."""
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/q-cockpit"))
import q_cockpit_plus as cockpit


class LocalDashboardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "project"
        self.root.mkdir()
        for args in (["init", "-q"], ["config", "user.name", "Test"],
                     ["config", "user.email", "test@example.invalid"]):
            self.git(*args)
        (self.root / ".gitignore").write_text(".cache/\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")
        handler = type("DashboardHandler", (cockpit.EnhancedHandler,), {})
        handler.project_root = self.root
        handler.session_manager = cockpit.EnhancedSessionManager(Path(self.temp.name) / "sessions")
        handler.active_session_dir = None
        handler.snapshot_worker = cockpit.ProjectSnapshotWorker(cockpit.legacy.ProjectScanner)
        self.addCleanup(handler.snapshot_worker.close)
        self.server = cockpit.legacy.ThreadedTCPServer(("127.0.0.1", 0), handler)
        self.addCleanup(self.server.server_close)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.shutdown)

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

    def cli(self, *args):
        return json.loads(subprocess.check_output(
            [sys.executable, str(ROOT / "tools/q-tasks/q_tasks.py"), "--project", str(self.root), *args], text=True))

    def get(self, path="/api/status"):
        with urllib.request.urlopen(f"http://127.0.0.1:{self.server.server_address[1]}{path}") as response:
            return json.load(response)

    def test_absent_ledger_is_not_created_by_status(self):
        self.assertEqual(self.get()["local_execution"]["status"], "absent")
        self.assertFalse((self.root / ".cache").exists())

    def test_live_ledger_refreshes_without_markdown_changes_and_hides_private_fields(self):
        self.cli("add", "T1", "<script>private title</script>")
        proof = self.cli("verify", "T1", "--request-id", "v1", "--", sys.executable, "-c", "pass")
        first = self.get()["local_execution"]
        self.assertEqual(first["tasks"][0]["state"], "verified")
        self.assertEqual(first["tasks"][0]["commit_sha"], proof["commit_sha"])
        for key in ("command", "log_path", "retry_reason", "child_pid"):
            self.assertNotIn(key, first["tasks"][0])
        self.cli("add", "T2", "New pending task")
        self.assertEqual(self.get()["local_execution"]["total"], 2)
        self.git("commit", "--allow-empty", "-qm", "next")
        task = next(task for task in self.get()["local_execution"]["tasks"] if task["id"] == "T1")
        self.assertTrue(task["evidence_stale"])

    def test_abandoned_runner_is_projected_uncertain_without_mutating_database(self):
        self.cli("add", "T1", "Feature")
        database = self.root / ".cache/q-agent-tasks/tasks.sqlite3"
        with sqlite3.connect(database) as db:
            db.execute("UPDATE tasks SET state='running'")
        self.assertEqual(self.get()["local_execution"]["tasks"][0]["state"], "uncertain")
        with sqlite3.connect(database) as db:
            self.assertEqual(db.execute("SELECT state FROM tasks").fetchone()[0], "running")

    def test_corrupt_ledger_does_not_hide_workflow_status(self):
        self.cli("add", "T1", "Feature")
        database = self.root / ".cache/q-agent-tasks/tasks.sqlite3"
        database.write_bytes(b"not a SQLite database")
        status = self.get()
        self.assertEqual(status["local_execution"]["status"], "unavailable")
        self.assertIn("project", status)
        self.assertNotIn("error", status["local_execution"])


if __name__ == "__main__":
    unittest.main()
