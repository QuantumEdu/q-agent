"""Configuration and instruction contracts; no live provider integration."""
import importlib.util
import json
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

    def test_retrieval_contract_and_entrypoints(self):
        contract = (ROOT / "references/context-retrieval.md").read_text(encoding="utf-8")
        for term in ("configured", "available", "authorized", "aggregate", "No query", "legacy", "untrusted", "HTML"):
            self.assertIn(term, contract)
        for path in ("SKILL.md", "skills/q-gbrain-assistant/SKILL.md", "skills/q-session-wrap/SKILL.md", "README.md"):
            self.assertIn("context-retrieval.md", (ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
