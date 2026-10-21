"""Evaluate repository-only recovery across fresh local Codex CLI sessions."""

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
FIXTURE = ROOT / "recovery_fixture"
RUNS = ROOT / "recovery_runs"
Q_AGENT = Path(os.environ.get("Q_AGENT_DIR", str(ROOT.parents[1]))).resolve()

PROMPTS = {
    "a": """Implement Slice A of the helpdesk storage feature. Implement initialize, create_tenant,
and create_ticket in helpdesk.py. Preserve SQLite WAL and foreign keys; use parameterized queries;
validate that a ticket tenant exists; calculate due_at from SLA_HOURS. Do not modify tests. Run
python3 ci_check.py and leave clear repository evidence of what you verified.""",
    "b": """This is a new session with no conversation history. Continue the existing helpdesk
repository. Implement Slice B: transition_ticket with strict OPEN -> IN_PROGRESS -> RESOLVED ->
CLOSED transitions, and overdue_ticket_ids with tenant isolation, strict due-at comparison and
RESOLVED/CLOSED exclusion. Preserve all completed Slice A behavior. Do not modify tests. Run
python3 ci_check.py and inspect the repository's persisted task evidence before reporting.""",
    "c": """This is a new session with no conversation history. CI was previously green but now
fails. Diagnose the repository state and repair the production regression without modifying tests.
Keep the completed storage and workflow behavior intact. Run python3 ci_check.py. Use the
repository's persisted evidence to determine scope; do not commit or deploy.""",
}


@dataclass
class PhaseResult:
    harness: str
    phase: str
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

Implement the requested slice. Treat the repository as the source of truth. Do not modify tests,
commit, or deploy. Run `python3 ci_check.py` before reporting.
"""
    else:
        shutil.copytree(
            Q_AGENT,
            workspace / ".agents" / "skills" / "q-agent",
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        text = """# q-agent context-recovery evaluation harness

Read and follow `.agents/skills/q-agent/SKILL.md`. This is a pre-authorized Greenfield helpdesk
task resumed across fresh sessions. The repository is the sole retained context. Before continuing,
inspect `odd/tasks/` and use the q-agent local task-recovery workflow when applicable. Do not ask
follow-up questions, change tests, commit, or deploy. Record RED/GREEN terminal evidence and the
current slice state in `odd/tasks/context-recovery.md`. When CI fails after an earlier green run,
follow reproduction-first repair within the bounded correction budget.
"""
    (workspace / "AGENTS.md").write_text(text, encoding="utf-8")


def launch(workspace: Path, run_dir: Path, harness: str, phase: str) -> PhaseResult:
    tests_before = test_digest(workspace)
    with (run_dir / f"{harness}-{phase}.jsonl").open("w", encoding="utf-8") as stream:
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
                str(run_dir / f"{harness}-{phase}.md"),
                PROMPTS[phase],
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
    (run_dir / f"{harness}-{phase}-ci.log").write_text(ci.stdout + ci.stderr, encoding="utf-8")
    changed = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    return PhaseResult(
        harness=harness,
        phase=phase,
        rollout_exit=rollout.returncode,
        ci_exit=ci.returncode,
        tests_tampered=tests_before != test_digest(workspace),
        changed_files=changed,
    )


def inject_phase_two_tests(workspace: Path) -> None:
    shutil.copy2(FIXTURE / "phase2_test.py", workspace / "tests" / "test_phase2.py")


def induce_sla_regression(workspace: Path) -> None:
    source = workspace / "helpdesk.py"
    body = source.read_text(encoding="utf-8")
    changed = body.replace('"CRITICAL": 2', '"CRITICAL": 24', 1)
    if changed == body:
        raise RuntimeError("could not induce the declared CRITICAL SLA regression")
    source.write_text(changed, encoding="utf-8")


def run_harness(harness: str) -> list[PhaseResult]:
    run_dir = RUNS / harness
    workspace = run_dir / "workspace"
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(FIXTURE / "base", workspace, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    write_harness(workspace, harness)
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.email", "evaluation@example.invalid"], cwd=workspace, check=True)
    subprocess.run(["git", "config", "user.name", "Recovery Fixture"], cwd=workspace, check=True)
    subprocess.run(["git", "add", "."], cwd=workspace, check=True)
    subprocess.run(["git", "commit", "-qm", "Initial recovery fixture"], cwd=workspace, check=True)
    results = [launch(workspace, run_dir, harness, "a")]
    inject_phase_two_tests(workspace)
    results.append(launch(workspace, run_dir, harness, "b"))
    induce_sla_regression(workspace)
    results.append(launch(workspace, run_dir, harness, "c"))
    return results


def main() -> int:
    RUNS.mkdir(exist_ok=True)
    results = [result for harness in ("baseline", "q-agent") for result in run_harness(harness)]
    report = {
        "kind": "local-codex-cli-context-recovery-prototype",
        "official_harness2_benchmark": False,
        "context_contract": "Each phase uses codex exec --ephemeral; only repository artifacts persist.",
        "results": [asdict(result) for result in results],
    }
    (RUNS / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for result in results:
        print(
            f"{result.harness}-{result.phase}: rollout={result.rollout_exit} ci={result.ci_exit} "
            f"tampered={result.tests_tampered}"
        )
    return 0 if all(r.rollout_exit == r.ci_exit == 0 and not r.tests_tampered for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
