"""Structural acceptance checks for consumed communication instructions, not runtime proof."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGACY = ("P04_propose.md", "P05_spec.md", "P06_design.md",
          "P07_tasks.md", "P08_apply_verify.md")
PRIMARY = ("P03_gate_metaorquestacion.md", "P04_odd_feature_log.md",
           "P06_terminal_evidence_gate.md", "P07_hygiene_and_blueprint.md")
POLICIES = ("SKILL.md", "references/attention-policy.md",
            "references/flight-recorder.md", "references/plans.md",
            "templates/task-log-template.md")


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class CommunicationPolicyTests(unittest.TestCase):
    def test_frozen_contract_vocabulary(self):
        contract = read("references/communication-contract.md")
        for term in ("emitter.kind", "executor", "orchestrator", "runtime_clock",
                     "timestamp_source", "measured", "estimated", "unavailable",
                     "null", "configured", "loaded", "invoked", "verified"):
            with self.subTest(term=term):
                self.assertIn(term, contract)

    def test_normative_crosswalk_has_all_stages_and_existing_primary_paths(self):
        guide = read("docs/communication-policy.md")
        rows = re.findall(r"^\| ([0-9]) \| (.+)$", guide, re.M)
        self.assertEqual([stage for stage, _ in rows], list("0123456789"))
        for stage, row in rows:
            with self.subTest(stage=stage):
                self.assertEqual(row.count("|"), 5)
                self.assertTrue(all(cell.strip() for cell in row.split("|")[:-1]))
        for path in re.findall(r"`(prompts/[^`]+\.md)`", guide):
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertIn("Step N is not a PN filename", guide)
        self.assertIn("Normative", guide)

    def test_consumers_link_canonical_contract(self):
        paths = POLICIES + tuple("prompts/" + p for p in PRIMARY)
        for path in paths:
            with self.subTest(path=path):
                self.assertIn("communication-contract.md", read(path))

    def test_routine_gates_record_without_redundant_chat(self):
        for name in PRIMARY[:2]:
            content = read("prompts/" + name)
            with self.subTest(prompt=name):
                for term in ("actionable_result", "blocking_decision", "hard_stop",
                             "status", "STOP", "record"):
                    self.assertIn(term, content)
                self.assertNotIn("Salida Obligatoria al Usuario", content)
                self.assertNotIn("Al crear la bitácora, notificar", content)

    def test_closure_is_checked_facts_with_limitations(self):
        closure = read("prompts/P07_hygiene_and_blueprint.md")
        for term in ("actionable_result", "limitaciones", "comprobados"):
            self.assertIn(term, closure)
        self.assertNotIn("Cero consumo de tokens", closure)

    def test_clock_actor_and_host_boundary_are_explicit(self):
        guide = read("docs/communication-policy.md")
        for term in ("[HH:mm:ss ±HH:mm] [emitter | workflow | phase]",
                     "host/tool clock", "time-unavailable", "timezone",
                     "executor", "orchestrator", "loaded", "CLI",
                     "provider-owned", "cannot intercept", "not native tool proof"):
            with self.subTest(term=term):
                self.assertIn(term, guide)

    def test_telemetry_states_reach_evidence_instructions(self):
        for path in ("references/flight-recorder.md", "templates/task-log-template.md",
                     "prompts/P06_terminal_evidence_gate.md"):
            with self.subTest(path=path):
                content = read(path)
                for term in ("measured", "estimated", "unavailable", "null",
                             "source", "basis"):
                    self.assertIn(term, content)

    def test_no_zero_usage_claims_in_touched_policy(self):
        paths = POLICIES + tuple("prompts/" + p for p in PRIMARY + LEGACY)
        pattern = r"(?i)(?:\b0\s+(?:LLM\s+)?tokens|cero (?:consumo de )?tokens|zero-token)"
        for path in paths:
            with self.subTest(path=path):
                self.assertNotRegex(read(path), pattern)

    def test_legacy_variants_remain_explicit_and_linked(self):
        for name in LEGACY:
            with self.subTest(prompt=name):
                content = read("prompts/" + name)
                self.assertIn("Compatibilidad", content)
                self.assertIn("../docs/communication-policy.md", content)
                self.assertIn("bitácora", content)
        guide = read("docs/communication-policy.md")
        for term in ("OpenSpec", "A-L", "execution-authority.md", "living log"):
            self.assertIn(term, guide)

    def test_preserve_version_size_and_previous_gate_invariants(self):
        skill = read("SKILL.md")
        self.assertLessEqual(len(skill.splitlines()), 200)
        self.assertIn("version: 2.14.1", skill.split("---", 2)[1])
        for name in PRIMARY + LEGACY:
            self.assertTrue(read("prompts/" + name).startswith("---\n"))
        self.assertIn("APPROVED", read("prompts/P06_terminal_evidence_gate.md"))
        self.assertIn("firma humana", skill)
        self.assertIn("Interaction mode changes pacing, never operation authority",
                      read("references/plans.md"))


if __name__ == "__main__":
    unittest.main()
