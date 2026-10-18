"""Local admission, output and diagnostic limits on real files/processes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools/q-tasks"))
import runtime_support as runtime


class RuntimeSupportTests(unittest.TestCase):
    def test_unknown_disk_measurement_is_blocked_instead_of_reported_as_zero(self):
        result = runtime.resources(Path('/nonexistent-q-agent-path'), 1)
        self.assertFalse(result['admitted'])
        self.assertIsNone(result['free_bytes'])
        self.assertEqual(result['reason'], 'measurement_unavailable')

    def test_private_output_keeps_bounded_head_and_tail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'output.log'
            with path.open('w+b') as output:
                capture = runtime.BoundedOutput(output, 1024)
                capture.write(b'HEAD' + b'x' * 10000)
                capture.write(b'TAIL')
            result = path.read_bytes()
            self.assertEqual(len(result), 1024)
            self.assertTrue(result.startswith(b'HEAD'))
            self.assertTrue(result.endswith(b'TAIL'))
            self.assertEqual(capture.total, 10008)

    def test_diagnostics_are_bounded_and_exclude_nonfixed_strings(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for _ in range(100):
                runtime.diagnostic(directory, {'operation': 'run', 'state': 'failed',
                    'exit_code': 3, 'command': 'secret-password', 'message': 'private-output'}, limit=512)
            paths = list(directory.glob('diagnostics*'))
            self.assertLessEqual(len(paths), 2)
            for path in paths:
                self.assertLessEqual(path.stat().st_size, 512)
                self.assertNotIn(b'secret-password', path.read_bytes())
                self.assertNotIn(b'private-output', path.read_bytes())
                for line in path.read_text().splitlines():
                    self.assertEqual(json.loads(line)['exit_code'], 3)

    def test_retention_removes_only_recorded_regular_uuid_logs(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            logs = [directory / (str(index).zfill(32) + '.log') for index in range(10)]
            for log in logs:
                log.write_text('output')
            unknown = directory / 'user-notes.log'
            unknown.write_text('keep')
            linked = directory / ('f' * 32 + '.log')
            linked.symlink_to(unknown)
            runtime.prune_logs(directory, [*logs, unknown, linked], keep=8)
            self.assertEqual(sum(log.exists() for log in logs), 8)
            self.assertEqual(unknown.read_text(), 'keep')
            self.assertTrue(linked.is_symlink())


if __name__ == '__main__':
    unittest.main()
