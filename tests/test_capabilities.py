"""Capability contracts verified without inference or account access."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAPS = ROOT / 'tools/q-tasks/capabilities.py'
TASKS = ROOT / 'tools/q-tasks/q_tasks.py'


class CapabilityTests(unittest.TestCase):
    def report(self, backend):
        return json.loads(subprocess.check_output([sys.executable, str(CAPS), '--backend', backend], text=True))

    def test_local_features_are_probed_and_isolation_is_not_invented(self):
        report = self.report('local')
        for name in ('durable_receipts', 'process_group_cancellation', 'bounded_output'):
            self.assertEqual(report['capabilities'][name]['status'], 'verified')
        for name in ('native_conversation_resume', 'delegation', 'workspace_isolation', 'process_containment'):
            self.assertEqual(report['capabilities'][name]['status'], 'unsupported')

    def test_external_executable_presence_does_not_claim_protocol_support(self):
        for backend in ('codex', 'claude', 'pi'):
            report = self.report(backend)
            self.assertIn(report['availability'], ('installed', 'missing'))
            self.assertTrue(all(cap['status'] == 'unknown' for cap in report['capabilities'].values()))
            self.assertNotIn('token', json.dumps(report).lower())

    def test_launcher_exposes_report(self):
        result = subprocess.check_output(['bash', str(ROOT / 'bin/q-agent'), 'capabilities', '--backend', 'local'], text=True)
        self.assertEqual(json.loads(result)['backend'], 'local')

    def test_required_unavailable_capability_rejects_before_command_or_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            subprocess.run(['git', '-C', str(root), '-c', 'user.name=Test', '-c',
                            'user.email=test@example.invalid', 'commit', '--allow-empty', '-qm', 'fixture'], check=True)
            def call(*args):
                return subprocess.run([sys.executable, str(TASKS), '--project', str(root), *args], capture_output=True, text=True)
            self.assertEqual(call('add', 'T1', 'Feature').returncode, 0)
            result = call('run', 'T1', '--request-id', 'isolated', '--require-capability', 'workspace_isolation',
                          '--', sys.executable, '-c', "from pathlib import Path; Path('effect').touch()")
            self.assertEqual(result.returncode, 2, result.stdout)
            self.assertFalse((root / 'effect').exists())
            self.assertEqual(json.loads(call('history', 'T1').stdout)['attempts'], [])
            result = call('run', 'T1', '--request-id', 'bounded', '--require-capability', 'bounded_output',
                          '--', sys.executable, '-c', 'pass')
            self.assertEqual(result.returncode, 0, result.stdout)
            proof = json.loads(result.stdout)
            self.assertEqual(json.loads(proof['required_capabilities']), ['bounded_output'])
            self.assertEqual(call('run', 'T1', '--request-id', 'bounded', '--', sys.executable, '-c', 'pass').returncode, 2)


if __name__ == '__main__':
    unittest.main()
