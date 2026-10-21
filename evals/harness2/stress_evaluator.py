"""Four-rollout local stress evaluation for q-agent and Codex CLI.

This is deliberately not an official Harness2 adapter. It preserves only the parts that can be
validated with a locally authenticated Codex CLI: equal fixtures, real CI, immutable tests,
captured trajectories, and independently reviewable diffs.
"""

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
FIXTURES = ROOT / "stress_fixtures"
RUNS = ROOT / "stress_runs"
Q_AGENT = Path(os.environ.get("Q_AGENT_DIR", str(ROOT.parents[1]))).resolve()

TASKS = {
    "workflow": """Implement the multi-tenant helpdesk workflow in helpdesk.py.

Keep SQLite WAL and all queries parameterized. Implement transition_ticket(db_path, tenant_id,
ticket_id, actor_role, new_state) with exactly these transitions:
OPEN -> IN_PROGRESS (support or manager), IN_PROGRESS -> RESOLVED (support or manager),
RESOLVED -> CLOSED (manager only). Reject every invalid role, tenant, state, or ticket with
ValueError and do not persist a state change or audit event when rejecting it. Successful changes
must write a ticket_events row. Implement overdue_ticket_ids(db_path, tenant_id, now): only the
given tenant, due strictly before now, excluding RESOLVED/CLOSED, ordered by id.

Do not modify tests. Run `python3 ci_check.py`, which is the required real CI gate.
""",
    "migration": """Implement the legacy helpdesk SLA migration in migrate.py.

migrate_add_sla(db_path) must be idempotent. It must add and populate a due_at column for every
legacy ticket from opened_at plus SLA hours (CRITICAL 2, HIGH 8, MEDIUM 24, LOW 72), preserving
every existing row. Reject an unsupported priority with ValueError and leave that transaction
uncommitted. Do not modify tests. Run `python3 ci_check.py`, which is the required real CI gate.
""",
}


@dataclass
class Result:
    case: str
    harness: str
    rollout_exit: int
    ci_exit: int
    tests_tampered: bool
    changed_files: list[str]
    run_dir: str


def digest_tests(workspace: Path) -> dict[str, str]:
    return {
        str(path.relative_to(workspace)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((workspace / "tests").glob("test_*.py"))
    }


def write_harness(workspace: Path, harness: str) -> None:
    if harness == "baseline":
        body = """# Task instructions

Implement the assigned feature directly. Do not modify tests. Run `python3 ci_check.py` and
report the complete result.
"""
    else:
        target = workspace / ".agents" / "skills" / "q-agent"
        shutil.copytree(Q_AGENT, target, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        body = """# q-agent stress-evaluation harness

Read and follow `.agents/skills/q-agent/SKILL.md` for this pre-authorized Greenfield evaluation.
The scope is only the assigned helpdesk task and the existing tests. Do not ask follow-up
questions, deploy, commit, or modify tests. A real CI check starts red: diagnose and correct it
using the relevant q-agent quality workflow. Create `odd/tasks/stress-<task>.md` containing the
requirements, RED evidence, GREEN `python3 ci_check.py` evidence, and any relevant quality gate.
"""
        body = body.replace("<task>", workspace.name.split("-")[0])
    (workspace / "AGENTS.md").write_text(body, encoding="utf-8")


def run_case(task: str, harness: str) -> Result:
    case = f"{task}-{harness}"
    run_dir = RUNS / case
    workspace = run_dir / "workspace"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(
        FIXTURES / task,
        workspace,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )
    write_harness(workspace, harness)
    tests_before = digest_tests(workspace)
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "evaluation@example.invalid"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "Stress Fixture"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "Stress fixture baseline"], cwd=workspace, check=True)
    run_dir.mkdir(parents=True, exist_ok=True)

    with (run_dir / "codex.jsonl").open("w", encoding="utf-8") as stream:
        rollout = subprocess.run(
            [
                "codex",
                "exec",
                "--json",
                "--sandbox",
                "workspace-write",
                "-C",
                str(workspace),
                "-o",
                str(run_dir / "final.md"),
                TASKS[task],
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
        ["git", "status", "--short"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return Result(
        case=case,
        harness=harness,
        rollout_exit=rollout.returncode,
        ci_exit=ci.returncode,
        tests_tampered=tests_before != digest_tests(workspace),
        changed_files=changed,
        run_dir=str(run_dir.relative_to(ROOT)),
    )


def main() -> int:
    RUNS.mkdir(exist_ok=True)
    results = [run_case(task, harness) for task in ("workflow", "migration") for harness in ("baseline", "q-agent")]
    report = {
        "kind": "local-codex-cli-stress-prototype",
        "official_harness2_benchmark": False,
        "results": [asdict(result) for result in results],
    }
    (RUNS / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(
            f"{result.case}: rollout={result.rollout_exit} ci={result.ci_exit} "
            f"tampered={result.tests_tampered}"
        )
    return 0 if all(r.rollout_exit == r.ci_exit == 0 and not r.tests_tampered for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
