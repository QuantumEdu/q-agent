"""Public-CLI coverage and structural retry-policy regressions."""

import json
import importlib.util
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools/q-audit-validator/validate_audit.py"
MANIFEST = ROOT / "references/audit-manifest.yml"


class AuditCoverageTests(unittest.TestCase):
    def test_fallback_membership_preserves_higher_levels(self):
        spec = importlib.util.spec_from_file_location("coverage_validator", VALIDATOR)
        validator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(validator)
        items = validator.parse_manifest_items(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(items), 22)
        for level, count in ((1, 13), (2, 17)):
            actual = {item["id"] for item in items
                      if item["id"].startswith("A") and item["level"] <= level}
            self.assertEqual(actual, {f"A{i:02}" for i in range(1, count + 1)})

    def test_default_audit_requires_injection_item(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = subprocess.run([sys.executable, str(VALIDATOR), "--cwd", str(root),
                                     "--mode", "manifest", "--level", "0"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            gaps = json.loads((root / "audit/AUDIT_GAPS.json").read_text())
            self.assertEqual({item["id"] for item in gaps["gaps"]},
                             {"A01", "A02", "A03", "A04", "A05", "A09"})

    def test_non_mvc_security_sources_are_in_scope(self):
        content = MANIFEST.read_text(encoding="utf-8")
        names = {
            "A02": ("prod.env", "settings.ini", "settings.cfg", "app.toml", "app.properties",
                    "settings.py", "config.py", "config/key.txt", "tools/run.sh", "run.bat", "run.ps1"),
            "A09": ("schema.sql", "db/client.py", "database/client.ts", "dao/storage.py",
                    "api/client.ts", "handlers/get.ts", "userrepository.java", "users_repo.ts",
                    "query.ts", "store.py", "db.py", "sql.py", "views.py"),
        }
        cases = [(item, name, 0) for item, paths in names.items() for name in paths]
        cases += [("A02", "arbitrary.py", 1), ("A09", "arbitrary.py", 1)]
        for item_id, source, expected in cases:
            with self.subTest(item=item_id, source=source), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "project"
                root.mkdir()
                block = next(block for block in re.split(r"(?m)^  - id: ", content)[1:]
                             if block.startswith(f'"{item_id}"'))
                # Keep harness YAML outside the audited scope (A02 scans YAML).
                manifest = Path(directory) / "manifest.yml"
                manifest.write_text("items:\n  - id: " + block, encoding="utf-8")
                output = re.search(r'output: "([^"]+)"', block).group(1)
                path = root / source
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("value = 1\n", encoding="utf-8")
                before = path.read_bytes()
                item_path = root / output
                item_path.parent.mkdir(parents=True)
                item_path.write_text(
                    '---\nstatus: "complete"\nseverity: "none"\n---\n'
                    '## Summary\nInspected the configuration or data access source.\n'
                    '## Violations\nNo violations.\n## Severity Justification\nVerified.\n'
                    '## EARS Spec\nN/A\n', encoding="utf-8",
                )
                result = subprocess.run([sys.executable, "-S", str(VALIDATOR), "--cwd", str(root),
                                         "--manifest", str(manifest), "--mode", "manifest", "--level", "1"],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(path.read_bytes(), before)
                if expected:
                    self.assertIn("EMPTY SCOPE", result.stdout)

    def test_workflow_and_reference_bound_correction_passes(self):
        for path in ("workflows/plan-c-audit.md", "references/plans.md"):
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertIn("máximo 2 pasadas de corrección por ítem", text)
                self.assertIn("AUDIT_GAPS.json", text)
                self.assertNotIn("ESTRICTAMENTE PROHIBIDO** interactuar con el usuario", text)
        self.assertIn("[6 ítems: A01–A05 y A09]", (ROOT / "workflows/plan-c-audit.md").read_text())


if __name__ == "__main__":
    unittest.main()
