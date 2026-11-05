"""Exercise the workflow's real environment initialization without a runner."""
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WorkflowEnvironmentTests(unittest.TestCase):
    def test_cockpit_home_is_exported_by_a_runner_step(self):
        workflow = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertNotIn('Q_COCKPIT_HOME: ${{ runner.temp }}', workflow)
        step = re.search(
            r'(?m)^      - name: Configure cockpit home\n        run: (.+)$',
            workflow,
        )
        self.assertIsNotNone(step, 'Initialize runner-dependent values in a step')
        self.assertLess(step.start(), workflow.index('      - name: Verify Python syntax'))
        with tempfile.TemporaryDirectory(prefix='ci-workflow.') as scratch:
            environment_file = Path(scratch) / 'github-env'
            environment_file.touch()
            result = subprocess.run(
                ['bash', '-e', '-c', step.group(1)],
                env={**os.environ, 'RUNNER_TEMP': scratch,
                     'GITHUB_ENV': str(environment_file)},
                capture_output=True, text=True,
            )
            self.assertEqual((result.returncode, result.stdout, result.stderr), (0, '', ''))
            self.assertEqual(environment_file.read_text(),
                             f'Q_COCKPIT_HOME={scratch}/q-agent-cockpit\n')


if __name__ == '__main__':
    unittest.main()
