"""Structural regression checks for consumed audit and rollback instructions."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RollbackPolicyTests(unittest.TestCase):
    def test_rollback_requires_baseline_and_preserves_ambiguous_ownership(self):
        prompt = (ROOT / "prompts/P08_apply_verify.md").read_text(encoding="utf-8")
        self.assertIn("git status --short", prompt)
        self.assertIn("antes de editar", prompt)
        self.assertIn("[ROLLBACK] [NOT-EXECUTED]", prompt)
        self.assertIn("propiedad ambigua", prompt)
        self.assertNotIn("Ejecuta rollback atómico del intento actual", prompt)

    def test_recoverable_rollback_records_verified_stash_identity(self):
        prompt = (ROOT / "prompts/P08_apply_verify.md").read_text(encoding="utf-8")
        self.assertIn("git stash push --include-untracked", prompt)
        self.assertIn("archivos explícitos", prompt)
        self.assertIn("git rev-parse refs/stash", prompt)
        self.assertIn("código de salida 0", prompt)
        self.assertIn("[ROLLBACK] [STASHED]", prompt)
        recorder = (ROOT / "references/flight-recorder.md").read_text(encoding="utf-8")
        self.assertIn("`STASHED`, `NOT-EXECUTED`, `ABORTED`", recorder)
        self.assertIn("stash commit identity", recorder)


if __name__ == "__main__":
    unittest.main()
