"""Public provenance contracts, using real JSONL files and native writers."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/q-cockpit'))
import cockpit_observability as obs
import q_cockpit_plus as cockpit


class CommunicationTests(unittest.TestCase):
    def test_compact_preserves_each_unnamed_emitter_kind(self):
        displays = []
        for kind in ('llm', 'tool', 'host', 'harness'):
            with self.subTest(kind=kind):
                display = obs.compact_event({'provenance': {'emitter': {'kind': kind, 'name': None}}})
                displays.append(display)
                self.assertEqual(display, f'[time unavailable] [{kind} (unknown) | unknown | unknown] unknown')
        self.assertEqual(len(set(displays)), 4)

    def test_compact_preserves_named_emitter_kind_and_name(self):
        display = obs.compact_event({'timestamp': '2026-11-04T12:34:56+02:00',
            'type': 'probe', 'provenance': {'emitter': {'kind': 'tool', 'name': 'q-cockpit'},
                                          'workflow': 'q-agent', 'phase': 'verification'}})
        self.assertEqual(display, '[12:34:56 +02:00] [tool (q-cockpit) | q-agent | verification] probe')
        self.assertEqual(obs.compact_event({}), '[time unavailable] [unknown | unknown | unknown] unknown')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='cockpit-provenance.')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_native_writers_protect_attribution_and_keep_return_contracts(self):
        for manager in (cockpit.legacy.SessionManager, cockpit.EnhancedSessionManager):
            with self.subTest(manager=manager.__name__):
                result = manager.append_event(self.root, {
                    'type': 'answer', 'timestamp': 'spoof', 'timestamp_source': 'spoof',
                    'provenance': {'emitter': {'name': 'fake'}, 'lifecycle': 'verified'},
                    'answer': 'private answer'})
                record = json.loads((self.root / 'events.jsonl').read_text().splitlines()[-1])
                self.assertEqual(record['timestamp_source'], 'runtime_clock')
                self.assertEqual(record['provenance']['emitter']['name'], 'q-cockpit')
                self.assertEqual(record['provenance']['lifecycle'], 'unknown')
                self.assertEqual(record['answer'], 'private answer')
                self.assertTrue(record['timestamp'].endswith('+00:00'))
                if manager is cockpit.legacy.SessionManager:
                    self.assertIsNone(result)
                else:
                    self.assertEqual(result, record['request_id'])

    def test_legacy_time_and_private_fields(self):
        for timestamp in (None, 'nonsense', '2026-01-02T03:04:05', '2026-01-02T03:04:05+02:00'):
            public = obs.public_event({'timestamp': timestamp, 'type': 'answer',
                'answer': 'secret', 'notes': 'secret', 'argv': ['secret'], 'path': '/secret'})
            self.assertEqual(public['timestamp'], timestamp if timestamp and timestamp.endswith('+02:00') else None)
            self.assertEqual(public['provenance']['emitter']['kind'], 'unknown')
            self.assertEqual(public['provenance']['lifecycle'], 'unknown')
            self.assertNotIn('secret', json.dumps(public))
            self.assertIn('unknown', obs.compact_event(public))
        self.assertIsNone(obs.public_event([]))

    def test_legacy_writer_preserves_existing_event_fields(self):
        event = {'type': 'task_result', 'operation': 'task_run',
                 'outcome': 'failed', 'request_id': 'caller-correlation',
                 'timestamp': 'spoof', 'provenance': {'emitter': {'name': 'fake'}}}
        with obs.request_context('handler-correlation'):
            result = cockpit.legacy.SessionManager.append_event(self.root, event)
        record = json.loads((self.root / 'events.jsonl').read_text())
        self.assertIsNone(result)
        for key in ('type', 'operation', 'outcome', 'request_id'):
            with self.subTest(key=key):
                self.assertEqual(record.get(key), event[key])
        self.assertEqual(record['timestamp_source'], 'runtime_clock')
        self.assertNotEqual(record['timestamp'], 'spoof')
        self.assertEqual(record['provenance']['emitter']['name'], 'q-cockpit')
        self.assertEqual(event['timestamp'], 'spoof')

    def test_measurements_require_sources_and_estimate_basis(self):
        for measurement, expected in (({'status': 'measured', 'value': 0}, 'unavailable'),
                ({'status': 'estimated', 'value': 4, 'source': 'manual'}, 'unavailable'),
                ({'status': 'estimated', 'value': 4, 'source': 'manual', 'basis': 'word count'}, 'estimated'),
                ({'status': 'measured', 'value': float('inf'), 'source': 'tool'}, 'unavailable')):
            value = obs.public_event({'telemetry': {'tokens': measurement}})['telemetry']['tokens']
            self.assertEqual(value['status'], expected)
            if expected == 'unavailable':
                self.assertIsNone(value['value'])

    def test_loaded_does_not_become_executed(self):
        event = obs.public_event({'provenance': {'lifecycle': 'loaded', 'workflow': 'q-agent'}})
        self.assertEqual(event['provenance']['lifecycle'], 'loaded')
        self.assertIsNone(event['provenance']['executor'])
        self.assertIsNone(event['provenance']['host'])

    def test_event_count_and_metadata_are_bounded(self):
        (self.root / 'events.jsonl').write_text(('{}\n' * 60))
        result = obs.communication_snapshot(self.root)
        self.assertEqual(len(result['events']), 40)
        self.assertTrue(result['truncated'])
        event = obs.public_event({'provenance': {'workflow': 'x' * 1000,
                                  'host': '/private/location', 'executor': {'bad': True}}})
        self.assertEqual(len(event['provenance']['workflow']), 96)
        self.assertIsNone(event['provenance']['host'])
        self.assertIsNone(event['provenance']['executor'])

    def test_task_diagnostic_adds_only_native_claims_and_keeps_private_mode(self):
        sys.path.insert(0, str(ROOT / 'tools/q-tasks'))
        import runtime_support
        runtime_support.diagnostic(self.root, {'operation': 'run', 'state': 'failed',
            'exit_code': 3, 'argv': ['private'], 'provenance': {'host': 'fake'}})
        path = self.root / 'diagnostics.jsonl'
        record = json.loads(path.read_text())
        self.assertEqual(record['exit_code'], 3)
        self.assertEqual(record['provenance']['emitter']['name'], 'q-tasks')
        self.assertIsNone(record['provenance']['host'])
        self.assertEqual(record['provenance']['lifecycle'], 'unknown')
        self.assertNotIn('private', path.read_text())
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_bounded_tail_skips_partial_malformed_and_nonobjects(self):
        path = self.root / 'events.jsonl'
        path.write_bytes(b'x' * 300000 + b'\n[]\n{bad}\n' +
                         b'{"type":"answer","notes":"secret"}\n{"type":"partial"}')
        result = obs.communication_snapshot(self.root)
        self.assertEqual(len(result['events']), 1)
        self.assertNotIn('secret', json.dumps(result))
        self.assertTrue(result['truncated'])

    def test_symlink_hardlink_and_parent_escapes_are_unavailable(self):
        outside = self.root / 'outside'
        outside.mkdir()
        (outside / 'events.jsonl').write_text('{}\n')
        session = self.root / 'session'
        session.mkdir()
        path = session / 'events.jsonl'
        path.symlink_to(outside / 'events.jsonl')
        self.assertEqual(obs.communication_snapshot(session)['status'], 'unavailable')
        path.unlink()
        os.link(outside / 'events.jsonl', path)
        self.assertEqual(obs.communication_snapshot(session)['status'], 'unavailable')
        alias = self.root / 'alias'
        alias.symlink_to(outside, target_is_directory=True)
        self.assertEqual(obs.communication_snapshot(alias)['status'], 'unavailable')

    def test_logger_reserved_fields_and_correlation(self):
        with obs.request_context('correlation'):
            value = obs.StructuredEventLogger(self.root / 'log.jsonl').emit('probe', {
                'request_id': 'fake', 'operation': 'fake', 'provenance': {'lifecycle': 'verified'}})
        record = json.loads((self.root / 'log.jsonl').read_text())
        self.assertEqual(value, 'correlation')
        self.assertEqual(record['operation'], 'probe')
        self.assertEqual(record['provenance']['lifecycle'], 'unknown')
