#!/usr/bin/env python3
"""Canonical Plan C runner: lifecycle, deterministic gates, and evidence index."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


lifecycle_module = _load("q_audit_lifecycle_runner", ROOT / "tools/q-audit-lifecycle/audit_lifecycle.py")
evidence_module = _load("q_audit_evidence_runner", ROOT / "tools/q-audit-evidence/evidence.py")
AuditLifecycle = lifecycle_module.AuditLifecycle
AuditState = lifecycle_module.AuditState


def _run(command: list[str], cwd: Path) -> int:
    result = subprocess.run(command, cwd=cwd, text=True, check=False)
    return result.returncode


def run_audit(root: Path, level: int, manifest: Path, signing_key: Path | None = None) -> dict[str, Any]:
    root = root.resolve()
    manifest = manifest.resolve()
    audit_dir = root / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    lifecycle = AuditLifecycle()
    lifecycle.transition(AuditState.DISPATCHED, f"level {level} manifest selected")
    validator = ROOT / "tools/q-audit-validator/validate_audit.py"
    aggregator = ROOT / "tools/q-audit-aggregator/generate_report.py"
    validator_code = _run(
        [sys.executable, str(validator), "--cwd", str(root), "--manifest", str(manifest), "--mode", "manifest", "--level", str(level)],
        root,
    )
    if validator_code != 0:
        lifecycle.transition(AuditState.BLOCKED, f"manifest validator exited {validator_code}")
        state = {"state": lifecycle.state.value, "history": lifecycle.history, "validator_exit": validator_code}
        (audit_dir / "AUDIT_RUN_STATE.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        return state
    lifecycle.transition(AuditState.CAPTURED, "all active item files are present")
    lifecycle.transition(AuditState.VALIDATED, "manifest validator passed")
    aggregator_code = _run(
        [sys.executable, str(aggregator), "--cwd", str(root), "--manifest", str(manifest), "--level", str(level)],
        root,
    )
    item_files = [path for path in audit_dir.glob("*.md") if path.name[:1] in {"A", "E"}]
    evidence_path = audit_dir / "AUDIT_EVIDENCE.json"
    evidence_error = None
    try:
        index = evidence_module.build_evidence_index(root, manifest, item_files)
        if signing_key:
            index["ed25519_signature"] = evidence_module.sign_evidence_index(index, signing_key)
        evidence_module.write_evidence_index(index, evidence_path)
    except Exception as exc:
        # Preserve the aggregator result while exposing indexing failures.
        evidence_error = f"{type(exc).__name__}: {exc}"

    report_path = audit_dir / "AUDIT_REPORT.md"
    report_text = report_path.read_text(encoding="utf-8") if report_path.is_file() else ""
    report_upper = report_text.upper()
    conditional_report = (
        aggregator_code == 1
        and "OVERALL VERDICT" in report_upper
        and "CONDITIONAL" in report_upper
    )
    aggregation_ok = aggregator_code == 0 or conditional_report
    if aggregation_ok:
        reason = "aggregator passed; evidence index written"
        if conditional_report:
            reason = (
                "aggregator produced a valid CONDITIONAL report; "
                "evidence index written"
            )
        lifecycle.transition(AuditState.AGGREGATED, reason)
    else:
        lifecycle.transition(AuditState.BLOCKED, f"aggregator exited {aggregator_code}")
    state = {
        "state": lifecycle.state.value,
        "history": lifecycle.history,
        "validator_exit": validator_code,
        "aggregator_exit": aggregator_code,
        "result": 0 if aggregation_ok else aggregator_code,
        "conditional": conditional_report,
    }
    if evidence_path.is_file():
        state["evidence"] = "audit/AUDIT_EVIDENCE.json"
    if evidence_error:
        state["evidence_error"] = evidence_error
    (audit_dir / "AUDIT_RUN_STATE.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return state


def main() -> int:
    parser = argparse.ArgumentParser(description="q-audit-runner: lifecycle-aware Plan C audit")
    parser.add_argument("--cwd", type=Path, default=Path("."))
    parser.add_argument("--manifest", type=Path, default=ROOT / "references/audit-manifest.yml")
    parser.add_argument("--level", type=int, default=2)
    parser.add_argument("--signing-key", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    state = run_audit(args.cwd, args.level, args.manifest, args.signing_key)
    if args.json:
        print(json.dumps(state, indent=2))
    else:
        print(f"Audit state: {state['state']}")
        print(f"Validator exit: {state['validator_exit']}")
        if "aggregator_exit" in state:
            print(f"Aggregator exit: {state['aggregator_exit']}")
    return 0 if state["state"] == AuditState.AGGREGATED.value else 1


if __name__ == "__main__":
    raise SystemExit(main())
