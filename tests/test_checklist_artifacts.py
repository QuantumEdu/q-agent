"""Exercise the interactive checklist and inspect its actual generated artifacts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/q-checklist/q_checklist.py"


class ChecklistArtifactsTests(unittest.TestCase):
    def generate(self, architecture=4, isolation=2, skillvault=1):
        with tempfile.TemporaryDirectory() as directory:
            # Empty PATH keeps the run hermetic: no `skillvault` binary is
            # picked up, so the marker is written verbatim, never via the
            # CLI against a real vault.
            env = {**os.environ, "PATH": ""}
            result = subprocess.run(
                [sys.executable, str(SCRIPT)], cwd=directory,
                input=f'Medical "appointments"\n\n{architecture}\n1\n2\n1\n{isolation}\n{skillvault}\ny\n',
                text=True, capture_output=True, timeout=10, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            root = Path(directory)
            agents_md = root / "AGENTS.md"
            return (
                (root / "CONSTITUTION.md").read_text(encoding="utf-8"),
                (root / "docs/adr/0001-stack-decisions.md").read_text(encoding="utf-8"),
                json.loads((root / ".q-agent.json").read_text(encoding="utf-8")),
                agents_md.read_text(encoding="utf-8") if agents_md.exists() else None,
            )

    def test_modular_selection_does_not_impose_hexagonal_layers(self):
        constitution, adr, _, _ = self.generate()
        self.assertIn("Monolito Modular", constitution)
        self.assertIn("slice", constitution.lower())
        self.assertIn("slice", adr.lower())
        for artifact in (constitution, adr):
            self.assertNotIn("Ports Layer", artifact)
            self.assertNotIn("Aislamiento Estricto de Capas", artifact)
            self.assertNotIn("Requiere escribir puertos", artifact)
            self.assertNotIn("desacoplamiento absoluto", artifact)
            self.assertNotIn("menos de 1 segundo", artifact)

    def test_architecture_specific_structures_and_tradeoffs(self):
        expectations = {
            1: ("Domain Layer", "puertos"),
            2: ("Casos de uso", "dependencias hacia el interior"),
            3: ("Servicios", "dependencias entre capas"),
            4: ("Slices", "límites entre módulos"),
        }
        for choice, (component, tradeoff) in expectations.items():
            with self.subTest(architecture=choice):
                constitution, adr, _, _ = self.generate(architecture=choice)
                self.assertIn(component, constitution)
                self.assertIn(tradeoff, adr)
                self.assertIn("SQLite", constitution)
                self.assertIn("API RESTful", adr)

    def test_runtime_and_models_are_unconfigured_in_both_entrypoints(self):
        template = json.loads((ROOT / "templates/q-agent.json").read_text(encoding="utf-8"))
        _, _, generated, _ = self.generate()
        for config in (template, generated):
            self.assertIsNone(config["runtime"]["executor"])
            self.assertIsNone(config["models"]["tier1_frontier"])
            self.assertIsNone(config["models"]["tier2_local"])
            self.assertEqual(config["runtime"]["interaction_mode"], "supervised")
            self.assertIsNone(config["execution_authority"]["evidence"])

    def test_generated_defaults_match_template_except_selected_isolation(self):
        template_bytes = (ROOT / "templates/q-agent.json").read_bytes()
        template = json.loads(template_bytes)
        for isolation, mode in ((1, "worktree"), (2, "inline")):
            with self.subTest(isolation=mode):
                _, _, generated, _ = self.generate(isolation=isolation)
                self.assertEqual(generated["workspace"]["isolation"], mode)
                template["workspace"]["isolation"] = mode
                self.assertEqual(generated, template)
        self.assertEqual((ROOT / "templates/q-agent.json").read_bytes(), template_bytes)

    def test_skillvault_disabled_by_default_writes_no_marker(self):
        _, _, generated, agents_md = self.generate()
        self.assertFalse(generated["context_retrieval"]["providers"]["skillvault"]["enabled"])
        self.assertIsNone(agents_md)

    def test_skillvault_enabled_writes_marker_and_config(self):
        _, _, generated, agents_md = self.generate(skillvault=2)
        provider = generated["context_retrieval"]["providers"]["skillvault"]
        self.assertTrue(provider["enabled"])
        self.assertEqual(provider["authorization"], "read")
        self.assertEqual(provider["project_slug"], "medical-appointments")
        self.assertEqual(provider["project_scope"], "medical-appointments")
        self.assertEqual(generated["context_retrieval"]["project_id"], "medical-appointments")
        self.assertIsNotNone(agents_md)
        self.assertIn("<!-- skillvault:start -->", agents_md)
        self.assertIn("<!-- skillvault:end -->", agents_md)
        self.assertIn('skillvault find "<topic>" --project medical-appointments', agents_md)
        self.assertIn("skillvault context --project medical-appointments", agents_md)


if __name__ == "__main__":
    unittest.main()
