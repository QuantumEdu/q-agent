"""Real Git/CLI tests for durable local work, without inference or mocks."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

CLI = Path(__file__).resolve().parents[1] / "tools/q-tasks/q_tasks.py"


class TaskRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for args in (["init", "-q"], ["config", "user.name", "Test"],
                     ["config", "user.email", "test@example.invalid"]):
            self.git(*args)
        (self.root / ".gitignore").write_text(".cache/\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True).strip()

    def cli(self, *args, code=0):
        result = subprocess.run([sys.executable, str(CLI), "--project", str(self.root), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, code, result.stderr + result.stdout)
        return json.loads(result.stdout)

    def test_verification_is_bound_to_commit_and_duplicate_does_not_run_again(self):
        self.cli("add", "T1", "Local feature")
        check = [sys.executable, "-c", "from pathlib import Path; p=Path('.cache/count'); p.write_text(p.read_text()+'x' if p.exists() else 'x')"]
        proof = self.cli("verify", "T1", "--request-id", "v1", "--", *check)
        self.assertEqual(proof["state"], "verified")
        self.assertEqual(proof["commit_sha"], self.git("rev-parse", "HEAD"))
        self.assertEqual(proof["exit_code"], 0)
        self.cli("verify", "T1", "--request-id", "v1", "--", *check)
        self.assertEqual((self.root / ".cache/count").read_text(), "x")
        self.cli("verify", "T1", "--request-id", "v1", "--", "other", code=2)
        self.git("commit", "--allow-empty", "-qm", "later")
        task = self.cli("resume")["tasks"][0]
        self.assertTrue(task["evidence_stale"])
        self.assertEqual(task["next_action"], "verify_current_checkout")

    def test_dirty_checkout_and_changes_during_verification_cannot_pass(self):
        self.cli("add", "T1", "Feature")
        (self.root / "untracked").write_text("work")
        self.cli("verify", "T1", "--request-id", "dirty", "--", sys.executable, "-c", "pass", code=2)
        (self.root / "untracked").unlink()
        result = self.cli("verify", "T1", "--request-id", "changed", "--", sys.executable,
                          "-c", "from pathlib import Path; Path('changed').write_text('x')", code=1)
        self.assertEqual(result["state"], "uncertain")
        self.assertFalse(result["checkout_matches"])

    def test_failed_work_is_not_verification_and_requires_explicit_retry(self):
        self.cli("add", "T1", "Feature")
        self.cli("run", "T1", "--request-id", "r1", "--", sys.executable, "-c", "raise SystemExit(4)", code=1)
        self.assertEqual(self.cli("resume")["tasks"][0]["state"], "failed")
        self.cli("run", "T1", "--request-id", "r2", "--", sys.executable, "-c", "pass", code=2)
        self.cli("retry", "T1", "--reason", "Inspected the failed command; retry is authorized")
        result = self.cli("run", "T1", "--request-id", "r2", "--", sys.executable, "-c", "pass")
        self.assertEqual(result["state"], "awaiting_verification")
        self.assertEqual(self.cli("history", "T1")["attempts"][0]["exit_code"], 4)

    def test_killed_runner_is_uncertain_and_resume_never_replays_work(self):
        self.cli("add", "T1", "Feature")
        marker = self.root / ".cache/started"
        command = [sys.executable, "-c", "from pathlib import Path; import time; Path('.cache/started').write_text('x'); time.sleep(30)"]
        runner = subprocess.Popen([sys.executable, str(CLI), "--project", str(self.root),
                                   "run", "T1", "--request-id", "crash", "--", *command],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            deadline = time.monotonic() + 5
            while not marker.exists() and runner.poll() is None and time.monotonic() < deadline:
                time.sleep(.02)
            self.assertTrue(marker.exists())
            self.assertEqual(self.cli("resume")["tasks"][0]["state"], "running")
            self.cli("run", "T1", "--request-id", "blocked", "--", *command, code=2)
            runner.kill()
            runner.wait(timeout=5)
            task = self.cli("resume")["tasks"][0]
            self.assertEqual(task["state"], "uncertain")
            self.assertEqual(task["next_action"], "inspect_effects_before_retry")
            self.cli("run", "T1", "--request-id", "crash", "--", *command, code=1)
            self.assertEqual(marker.read_text(), "x")
        finally:
            if runner.poll() is None:
                runner.kill()
                runner.wait()
            history = self.cli("history", "T1")["attempts"]
            if history and history[0].get("child_pid"):
                try:
                    os.killpg(history[0]["child_pid"], signal.SIGKILL)
                except ProcessLookupError:
                    pass

    def test_timeout_records_uncertainty(self):
        self.cli("add", "T1", "Feature")
        result = self.cli("run", "T1", "--request-id", "timeout", "--timeout", "0.1", "--",
                          sys.executable, "-c", "import time; time.sleep(20)", code=1)
        self.assertEqual(result["state"], "uncertain")
        self.assertEqual(result["error"], "timeout")

    def test_invalid_timeout_does_not_dispatch_and_failed_verification_keeps_exit(self):
        self.cli("add", "T1", "Feature")
        for timeout in ("0", "-1", "nan", "inf", "901"):
            self.cli("run", "T1", "--request-id", "bad", "--timeout", timeout, "--",
                     sys.executable, "-c", "raise SystemExit(99)", code=2)
        self.assertEqual(self.cli("history", "T1")["attempts"], [])
        proof = self.cli("verify", "T1", "--request-id", "fail", "--", sys.executable,
                         "-c", "raise SystemExit(3)", code=1)
        self.assertEqual(proof["state"], "failed")
        self.assertEqual(proof["exit_code"], 3)

    def test_launcher_targets_project_and_repeated_add_preserves_title(self):
        launcher = CLI.parents[2] / "bin/q-agent"
        for args in (["task", "--project", str(self.root), "add", "T1", "Feature"],
                     ["resume", "--project", str(self.root)]):
            result = subprocess.run(["bash", str(launcher), *args], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout))
        self.cli("add", "T1", "Feature")
        self.cli("add", "T1", "Conflicting title", code=2)


if __name__ == "__main__":
    unittest.main()
