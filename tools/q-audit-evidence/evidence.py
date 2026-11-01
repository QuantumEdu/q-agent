"""Backward-compatible re-export of audit evidence utilities from q-audit-runner."""

from __future__ import annotations

import sys
from pathlib import Path

_RUNNER_DIR = Path(__file__).resolve().parent.parent / "q-audit-runner"
if str(_RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNNER_DIR))

from evidence import (
    build_evidence_index,
    sha256_file,
    sign_evidence_index,
    write_evidence_index,
)

__all__ = [
    "build_evidence_index",
    "sha256_file",
    "sign_evidence_index",
    "write_evidence_index",
]
