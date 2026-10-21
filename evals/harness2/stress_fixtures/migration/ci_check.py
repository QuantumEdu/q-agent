from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path


def main() -> int:
    source = Path("migrate.py").read_text(encoding="utf-8")
    ast.parse(source)
    if "TODO" in source:
        raise SystemExit("CI rejected unresolved TODO markers")
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=False
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
