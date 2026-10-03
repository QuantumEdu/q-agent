#!/usr/bin/env python3
"""Enhanced q-cockpit entrypoint with bounded snapshots and recovery controls.

The legacy q_cockpit module remains API-compatible; this thin transport facade
owns the new operational concerns so they can evolve independently.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent


def _load_legacy():
    spec = importlib.util.spec_from_file_location("q_cockpit_legacy", HERE / "q_cockpit.py")
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load q_cockpit.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


legacy = _load_legacy()


def _load_local(module_name: str, filename: str):
    qualified_name = f"q_cockpit_{module_name}"
    existing = sys.modules.get(qualified_name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(qualified_name, HERE / filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_services = _load_local("services", "cockpit_services.py")
_observability = _load_local("observability", "cockpit_observability.py")
_recovery = _load_local("recovery", "recovery.py")
ProjectSnapshotWorker = _services.ProjectSnapshotWorker
action_catalog = _services.action_catalog
current_request_id = _observability.current_request_id
new_request_id = _observability.new_request_id
request_context = _observability.request_context
backup_sessions = _recovery.backup_sessions
health_report = _recovery.health_report
restore_sessions = _recovery.restore_sessions


class EnhancedSessionManager(legacy.SessionManager):
    """Compatibility session manager with structured event records."""

    @staticmethod
    def append_event(session_dir: Path, event: dict[str, Any], *, request_id: str | None = None) -> str:
        correlation_id = request_id or current_request_id() or new_request_id()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": correlation_id,
            "operation": event.get("type", "session_event"),
            "outcome": "ok",
        }
        record.update({key: value for key, value in event.items() if key not in record})
        try:
            events_file = Path(session_dir) / "events.jsonl"
            with events_file.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        except OSError as exc:
            raise RuntimeError(f"Unable to append session event: {exc}") from exc
        return correlation_id


class EnhancedHandler(legacy.CockpitHTTPHandler):
    snapshot_worker: ProjectSnapshotWorker | None = None
    request_id: str | None = None

    def do_GET(self) -> None:
        self.request_id = new_request_id()
        with request_context(self.request_id):
            path = self.path.split("?", 1)[0]
            if path == "/api/actions":
                self.send_json({"actions": action_catalog()})
                return
            if path == "/health":
                self.send_json(health_report(self.session_manager.sessions_root, self.active_session_dir))
                return
            super().do_GET()

    def do_POST(self) -> None:
        self.request_id = new_request_id()
        with request_context(self.request_id):
            super().do_POST()

    def serve_api_status(self) -> None:
        worker = self.snapshot_worker
        if worker is None:
            worker = ProjectSnapshotWorker(legacy.ProjectScanner)
            self.snapshot_worker = worker
        snapshot = worker.get(self.project_root)
        if not self.active_session_dir or not self.active_session_dir.exists():
            self.active_session_dir = self.session_manager.get_latest_session(self.project_root)
        if self.active_session_dir and (self.active_session_dir / "state.json").exists():
            session_state = self.session_manager.read_json(self.active_session_dir / "state.json")
        else:
            session_state = {"topic": "q-agent Workspace", "status": "idle", "questions": [], "gates": {}}
        tasks = snapshot["tasks"]
        unanswered = [q for q in session_state.get("questions", []) if q.get("status") not in ("answered", "resolved")]
        in_progress = [task for task in tasks if task.get("status") == "in_progress"]
        active_phase = None if not unanswered and not in_progress else (session_state.get("phase") or ("P04" if unanswered else "P08"))
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": {
                "name": self.project_root.name,
                "path": str(self.project_root),
                "version": snapshot["version"],
                "status": "idle" if active_phase is None else "active",
                "active_phase": active_phase,
                "git": snapshot["git"],
            },
            "session": session_state,
            "tasks": tasks,
            "artifacts": snapshot["artifacts"],
            "has_visual": bool((self.project_root / "visual.html").exists()),
            "snapshot": snapshot["snapshot"],
        }
        self.send_json(payload)

    def send_json(self, data: Any, code: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        if self.request_id:
            self.send_header("X-Request-ID", self.request_id)
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(raw)


def run_server(port: int = 4242, project: Path | None = None, session: Path | None = None, host: str = "127.0.0.1") -> None:
    root = legacy.get_git_root(project or Path.cwd())
    manager = EnhancedSessionManager()
    active = session or manager.get_latest_session(root) or manager.create_session(root, f"Auditoría y Plan {root.name}")
    EnhancedHandler.project_root = root
    EnhancedHandler.session_manager = manager
    EnhancedHandler.active_session_dir = active
    EnhancedHandler.snapshot_worker = ProjectSnapshotWorker(legacy.ProjectScanner)
    print(f"q-cockpit-plus running at http://{host}:{port} for {root}")
    with legacy.ThreadedTCPServer((host, port), EnhancedHandler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
        finally:
            if EnhancedHandler.snapshot_worker:
                EnhancedHandler.snapshot_worker.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="q-cockpit-plus: enhanced q-agent cockpit")
    subparsers = parser.add_subparsers(dest="command", required=True)
    serve = subparsers.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=4242)
    serve.add_argument("--project", type=Path)
    serve.add_argument("--session", type=Path)
    subparsers.add_parser("actions")
    backup = subparsers.add_parser("backup")
    backup.add_argument("--sessions-root", type=Path, default=Path.home() / ".q-cockpit" / "sessions")
    backup.add_argument("--output", type=Path, required=True)
    restore = subparsers.add_parser("restore")
    restore.add_argument("--archive", type=Path, required=True)
    restore.add_argument("--destination", type=Path, required=True)
    restore.add_argument("--overwrite", action="store_true")
    health = subparsers.add_parser("health")
    health.add_argument("--sessions-root", type=Path, default=Path.home() / ".q-cockpit" / "sessions")
    health.add_argument("--session", type=Path)
    args = parser.parse_args()
    if args.command == "serve":
        run_server(args.port, args.project, args.session, args.host)
    elif args.command == "actions":
        print(json.dumps({"actions": action_catalog()}, indent=2))
    elif args.command == "backup":
        print(backup_sessions(args.sessions_root, args.output))
    elif args.command == "restore":
        print(restore_sessions(args.archive, args.destination, overwrite=args.overwrite))
    elif args.command == "health":
        print(json.dumps(health_report(args.sessions_root, args.session), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
