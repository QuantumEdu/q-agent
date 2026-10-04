"""Regression tests for q-agent operational and strategic evolution features."""

import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
COCKPIT_DIR = ROOT / "tools" / "q-cockpit"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_legacy = _load_module("q_cockpit_legacy", COCKPIT_DIR / "q_cockpit.py")
_services = _load_module("q_cockpit_services", COCKPIT_DIR / "cockpit_services.py")
_observability = _load_module("q_cockpit_observability", COCKPIT_DIR / "cockpit_observability.py")
_recovery = _load_module("q_cockpit_recovery", COCKPIT_DIR / "recovery.py")
_plus = _load_module("q_cockpit_plus", COCKPIT_DIR / "q_cockpit_plus.py")
_runner = _load_module("q_audit_runner", ROOT / "tools" / "q-audit-runner" / "run_audit.py")
_lifecycle = _load_module("q_audit_lifecycle", ROOT / "tools" / "q-audit-lifecycle" / "audit_lifecycle.py")
_evidence = _load_module("q_audit_evidence", ROOT / "tools" / "q-audit-evidence" / "evidence.py")
_benchmark = _load_module("q_benchmark", ROOT / "tools" / "q-benchmark" / "benchmark.py")

ProjectSnapshotWorker = _services.ProjectSnapshotWorker
action_catalog = _services.action_catalog
StructuredEventLogger = _observability.StructuredEventLogger
request_context = _observability.request_context
EnhancedSessionManager = _plus.EnhancedSessionManager
backup_sessions = _recovery.backup_sessions
health_report = _recovery.health_report
restore_sessions = _recovery.restore_sessions
AuditLifecycle = _lifecycle.AuditLifecycle
AuditState = _lifecycle.AuditState
build_evidence_index = _evidence.build_evidence_index
run_benchmark = _benchmark.run_benchmark


class EvolutionTests(unittest.TestCase):
    def test_action_catalog_is_shared_and_stable(self):
        actions = action_catalog()
        ids = [action["id"] for action in actions]
        self.assertEqual(ids, ["status", "new_session", "inspect_artifact", "approve_gate", "wait"])
        self.assertTrue(all("label" in action and "description" in action for action in actions))

    def test_snapshot_worker_returns_cache_and_refresh_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Snapshot\n", encoding="utf-8")
            worker = ProjectSnapshotWorker(_legacy.ProjectScanner)
            first = worker.get(root)
            self.assertEqual(first["snapshot"]["state"], "fresh")
            self.assertIn("git", first)
            second = worker.get(root)
            self.assertIn(second["snapshot"]["state"], {"fresh", "refreshing"})
            worker.close()

    def test_snapshot_invalidates_after_project_file_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "project.txt"
            source.write_text("before\n", encoding="utf-8")
            worker = ProjectSnapshotWorker(_legacy.ProjectScanner)
            first = worker.get(root)
            source.write_text("after\n", encoding="utf-8")
            second = worker.get(root)
            self.assertNotEqual(first["snapshot"]["signature"], second["snapshot"]["signature"])
            self.assertIn(second["snapshot"]["state"], {"fresh", "refreshing", "stale"})
            worker.close()

    def test_structured_event_logger_writes_correlation_and_outcome(self):
        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "events.jsonl"
            logger = StructuredEventLogger(events)
            request_id = logger.emit("gate_decision", {"gate": "P04"}, outcome="approved")
            record = json.loads(events.read_text(encoding="utf-8").strip())
            self.assertEqual(record["request_id"], request_id)
            self.assertEqual(record["operation"], "gate_decision")
            self.assertEqual(record["outcome"], "approved")
            self.assertIn("timestamp", record)

    def test_reserved_event_fields_cannot_be_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "events.jsonl"
            logger = StructuredEventLogger(events)
            request_id = logger.emit(
                "operation",
                {
                    "request_id": "caller-id",
                    "operation": "caller-operation",
                    "outcome": "caller-outcome",
                    "timestamp": "caller-time",
                    "value": 42,
                },
                request_id="request-1",
            )
            record = json.loads(events.read_text(encoding="utf-8").strip())
            self.assertEqual(request_id, "request-1")
            self.assertEqual(record["request_id"], "request-1")
            self.assertEqual(record["operation"], "operation")
            self.assertEqual(record["outcome"], "ok")
            self.assertNotEqual(record["timestamp"], "caller-time")
            self.assertEqual(record["value"], 42)

    def test_inherited_event_handler_uses_request_context(self):
        with tempfile.TemporaryDirectory() as directory:
            session = Path(directory)
            events = session / "events.jsonl"
            with request_context("request-42"):
                correlation_id = EnhancedSessionManager.append_event(
                    session,
                    {"type": "gate_decision", "request_id": "caller-id", "operation": "spoofed"},
                )
            record = json.loads(events.read_text(encoding="utf-8").strip())
            self.assertEqual(correlation_id, "request-42")
            self.assertEqual(record["request_id"], "request-42")
            self.assertEqual(record["operation"], "gate_decision")

    def test_backup_rejects_archive_inside_source_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "sessions"
            source.mkdir()
            with self.assertRaises(ValueError):
                backup_sessions(source, source / "backup.zip")
            outside = root / "outside.txt"
            outside.write_text("secret", encoding="utf-8")
            link = source / "escape.txt"
            try:
                link.symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable")
            with self.assertRaises(ValueError):
                backup_sessions(source, root / "backup.zip")

    def test_restore_validates_before_touching_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "invalid.zip"
            destination = root / "restored"
            destination.mkdir()
            (destination / "keep.txt").write_text("keep", encoding="utf-8")
            with zipfile.ZipFile(archive, "w") as bundle:
                bundle.writestr("backup-manifest.json", '{"format": "q-cockpit-session-backup-v1"}\n')
                bundle.writestr("good.txt", "new")
                bundle.writestr("../escape.txt", "unsafe")
            with self.assertRaises(ValueError):
                restore_sessions(archive, destination)
            self.assertEqual((destination / "keep.txt").read_text(encoding="utf-8"), "keep")
            self.assertFalse((root / "escape.txt").exists())

    def test_backup_restore_and_health_report(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "sessions"
            destination = Path(directory) / "restored"
            source.mkdir()
            (source / "project" / "session").mkdir(parents=True)
            (source / "project" / "session" / "state.json").write_text("{}\n", encoding="utf-8")
            archive = Path(directory) / "backup.zip"
            backup_sessions(source, archive)
            self.assertTrue(zipfile.is_zipfile(archive))
            restore_sessions(archive, destination)
            self.assertTrue((destination / "project" / "session" / "state.json").exists())
            report = health_report(destination)
            self.assertTrue(report["healthy"])
            self.assertTrue(report["checks"]["sessions_root"])

    def test_runner_blocks_when_aggregator_fails_and_keeps_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.yml"
            manifest.write_text("items: []\n", encoding="utf-8")
            (root / "audit").mkdir()
            (root / "audit" / "A01-result.md").write_text("result\n", encoding="utf-8")
            with patch.object(_runner, "_run", side_effect=[0, 9]):
                state = _runner.run_audit(root, 2, manifest)
            self.assertEqual(state["state"], "blocked")
            self.assertEqual(state["aggregator_exit"], 9)
            self.assertEqual(state["result"], 9)
            self.assertTrue((root / "audit" / "AUDIT_EVIDENCE.json").exists())

    def test_runner_accepts_conditional_report_as_aggregated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.yml"
            manifest.write_text("items: []\n", encoding="utf-8")
            audit_dir = root / "audit"
            audit_dir.mkdir()
            (audit_dir / "A01-result.md").write_text("result\n", encoding="utf-8")
            (audit_dir / "AUDIT_REPORT.md").write_text(
                "> **Overall Verdict:** `CONDITIONAL`\n", encoding="utf-8"
            )
            with patch.object(_runner, "_run", side_effect=[0, 1]):
                state = _runner.run_audit(root, 2, manifest)
            self.assertEqual(state["state"], "aggregated")
            self.assertTrue(state["conditional"])
            self.assertEqual(state["result"], 0)

    def test_audit_lifecycle_rejects_invalid_transition(self):
        lifecycle = AuditLifecycle()
        self.assertEqual(lifecycle.state, AuditState.DISCOVERED)
        lifecycle.transition(AuditState.DISPATCHED, "items selected")
        lifecycle.transition(AuditState.CAPTURED, "items written")
        with self.assertRaises(ValueError):
            lifecycle.transition(AuditState.AGGREGATED, "skip validation")
        lifecycle.transition(AuditState.VALIDATED, "22 items passed")
        lifecycle.transition(AuditState.AGGREGATED, "report generated")
        self.assertEqual(lifecycle.state, AuditState.AGGREGATED)

    def test_evidence_index_hashes_manifest_and_items(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.yml"
            item = root / "item.md"
            manifest.write_text("items: []\n", encoding="utf-8")
            item.write_text("audit item\n", encoding="utf-8")
            index = build_evidence_index(root, manifest, [item], base_commit="abc123")
            self.assertEqual(index["base_commit"], "abc123")
            self.assertEqual(index["manifest_sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest())
            self.assertEqual(index["items"][0]["sha256"], hashlib.sha256(item.read_bytes()).hexdigest())

    def test_benchmark_returns_machine_readable_metrics(self):
        report = run_benchmark(ROOT, iterations=1)
        self.assertEqual(report["iterations"], 1)
        self.assertIn("environment", report)
        self.assertIn("metrics", report)
        self.assertIn("project_scan_ms", report["metrics"])


if __name__ == "__main__":
    unittest.main()
