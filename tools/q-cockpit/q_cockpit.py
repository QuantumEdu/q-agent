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
import html
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

            # Calculate slice LOC count (heurística ~400 LOC)
            loc_res = subprocess.run(["git", "diff", "--numstat", "HEAD"], cwd=root, capture_output=True, text=True)
            stat_out = loc_res.stdout if (loc_res.returncode == 0 and loc_res.stdout.strip()) else ""
            if not stat_out.strip():
                loc_res2 = subprocess.run(["git", "diff", "--numstat", "HEAD~1..HEAD"], cwd=root, capture_output=True, text=True)
                if loc_res2.returncode == 0:
                    stat_out = loc_res2.stdout
            add_tot = 0
            del_tot = 0
            for line in stat_out.splitlines():
                p = line.strip().split("\t")
                if len(p) >= 3 and p[0].isdigit() and p[1].isdigit():
                    add_tot += int(p[0])
                    del_tot += int(p[1])
            info["slice_loc"] = add_tot + del_tot

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
            info["commit_sha"] = commits[0]["hash"] if commits else "unknown"
            info["latest_commit"] = commits[0] if commits else None
        except Exception:
            pass
        return info

    @staticmethod
    def get_project_version(root: Path) -> str:
        for fname in ["skill.json", "package.json"]:
            fpath = root / fname
            if fpath.is_file():
                try:
                    data = json.loads(fpath.read_text(encoding="utf-8"))
                    if "version" in data and data["version"]:
                        return str(data["version"])
                except Exception:
                    pass
        return "2.5.2"

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
            
            # 1. Parse Terminal Evidence Table if present
            # | Wave | Tarea ID | Comando Ejecutado en Terminal | Código de Salida (Exit Code) | Resultado Observado / Evidencia | Estado |
            evidence_map = {}
            for line in content.splitlines():
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 6:
                        t_id = parts[2].replace("`", "").strip().upper()
                        if t_id and (t_id.startswith("TASK-") or t_id.startswith("T-")):
                            evidence_map[t_id] = {
                                "cmd": parts[3].replace("`", "").strip(),
                                "exit_code": parts[4].replace("`", "").strip(),
                                "output": parts[5].strip(),
                                "status": parts[6].strip() if len(parts) > 6 else ""
                            }

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

                    # Extract task ID (e.g. TASK-01)
                    task_id = None
                    id_match = re.search(r"\b(TASK-\d+|T-\d+)\b", text, re.IGNORECASE)
                    if id_match:
                        task_id = id_match.group(1).upper()

                    # Extract commit hash if present
                    commit = None
                    commit_match = re.search(r"\(Commit:\s*([a-f0-9]+)\)", text, re.IGNORECASE)
                    if commit_match:
                        commit = commit_match.group(1)

                    task_entry = {"text": text, "status": status, "source": found_file.name}
                    if wave:
                        task_entry["wave"] = wave
                    if task_id:
                        task_entry["task_id"] = task_id
                        if task_id in evidence_map:
                            task_entry["evidence"] = evidence_map[task_id]
                    if commit:
                        task_entry["commit"] = commit

                    tasks.append(task_entry)

        return tasks

    @staticmethod
    def scan_artifacts(root: Path) -> List[Dict[str, Any]]:
        artifacts: List[Dict[str, Any]] = []
        seen = set()

        def add_item(file_path: Path, category: str):
            if not file_path.is_file():
                return
            try:
                rel = file_path.relative_to(root).as_posix()
            except ValueError:
                return
            if rel in seen:
                return
            seen.add(rel)
            st = file_path.stat()
            artifacts.append({
                "name": rel,
                "path": rel,
                "category": category,
                "size_bytes": st.st_size,
                "last_modified": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
                "is_dir": False,
            })

        # Core governance and project manifests
        add_item(root / "CONSTITUTION.md", "Core Governance")
        add_item(root / "README.md", "Documentation")
        add_item(root / "SKILL.md", "Agent Definition")
        add_item(root / "CHANGELOG.md", "Changelog")
        add_item(root / "CLAUDE.md", "Agent Instructions")
        add_item(root / "references" / "audit-manifest.yml", "Audit Manifest")

        # ODD task lists (odd/tasks/*.md)
        odd_tasks_dir = root / "odd" / "tasks"
        if odd_tasks_dir.is_dir():
            for md in sorted(odd_tasks_dir.glob("*.md")):
                add_item(md, "ODD Task List")

        # Audit deliverables (audit/*.md)
        audit_dir = root / "audit"
        if audit_dir.is_dir():
            for md in sorted(audit_dir.glob("*.md")):
                add_item(md, "Audit Deliverable")

        # Documentation (docs/**/*.md)
        docs_dir = root / "docs"
        if docs_dir.is_dir():
            for md in sorted(docs_dir.glob("**/*.md")):
                add_item(md, "Documentation")

        # OpenSpec contract
        openspec_dir = root / "openspec"
        if openspec_dir.is_dir():
            for md in sorted(openspec_dir.glob("**/*.md")):
                add_item(md, "OpenSpec Contract")

        artifacts.sort(key=lambda a: (a["category"], a["path"]))
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

    def _send_html(self, content: bytes) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _render_mermaid_page(self, diagrams: List[Dict[str, str]]) -> str:
        diagram_cards = []
        for idx, d in enumerate(diagrams):
            escaped_code = html.escape(d["code"])
            escaped_src = html.escape(d["source"])
            diagram_cards.append(f"""
    <div class="diagram-card" id="card-{idx}">
      <div class="diagram-header">
        <div class="diagram-title">
          <span>Diagrama #{idx+1} · Fuente: <code>{escaped_src}</code></span>
          <span class="badge">Mermaid.js Live</span>
        </div>
        <div class="zoom-toolbar">
          <button type="button" class="zoom-btn" onclick="zoomDiagram({idx}, -0.15)" title="Reducir zoom (Zoom Out)">[-]</button>
          <span class="zoom-badge" id="zoom-val-{idx}">100%</span>
          <button type="button" class="zoom-btn" onclick="zoomDiagram({idx}, 0.15)" title="Aumentar zoom (Zoom In)">[+]</button>
          <button type="button" class="zoom-btn" onclick="resetZoom({idx})" title="Tamaño real 100% (1:1)">[1:1]</button>
          <button type="button" class="zoom-btn" onclick="fitDiagram({idx})" title="Ajustar al ancho (Fit to width)">[↔ Fit]</button>
          <button type="button" class="zoom-btn" id="fullscreen-btn-{idx}" onclick="toggleFullscreen({idx})" title="Pantalla completa (Fullscreen)">[⛶]</button>
        </div>
      </div>
      <div class="diagram-body" id="body-{idx}">
        <div class="diagram-viewport" id="viewport-{idx}">
          <pre class="mermaid" id="mermaid-{idx}">{escaped_code}</pre>
          <div class="offline-fallback" style="display:none; font-family:monospace; font-size:12px; white-space:pre-wrap; color:#a5d6ff;">
            <code>{escaped_code}</code>
          </div>
        </div>
      </div>
    </div>
""")
        cards_html = "\n".join(diagram_cards)

        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>q-cockpit · Diagramas Inferidos</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    body {{
      background-color: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 20px;
    }}
    .header-bar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 12px;
      border-bottom: 1px solid #30363d;
    }}
    .header-title {{
      font-size: 15px;
      font-weight: 600;
      color: #f0f6fc;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .diagram-card {{
      background-color: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      margin-bottom: 24px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
      transition: all 0.2s ease;
    }}
    .diagram-card.is-fullscreen {{
      position: fixed !important;
      top: 0 !important;
      left: 0 !important;
      width: 100vw !important;
      height: 100vh !important;
      max-width: 100vw !important;
      max-height: 100vh !important;
      z-index: 99999 !important;
      margin: 0 !important;
      border-radius: 0 !important;
      border: none !important;
      background-color: rgba(13, 17, 23, 0.96) !important;
      backdrop-filter: blur(12px) !important;
      -webkit-backdrop-filter: blur(12px) !important;
      display: flex !important;
      flex-direction: column !important;
    }}
    .diagram-card.is-fullscreen .diagram-header {{
      background-color: #161b22;
      padding: 12px 20px;
      border-bottom: 1px solid #30363d;
    }}
    .diagram-card.is-fullscreen .diagram-body {{
      flex: 1 1 auto !important;
      height: calc(100vh - 54px) !important;
      max-height: calc(100vh - 54px) !important;
      min-height: 0 !important;
    }}
    .diagram-header {{
      background-color: #21262d;
      padding: 10px 16px;
      font-size: 12px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid #30363d;
      gap: 12px;
      flex-wrap: wrap;
    }}
    .diagram-title {{
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
    }}
    .zoom-toolbar {{
      display: flex;
      align-items: center;
      gap: 6px;
      user-select: none;
    }}
    .zoom-btn {{
      background-color: #21262d;
      color: #c9d1d9;
      border: 1px solid #30363d;
      border-radius: 6px;
      padding: 4px 10px;
      font-size: 12px;
      font-family: inherit;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: background-color 0.15s, border-color 0.15s, color 0.15s;
      line-height: 1.2;
    }}
    .zoom-btn:hover {{
      background-color: #30363d;
      color: #58a6ff;
      border-color: #58a6ff;
    }}
    .zoom-btn:active {{
      background-color: #1f6feb;
      color: #ffffff;
      border-color: #1f6feb;
    }}
    .zoom-badge {{
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      font-size: 11px;
      color: #8b949e;
      min-width: 44px;
      text-align: center;
      padding: 3px 6px;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 4px;
      user-select: none;
    }}
    .badge {{
      background-color: rgba(56, 189, 248, 0.15);
      color: #38bdf8;
      border: 1px solid rgba(56, 189, 248, 0.3);
      padding: 2px 8px;
      border-radius: 10px;
      font-size: 11px;
      font-family: monospace;
      font-weight: 600;
    }}
    .diagram-body {{
      height: 520px;
      min-height: 450px;
      max-height: 75vh;
      overflow: auto;
      scrollbar-width: thin;
      scrollbar-color: #388bfd #161b22;
      cursor: grab;
      user-select: none;
      position: relative;
      background-color: #0b0e14;
      padding: 24px;
      box-sizing: border-box;
    }}
    .diagram-body.is-dragging {{
      cursor: grabbing !important;
    }}
    .diagram-body::-webkit-scrollbar {{
      width: 8px;
      height: 8px;
    }}
    .diagram-body::-webkit-scrollbar-track {{
      background: #161b22;
    }}
    .diagram-body::-webkit-scrollbar-thumb {{
      background: #388bfd;
      border-radius: 4px;
    }}
    .diagram-body::-webkit-scrollbar-thumb:hover {{
      background: #58a6ff;
    }}
    .diagram-viewport {{
      transform-origin: 0 0;
      transition: transform 0.12s ease-out;
      display: inline-block;
      min-width: 100%;
    }}
    .mermaid svg,
    .diagram-viewport svg {{
      max-width: none !important;
      height: auto !important;
      display: block;
      margin: auto;
    }}
    pre.mermaid {{
      margin: 0;
      width: 100%;
      text-align: center;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      color: #79c0ff;
    }}
  </style>
</head>
<body>
  <div class="header-bar">
    <div class="header-title">
      <span>📊</span>
      <span>Diagramas de Arquitectura (Inferidos de Documentación)</span>
    </div>
    <span class="badge">{len(diagrams)} detectado(s)</span>
  </div>
  {cards_html}
  <script>
    if (typeof mermaid !== 'undefined') {{
      mermaid.initialize({{
        startOnLoad: true,
        theme: 'dark',
        themeVariables: {{
          darkMode: true,
          background: '#0b0e14',
          primaryColor: '#1f6feb',
          primaryTextColor: '#f0f6fc',
          primaryBorderColor: '#388bfd',
          lineColor: '#58a6ff',
          secondaryColor: '#238636',
          tertiaryColor: '#21262d'
        }}
      }});
    }} else {{
      document.querySelectorAll('.offline-fallback').forEach(el => el.style.display = 'block');
    }}

    const diagramStates = {{}};

    function getDiagramState(idx) {{
      if (!diagramStates[idx]) {{
        diagramStates[idx] = {{
          scale: 1.0,
          isDragging: false,
          startX: 0,
          startY: 0,
          scrollLeft: 0,
          scrollTop: 0
        }};
      }}
      return diagramStates[idx];
    }}

    function applyScale(idx) {{
      const state = getDiagramState(idx);
      const viewport = document.getElementById('viewport-' + idx);
      const badge = document.getElementById('zoom-val-' + idx);
      if (viewport) {{
        viewport.style.transform = `scale(${{state.scale}})`;
      }}
      if (badge) {{
        badge.textContent = Math.round(state.scale * 100) + '%';
      }}
    }}

    function zoomDiagram(idx, delta) {{
      const state = getDiagramState(idx);
      let newScale = state.scale + delta;
      newScale = Math.max(0.2, Math.min(4.0, Math.round(newScale * 100) / 100));
      state.scale = newScale;
      applyScale(idx);
    }}

    function zoom(idx, delta) {{
      zoomDiagram(idx, delta);
    }}

    function resetZoom(idx) {{
      const state = getDiagramState(idx);
      state.scale = 1.0;
      applyScale(idx);
      const body = document.getElementById('body-' + idx);
      if (body) {{
        body.scrollLeft = 0;
        body.scrollTop = 0;
      }}
    }}

    function fitDiagram(idx) {{
      const body = document.getElementById('body-' + idx);
      if (!body) return;
      const svg = body.querySelector('svg');
      if (!svg) return;
      const state = getDiagramState(idx);

      const availWidth = body.clientWidth - 48;
      if (availWidth <= 0) return;

      let naturalWidth = 0;
      if (svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width > 0) {{
        naturalWidth = svg.viewBox.baseVal.width;
      }} else if (svg.getBoundingClientRect().width > 0) {{
        naturalWidth = svg.getBoundingClientRect().width / (state.scale || 1.0);
      }}

      if (naturalWidth > 0) {{
        let fitScale = availWidth / naturalWidth;
        fitScale = Math.max(0.2, Math.min(4.0, Math.round(fitScale * 100) / 100));
        state.scale = fitScale;
        applyScale(idx);
        body.scrollLeft = 0;
        body.scrollTop = 0;
      }}
    }}

    function toggleFullscreen(idx) {{
      const card = document.getElementById('card-' + idx);
      if (!card) return;
      const isFull = card.classList.toggle('is-fullscreen');
      const btn = document.getElementById('fullscreen-btn-' + idx);
      if (btn) {{
        btn.textContent = isFull ? '[✕]' : '[⛶]';
        btn.title = isFull ? 'Salir de pantalla completa (Esc)' : 'Pantalla completa';
      }}
      if (isFull) {{
        document.body.style.overflow = 'hidden';
      }} else {{
        document.body.style.overflow = '';
      }}
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape') {{
        const fullCard = document.querySelector('.diagram-card.is-fullscreen');
        if (fullCard) {{
          const idx = fullCard.id.replace('card-', '');
          toggleFullscreen(idx);
        }}
      }}
    }});

    let activeDragIdx = null;
    let dragStartX = 0;
    let dragStartY = 0;
    let dragScrollLeft = 0;
    let dragScrollTop = 0;

    function initPanZoom() {{
      document.querySelectorAll('.diagram-body').forEach(body => {{
        const idx = body.id.replace('body-', '');

        body.addEventListener('mousedown', (e) => {{
          if (e.target.closest('button') || e.target.closest('a')) return;
          activeDragIdx = idx;
          dragStartX = e.clientX;
          dragStartY = e.clientY;
          dragScrollLeft = body.scrollLeft;
          dragScrollTop = body.scrollTop;
          body.classList.add('is-dragging');
        }});

        body.addEventListener('mousemove', (e) => {{
          if (activeDragIdx === idx) {{
            const dx = e.clientX - dragStartX;
            const dy = e.clientY - dragStartY;
            body.scrollLeft = dragScrollLeft - dx;
            body.scrollTop = dragScrollTop - dy;
          }}
        }});

        body.addEventListener('mouseup', () => {{
          if (activeDragIdx === idx) {{
            body.classList.remove('is-dragging');
            activeDragIdx = null;
          }}
        }});

        body.addEventListener('mouseleave', () => {{
          // Handled by window mouseup / mousemove
        }});

        body.addEventListener('wheel', (e) => {{
          if (e.ctrlKey || e.metaKey) {{
            e.preventDefault();
            const state = getDiagramState(idx);
            const delta = e.deltaY < 0 ? 0.15 : -0.15;
            const oldScale = state.scale;
            let newScale = oldScale + delta;
            newScale = Math.max(0.2, Math.min(4.0, Math.round(newScale * 100) / 100));
            if (newScale !== oldScale) {{
              const rect = body.getBoundingClientRect();
              const mouseX = e.clientX - rect.left;
              const mouseY = e.clientY - rect.top;
              state.scale = newScale;
              applyScale(idx);
              body.scrollLeft = (body.scrollLeft + mouseX) * (newScale / oldScale) - mouseX;
              body.scrollTop = (body.scrollTop + mouseY) * (newScale / oldScale) - mouseY;
            }}
          }}
        }}, {{ passive: false }});
      }});

      window.addEventListener('mousemove', (e) => {{
        if (activeDragIdx === null) return;
        const body = document.getElementById('body-' + activeDragIdx);
        if (!body) return;
        e.preventDefault();
        const dx = e.clientX - dragStartX;
        const dy = e.clientY - dragStartY;
        body.scrollLeft = dragScrollLeft - dx;
        body.scrollTop = dragScrollTop - dy;
      }});

      window.addEventListener('mouseup', () => {{
        if (activeDragIdx !== null) {{
          const body = document.getElementById('body-' + activeDragIdx);
          if (body) {{
            body.classList.remove('is-dragging');
          }}
          activeDragIdx = null;
        }}
      }});
    }}

    initPanZoom();
  </script>
</body>
</html>"""

    def _render_blueprint_page(self) -> str:
        project_name = html.escape(self.project_root.name)
        return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>q-cockpit · Blueprint de Arquitectura</title>
  <style>
    body {{
      background-color: #0d1117;
      color: #c9d1d9;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 28px;
    }}
    .blueprint-card {{
      background-color: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 24px;
      max-width: 820px;
      margin: 0 auto;
    }}
    .blueprint-header {{
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid #30363d;
      padding-bottom: 16px;
      margin-bottom: 20px;
    }}
    .header-text h2 {{
      margin: 0 0 4px 0;
      font-size: 18px;
      color: #f0f6fc;
    }}
    .header-text p {{
      margin: 0;
      font-size: 12px;
      color: #8b949e;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin: 20px 0;
    }}
    .box {{
      background-color: #21262d;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 14px;
    }}
    .box-title {{
      font-size: 13px;
      font-weight: 600;
      color: #58a6ff;
      margin-bottom: 6px;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .box-desc {{
      font-size: 12px;
      color: #8b949e;
      line-height: 1.4;
    }}
    .hint-container {{
      background-color: rgba(56, 189, 248, 0.08);
      border-left: 3px solid #38bdf8;
      border-radius: 0 6px 6px 0;
      padding: 14px 18px;
      font-size: 13px;
      color: #a5d6ff;
      line-height: 1.5;
      margin-top: 20px;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
      color: #79c0ff;
      background-color: rgba(110, 118, 129, 0.4);
      padding: 2px 5px;
      border-radius: 4px;
      font-size: 12px;
    }}
  </style>
</head>
<body>
  <div class="blueprint-card">
    <div class="blueprint-header">
      <div style="font-size: 28px;">🏛️</div>
      <div class="header-text">
        <h2>Vista Arquitectónica & Blueprint</h2>
        <p>Espacio de trabajo: <strong>{project_name}</strong></p>
      </div>
    </div>

    <p style="font-size: 13px; color: #c9d1d9; line-height: 1.5; margin-bottom: 16px;">
      No se ha generado aún un prototipo visual interactivo (<code>visual.html</code>) ni se detectaron diagramas Mermaid embebidos en la documentación (<code>README.md</code>, <code>odd/tasks/*.md</code>, <code>docs/**/*.md</code>).
    </p>

    <div class="grid">
      <div class="box">
        <div class="box-title"><span>📜</span> Gobernanza & Specs</div>
        <div class="box-desc">Auditoría atómica, constitución del proyecto y especificaciones técnicas.</div>
      </div>
      <div class="box">
        <div class="box-title"><span>⚡</span> Flujo ODD & Slices</div>
        <div class="box-desc">Bitácoras en <code>odd/tasks/</code> con límites controlados de ~400 LOC.</div>
      </div>
      <div class="box">
        <div class="box-title"><span>🛡️</span> Quality Gates & TDD</div>
        <div class="box-desc">Verificación Reproduction-First en terminal antes de deploy.</div>
      </div>
    </div>

    <div class="hint-container">
      <strong>💡 Cómo visualizar diagramas automáticamente:</strong><br>
      Agrega bloques <code>```mermaid</code> a cualquier archivo Markdown de tu proyecto (como <code>README.md</code> o bitácoras en <code>odd/tasks/</code>), o genera un prototipo <code>visual.html</code> durante la sesión de elicitación. El Cockpit lo detectará y renderizará en tiempo real.
    </div>
  </div>
</body>
</html>"""

    def serve_visual(self) -> None:
        if self.active_session_dir:
            vis_file = self.active_session_dir / "visual.html"
            if vis_file.is_file():
                content = vis_file.read_bytes()
                self._send_html(content)
                return

        root_vis = self.project_root / "visual.html"
        if root_vis.is_file():
            content = root_vis.read_bytes()
            self._send_html(content)
            return

        # Scan Markdown files for Mermaid diagrams
        diagrams: List[Dict[str, str]] = []
        md_candidates: List[Path] = []
        readme = self.project_root / "README.md"
        if readme.is_file():
            md_candidates.append(readme)

        odd_tasks = self.project_root / "odd" / "tasks"
        if odd_tasks.is_dir():
            md_candidates.extend(sorted(odd_tasks.glob("*.md")))

        docs_dir = self.project_root / "docs"
        if docs_dir.is_dir():
            md_candidates.extend(sorted(docs_dir.glob("**/*.md")))

        mermaid_pattern = re.compile(r"```mermaid\s*\n(.*?)\n```", re.DOTALL)
        for md_path in md_candidates:
            try:
                rel = md_path.relative_to(self.project_root).as_posix()
                text = md_path.read_text(encoding="utf-8", errors="replace")
                for match in mermaid_pattern.finditer(text):
                    code = match.group(1).strip()
                    if code:
                        diagrams.append({"source": rel, "code": code})
            except Exception:
                continue

        if diagrams:
            html_content = self._render_mermaid_page(diagrams)
            self._send_html(html_content.encode("utf-8"))
            return

        # Fallback architecture blueprint
        html_content = self._render_blueprint_page()
        self._send_html(html_content.encode("utf-8"))

    def serve_api_status(self) -> None:
        # Load or refresh active session state
        session_state = {}
        if not self.active_session_dir or not self.active_session_dir.exists():
            self.active_session_dir = self.session_manager.get_latest_session(self.project_root)

        if self.active_session_dir and (self.active_session_dir / "state.json").exists():
            session_state = self.session_manager.read_json(self.active_session_dir / "state.json")
        else:
            session_state = {
                "topic": "q-agent Workspace",
                "status": "idle",
                "questions": [],
                "gates": {},
            }

        git_info = ProjectScanner.scan_git_info(self.project_root)
        tasks = ProjectScanner.scan_tasks(self.project_root)
        artifacts = ProjectScanner.scan_artifacts(self.project_root)
        project_version = ProjectScanner.get_project_version(self.project_root)

        # Detect active vs idle:
        # If no active interview questions and no in-progress tasks, status = "idle"
        unanswered_questions = [
            q for q in session_state.get("questions", [])
            if q.get("status") not in ("answered", "resolved")
        ]
        in_progress_tasks = [
            t for t in tasks
            if t.get("status") == "in_progress"
        ]

        if not unanswered_questions and not in_progress_tasks:
            project_status = "idle"
            active_phase = None
        else:
            project_status = "active"
            if unanswered_questions:
                active_phase = session_state.get("phase") or "P04"
            else:
                active_phase = session_state.get("phase") or "P08"

        has_visual = bool(
            (self.active_session_dir and (self.active_session_dir / "visual.html").exists())
            or (self.project_root / "visual.html").exists()
        )

        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "project": {
                "name": self.project_root.name,
                "path": str(self.project_root),
                "version": project_version,
                "status": project_status,
                "active_phase": active_phase,
                "git": git_info,
            },
            "session": session_state,
            "tasks": tasks,
            "artifacts": artifacts,
            "has_visual": has_visual,
        }

        self.send_json(payload)

    def serve_api_diff(self) -> None:
        diff_text = ""
        additions = 0
        deletions = 0
        files_list = []
        try:
            res = subprocess.run(["git", "diff", "HEAD"], cwd=self.project_root, capture_output=True, text=True)
            diff_text = res.stdout if res.returncode == 0 else ""
            if not diff_text.strip():
                # If working tree is clean, show diff of latest commit
                res2 = subprocess.run(["git", "diff", "HEAD~1..HEAD"], cwd=self.project_root, capture_output=True, text=True)
                if res2.returncode == 0 and res2.stdout.strip():
                    diff_text = res2.stdout

            # Parse numstat
            n_res = subprocess.run(["git", "diff", "--numstat", "HEAD"], cwd=self.project_root, capture_output=True, text=True)
            stat_out = n_res.stdout if (n_res.returncode == 0 and n_res.stdout.strip()) else ""
            if not stat_out.strip():
                n_res2 = subprocess.run(["git", "diff", "--numstat", "HEAD~1..HEAD"], cwd=self.project_root, capture_output=True, text=True)
                if n_res2.returncode == 0:
                    stat_out = n_res2.stdout

            for line in stat_out.splitlines():
                parts = line.strip().split("\t")
                if len(parts) >= 3:
                    a = int(parts[0]) if parts[0].isdigit() else 0
                    d = int(parts[1]) if parts[1].isdigit() else 0
                    additions += a
                    deletions += d
                    files_list.append({"file": parts[2], "add": a, "del": d})
        except Exception as e:
            diff_text = f"Error capturing diff: {e}"

        self.send_json({
            "diff": diff_text,
            "stats": {
                "files_changed": len(files_list),
                "additions": additions,
                "deletions": deletions,
                "total_loc": additions + deletions,
                "files": files_list,
            }
        })

    def serve_api_file(self, query: Dict[str, List[str]]) -> None:
        rel_path = query.get("path", [""])[0]
        if not rel_path:
            self.send_error(400, "Missing path parameter")
            return

        target = (self.project_root / rel_path).resolve()
        # Security check: must stay strictly within project root
        try:
            target.relative_to(self.project_root.resolve())
        except ValueError:
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

    def _set_cors_headers(self) -> None:
        origin = self.headers.get("Origin", "")
        if origin:
            parsed = urlparse(origin)
            if parsed.hostname in ("localhost", "127.0.0.1", "::1"):
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.send_header("Vary", "Origin")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def send_json(self, data: Any, code: int = 200) -> None:
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(raw)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def run_server(port: int = DEFAULT_PORT, project_dir: Optional[Path] = None, session_dir: Optional[Path] = None, host: str = "127.0.0.1") -> None:
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
    print(f"   ➜ http://{host}:{port}")
    print(f"   📁 Project: {root}")
    print(f"   🏷️  Session: {active_session.name if active_session else 'Default'}")
    print(f"   💡 Zero Node.js / Pure Python 3 runtime.\n")

    with ThreadedTCPServer((host, port), CockpitHTTPHandler) as httpd:
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
    serve_p.add_argument("--host", type=str, default="127.0.0.1", help="Host interface to bind (default: 127.0.0.1)")
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
        run_server(port=args.port, project_dir=p_dir, session_dir=s_dir, host=args.host)

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
