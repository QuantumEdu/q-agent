"""Audit-gate regressions through real public CLIs and isolated project files."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools/q-audit-validator/validate_audit.py"
AGGREGATOR = ROOT / "tools/q-audit-aggregator/generate_report.py"
RUNNER = ROOT / "tools/q-audit-runner/run_audit.py"


class AuditGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.manifest = self.root / "manifest.yml"
        self.item_path = self.root / "audit/A01-check.md"
        self.item_path.parent.mkdir()
        self.manifest.write_text(
            'items:\n  - id: "A01"\n    slug: "check"\n    level: 0\n'
            '    category: "quality"\n    scope_patterns:\n      - "**/services/**"\n'
            '    output: "audit/A01-check.md"\n', encoding="utf-8",
        )

    def item(self, status="complete", severity="none", summary=None,
             violations="No violations detected.", ears="N/A", strategic=False):
        summary = summary or "Inspected the project source files and their runtime behavior."
        severity_line = f'severity: "{severity}"\n' if severity is not None else ""
        text = (f'---\nid: "A01"\nstatus: "{status}"\n{severity_line}---\n\n'
                f'## Summary\n\n{summary}\n\n## Violations\n\n{violations}\n\n'
                f'## Severity Justification\n\nVerified source behavior.\n\n## EARS Spec\n\n{ears}\n')
        if strategic:
            text = ('---\nstatus: "complete"\n---\n\n## Summary\n\nInspected source.\n'
                    '## Current Bottlenecks\n\nNone.\n## Proposed Architecture\n\nRetain.\n'
                    '## Expected Impact\n\nNo changes.\n')
        self.item_path.write_text(text, encoding="utf-8")

    def source(self):
        path = self.root / "services/billing.py"
        path.parent.mkdir(exist_ok=True)
        path.write_text("value = 1\nvalue += 1\n", encoding="utf-8")
        return path

    def cli(self, script=VALIDATOR, *extra, no_site=False):
        command = [sys.executable] + (["-S"] if no_site else [])
        command += [str(script), "--cwd", str(self.root), "--manifest", str(self.manifest),
                    "--level", "0"]
        if script == VALIDATOR:
            command += ["--mode", "manifest"]
        return subprocess.run(command + list(extra), capture_output=True, text=True, check=False)

    def rejected(self, message):
        result = self.cli()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(message, result.stdout)
        gaps = json.loads((self.root / "audit/AUDIT_GAPS.json").read_text())
        self.assertEqual(gaps["gaps"][0]["id"], "A01")

    def test_empty_scope_cannot_be_certified_clean(self):
        self.item()
        self.rejected("EMPTY SCOPE")

    def test_unassessed_requires_empty_scope_and_omitted_severity(self):
        self.item(status="not_assessed", severity=None)
        self.assertEqual(self.cli().returncode, 0)
        self.source()
        self.rejected("only allowed when")
        self.source().unlink()
        self.item(status="not_assessed", severity="high")
        self.rejected("omit severity")

    def test_real_widened_scope_evidence_is_accepted(self):
        (self.root / "app.py").write_text("value = 1\n", encoding="utf-8")
        self.item(summary="Inspected flat layout [OBSERVED: app.py#L1].")
        self.assertEqual(self.cli().returncode, 0)

    def test_fenced_example_cannot_certify_empty_scope(self):
        source = self.root / "app.py"
        source.write_text("value = 1\n", encoding="utf-8")
        self.item(violations="```markdown\n[OBSERVED: app.py#L1]\n```")
        before = {str(p): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.rejected("EMPTY SCOPE")
        self.assertEqual(before, {name: Path(name).read_bytes() for name in before})

    def test_invalid_and_malformed_observed_evidence_is_rejected(self):
        self.source()
        for citation in ("[OBSERVED: absent.py#L1]", "[OBSERVED: services/billing.py#L90]",
                         "[OBSERVED: services/billing.py]", "[observed: services/billing.py#L0]",
                         "[OBSERVED: services/billing.py#L1", "[OBSERVED: ../outside.py#L1]"):
            with self.subTest(citation=citation):
                self.item(severity="high", violations=citation, ears="THE SYSTEM SHALL validate.")
                self.rejected("INVALID EVIDENCE")

    def test_generated_audit_files_cannot_be_evidence(self):
        for citation in ("audit/A01-check.md", "alias.md"):
            with self.subTest(citation=citation):
                if citation == "alias.md":
                    (self.root / citation).symlink_to(self.item_path)
                self.item(summary=f"Inspected this generated result [OBSERVED: {citation}#L1].")
                self.rejected("INVALID EVIDENCE")

    def test_outside_symlink_does_not_supply_scope(self):
        outside = self.root.parent / (self.root.name + "-outside.py")
        outside.write_text("secret = 1\n", encoding="utf-8")
        self.addCleanup(outside.unlink)
        (self.root / "services").mkdir()
        (self.root / "services/linked.py").symlink_to(outside)
        self.item()
        self.rejected("EMPTY SCOPE")
        self.item(summary="Inspected linked source [OBSERVED: services/linked.py#L1].")
        self.rejected("INVALID EVIDENCE")

    def test_unfilled_template_and_fake_headings_are_rejected(self):
        self.source()
        template = (ROOT / "templates/audit-item.md").read_text()
        self.item_path.write_text(template.replace('status: "pending"', 'status: "complete"'))
        self.rejected("EMPTY SUMMARY")
        for replacement in ("Mention ## Violations inline", "```markdown\n## Violations\n```",
                            "## Violations impostor"):
            self.item()
            self.item_path.write_text(self.item_path.read_text().replace("## Violations", replacement))
            self.rejected("MISSING SECTION")

    def test_findings_need_evidence_and_ears(self):
        self.source()
        self.item(severity="high", violations="Something is wrong.", ears="TODO")
        self.rejected("UNSUPPORTED SEVERITY")
        self.assertIn("MISSING EARS", self.cli().stdout)
        self.item(severity="high", violations="[INFERRED] A realistic runtime risk.",
                  ears="THE SYSTEM SHALL validate input.")
        self.assertEqual(self.cli().returncode, 0)

    def test_empty_active_manifest_fails(self):
        self.manifest.write_text("items: []\n", encoding="utf-8")
        self.assertEqual(self.cli().returncode, 1)

    def test_fallback_parser_keeps_fields_with_their_item(self):
        self.source()
        self.item()
        self.manifest.write_text(
            "items:\n  - id: 'A01'\n    level: 0 # active\n    category: 'quality'\n"
            "    scope_patterns:\n      # a comment inside a list\n      - '**/services/**'\n"
            "    output: 'audit/A01-check.md'\n"
            "  - id: 'A02'\n    slug: 'second'\n    level: 1\n    output: 'audit/second.md'\n",
            encoding="utf-8",
        )
        result = self.cli(no_site=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_previous_valid_item_and_technical_cli_remain_supported(self):
        self.source()
        self.item()
        self.assertEqual(self.cli().returncode, 0)
        result = subprocess.run([sys.executable, str(VALIDATOR), "--cwd", str(ROOT),
                                 "--mode", "technical", "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
