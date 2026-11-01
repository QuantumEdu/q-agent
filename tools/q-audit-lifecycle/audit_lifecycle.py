"""Backward-compatible re-export of AuditLifecycle and AuditState from q-audit-runner."""

from __future__ import annotations

import sys
from pathlib import Path

_RUNNER_DIR = Path(__file__).resolve().parent.parent / "q-audit-runner"
if str(_RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(_RUNNER_DIR))

from audit_lifecycle import AuditLifecycle, AuditState, _ALLOWED

__all__ = ["AuditLifecycle", "AuditState", "_ALLOWED"]
