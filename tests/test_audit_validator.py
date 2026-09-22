"""
Test suite for q-audit-validator manifest loading and validation logic.
"""

import importlib.util
import json
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
