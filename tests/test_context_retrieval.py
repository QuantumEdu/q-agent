"""Configuration and instruction contracts; no live provider integration."""
import contextlib
import importlib.util
import io
import json
import os
import re
from pathlib import Path
import tempfile
import unittest
from unittest import mock

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
        # SkillVault backend fields (template 1.3): the memory backend only;
        # the local skills directory moved to skill_explorer.
        skillvault = context["providers"]["skillvault"]
        self.assertNotIn("path", skillvault)
        self.assertEqual(skillvault["binary"], "skillvault")
        self.assertEqual(skillvault["vault_path"], "~/.skillvault/vault.db")
        self.assertIsNone(skillvault["project_slug"])
        self.assertIsNone(skillvault["mcp_server"])
        explorer = context["skill_explorer"]
        self.assertFalse(explorer["enabled"])
        self.assertEqual(explorer["path"], "skills/")
        self.assertFalse(self.template["integrations"]["skillvault_mcp"])

    def test_skillvault_enabled_generation_links_marker(self):
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        selections["skillvault"] = checklist.DECISION_OPTIONS["skillvault"]["options"][1]
        with mock.patch.object(checklist.shutil, "which", return_value=None):
            with tempfile.TemporaryDirectory() as directory:
                checklist.generate_artifacts(Path(directory), "Sample Project", selections)
                generated = json.loads((Path(directory) / ".q-agent.json").read_text(encoding="utf-8"))
                marker = (Path(directory) / "AGENTS.md").read_text(encoding="utf-8")
        provider = generated["context_retrieval"]["providers"]["skillvault"]
        self.assertTrue(provider["enabled"])
        self.assertEqual(provider["authorization"], "read")
        self.assertEqual(provider["project_slug"], "sample-project")
        self.assertEqual(provider["project_scope"], "sample-project")
        self.assertEqual(generated["context_retrieval"]["project_id"], "sample-project")
        self.assertIn("<!-- skillvault:start -->", marker)
        self.assertIn("<!-- skillvault:end -->", marker)
        self.assertIn('skillvault find "<topic>" --project sample-project', marker)
        self.assertIn("skillvault context --project sample-project", marker)

    def test_resolve_skillvault_paths(self):
        fake_binary = "/opt/fakebin/skillvault"
        with mock.patch.object(checklist.shutil, "which", return_value=fake_binary):
            with mock.patch.dict(os.environ, {"SKILLVAULT_HOME": "/tmp/vault-home"}):
                self.assertEqual(
                    checklist.resolve_skillvault_paths(),
                    (fake_binary, "/tmp/vault-home/vault.db"),
                )
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("SKILLVAULT_HOME", None)
                binary, vault_path = checklist.resolve_skillvault_paths()
                self.assertEqual(binary, fake_binary)
                self.assertEqual(vault_path, os.path.join(os.path.expanduser("~"), ".skillvault", "vault.db"))
        with mock.patch.object(checklist.shutil, "which", return_value=None):
            with mock.patch.dict(os.environ, {"SKILLVAULT_HOME": "/tmp/vault-home"}):
                self.assertEqual(
                    checklist.resolve_skillvault_paths(),
                    (None, "/tmp/vault-home/vault.db"),
                )

    def test_skillvault_enabled_generation_writes_resolved_paths(self):
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        selections["skillvault"] = checklist.DECISION_OPTIONS["skillvault"]["options"][1]
        fake_binary = "/tmp/fakebin/skillvault"
        with mock.patch.object(checklist.shutil, "which", return_value=fake_binary):
            with tempfile.TemporaryDirectory() as directory:
                vault_home = os.path.join(directory, "vault")
                with mock.patch.dict(os.environ, {"SKILLVAULT_HOME": vault_home}):
                    checklist.generate_artifacts(Path(directory), "Sample Project", selections)
                    generated = json.loads((Path(directory) / ".q-agent.json").read_text(encoding="utf-8"))
                    marker = (Path(directory) / "AGENTS.md").read_text(encoding="utf-8")
        provider = generated["context_retrieval"]["providers"]["skillvault"]
        self.assertTrue(provider["enabled"])
        # The fake binary does not exist, so link-project cannot run and the
        # marker falls back to verbatim — but the config must still record
        # the resolved paths, and the marker must agree with them.
        self.assertEqual(provider["binary"], fake_binary)
        self.assertEqual(provider["vault_path"], os.path.join(vault_home, "vault.db"))
        self.assertEqual(provider["availability"], "available")
        self.assertEqual(provider["capabilities"], ["search", "read"])
        self.assertIn(f"- Vault: `{vault_home}/vault.db` (binary: `{fake_binary}`)", marker)
        self.assertIn(f'`{fake_binary} find "<topic>" --project sample-project', marker)

    def test_skillvault_enabled_without_binary_keeps_template_binary(self):
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        selections["skillvault"] = checklist.DECISION_OPTIONS["skillvault"]["options"][1]
        with mock.patch.object(checklist.shutil, "which", return_value=None):
            with tempfile.TemporaryDirectory() as directory:
                vault_home = os.path.join(directory, "vault")
                with mock.patch.dict(os.environ, {"SKILLVAULT_HOME": vault_home}):
                    checklist.generate_artifacts(Path(directory), "Sample Project", selections)
                    generated = json.loads((Path(directory) / ".q-agent.json").read_text(encoding="utf-8"))
                    marker = (Path(directory) / "AGENTS.md").read_text(encoding="utf-8")
        provider = generated["context_retrieval"]["providers"]["skillvault"]
        self.assertTrue(provider["enabled"])
        self.assertEqual(provider["binary"], "skillvault")
        self.assertEqual(provider["vault_path"], os.path.join(vault_home, "vault.db"))
        self.assertEqual(provider["availability"], "unknown")
        self.assertEqual(provider["capabilities"], [])
        self.assertIn(f"- Vault: `{vault_home}/vault.db` (binary: `skillvault`)", marker)
        self.assertIn('skillvault find "<topic>" --project sample-project', marker)

    def test_skillvault_link_failure_warns_on_stderr(self):
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        selections["skillvault"] = checklist.DECISION_OPTIONS["skillvault"]["options"][1]
        # Mocked binary path does not exist, so the CLI cannot run and the
        # marker falls back to verbatim — the pre-flight must say so.
        with mock.patch.object(checklist.shutil, "which", return_value="/tmp/fakebin/skillvault"):
            with tempfile.TemporaryDirectory() as directory:
                err = io.StringIO()
                with contextlib.redirect_stderr(err):
                    checklist.generate_artifacts(Path(directory), "Sample Project", selections)
                marker = (Path(directory) / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("link-project", err.getvalue())
        self.assertIn("verbatim", err.getvalue())
        self.assertIn("id `sample-project`", marker)

    def test_skillvault_disabled_by_default_writes_no_marker(self):
        selections = {key: value["options"][0] for key, value in checklist.DECISION_OPTIONS.items()}
        with tempfile.TemporaryDirectory() as directory:
            checklist.generate_artifacts(Path(directory), "sample-project", selections)
            self.assertFalse((Path(directory) / "AGENTS.md").exists())
            generated = json.loads((Path(directory) / ".q-agent.json").read_text(encoding="utf-8"))
        self.assertFalse(generated["context_retrieval"]["providers"]["skillvault"]["enabled"])

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
        for path in ("SKILL.md", "skills/q-gbrain-assistant/SKILL.md", "skills/q-skillvault-assistant/SKILL.md", "skills/q-session-wrap/SKILL.md", "README.md"):
            self.assertIn("context-retrieval.md", (ROOT / path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
