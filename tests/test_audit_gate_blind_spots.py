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
        result = self.cli(AGGREGATOR, no_site=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_previous_valid_item_and_technical_cli_remain_supported(self):
        self.source()
        self.item()
        self.assertEqual(self.cli().returncode, 0)
        result = subprocess.run([sys.executable, str(VALIDATOR), "--cwd", str(ROOT),
                                 "--mode", "technical", "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def report(self):
        return (self.root / "audit/AUDIT_REPORT.md").read_text(encoding="utf-8")

    def test_aggregation_missing_invalid_and_pending_items_are_incomplete(self):
        cases = (None, {"severity": "unexpected"}, {"status": "pending"},
                 {"status": "not_assessed", "severity": None},
                 {"status": "not_assessed", "severity": "high"})
        for options in cases:
            with self.subTest(options=options):
                if options is not None:
                    self.item(**options)
                result = self.cli(AGGREGATOR)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("**Overall Verdict:** `INCOMPLETE`", self.report())
                gaps = json.loads((self.root / "audit/AUDIT_GAPS.json").read_text())
                self.assertEqual(gaps["blocked_defect_items"][0]["id"], "A01")

    def test_aggregation_outputs_version_root_opt_in_and_gap_recovery(self):
        self.item(status="pending")
        self.assertEqual(self.cli(AGGREGATOR).returncode, 1)
        self.item()
        self.assertEqual(self.cli(AGGREGATOR).returncode, 0)
        version = json.loads((ROOT / "skill.json").read_text())["version"]
        self.assertIn(f"q-agent v{version}", self.report())
        self.assertFalse((self.root / "PLAN_DE_MEJORA.md").exists())
        self.assertFalse((self.root / "audit/AUDIT_GAPS.json").exists())
        self.assertEqual(self.cli(AGGREGATOR, "--root-copies").returncode, 0)
        self.assertEqual((self.root / "PLAN_DE_MEJORA.md").read_bytes(),
                         (self.root / "audit/PLAN_DE_MEJORA.md").read_bytes())

    def test_aggregation_preserves_severity_verdicts(self):
        for severity, verdict, code in (("none", "PASS", 0), ("low", "PASS WITH WARNINGS", 0),
                                        ("medium", "CONDITIONAL", 1), ("high", "BLOCKED", 1)):
            with self.subTest(severity=severity):
                self.item(severity=severity)
                result = self.cli(AGGREGATOR, no_site=True)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                self.assertIn(f"**Overall Verdict:** `{verdict}`", self.report())

    def test_optional_unassessed_rejects_explicit_unknown_severity(self):
        self.manifest.write_text(
            'items:\n  - id: "A01"\n    slug: "optional"\n    level: 1\n'
            '    category: "quality"\n    output: "audit/A01-check.md"\n'
            '  - id: "A02"\n    slug: "assessed"\n    level: 0\n'
            '    category: "quality"\n    output: "audit/A02-check.md"\n', encoding="utf-8",
        )
        self.item()
        assessed = self.root / "audit/A02-check.md"
        assessed.write_bytes(self.item_path.read_bytes())
        for severity, code in ((None, 0), ("unknown", 1)):
            with self.subTest(severity=severity):
                self.item(status="not_assessed", severity=severity)
                inputs = [self.manifest, self.item_path, assessed]
                before = {path: path.read_bytes() for path in inputs}
                result = self.cli(AGGREGATOR, "--level", "1", no_site=True)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                self.assertEqual(result.stderr, "")
                self.assertEqual(before, {path: path.read_bytes() for path in inputs})
                if code:
                    self.assertIn("**Overall Verdict:** `INCOMPLETE`", self.report())
                    gaps = json.loads((self.root / "audit/AUDIT_GAPS.json").read_text())
                    self.assertIn("A01", [item["id"] for item in gaps["blocked_defect_items"]])

    def test_empty_manifest_fails_aggregation(self):
        self.manifest.write_text("items: []\n", encoding="utf-8")
        self.assertEqual(self.cli(AGGREGATOR).returncode, 1)

    def test_runner_uses_verdict_header_not_conditional_word_in_body(self):
        self.item(status="not_assessed", severity=None,
                  summary="No matching source exists; CONDITIONAL is example wording only.")
        result = self.cli(RUNNER)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        state = json.loads((self.root / "audit/AUDIT_RUN_STATE.json").read_text())
        self.assertEqual(state["state"], "blocked")
        self.assertFalse(state["conditional"])

    def test_real_runner_preserves_pass_conditional_and_blocked(self):
        self.source()
        for severity, code, expected in (("none", 0, "aggregated"),
                                         ("medium", 0, "aggregated"), ("high", 1, "blocked")):
            with self.subTest(severity=severity):
                self.item(severity=severity, violations="[OBSERVED: services/billing.py#L1] risk",
                          ears="THE SYSTEM SHALL validate input.")
                result = self.cli(RUNNER)
                self.assertEqual(result.returncode, code, result.stdout + result.stderr)
                state = json.loads((self.root / "audit/AUDIT_RUN_STATE.json").read_text())
                self.assertEqual(state["state"], expected)
                self.assertEqual(state["conditional"], severity == "medium")


if __name__ == "__main__":
    unittest.main()
