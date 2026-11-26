"""Repeatable local performance measurements for q-agent tooling."""

from __future__ import annotations

import argparse
import ast
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


SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache",
             ".q-worktrees", ".q-agent", ".q-cockpit", "dist", "build"}


def python_skeleton(source: str) -> str:
    """Return imports, class/function signatures and docstrings, without bodies."""
    tree = ast.parse(source)
    lines: list[str] = []

    def visit(nodes: list[ast.stmt], depth: int) -> None:
        pad = "    " * depth
        for node in nodes:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                lines.append(pad + ast.unparse(node))
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                header = ast.unparse(node).splitlines()
                decorators = [f"{pad}@{ast.unparse(d)}" for d in node.decorator_list]
                signature = next(line for line in header if not line.lstrip().startswith("@"))
                lines.extend(decorators + [pad + signature.strip()])
                doc = ast.get_docstring(node)
                if doc:
                    lines.append(f'{pad}    """{doc}"""')
                if isinstance(node, ast.ClassDef):
                    visit(node.body, depth + 1)
                else:
                    lines.append(pad + "    ...")

    module_doc = ast.get_docstring(tree)
    if module_doc:
        lines.append(f'"""{module_doc}"""')
    visit(tree.body, 0)
    return "\n".join(lines) + "\n"


def measure_context(root: Path) -> dict[str, Any]:
    """Compare full Python sources with their AST skeletons (tokens estimated as chars / 4)."""
    root = Path(root).resolve()
    full_chars = skeleton_chars = files = skipped = 0
    for path in sorted(root.rglob("*.py")):
        if SKIP_DIRS.intersection(path.relative_to(root).parts):
            continue
        try:
            source = path.read_text(encoding="utf-8")
            skeleton = python_skeleton(source)
        except (OSError, UnicodeDecodeError, SyntaxError):
            skipped += 1
            continue
        files += 1
        full_chars += len(source)
        skeleton_chars += len(skeleton)
    reduction = (1 - skeleton_chars / full_chars) * 100 if full_chars else 0.0
    return {
        "method": "python-ast-skeleton; tokens estimated as chars/4",
        "python_files": files,
        "skipped_files": skipped,
        "full_tokens_est": full_chars // 4,
        "skeleton_tokens_est": skeleton_chars // 4,
        "reduction_pct": round(reduction, 1),
    }


def run_benchmark(root: Path, *, iterations: int = 3, context: bool = False) -> dict[str, Any]:
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
    report: dict[str, Any] = {
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
    if context:
        report["context"] = measure_context(root)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="q-benchmark: deterministic local q-agent measurements")
    parser.add_argument("--project", default=".", help="Project root to scan")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--context", action="store_true",
                        help="Also measure full-file vs AST-skeleton context size for Python sources")
    args = parser.parse_args()
    report = run_benchmark(Path(args.project), iterations=args.iterations, context=args.context)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"q-agent benchmark: {report['project']}")
        for name, value in report["metrics"].items():
            print(f"  {name}: {value} ms")
        if "context" in report:
            ctx = report["context"]
            print(f"  ast_skeleton: {ctx['python_files']} files, ~{ctx['full_tokens_est']} -> "
                  f"~{ctx['skeleton_tokens_est']} tokens ({ctx['reduction_pct']}% smaller)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
