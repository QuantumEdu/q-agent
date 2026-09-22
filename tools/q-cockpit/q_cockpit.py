#!/usr/bin/env python3
"""
q-cockpit: Unified Visual Elicitation & Multi-Agent Observability Cockpit for q-agent.
Zero external dependencies (Pure Python 3 standard library).

Combines:
  1. The Socratic Grill (JasonKu09 grill-with-ui pattern):
     Interactive question cards, staged responses, visual diagrams/prototypes.
  2. The Mission Cockpit (Uncle Bob SwarmForge pattern):
     TDD Task Kanban, Gate approval semaphores (P03, P04, P08), and artifact inspection.
"""

from __future__ import annotations

import argparse
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

# Base directories
HERE = Path(__file__).resolve().parent
UI_DIR = HERE / "ui"
DEFAULT_PORT = 4242
COCKPIT_HOME = Path(os.environ.get("Q_COCKPIT_HOME") or os.environ.get("GRILL_HOME") or (Path.home() / ".q-cockpit"))


def get_git_root(cwd: Optional[Path] = None) -> Path:
    """Resolve the git common root or fallback to cwd."""
    target = cwd or Path.cwd()
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=target,
            capture_output=True,
            text=True,
            check=True,
        )
        common_dir = Path(res.stdout.strip())
        return common_dir.parent.resolve()
    except Exception:
        return target.resolve()


def project_key(root: Path) -> str:
    """Generate safe directory key from root path."""
    return re.sub(r"^[/\\]+", "", str(root)).replace("/", "-").replace("\\", "-").replace(":", "-")


class SessionManager:
    """Manages sessions on disk with zero external dependencies."""

    def __init__(self, base_home: Path = COCKPIT_HOME):
        self.base_home = base_home
        self.sessions_root = self.base_home / "sessions"
        self.sessions_root.mkdir(parents=True, exist_ok=True)

    def get_project_sessions_dir(self, p_key: str) -> Path:
        p_dir = self.sessions_root / p_key
        p_dir.mkdir(parents=True, exist_ok=True)
        return p_dir

    def create_session(self, root: Path, topic: str, doc_path: Optional[str] = None) -> Path:
        p_key = project_key(root)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        session_dir = self.get_project_sessions_dir(p_key) / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)

        target_doc = doc_path or f"docs/{re.sub(r'[^a-zA-Z0-9_-]', '-', topic.lower())}-design.md"

        state = {
            "version": "2.0.0",
            "topic": topic,
            "doc": target_doc,
            "project_root": str(root),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "interviewing",  # interviewing | visualizing | approved | finished
            "questions": [],
            "threads": [],
            "gates": {
                "P03_metaorchestration": {"status": "pending", "updated_at": None, "notes": ""},
                "P04_scope_freeze": {"status": "pending", "updated_at": None, "notes": ""},
                "P08_deploy_gate": {"status": "pending", "updated_at": None, "notes": ""},
            },
        }

        self.write_json(session_dir / "state.json", state)
        # Touch events.jsonl
        (session_dir / "events.jsonl").touch(exist_ok=True)
        return session_dir

    def get_latest_session(self, root: Path) -> Optional[Path]:
        p_key = project_key(root)
        p_dir = self.get_project_sessions_dir(p_key)
        sessions = sorted([s for s in p_dir.iterdir() if s.is_dir()], reverse=True)
        return sessions[0] if sessions else None

    @staticmethod
    def read_json(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def write_json(path: Path, data: Dict[str, Any]) -> None:
        tmp = path.with_suffix(f".tmp.{os.getpid()}")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        tmp.replace(path)

    @staticmethod
    def append_event(session_dir: Path, event: Dict[str, Any]) -> None:
        events_file = session_dir / "events.jsonl"
        event_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **event,
        }
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_record, ensure_ascii=False) + "\n")


class ProjectScanner:
    """Scans project repository for tasks, constitution, git status, and artifacts."""

    @staticmethod
    def scan_git_info(root: Path) -> Dict[str, Any]:
        info: Dict[str, Any] = {"branch": "unknown", "clean": True, "diff": "", "recent_commits": []}
        try:
            b_res = subprocess.run(
                ["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=True
            )
            info["branch"] = b_res.stdout.strip()

            s_res = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
            info["clean"] = len(s_res.stdout.strip()) == 0

            l_res = subprocess.run(
                ["git", "log", "-5", "--pretty=format:%h|%an|%ar|%s"],
                cwd=root,
                capture_output=True,
                text=True,
            )
            commits = []
            for line in l_res.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|", 3)
                    if len(parts) == 4:
                        commits.append({"hash": parts[0], "author": parts[1], "relative": parts[2], "message": parts[3]})
            info["recent_commits"] = commits
        except Exception:
            pass
        return info

    @staticmethod
    def scan_tasks(root: Path) -> List[Dict[str, Any]]:
        """Parse tasks from tasks.md, openspec/, or standard task files."""
        tasks: List[Dict[str, Any]] = []
        candidate_paths = [
            root / "tasks.md",
            root / "openspec" / "tasks.md",
            root / "docs" / "tasks.md",
        ]

        found_file = None
        for p in candidate_paths:
            if p.exists():
                found_file = p
                break

        if not found_file:
            # Check q-tasks or odd/tasks directories (ODD Bitácora)
            for tasks_dir in [root / "q-tasks", root / "odd" / "tasks", root / "openspec"]:
                if tasks_dir.exists():
                    for md in sorted(tasks_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True):
                        found_file = md
                        break
                    if found_file:
                        break

        if found_file:
            content = found_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                line_s = line.strip()
                match = re.match(r"^-\s*\[([ xX~])\]\s*(.+)$", line_s)
                if match:
                    mark = match.group(1).lower()
                    text = match.group(2)
                    status = "done" if mark == "x" else ("in_progress" if mark == "~" else "todo")
                    
                    # Extract wave metadata if present (e.g. [Wave 1], [W1], Wave 1)
                    wave = None
                    wave_match = re.search(r"\[(Wave\s*\d+|W\d+)\]|\b(Wave\s*\d+)\b", text, re.IGNORECASE)
                    if wave_match:
                        raw_wave = wave_match.group(1) or wave_match.group(2)
                        wave = raw_wave.strip().replace("W", "Wave ").replace("Wave  ", "Wave ").title()

                    task_entry = {"text": text, "status": status, "source": found_file.name}
                    if wave:
                        task_entry["wave"] = wave
                    tasks.append(task_entry)

        # Provide defaults if none found
        if not tasks:
            tasks = [
                {"text": "P01 Discovery & Audit Baseline", "status": "done", "source": "q-agent-pipeline"},
                {"text": "P02 Architectural & Hexagonal Scaffolding", "status": "done", "source": "q-agent-pipeline"},
                {"text": "P04 Scope & Elicitation Gate (/propose)", "status": "in_progress", "source": "q-agent-pipeline"},
                {"text": "P05 BDD Spec Definitions (Given/When/Then)", "status": "todo", "source": "q-agent-pipeline"},
                {"text": "P07 Atomic TDD Task Matrix", "status": "todo", "source": "q-agent-pipeline"},
                {"text": "P08 Reproduction-First Implementation", "status": "todo", "source": "q-agent-pipeline"},
            ]
        return tasks

    @staticmethod
    def scan_artifacts(root: Path) -> List[Dict[str, Any]]:
        artifacts = []
        targets = [
            ("CONSTITUTION.md", "Core Governance"),
            ("README.md", "Documentation"),
            ("SKILL.md", "Agent Definition"),
            ("CLAUDE.md", "Agent Instructions"),
            ("docs/adr", "Architectural Decision Records"),
            ("openspec", "OpenSpec Contract"),
        ]
        for rel_path, category in targets:
            full = root / rel_path
            if full.exists():
                artifacts.append({
                    "name": rel_path,
                    "category": category,
                    "is_dir": full.is_dir(),
                    "size_bytes": full.stat().st_size if full.is_file() else sum(f.stat().st_size for f in full.glob("**/*") if f.is_file()),
                })
        return artifacts


class CockpitHTTPHandler(http.server.BaseHTTPRequestHandler):
    project_root: Path = Path.cwd()
    session_manager: SessionManager
    active_session_dir: Optional[Path] = None

    def log_message(self, format: str, *args: Any) -> None:
        # Keep server console clean
        pass

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            self.serve_ui()
        elif path == "/visual":
            self.serve_visual()
        elif path == "/api/status":
            self.serve_api_status()
        elif path == "/api/diff":
            self.serve_api_diff()
        elif path == "/api/file":
            self.serve_api_file(parse_qs(parsed.query))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get("Content-Length", 0))
        raw_data = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            body = json.loads(raw_data)
        except json.JSONDecodeError:
            body = {}

        if path == "/api/grill/answer":
            self.handle_grill_answer(body)
        elif path == "/api/gate/action":
            self.handle_gate_action(body)
        elif path == "/api/grill/add_question":
            self.handle_add_question(body)
        elif path == "/api/session/new":
            self.handle_new_session(body)
        else:
            self.send_error(404, "Unknown API Action")

    def serve_ui(self) -> None:
        index_file = UI_DIR / "index.html"
        if not index_file.exists():
            self.send_error(500, "UI template not found")
            return
        content = index_file.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def serve_visual(self) -> None:
        if self.active_session_dir:
            vis_file = self.active_session_dir / "visual.html"
            if vis_file.exists():
                content = vis_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        placeholder = (
            "<!DOCTYPE html><html><body style='font-family:sans-serif;color:#888;padding:40px;text-align:center;'>"
            "<h3>No visual prototype or diagram generated yet.</h3>"
            "<p>When an agent generates visual.html or a Mermaid diagram, it will render here live.</p>"
            "</body></html>"
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(placeholder)))
        self.end_headers()
        self.wfile.write(placeholder)

    def serve_api_status(self) -> None:
        # Load or refresh active session state
        session_state = {}
        if not self.active_session_dir or not self.active_session_dir.exists():
            self.active_session_dir = self.session_manager.get_latest_session(self.project_root)

        if self.active_session_dir and (self.active_session_dir / "state.json").exists():
            session_state = self.session_manager.read_json(self.active_session_dir / "state.json")
        else:
            # Fallback mock session for visual preview
            session_state = {
                "topic": "q-agent Default Workspace",
                "doc": "docs/architecture-design.md",
                "status": "ready",
                "questions": [
                    {
                        "id": "q1",
                        "title": "Aislamiento de Entorno",
                        "question": "¿Deseás forzar Git Worktrees en el directorio hermano '../{repo}-worktrees/' para aislar los agentes?",
                        "recommendation": "Recomendado: Sí, evita colisiones de checkout en tu editor principal.",
                        "status": "unanswered",
                    },
                    {
                        "id": "q2",
                        "title": "Estrategia TDD",
                        "question": "¿El pipeline debe rechazar cualquier implementación sin un test en ROJO confirmado?",
                        "recommendation": "Recomendado: Sí, Reproduction-First previene alucinaciones y vibe-coding.",
                        "status": "unanswered",
                    },
                ],
                "gates": {
                    "P03_metaorchestration": {"status": "approved", "updated_at": "2026-09-18T14:00:00Z", "notes": "Dual Engine validado"},
                    "P04_scope_freeze": {"status": "pending", "updated_at": None, "notes": "Esperando elicitation"},
                    "P08_deploy_gate": {"status": "pending", "updated_at": None, "notes": "Pendiente de TDD"},
                },
            }

        git_info = ProjectScanner.scan_git_info(self.project_root)
        tasks = ProjectScanner.scan_tasks(self.project_root)
        artifacts = ProjectScanner.scan_artifacts(self.project_root)

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": {
                "name": self.project_root.name,
                "path": str(self.project_root),
                "git": git_info,
            },
            "session": session_state,
            "tasks": tasks,
            "artifacts": artifacts,
            "has_visual": bool(self.active_session_dir and (self.active_session_dir / "visual.html").exists()),
        }

        self.send_json(payload)

    def serve_api_diff(self) -> None:
        diff_text = ""
        try:
            res = subprocess.run(["git", "diff", "HEAD"], cwd=self.project_root, capture_output=True, text=True)
            diff_text = res.stdout
        except Exception as e:
            diff_text = f"Error capturing diff: {e}"
        self.send_json({"diff": diff_text})

    def serve_api_file(self, query: Dict[str, List[str]]) -> None:
        rel_path = query.get("path", [""])[0]
        if not rel_path:
            self.send_error(400, "Missing path parameter")
            return

        target = (self.project_root / rel_path).resolve()
        # Security check: must stay within project root
        if not str(target).startswith(str(self.project_root.resolve())):
            self.send_error(403, "Access Denied")
            return

        if not target.exists() or target.is_dir():
            self.send_error(404, "File not found")
            return

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            self.send_json({"path": rel_path, "content": content})
        except Exception as e:
            self.send_error(500, str(e))

    def handle_grill_answer(self, body: Dict[str, Any]) -> None:
        if not self.active_session_dir:
            self.send_error(400, "No active session")
            return

        # Record event in events.jsonl
        self.session_manager.append_event(self.active_session_dir, {
            "type": "answer_submitted",
            "answers": body.get("answers", {}),
            "feedback": body.get("feedback", ""),
        })

        # Update state.json questions status
        state_file = self.active_session_dir / "state.json"
        if state_file.exists():
            state = self.session_manager.read_json(state_file)
            answers = body.get("answers", {})
            for q in state.get("questions", []):
                qid = q.get("id")
                if qid in answers:
                    q["status"] = "answered"
                    q["user_answer"] = answers[qid]
            self.session_manager.write_json(state_file, state)

        self.send_json({"status": "ok", "message": "Answers recorded"})

    def handle_gate_action(self, body: Dict[str, Any]) -> None:
        gate_name = body.get("gate")
        action = body.get("action")  # approve | reject
        notes = body.get("notes", "")

        if not gate_name or action not in ["approve", "reject"]:
            self.send_error(400, "Invalid gate action")
            return

        if self.active_session_dir:
            self.session_manager.append_event(self.active_session_dir, {
                "type": "gate_decision",
                "gate": gate_name,
                "action": action,
                "notes": notes,
            })
            state_file = self.active_session_dir / "state.json"
            if state_file.exists():
                state = self.session_manager.read_json(state_file)
                gates = state.setdefault("gates", {})
                gates[gate_name] = {
                    "status": "approved" if action == "approve" else "rejected",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "notes": notes,
                }
                self.session_manager.write_json(state_file, state)

        self.send_json({"status": "ok", "gate": gate_name, "decision": action})

    def handle_add_question(self, body: Dict[str, Any]) -> None:
        if not self.active_session_dir:
            self.send_error(400, "No active session")
            return

        state_file = self.active_session_dir / "state.json"
        if not state_file.exists():
            self.send_error(400, "state.json missing")
            return

        state = self.session_manager.read_json(state_file)
        questions = state.setdefault("questions", [])
        new_q = {
            "id": f"q{len(questions) + 1}",
            "title": body.get("title", f"Pregunta #{len(questions) + 1}"),
            "question": body.get("question", ""),
            "recommendation": body.get("recommendation", ""),
            "status": "unanswered",
        }
        questions.append(new_q)
        self.session_manager.write_json(state_file, state)
        self.send_json({"status": "ok", "question": new_q})

    def handle_new_session(self, body: Dict[str, Any]) -> None:
        topic = body.get("topic", "Architectural Review")
        doc = body.get("doc")
        new_session = self.session_manager.create_session(self.project_root, topic, doc)
        self.active_session_dir = new_session
        self.send_json({"status": "ok", "session_dir": str(new_session)})

    def send_json(self, data: Any, code: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_server(port: int = DEFAULT_PORT, project_dir: Optional[Path] = None, session_dir: Optional[Path] = None) -> None:
    root = get_git_root(project_dir or Path.cwd())
    manager = SessionManager()

    active_session = session_dir
    if not active_session:
        active_session = manager.get_latest_session(root)
        if not active_session:
            active_session = manager.create_session(root, topic=f"Auditoría y Plan {root.name}")

    CockpitHTTPHandler.project_root = root
    CockpitHTTPHandler.session_manager = manager
    CockpitHTTPHandler.active_session_dir = active_session

    print(f"\n🚀 [q-cockpit] Cockpit Web Server running at:")
    print(f"   ➜ http://localhost:{port}")
    print(f"   📁 Project: {root}")
    print(f"   🏷️  Session: {active_session.name if active_session else 'Default'}")
    print(f"   💡 Zero Node.js / Pure Python 3 runtime.\n")

    with ThreadedTCPServer(("0.0.0.0", port), CockpitHTTPHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down q-cockpit...")
            httpd.shutdown()


def cli_main() -> None:
    parser = argparse.ArgumentParser(description="q-cockpit: Visual Elicitation & Mission Cockpit for q-agent")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # serve command
    serve_p = subparsers.add_parser("serve", help="Launch interactive web cockpit")
    serve_p.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind (default: 4242)")
    serve_p.add_argument("--project", type=str, default=None, help="Target project directory")
    serve_p.add_argument("--session", type=str, default=None, help="Specific session directory")

    # new session
    new_p = subparsers.add_parser("new", help="Create a new interview session")
    new_p.add_argument("--topic", type=str, required=True, help="Topic of the interview/grill")
    new_p.add_argument("--doc", type=str, default=None, help="Target markdown design doc path")
    new_p.add_argument("--project", type=str, default=None, help="Target project directory")

    # wait command (for agent CLI integration)
    wait_p = subparsers.add_parser("wait", help="Wait for user input in events.jsonl")
    wait_p.add_argument("--session", type=str, required=True, help="Session directory to watch")
    wait_p.add_argument("--timeout", type=int, default=300, help="Max wait time in seconds")

    args = parser.parse_args()

    if args.command == "serve":
        p_dir = Path(args.project).resolve() if args.project else None
        s_dir = Path(args.session).resolve() if args.session else None
        run_server(port=args.port, project_dir=p_dir, session_dir=s_dir)

    elif args.command == "new":
        root = get_git_root(Path(args.project).resolve() if args.project else Path.cwd())
        mgr = SessionManager()
        sess = mgr.create_session(root, args.topic, args.doc)
        print(json.dumps({
            "status": "created",
            "session_dir": str(sess),
            "topic": args.topic,
            "project": str(root),
        }, indent=2))

    elif args.command == "wait":
        sess_dir = Path(args.session).resolve()
        events_file = sess_dir / "events.jsonl"
        if not events_file.exists():
            print(f"Error: {events_file} does not exist", file=sys.stderr)
            sys.exit(1)

        start_size = events_file.stat().st_size
        start_time = time.time()
        print(f"Waiting for new events in {events_file}...")

        while time.time() - start_time < args.timeout:
            current_size = events_file.stat().st_size
            if current_size > start_size:
                with open(events_file, "r", encoding="utf-8") as f:
                    f.seek(start_size)
                    new_lines = f.readlines()
                print("".join(new_lines).strip())
                sys.exit(0)
            time.sleep(1)

        print("Timeout waiting for user input", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    cli_main()
