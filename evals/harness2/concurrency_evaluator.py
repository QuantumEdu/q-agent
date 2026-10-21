"""Evaluate high-concurrency and SQLite lock contention handling under local Codex CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "concurrency_fixture" / "base"
RUNS = ROOT / "concurrency_runs"
Q_AGENT = Path(os.environ.get("Q_AGENT_DIR", str(ROOT.parents[1]))).resolve()

PROMPT = """Implement atomic ticket claiming and high-concurrency lock contention handling in helpdesk.py.

Requirements:
- Implement `claim_ticket(db_path, tenant_id, ticket_id, actor_role, assignee)`:
  * Atomically transition state from 'OPEN' to 'IN_PROGRESS' and set assignee to the given assignee string.
  * Record an audit event in `ticket_events` (ticket_id, old_state='OPEN', new_state='IN_PROGRESS', actor_role=actor_role).
  * If the ticket is not in state 'OPEN', does not belong to tenant_id, or actor_role is not 'support', raise ValueError.
  * Under concurrent race conditions where multiple workers attempt to claim the same OPEN ticket simultaneously,
    exactly ONE worker must succeed (rowcount == 1) and all other concurrent workers must fail with ValueError,
    without corrupting database state or leaving orphan audit events.
- Configure `_connection` (or connection parameters) to handle high-concurrency write bursts under SQLite WAL mode
  without raising unhandled `sqlite3.OperationalError: database is locked` exceptions (e.g. use `timeout=15.0` or
  PRAGMA busy_timeout = 10000).
- Preserve existing functions: `initialize`, `create_tenant`, `create_ticket`, `transition_ticket`, and `overdue_ticket_ids`.
- Do not modify tests. Run `python3 ci_check.py` and leave clear repository evidence in `odd/tasks/` when the q-agent harness requests it.
"""


@dataclass
class ConcurrencyResult:
    harness: str
    rollout_exit: int
    ci_exit: int
    tests_tampered: bool
    changed_files: list[str]


def test_digest(workspace: Path) -> dict[str, str]:
    return {
        str(path.relative_to(workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((workspace / "tests").glob("test_*.py"))
    }


def write_harness(workspace: Path, harness: str) -> None:
    if harness == "baseline":
        text = """# Task instructions

Implement the requested concurrency features. Treat the repository as the source of truth.
Do not modify tests, commit, or deploy. Run `python3 ci_check.py` before reporting.
"""
    else:
        skill_target = workspace / ".agents" / "skills" / "q-agent"
        shutil.copytree(
            Q_AGENT,
            skill_target,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "evals"),
        )
        text = """# q-agent concurrency evaluation harness

Read and follow `.agents/skills/q-agent/SKILL.md`. This is a pre-authorized Greenfield/Brownfield concurrency task.
The repository is the sole source of truth. Use the q-agent workflow, enforce Article ARQ-01 (Vertical Slices,
zero mocks, SQLite WAL), record RED/GREEN terminal evidence in `odd/tasks/concurrency.md`, and do not modify tests.
"""
    (workspace / "AGENTS.md").write_text(text, encoding="utf-8")


def run_case(harness: str) -> ConcurrencyResult:
    run_dir = RUNS / harness
    workspace = run_dir / "workspace"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(FIXTURE, workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    write_harness(workspace, harness)
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "eval@example.invalid"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "Concurrency Eval"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "Initial concurrency fixture"], cwd=workspace, check=True)

    tests_before = test_digest(workspace)
    with (run_dir / "codex.jsonl").open("w", encoding="utf-8") as stream:
        rollout = subprocess.run(
            [
                "codex",
                "exec",
                "--ephemeral",
                "--json",
                "--sandbox",
                "workspace-write",
                "-C",
                str(workspace),
                "-o",
                str(run_dir / "final.md"),
                PROMPT,
            ],
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1_200,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )

    ci = subprocess.run(
        [sys.executable, "ci_check.py"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=90,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    (run_dir / "ci.log").write_text(ci.stdout + ci.stderr, encoding="utf-8")
    changed = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()

    # Preserve odd/tasks/concurrency.md if created by q-agent
    odd_task = workspace / "odd" / "tasks" / "concurrency.md"
    if odd_task.is_file():
        shutil.copy2(odd_task, run_dir / "concurrency.md")

    return ConcurrencyResult(
        harness=harness,
        rollout_exit=rollout.returncode,
        ci_exit=ci.returncode,
        tests_tampered=tests_before != test_digest(workspace),
        changed_files=changed,
    )


def main() -> int:
    RUNS.mkdir(exist_ok=True)
    results = [run_case(harness) for harness in ("baseline", "q-agent")]
    report = {
        "kind": "local-codex-cli-concurrency-stress-prototype",
        "official_harness2_benchmark": False,
        "task": "Atomic ticket claiming and high-concurrency lock contention under SQLite WAL",
        "results": [asdict(r) for r in results],
    }
    (RUNS / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for r in results:
        print(f"{r.harness}: rollout={r.rollout_exit} ci={r.ci_exit} tampered={r.tests_tampered} changed={r.changed_files}")
    return 0 if all(r.rollout_exit == r.ci_exit == 0 and not r.tests_tampered for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
