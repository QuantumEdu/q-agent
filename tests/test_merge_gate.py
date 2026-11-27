"""
Unit tests for tools/q-merge-gate/q_merge_gate.py
"""

import json
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


    def _commit_on_branch(self, branch, files):
        q_merge_gate.run_git(["checkout", "-b", branch], cwd=self.repo_dir)
        for rel, content in files.items():
            target = self.repo_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            q_merge_gate.run_git(["add", rel], cwd=self.repo_dir)
        q_merge_gate.run_git(["commit", "-m", f"feat: {branch}"], cwd=self.repo_dir)
        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=500, cwd=self.repo_dir)
        self.assertIsNone(err)
        return report

    def test_ddl_outside_migration_paths_requires_human_action(self):
        report = self._commit_on_branch("feat/ddl", {
            "app/storage.py": 'conn.execute("ALTER TABLE orders ADD COLUMN note TEXT")\n',
        })
        self.assertEqual(report["exit_code"], 8)
        self.assertEqual(report["content_findings"]["schema"], ["app/storage.py"])
        self.assertEqual(report["path_findings"]["schema"], [])

    def test_money_logic_in_neutral_path_requires_approval(self):
        report = self._commit_on_branch("feat/orders", {
            "app/services/orders.py": "total = Decimal(line.unit_price) * qty\n",
        })
        self.assertEqual(report["exit_code"], 7)
        self.assertIn("app/services/orders.py", report["findings"]["money"])

    def test_sales_and_cash_paths_are_money_domain(self):
        report = self._commit_on_branch("feat/sales", {
            "app/sale_service.py": "def close():\n    return None\n",
            "app/cash_sessions.py": "def open_shift():\n    return None\n",
        })
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["findings"]["money"], ["app/cash_sessions.py", "app/sale_service.py"])

    def test_author_and_tokenizer_paths_are_not_auth(self):
        report = self._commit_on_branch("docs/authors", {
            "AUTHORS.md": "Jane Doe\n",
            "nlp/tokenizer.py": "def split(text):\n    return text.split()\n",
        })
        self.assertEqual(report["exit_code"], 0, report)

    def test_authorization_paths_are_auth(self):
        report = self._commit_on_branch("feat/authz", {
            "app/authorization.py": "def can(user):\n    return True\n",
        })
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["findings"]["auth"], ["app/authorization.py"])

    def test_tests_and_docs_are_excluded_from_content_scan(self):
        report = self._commit_on_branch("test/fixtures", {
            "tests/test_storage.py": 'conn.execute("CREATE TABLE t (price NUMERIC)")\n',
            "docs/guide.md": "Run CREATE TABLE before setting the password.\n",
        })
        self.assertEqual(report["exit_code"], 0, report)

    def test_project_config_extends_patterns(self):
        (self.repo_dir / ".q-agent.json").write_text(json.dumps({
            "merge_gate": {"patterns": {"money": ["orden"]}, "content_patterns": {"auth": ["\\bpin_code\\b"]}}
        }), encoding="utf-8")
        report = self._commit_on_branch("feat/orden", {
            "app/orden_service.py": "def build():\n    return None\n",
            "app/kiosk.py": "pin_code = read()\n",
        })
        self.assertEqual(report["exit_code"], 7)
        self.assertEqual(report["findings"]["money"], ["app/orden_service.py"])
        self.assertEqual(report["findings"]["auth"], ["app/kiosk.py"])
        self.assertTrue(report["config"].endswith(".q-agent.json"))

    def test_replace_defaults_and_disable_content_scan(self):
        (self.repo_dir / ".q-agent.json").write_text(json.dumps({
            "merge_gate": {"replace_defaults": True, "content_scan": False, "max_loc": 1000}
        }), encoding="utf-8")
        report = self._commit_on_branch("feat/payments", {
            "payments/stripe_payment.py": "amount = Decimal('1.00')\n",
        })
        self.assertEqual(report["exit_code"], 0, report)
        self.assertFalse(report["content_scan"])
        self.assertEqual(report["max_loc_threshold"], 500)

    def test_invalid_config_regex_is_an_error(self):
        (self.repo_dir / ".q-agent.json").write_text(json.dumps({
            "merge_gate": {"patterns": {"auth": ["("]}}
        }), encoding="utf-8")
        report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", cwd=self.repo_dir)
        self.assertIsNone(report)
        self.assertIn("Invalid regex", err)

    def test_unknown_base_is_an_error(self):
        report, err = q_merge_gate.analyze_diff(base="does-not-exist", head="HEAD", cwd=self.repo_dir)
        self.assertIsNone(report)
        self.assertIn("failed", err)

    def test_parse_unified_diff_tracks_renames_and_deletions(self):
        diff = (
            "diff --git a/old.sql b/old.sql\n--- a/old.sql\n+++ /dev/null\n@@ -1 +0,0 @@\n-DROP TABLE x;\n"
            "diff --git a/a.py b/b.py\n--- a/a.py\n+++ b/b.py\n@@ -1 +1 @@\n-x = 1\n+x = 2\n"
        )
        self.assertEqual(q_merge_gate.parse_unified_diff(diff), {
            "old.sql": ["DROP TABLE x;"],
            "b.py": ["x = 1", "x = 2"],
        })


if __name__ == "__main__":
    unittest.main()
