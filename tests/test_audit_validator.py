"""
Test suite for q-audit-validator manifest loading and validation logic.
"""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = ROOT_DIR / "tools" / "q-audit-validator" / "validate_audit.py"

# Import validate_audit dynamically
spec = importlib.util.spec_from_file_location("validate_audit", str(VALIDATOR_PATH))
validate_audit = importlib.util.module_from_spec(spec)
sys.modules["validate_audit"] = validate_audit
spec.loader.exec_module(validate_audit)


class TestAuditValidator(unittest.TestCase):
    def test_load_canonical_manifest(self):
        manifest_path = ROOT_DIR / "references" / "audit-manifest.yml"
        self.assertTrue(manifest_path.exists())

        manifest = validate_audit.load_manifest(manifest_path)
        self.assertIn("items", manifest)
        items = manifest["items"]
        self.assertGreater(len(items), 0)

        # Check item structure
        item0 = items[0]
        self.assertEqual(item0["id"], "A01")
        self.assertEqual(item0["level"], 0)
        self.assertEqual(item0.get("wave"), 2)
        self.assertIn("output", item0)
        self.assertIn("required_sections", item0)

        # Check all 17 items have valid wave
        for item in items:
            self.assertIn("wave", item)
            if item["id"].startswith("A"):
                self.assertIn(item["wave"], {1, 2, 3, 4}, f"Item {item['id']} has invalid wave {item['wave']}")
            elif item["id"].startswith("E"):
                self.assertEqual(item["wave"], 5, f"Strategic item {item['id']} should have wave 5")

    def test_validate_manifest_mode_with_missing_files(self):
        manifest_path = ROOT_DIR / "references" / "audit-manifest.yml"
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            code = validate_audit.validate_manifest(tmp_path, manifest_path, level=0)
            self.assertEqual(code, 1, "Validation should fail with exit code 1 when files are missing")

            gaps_file = tmp_path / "audit" / "AUDIT_GAPS.json"
            self.assertTrue(gaps_file.exists(), "AUDIT_GAPS.json must be generated upon validation failure")

            with open(gaps_file, "r", encoding="utf-8") as f:
                gaps = json.load(f)
            self.assertIn("gaps", gaps)
            failed_ids = {g["id"] for g in gaps["gaps"]}
            self.assertEqual(failed_ids, {"A01", "A02", "A03", "A04", "A05"})

    def test_audit_technical_contracts_on_current_repo(self):
        report = validate_audit.audit_technical_contracts(ROOT_DIR)
        self.assertIn("contracts", report)
        self.assertIn("summary", report)

        contracts = report["contracts"]
        self.assertIn("A03_github_ci_integrity", contracts)
        self.assertIn("A17_disaster_recovery", contracts)
        self.assertIn("A14_observability_telemetry", contracts)
        self.assertIn("A06_api_contracts", contracts)

        # In current repo, critical failures must be zero
        self.assertEqual(report["summary"]["critical"], 0)

        # A03 checks must pass in current repo
        a03_checks = {c["id"]: c["status"] for c in contracts["A03_github_ci_integrity"]["checks"]}
        self.assertEqual(a03_checks.get("A03-GITIGNORE"), "PASS")
        self.assertEqual(a03_checks.get("A03-WORKFLOWS"), "PASS")
        self.assertEqual(a03_checks.get("A03-TRIGGERS"), "PASS")
        self.assertEqual(a03_checks.get("A03-TEST-LINT"), "PASS")
        self.assertEqual(a03_checks.get("A03-DEPENDABOT"), "PASS")

    def test_audit_technical_contracts_missing_critical(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            report = validate_audit.audit_technical_contracts(tmp_path)
            self.assertGreater(report["summary"]["critical"], 0)

            # validate_technical should return 1 on critical failure
            exit_code = validate_audit.validate_technical(tmp_path)
            self.assertEqual(exit_code, 1)

    def test_audit_technical_contracts_full_compliance(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            # 1. .gitignore
            (tmp_path / ".gitignore").write_text("node_modules/\n.env\n", encoding="utf-8")

            # 2. CI workflows
            wf_dir = tmp_path / ".github" / "workflows"
            wf_dir.mkdir(parents=True)
            (wf_dir / "ci.yml").write_text(
                "name: CI\non:\n  push:\n  pull_request:\njobs:\n  test:\n    steps:\n      - run: npm test\n      - run: ./deploy.sh --rollback\n",
                encoding="utf-8",
            )

            # 3. Dependabot
            (tmp_path / ".github" / "dependabot.yml").write_text("version: 2\n", encoding="utf-8")

            # 4. Disaster recovery (backup script + healthcheck)
            scripts_dir = tmp_path / "scripts"
            scripts_dir.mkdir()
            (scripts_dir / "backup.sh").write_text("#!/bin/bash\npg_dump db > backup.sql\n", encoding="utf-8")
            (tmp_path / "Dockerfile").write_text("FROM alpine\nHEALTHCHECK CMD curl -f http://localhost/health\n", encoding="utf-8")

            # 5. Observability (logging + correlation)
            (tmp_path / "package.json").write_text(
                json.dumps({"dependencies": {"winston": "^3.0.0"}}),
                encoding="utf-8",
            )
            src_dir = tmp_path / "src"
            src_dir.mkdir()
            (src_dir / "middleware.js").write_text("const reqId = req.headers['x-request-id'];\n", encoding="utf-8")

            # 6. API contracts (OpenAPI + routes)
            (tmp_path / "openapi.yaml").write_text("openapi: 3.0.0\ninfo:\n  title: API\n", encoding="utf-8")
            (tmp_path / "routes").mkdir()
            (tmp_path / "routes" / "index.js").write_text("module.exports = {};\n", encoding="utf-8")

            report = validate_audit.audit_technical_contracts(tmp_path)
            self.assertEqual(report["summary"]["critical"], 0)
            self.assertEqual(report["summary"]["warnings"], 0)
            self.assertEqual(report["summary"]["passed"], report["summary"]["total"])

            # Strict mode should pass with 0 exit code
            code = validate_audit.validate_technical(tmp_path, strict=True)
            self.assertEqual(code, 0)

    def test_technical_mode_cli_invocation(self):
        res = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), "--mode", "technical", "--cwd", str(ROOT_DIR)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"validate_audit failed: {res.stderr}")
        self.assertIn("TECHNICAL CONTRACTS AUDIT REPORT", res.stdout)
        self.assertIn("Result: PASSED", res.stdout)

    def test_technical_mode_cli_json_output(self):
        res = subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), "--mode", "technical", "--cwd", str(ROOT_DIR), "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"validate_audit --json failed: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("contracts", data)
        self.assertIn("summary", data)
        self.assertEqual(data["summary"]["critical"], 0)
        self.assertEqual(data["summary"]["verdict"], "PASSED")

    def test_node_contracts_script_invocation(self):
        script_path = ROOT_DIR / "scripts" / "audit_api_contracts.js"
        self.assertTrue(script_path.exists(), "scripts/audit_api_contracts.js must exist")

        node_bin = shutil.which("node")
        if not node_bin:
            self.skipTest("node binary not found on PATH")

        # Test terminal report
        res = subprocess.run(
            [node_bin, str(script_path), "--cwd", str(ROOT_DIR)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"audit_api_contracts.js failed: {res.stderr}")
        self.assertIn("TECHNICAL CONTRACTS AUDIT REPORT", res.stdout)
        self.assertIn("Result: PASSED", res.stdout)

        # Test JSON report
        res_json = subprocess.run(
            [node_bin, str(script_path), "--cwd", str(ROOT_DIR), "--json"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res_json.returncode, 0, f"audit_api_contracts.js --json failed: {res_json.stderr}")
        data = json.loads(res_json.stdout)
        self.assertIn("contracts", data)
        self.assertEqual(data["summary"]["critical"], 0)
        self.assertEqual(data["summary"]["verdict"], "PASSED")


if __name__ == "__main__":
    unittest.main()
