"""Configuration and instruction contracts; no live provider integration."""
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("q_checklist", ROOT / "tools/q-checklist/q_checklist.py")
checklist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checklist)


class ContextRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.template = json.loads((ROOT / "templates/q-agent.json").read_text(encoding="utf-8"))

    def test_optional_provider_defaults(self):
        context = self.template["context_retrieval"]
        self.assertEqual(context["mode"], "on-demand")
        self.assertEqual(context["project_id"], None)
        self.assertEqual(context["local_sources"], ["project-files"])
        for name in ("gbrain", "engram", "skillvault"):
            provider = context["providers"][name]
            self.assertFalse(provider["enabled"])
            self.assertEqual(provider["authorization"], "none")
            self.assertEqual(provider["availability"], "unknown")
            self.assertEqual(provider["capabilities"], [])
        self.assertTrue(context["require_project_scope"])
        self.assertFalse(context["allow_cross_project"])
        self.assertEqual(context["budget"]["max_results"], 3)
        self.assertEqual(context["budget"]["max_chars"], 6000)
        self.assertEqual(context["budget"]["max_tokens_estimate"], 1500)
        self.assertEqual(context["persistence"], {"local_first": True, "external_write": False, "sqlite_backup": False})

    def test_generated_configuration_matches_template(self):
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        with tempfile.TemporaryDirectory() as directory:
            checklist.generate_artifacts(Path(directory), "sample-project", selections)
            generated = json.loads((Path(directory) / ".q-agent.json").read_text(encoding="utf-8"))
        self.assertEqual(generated["context_retrieval"], self.template["context_retrieval"])
        self.assertFalse(generated["integrations"]["gbrain_mcp"])

    def test_authority_defaults_and_generated_parity(self):
        authority = self.template["execution_authority"]
        self.assertEqual(authority, {
            "evidence": None, "operations": [], "delegated_decisions": [],
            "expires_at": None, "revoked": False,
        })
        for provider in self.template["context_retrieval"]["providers"].values():
            self.assertEqual(provider["scope_class"], "private-project")
            self.assertIsNone(provider["authorization_evidence"])
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        with tempfile.TemporaryDirectory() as directory:
            checklist.generate_artifacts(Path(directory), "sample-project", selections)
            generated = json.loads((Path(directory) / ".q-agent.json").read_text(encoding="utf-8"))
        self.assertEqual(generated["execution_authority"], authority)

    def test_typed_activation_example_matches_contract(self):
        contract = (ROOT / "references/context-retrieval.md").read_text(encoding="utf-8")
        example = json.loads(re.search(r"```json\n(.*?)\n```", contract, re.S).group(1))
        activated = example["context_retrieval"]["providers"]["gbrain"]
        defaults = self.template["context_retrieval"]["providers"]["gbrain"]
        self.assertEqual(set(activated), set(defaults))
        self.assertTrue(activated["enabled"])
        self.assertEqual(activated["availability"], "available")
        self.assertEqual(activated["authorization"], "read")
        self.assertEqual(activated["capabilities"], ["search", "read"])
        self.assertEqual(activated["project_scope"], "sample-project")
        self.assertEqual(activated["scope_class"], "private-project")
        self.assertIn("source_ref", activated["authorization_evidence"])
        self.assertEqual(activated["authorization_evidence"]["operations"], ["search", "read"])
        for field in ("expires_at", "revoked", "destination", "credential_session"):
            self.assertIn(field, activated["authorization_evidence"])

    def test_entrypoint_authority_and_no_unconditional_probing(self):
        for path in ("SKILL.md", "README.md", "references/plans.md",
                     "prompts/P03_gate_metaorquestacion.md", "skills/q-deliberate/SKILL.md"):
            self.assertIn("execution-authority.md", (ROOT / path).read_text(encoding="utf-8"))
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertNotIn("gh auth status", skill)
        self.assertNotIn("Presentar y esperar respuesta del usuario (no continuar sin respuesta):", skill)
        p03 = (ROOT / "prompts/P03_gate_metaorquestacion.md").read_text(encoding="utf-8")
        self.assertNotIn("vincular el proyecto con `mem_current_project` y guardar el estado", p03)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("used as context for all subsequent steps", readme)
        self.assertNotIn("End-to-end execution without prompts", readme)
        self.assertNotIn("Mandatory human-in-the-loop stopping gates", readme)
        retrieval = (ROOT / "references/context-retrieval.md").read_text(encoding="utf-8")
        self.assertNotIn("Cross-project research requires explicit scope approval", retrieval)

    def test_source_classes_and_initial_authority_contract(self):
        retrieval = (ROOT / "references/context-retrieval.md").read_text(encoding="utf-8")
        authority = (ROOT / "references/execution-authority.md").read_text(encoding="utf-8")
        for term in ("public-web", "general-reference", "private-project", "necessary",
                     "revoked", "expired", "disabled"):
            self.assertIn(term, retrieval)
        for term in ("human", "delegated_decisions", "unresolved", "autonomous",
                     "research", "installation", "deploy", "merge", "revoked", "expired"):
            self.assertIn(term, authority)

    def test_retrieval_contract_and_entrypoints(self):
        contract = (ROOT / "references/context-retrieval.md").read_text(encoding="utf-8")
        for term in ("configured", "available", "authorized", "aggregate", "No query", "legacy", "untrusted", "HTML"):
            self.assertIn(term, contract)
        for path in ("SKILL.md", "skills/q-gbrain-assistant/SKILL.md", "skills/q-session-wrap/SKILL.md", "README.md"):
            self.assertIn("context-retrieval.md", (ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
