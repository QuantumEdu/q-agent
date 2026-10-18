"""Exercise the interactive checklist and inspect its actual generated artifacts."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/q-checklist/q_checklist.py"


class ChecklistArtifactsTests(unittest.TestCase):
    def generate(self, architecture=4, isolation=2):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(SCRIPT)], cwd=directory,
                input=f'Medical "appointments"\n\n{architecture}\n1\n2\n1\n{isolation}\ny\n',
                text=True, capture_output=True, timeout=10,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            root = Path(directory)
            return (
                (root / "CONSTITUTION.md").read_text(encoding="utf-8"),
                (root / "docs/adr/0001-stack-decisions.md").read_text(encoding="utf-8"),
                json.loads((root / ".q-agent.json").read_text(encoding="utf-8")),
            )

    def test_modular_selection_does_not_impose_hexagonal_layers(self):
        constitution, adr, _ = self.generate()
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
                constitution, adr, _ = self.generate(architecture=choice)
                self.assertIn(component, constitution)
                self.assertIn(tradeoff, adr)
                self.assertIn("SQLite", constitution)
                self.assertIn("API RESTful", adr)

    def test_runtime_and_models_are_unconfigured_in_both_entrypoints(self):
        template = json.loads((ROOT / "templates/q-agent.json").read_text(encoding="utf-8"))
        _, _, generated = self.generate()
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
                _, _, generated = self.generate(isolation=isolation)
                self.assertEqual(generated["workspace"]["isolation"], mode)
                template["workspace"]["isolation"] = mode
                self.assertEqual(generated, template)
        self.assertEqual((ROOT / "templates/q-agent.json").read_bytes(), template_bytes)


if __name__ == "__main__":
    unittest.main()
