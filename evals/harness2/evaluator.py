"""Run a local, non-official Harness2-style comparison with Codex CLI."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "fixture"
RUNS = ROOT / "runs"
Q_AGENT = Path(os.environ.get("Q_AGENT_DIR", str(ROOT.parents[1]))).resolve()
TASK = """Implement the ticket workflow in ticket_store.py.

Requirements:
- Use the existing SQLite database and retain WAL mode.
- Implement a strict lifecycle: OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED.
- Reject every invalid transition with ValueError and do not change persisted state.
- Implement overdue_ticket_ids(db_path, now) to return ticket IDs whose SLA due time is before now
  and whose state is neither RESOLVED nor CLOSED.
- SLA durations: CRITICAL 2 hours, HIGH 8 hours, MEDIUM 24 hours, LOW 72 hours.
- Do not modify tests. Run the real test suite and leave terminal evidence in odd/tasks/
  when the q-agent harness requests it.
"""


@dataclass
class Result:
    name: str
    returncode: int
    tests_returncode: int
    tests_tampered: bool
    changed_files: list[str]
    run_dir: str


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_baseline_harness(workspace: Path) -> None:
    (workspace / "AGENTS.md").write_text(
        """# Task instructions

Implement the requested feature directly and safely. Read the existing code and tests, do not edit
tests, run `python3 -m unittest discover -s tests -v`, and report the result.
""",
        encoding="utf-8",
    )


def write_q_agent_harness(workspace: Path) -> None:
    skill_target = workspace / ".agents" / "skills" / "q-agent"
    shutil.copytree(Q_AGENT, skill_target, ignore=shutil.ignore_patterns(".git", "__pycache__"))
    (workspace / "AGENTS.md").write_text(
        """# q-agent evaluation harness

When implementing this feature, read and follow `.agents/skills/q-agent/SKILL.md`.
This is a pre-authorized Greenfield evaluation task: the scope is limited to the SQLite ticket
workflow and its existing tests. Use the available Gentle-AI engine when relevant. Do not ask
follow-up questions, do not deploy, do not commit, and do not modify tests. Create a live ODD task
log in `odd/tasks/ticket-workflow.md`; record the real test command and its result as terminal
evidence before reporting completion.
""",
        encoding="utf-8",
    )


def run_case(name: str) -> Result:
    run_dir = RUNS / name
    workspace = run_dir / "workspace"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(FIXTURE, workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    tests_before = digest(workspace / "tests" / "test_ticket_store.py")

    if name == "baseline":
        write_baseline_harness(workspace)
    else:
        write_q_agent_harness(workspace)

    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "evaluation@example.invalid"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "Evaluation Fixture"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "Fixture baseline"], cwd=workspace, check=True)
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
                TASK,
            ],
            cwd=workspace,
            stdin=subprocess.DEVNULL,
            stdout=stream,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=1_200,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )
    (run_dir / "tests.log").write_text(tests.stdout + tests.stderr, encoding="utf-8")
    changed = subprocess.run(
        ["git", "status", "--short"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.splitlines()
    return Result(
        name=name,
        returncode=rollout.returncode,
        tests_returncode=tests.returncode,
        tests_tampered=tests_before != digest(workspace / "tests" / "test_ticket_store.py"),
        changed_files=changed,
        run_dir=str(run_dir.relative_to(ROOT)),
    )


def main() -> int:
    if not Q_AGENT.is_dir():
        raise SystemExit(f"q-agent source is missing: {Q_AGENT}")
    RUNS.mkdir(exist_ok=True)
    started = datetime.now(UTC).isoformat()
    results = [run_case("baseline"), run_case("q-agent")]
    report = {
        "kind": "local-codex-cli-prototype",
        "official_harness2_benchmark": False,
        "started_at": started,
        "task": TASK,
        "results": [asdict(result) for result in results],
    }
    (RUNS / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(
            f"{result.name}: rollout={result.returncode} tests={result.tests_returncode} "
            f"tampered={result.tests_tampered}"
        )
    return 0 if all(r.returncode == r.tests_returncode == 0 and not r.tests_tampered for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
