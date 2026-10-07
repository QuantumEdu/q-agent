"""
Unit tests for tools/q-merge-gate/q_merge_gate.py
"""

import os
import sys
import tempfile
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
MERGE_GATE_DIR = ROOT_DIR / "tools" / "q-merge-gate"
if str(MERGE_GATE_DIR) not in sys.path:
    sys.path.insert(0, str(MERGE_GATE_DIR))

import q_merge_gate


class TestQMergeGate(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.test_dir.name)

        # Initialize git repo with main branch
        q_merge_gate.run_git(["init", "-b", "main"], cwd=self.repo_dir)
        q_merge_gate.run_git(["config", "user.name", "Test User"], cwd=self.repo_dir)
        q_merge_gate.run_git(["config", "user.email", "test@example.com"], cwd=self.repo_dir)

        # Create dummy file and initial commit
        base_file = self.repo_dir / "index.txt"
        base_file.write_text("initial content\n", encoding="utf-8")
        q_merge_gate.run_git(["add", "index.txt"], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", "init: base commit"], cwd=self.repo_dir)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_clean_slice_proceeds_exit_0(self):
        # Create a clean feature branch
        q_merge_gate.run_git(["checkout", "-b", "feat/clean"], cwd=self.repo_dir)
        feat_file = self.repo_dir / "service.txt"
        feat_file.write_text("clean service logic\n", encoding="utf-8")
        q_merge_gate.run_git(["add", "service.txt"], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", "feat: clean service"], cwd=self.repo_dir)

        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=500, cwd=self.repo_dir)
        self.assertIsNone(err)
        self.assertEqual(report["exit_code"], 0)
        self.assertEqual(report["status"], "PROCEED")

    def test_auth_domain_requires_human_approval_exit_7(self):
        q_merge_gate.run_git(["checkout", "-b", "feat/auth"], cwd=self.repo_dir)
        auth_file = self.repo_dir / "auth_handler.go"
        auth_file.write_text("jwt token verification\n", encoding="utf-8")
        q_merge_gate.run_git(["add", "auth_handler.go"], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", "feat: auth handler"], cwd=self.repo_dir)

        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=500, cwd=self.repo_dir)
        self.assertIsNone(err)
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["status"], "HUMAN_APPROVAL_REQUIRED")
        self.assertIn("auth_handler.go", report["findings"]["auth"])

    def test_money_domain_requires_human_approval_exit_7(self):
        q_merge_gate.run_git(["checkout", "-b", "feat/billing"], cwd=self.repo_dir)
        billing_file = self.repo_dir / "stripe_payment.py"
        billing_file.write_text("process payment\n", encoding="utf-8")
        q_merge_gate.run_git(["add", "stripe_payment.py"], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", "feat: billing stripe"], cwd=self.repo_dir)

        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=500, cwd=self.repo_dir)
        self.assertIsNone(err)
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["status"], "HUMAN_APPROVAL_REQUIRED")
        self.assertIn("stripe_payment.py", report["findings"]["money"])

    def test_schema_migration_requires_human_action_exit_8(self):
        q_merge_gate.run_git(["checkout", "-b", "feat/migration"], cwd=self.repo_dir)
        schema_file = self.repo_dir / "schema.sql"
        schema_file.write_text("CREATE TABLE users (id INT);\n", encoding="utf-8")
        q_merge_gate.run_git(["add", "schema.sql"], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", "feat: add schema table"], cwd=self.repo_dir)

        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=500, cwd=self.repo_dir)
        self.assertIsNone(err)
        self.assertEqual(report["exit_code"], 8)
        self.assertEqual(report["status"], "HUMAN_ACTION_REQUIRED")
        self.assertIn("schema.sql", report["findings"]["schema"])

    def test_loc_threshold_exceeded_exit_7(self):
        q_merge_gate.run_git(["checkout", "-b", "feat/huge"], cwd=self.repo_dir)
        huge_file = self.repo_dir / "huge.txt"
        huge_file.write_text("\n".join([f"line {i}" for i in range(100)]), encoding="utf-8")
        q_merge_gate.run_git(["add", "huge.txt"], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", "feat: huge diff"], cwd=self.repo_dir)

        # Set max_loc to 50
        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=50, cwd=self.repo_dir)
        self.assertIsNone(err)
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["status"], "HUMAN_APPROVAL_REQUIRED")


if __name__ == "__main__":
    unittest.main()
