"""Ensure the repair drill exposes actual HTTP defects rather than mocked failures."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UnattendedDrillTests(unittest.TestCase):
    def test_seed_exposes_two_real_defects_and_a_passing_control(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'clinic'
            shutil.copytree(ROOT / 'examples/unattended-e2e', target)
            result = subprocess.run(
                [sys.executable, '-m', 'unittest', '-v', 'test_clinic'],
                cwd=target, capture_output=True, text=True, timeout=30,
            )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('Ran 3 tests', result.stderr)
        self.assertIn('FAILED (failures=2)', result.stderr)
        self.assertRegex(result.stderr, r'test_create .* \.\.\. ok')
        self.assertIn('AssertionError: 201 != 400', result.stderr)
        self.assertIn('AssertionError: 201 != 409', result.stderr)


if __name__ == '__main__':
    unittest.main()
