"""Repeatable local performance measurements for q-agent tooling."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time
from typing import Any


def _measure(callable_fn: Any, iterations: int) -> list[float]:
    values = []
    for _ in range(iterations):
        started = time.perf_counter()
        callable_fn()
        values.append((time.perf_counter() - started) * 1000)
    return values


def run_benchmark(root: Path, *, iterations: int = 3) -> dict[str, Any]:
    root = Path(root).resolve()
    iterations = max(1, int(iterations))
    cockpit_dir = root / "tools" / "q-cockpit"
    if str(cockpit_dir) not in sys.path:
        sys.path.insert(0, str(cockpit_dir))
    spec = importlib.util.spec_from_file_location("q_cockpit_benchmark", cockpit_dir / "q_cockpit.py")
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load q_cockpit.py")
    cockpit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cockpit)
    ProjectScanner = cockpit.ProjectScanner

    scan_values = _measure(lambda: (
        ProjectScanner.scan_git_info(root),
        ProjectScanner.scan_tasks(root),
        ProjectScanner.scan_artifacts(root),
    ), iterations)
    help_values = _measure(
        lambda: subprocess.run(
            [sys.executable, str(cockpit_dir / "q_cockpit.py"), "--help"],
            cwd=root,
            capture_output=True,
            check=True,
            text=True,
        ),
        iterations,
    )
    return {
        "format": "q-agent-benchmark-v1",
        "project": str(root),
        "iterations": iterations,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
        },
        "metrics": {
            "project_scan_ms": round(statistics.median(scan_values), 3),
            "cockpit_help_ms": round(statistics.median(help_values), 3),
        },
        "samples_ms": {
            "project_scan": [round(value, 3) for value in scan_values],
            "cockpit_help": [round(value, 3) for value in help_values],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="q-benchmark: deterministic local q-agent measurements")
    parser.add_argument("--project", default=".", help="Project root to scan")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    report = run_benchmark(Path(args.project), iterations=args.iterations)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"q-agent benchmark: {report['project']}")
        for name, value in report["metrics"].items():
            print(f"  {name}: {value} ms")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
