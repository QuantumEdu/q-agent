#!/usr/bin/env python3
"""
q_cockpit_tui: Zero-dependency ANSI Terminal User Interface for q-agent.
Cross-platform: Windows (CMD / PowerShell / Windows Terminal), Linux, macOS, WSL.

Features:
  - Header: Project Name, Version, Git Branch, Status (IDLE/ACTIVE), Slice LOC.
  - View [1]: Dashboard Overview (active phase, quality gates, metrics).
  - View [2]: Kanban Tasks (Backlog, In Progress, Done with terminal evidence).
  - View [3]: Git Commits & Diff Summary (recent commits, working tree, slice LOC).
  - View [4]: SkillVault Explorer (search/browse skills, display skill content).
  - Navigation: Keys '1', '2', '3', '4', 'r' (refresh), 'q' (quit).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure UTF-8 encoding on standard streams to avoid Windows cp1252 charmap errors
for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

# Enable ANSI color escape sequences on Windows console
if sys.platform == "win32":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        hOut = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        mode = ctypes.c_ulong()
        if kernel32.GetConsoleMode(hOut, ctypes.byref(mode)):
            kernel32.SetConsoleMode(hOut, mode.value | 0x0004)  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        pass
    os.system("")

# Import scanners from sibling q_cockpit module
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

try:
    from q_cockpit import ProjectScanner, SessionManager, get_git_root
except ImportError:
    from tools.q_cockpit.q_cockpit import ProjectScanner, SessionManager, get_git_root

# ANSI Escape Sequences
CLEAR_SCREEN = "\033[2J\033[H"
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
UNDERLINE = "\033[4m"

# Colors
C_RED = "\033[31m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_BLUE = "\033[34m"
C_MAGENTA = "\033[35m"
C_CYAN = "\033[36m"
C_WHITE = "\033[37m"

C_BR_BLACK = "\033[90m"
C_BR_RED = "\033[91m"
C_BR_GREEN = "\033[92m"
C_BR_YELLOW = "\033[93m"
C_BR_BLUE = "\033[94m"
C_BR_MAGENTA = "\033[95m"
C_BR_CYAN = "\033[96m"
C_BR_WHITE = "\033[97m"

BG_BLUE = "\033[44m"
BG_DARK = "\033[48;5;236m"
BG_CARD = "\033[48;5;235m"


def get_key() -> str:
    """Read a single keypress without waiting for Enter (cross-platform)."""
    if not sys.stdin.isatty():
        return "q"

    if sys.platform == "win32":
        try:
            import msvcrt
            ch = msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                return "arrow"
            return ch.decode("utf-8", errors="ignore").lower()
        except Exception:
            return "q"
    else:
        try:
            import select
            import termios
            import tty

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    ch = sys.stdin.read(1)
                    return ch.lower()
                return ""
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception:
            return "q"


class CockpitTUI:
    """Interactive zero-dependency terminal dashboard."""

    def __init__(self, project_dir: Optional[Path] = None, initial_view: int = 1):
        self.root = get_git_root(project_dir or Path.cwd())
        self.current_view = initial_view
        self.selected_skill_index: Optional[int] = None
        self.session_mgr = SessionManager()
        self.data: Dict[str, Any] = {}
        self.refresh_data()

    def refresh_data(self) -> None:
        """Scan project repository and load fresh state."""
        git_info = ProjectScanner.scan_git_info(self.root)
        version = ProjectScanner.get_project_version(self.root)
        tasks = ProjectScanner.scan_tasks(self.root)
        artifacts = ProjectScanner.scan_artifacts(self.root)
        skillvault = ProjectScanner.scan_skillvault(self.root)

        active_session_dir = self.session_mgr.get_latest_session(self.root)
        session_state: Dict[str, Any] = {}
        if active_session_dir and (active_session_dir / "state.json").exists():
            session_state = self.session_mgr.read_json(active_session_dir / "state.json")

        unanswered = [
            q for q in session_state.get("questions", [])
            if q.get("status") not in ("answered", "resolved")
        ]
        in_progress = [t for t in tasks if t.get("status") == "in_progress"]

        if not unanswered and not in_progress:
            status = "idle"
            active_phase = None
        else:
            status = "active"
            active_phase = session_state.get("phase") or ("P04" if unanswered else "P08")

        self.data = {
            "root": self.root,
            "project_name": self.root.name,
            "version": version,
            "git": git_info,
            "tasks": tasks,
            "artifacts": artifacts,
            "skillvault": skillvault,
            "session": session_state,
            "status": status,
            "active_phase": active_phase,
        }

    def render_header(self, width: int) -> List[str]:
        """Render top navbar and global status line."""
        name = self.data.get("project_name", "q-agent")
        ver = f"v{self.data.get('version', '2.5.2')}"
        branch = self.data["git"].get("branch", "unknown")
        status = self.data.get("status", "idle").upper()
        slice_loc = self.data["git"].get("slice_loc", 0)

        # Slice heuristic indicator
        if slice_loc > 400:
            slice_col = f"{C_BR_RED}{BOLD}{slice_loc}/400 LOC (EXCEEDED){RESET}"
        elif slice_loc >= 320:
            slice_col = f"{C_BR_YELLOW}{BOLD}{slice_loc}/400 LOC (WARN){RESET}"
        else:
            slice_col = f"{C_BR_GREEN}{slice_loc}/400 LOC (SAFE){RESET}"

        status_badge = f"{C_BR_GREEN}🟢 ACTIVE{RESET}" if status == "ACTIVE" else f"{C_BR_BLACK}⚪ IDLE{RESET}"

        line1 = f" {C_BR_CYAN}{BOLD}⚡ Q-COCKPIT TUI{RESET} · {BOLD}{name}{RESET} {C_BR_BLACK}{ver}{RESET}  │  Branch: {C_BR_WHITE}{branch}{RESET}  │  Status: {status_badge}  │  Slice: {slice_col}"
        
        # Tabs bar
        tabs = [
            ("[1] Dashboard", 1),
            ("[2] Kanban Tasks", 2),
            ("[3] Git Diff", 3),
            ("[4] SkillVault", 4),
        ]
        tab_strs = []
        for label, vid in tabs:
            if vid == self.current_view:
                tab_strs.append(f"{C_BR_CYAN}{BOLD}▶ {label}{RESET}")
            else:
                tab_strs.append(f"{C_BR_BLACK}  {label}{RESET}")

        tabs_line = "  " + "   ".join(tab_strs) + f"   {C_BR_BLACK}│  [r] Refresh  [q] Quit{RESET}"

        border = "═" * min(width, 100)
        sub_border = "─" * min(width, 100)

        return [border, line1, border, tabs_line, sub_border]

    def render_view_dashboard(self, width: int) -> List[str]:
        """View 1: Dashboard Overview."""
        lines: List[str] = []
        lines.append(f"{C_BR_WHITE}{BOLD}📊 DASHBOARD OVERVIEW & MISSION HEALTH{RESET}\n")

        # Project summary
        phase = self.data.get("active_phase") or "None (Pipeline Idle)"
        session_topic = self.data["session"].get("topic", "Architectural Review")
        lines.append(f"  • {BOLD}Active Phase:{RESET}   {C_CYAN}{phase}{RESET}")
        lines.append(f"  • {BOLD}Session Topic:{RESET}  {session_topic}")
        lines.append(f"  • {BOLD}Project Path:{RESET}   {C_BR_BLACK}{self.root}{RESET}\n")

        # Quality Gates Section
        lines.append(f"{C_BR_WHITE}{BOLD}🛡️  QUALITY GATES & HUMAN SEMAPHORES{RESET}")
        gates = self.data["session"].get("gates", {})
        if not gates:
            lines.append(f"  {C_BR_BLACK}No gate decisions recorded in active session.{RESET}")
        else:
            for g_name, g_info in gates.items():
                g_stat = g_info.get("status", "pending").lower()
                if g_stat == "approved":
                    pill = f"{C_BR_GREEN}✓ APPROVED{RESET}"
                elif g_stat == "rejected":
                    pill = f"{C_BR_RED}✕ REJECTED{RESET}"
                else:
                    pill = f"{C_BR_YELLOW}⏳ PENDING{RESET}"
                notes = f" - {g_info.get('notes')}" if g_info.get("notes") else ""
                lines.append(f"  • {BOLD}{g_name}:{RESET} {pill}{C_BR_BLACK}{notes}{RESET}")
        lines.append("")

        # Metrics Card
        tasks = self.data.get("tasks", [])
        todo_cnt = sum(1 for t in tasks if t.get("status") == "todo")
        prog_cnt = sum(1 for t in tasks if t.get("status") == "in_progress")
        done_cnt = sum(1 for t in tasks if t.get("status") == "done")

        artifacts = self.data.get("artifacts", [])
        sv = self.data.get("skillvault", {})
        sv_status = f"{C_BR_GREEN}ACTIVE ({len(sv.get('skills', []))} skills){RESET}" if sv.get("enabled") else f"{C_BR_BLACK}DISABLED{RESET}"
        clean_str = f"{C_BR_GREEN}CLEAN{RESET}" if self.data["git"].get("clean") else f"{C_BR_YELLOW}DIRTY (Uncommitted changes){RESET}"

        lines.append(f"{C_BR_WHITE}{BOLD}📈 QUICK METRICS{RESET}")
        lines.append(f"  • {BOLD}Kanban Tasks:{RESET}    {C_CYAN}{len(tasks)}{RESET} total  │  {C_BR_GREEN}{done_cnt} Done{RESET}  │  {C_BR_YELLOW}{prog_cnt} In Progress{RESET}  │  {C_BR_BLACK}{todo_cnt} Backlog{RESET}")
        lines.append(f"  • {BOLD}Working Tree:{RESET}    {clean_str}")
        lines.append(f"  • {BOLD}Artifacts:{RESET}       {len(artifacts)} detected in repo")
        lines.append(f"  • {BOLD}SkillVault:{RESET}      {sv_status}")

        recent = self.data["git"].get("recent_commits", [])
        if recent:
            c = recent[0]
            lines.append(f"\n{C_BR_WHITE}{BOLD}🔖 LATEST COMMIT{RESET}")
            lines.append(f"  {C_BR_YELLOW}{c['hash']}{RESET} {c['message']} {C_BR_BLACK}({c['relative']} by {c['author']}){RESET}")

        return lines

    def render_view_kanban(self, width: int) -> List[str]:
        """View 2: Kanban Tasks with Terminal Evidence."""
        lines: List[str] = []
        tasks: List[Dict[str, Any]] = self.data.get("tasks", [])

        lines.append(f"{C_BR_WHITE}{BOLD}📋 KANBAN TASKS & TDD MATRIX{RESET}  {C_BR_BLACK}({len(tasks)} tasks detected){RESET}\n")

        if not tasks:
            lines.append(f"  {C_BR_BLACK}No task logs found in odd/tasks/*.md or tasks.md.{RESET}")
            lines.append(f"  {C_BR_BLACK}Project is in idle state.{RESET}")
            return lines

        categories = [
            ("⚡ IN PROGRESS", "in_progress", C_BR_YELLOW),
            ("📋 BACKLOG / TO DO", "todo", C_BR_BLACK),
            ("✅ COMPLETED & VERIFIED", "done", C_BR_GREEN),
        ]

        for cat_label, status_key, color in categories:
            cat_tasks = [t for t in tasks if t.get("status") == status_key]
            lines.append(f"{color}{BOLD}{cat_label} ({len(cat_tasks)}){RESET}")
            if not cat_tasks:
                lines.append(f"  {C_BR_BLACK}(none){RESET}")
            else:
                for t in cat_tasks:
                    t_id = f"[{t.get('task_id')}] " if t.get("task_id") else ""
                    wave = f"{C_CYAN}[{t.get('wave')}]{RESET} " if t.get("wave") else ""
                    commit = f" {C_BR_YELLOW}(Commit: {t.get('commit')}){RESET}" if t.get("commit") else ""
                    lines.append(f"  • {wave}{BOLD}{t_id}{RESET}{t.get('text', '')}{commit}")

                    # Render Terminal Evidence if present
                    ev = t.get("evidence")
                    if ev:
                        code_str = f"Exit: {ev.get('exit_code')}"
                        code_col = C_BR_GREEN if str(ev.get("exit_code")) == "0" else C_BR_RED
                        lines.append(f"    {C_BR_BLACK}└─ Evidence:{RESET} {C_BR_WHITE}`{ev.get('cmd')}`{RESET} → {code_col}{code_str}{RESET} │ {C_BR_BLACK}{ev.get('output')}{RESET}")
            lines.append("")

        return lines

    def render_view_diff(self, width: int) -> List[str]:
        """View 3: Git Commits & Diff Summary."""
        lines: List[str] = []
        git_info = self.data["git"]

        lines.append(f"{C_BR_WHITE}{BOLD}🔍 GIT COMMITS & WORKING TREE DIFF SUMMARY{RESET}\n")

        # Slice LOC summary
        slice_loc = git_info.get("slice_loc", 0)
        lines.append(f"{BOLD}Slice Delivery Budget (ARQ-01 ~400 LOC Heuristic):{RESET}")
        lines.append(f"  Accumulated LOC: {C_BR_WHITE}{BOLD}{slice_loc}{RESET} / 400 LOC limit")
        if slice_loc > 400:
            lines.append(f"  {C_BR_RED}⚠️ Alert: Monolithic slice. Recommended to split into chained PR or commit work unit.{RESET}")
        else:
            lines.append(f"  {C_BR_GREEN}✓ Within healthy single-slice budget.{RESET}")
        lines.append("")

        # Recent Commits
        lines.append(f"{C_BR_WHITE}{BOLD}Recent Commits:{RESET}")
        commits = git_info.get("recent_commits", [])
        if not commits:
            lines.append(f"  {C_BR_BLACK}No git history detected.{RESET}")
        else:
            for c in commits:
                lines.append(f"  • {C_BR_YELLOW}{c['hash']}{RESET} {c['message']} {C_BR_BLACK}({c['relative']} by {c['author']}){RESET}")
        lines.append("")

        # Diff snippet
        diff_text = git_info.get("diff", "")
        if not diff_text.strip():
            # Try capturing on the fly
            try:
                r = subprocess.run(["git", "diff", "--stat"], cwd=self.root, capture_output=True, text=True)
                diff_text = r.stdout
            except Exception:
                diff_text = ""

        lines.append(f"{C_BR_WHITE}{BOLD}Working Tree Status & Stat:{RESET}")
        if not diff_text.strip():
            lines.append(f"  {C_BR_GREEN}✓ Working tree clean. No uncommitted modifications.{RESET}")
        else:
            for d_line in diff_text.strip().splitlines()[:15]:
                if d_line.startswith("+"):
                    lines.append(f"  {C_BR_GREEN}{d_line}{RESET}")
                elif d_line.startswith("-"):
                    lines.append(f"  {C_BR_RED}{d_line}{RESET}")
                else:
                    lines.append(f"  {C_BR_BLACK}{d_line}{RESET}")
            if len(diff_text.strip().splitlines()) > 15:
                lines.append(f"  {C_BR_BLACK}... (truncated for terminal view){RESET}")

        return lines

    def render_view_skillvault(self, width: int) -> List[str]:
        """View 4: SkillVault Explorer."""
        lines: List[str] = []
        sv = self.data.get("skillvault", {})
        enabled = sv.get("enabled", False)
        skills: List[Dict[str, Any]] = sv.get("skills", [])

        lines.append(f"{C_BR_WHITE}{BOLD}⚡ SKILLVAULT EXPLORER{RESET}\n")

        if not enabled:
            lines.append(f"{C_BR_YELLOW}┌────────────────────────────────────────────────────────────────────────┐{RESET}")
            lines.append(f"{C_BR_YELLOW}│  ⚡ SkillVault Provider is DISABLED in .q-agent.json                   │{RESET}")
            lines.append(f"{C_BR_YELLOW}│                                                                        │{RESET}")
            lines.append(f"{C_BR_YELLOW}│  To enable SkillVault scanning:                                        │{RESET}")
            lines.append(f"{C_BR_YELLOW}│  Set context_retrieval.providers.skillvault.enabled: true             │{RESET}")
            lines.append(f"{C_BR_YELLOW}│  in your .q-agent.json file.                                           │{RESET}")
            lines.append(f"{C_BR_YELLOW}└────────────────────────────────────────────────────────────────────────┘{RESET}")
            return lines

        # Detail view for single skill if selected
        if self.selected_skill_index is not None and 0 <= self.selected_skill_index < len(skills):
            sk = skills[self.selected_skill_index]
            lines.append(f"{C_BR_CYAN}{BOLD}◀ Press 'b' to return to skills list{RESET}\n")
            lines.append(f"{BOLD}Skill:{RESET}       {C_BR_WHITE}{sk.get('name')}{RESET}  {C_BR_CYAN}(v{sk.get('version', '1.0.0')}){RESET}")
            lines.append(f"{BOLD}Location:{RESET}    {C_BR_BLACK}{sk.get('path')}{RESET}")
            lines.append(f"{BOLD}Description:{RESET} {sk.get('description')}\n")
            lines.append(f"{C_BR_BLACK}{'─' * min(width, 100)}{RESET}")
            content_lines = sk.get("content", "").splitlines()
            for c_line in content_lines[:40]:
                lines.append(f"  {c_line}")
            if len(content_lines) > 40:
                lines.append(f"\n  {C_BR_BLACK}... ({len(content_lines) - 40} more lines in {sk.get('path')}){RESET}")
            return lines

        lines.append(f"Discovered {C_BR_GREEN}{len(skills)}{RESET} modular skills in repository:")
        lines.append(f"{C_BR_BLACK}(Type the skill index number 1..{len(skills)} to preview markdown content){RESET}\n")

        for idx, sk in enumerate(skills, 1):
            s_name = sk.get("name", "unnamed")
            s_ver = sk.get("version", "1.0.0")
            s_path = sk.get("path", "")
            s_desc = sk.get("description", "")
            # Truncate description for compact view
            if len(s_desc) > 80:
                s_desc = s_desc[:77] + "..."
            lines.append(f"  {C_BR_CYAN}[{idx}]{RESET} {BOLD}{s_name}{RESET} {C_BR_BLACK}(v{s_ver}){RESET} ─ {C_BR_BLACK}{s_path}{RESET}")
            if s_desc:
                lines.append(f"      {s_desc}")
            lines.append("")

        return lines

    def render(self) -> None:
        """Render complete screen to stdout."""
        term_size = shutil.get_terminal_size((80, 24))
        width = term_size.columns

        output: List[str] = [CLEAR_SCREEN]
        output.extend(self.render_header(width))
        output.append("")

        if self.current_view == 1:
            output.extend(self.render_view_dashboard(width))
        elif self.current_view == 2:
            output.extend(self.render_view_kanban(width))
        elif self.current_view == 3:
            output.extend(self.render_view_diff(width))
        elif self.current_view == 4:
            output.extend(self.render_view_skillvault(width))

        sys.stdout.write("\n".join(output) + "\n")
        sys.stdout.flush()

    def run_loop(self) -> int:
        """Main interactive event loop."""
        while True:
            self.render()
            key = get_key()
            if not key:
                time.sleep(0.05)
                continue

            if key in ("q", "\x03"):  # 'q' or Ctrl+C
                sys.stdout.write(f"\n{C_BR_BLACK}Exiting q-cockpit TUI...{RESET}\n")
                return 0
            elif key == "r":
                self.refresh_data()
            elif key == "1":
                self.current_view = 1
                self.selected_skill_index = None
            elif key == "2":
                self.current_view = 2
                self.selected_skill_index = None
            elif key == "3":
                self.current_view = 3
                self.selected_skill_index = None
            elif key == "4":
                self.current_view = 4
                self.selected_skill_index = None
            elif self.current_view == 4:
                if key == "b":
                    self.selected_skill_index = None
                elif key.isdigit():
                    num = int(key) - 1
                    skills = self.data.get("skillvault", {}).get("skills", [])
                    if 0 <= num < len(skills):
                        self.selected_skill_index = num


def main(project_dir: Optional[str] = None, view: int = 1, once: bool = False) -> int:
    parser = argparse.ArgumentParser(description="q-cockpit TUI: Terminal User Interface for q-agent")
    parser.add_argument("--project", type=str, default=project_dir, help="Target project directory")
    parser.add_argument("--view", type=int, default=view, choices=[1, 2, 3, 4], help="Initial view (1: Dashboard, 2: Kanban, 3: Diff, 4: SkillVault)")
    parser.add_argument("--once", action="store_true", default=once, help="Render once and exit (for non-interactive use)")

    args, _ = parser.parse_known_args()

    tui = CockpitTUI(project_dir=Path(args.project).resolve() if args.project else None, initial_view=args.view)

    if args.once or not sys.stdin.isatty():
        tui.render()
        return 0

    try:
        return tui.run_loop()
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{C_BR_BLACK}Exiting q-cockpit TUI...{RESET}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main())
