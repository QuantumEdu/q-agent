from __future__ import annotations

import subprocess
import sys


if __name__ == "__main__":
    raise SystemExit(
        subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], check=False
        ).returncode
    )
