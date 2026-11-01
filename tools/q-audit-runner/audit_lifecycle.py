"""Small state machine for deterministic Plan C audit runs."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AuditState(str, Enum):
    DISCOVERED = "discovered"
    DISPATCHED = "dispatched"
    CAPTURED = "captured"
    VALIDATED = "validated"
    AGGREGATED = "aggregated"
    BLOCKED = "blocked"


_ALLOWED = {
    AuditState.DISCOVERED: {AuditState.DISPATCHED, AuditState.BLOCKED},
    AuditState.DISPATCHED: {AuditState.CAPTURED, AuditState.BLOCKED},
    AuditState.CAPTURED: {AuditState.VALIDATED, AuditState.BLOCKED},
    AuditState.VALIDATED: {AuditState.AGGREGATED, AuditState.BLOCKED},
    AuditState.AGGREGATED: set(),
    AuditState.BLOCKED: {AuditState.DISCOVERED},
}


@dataclass
class AuditLifecycle:
    state: AuditState = AuditState.DISCOVERED
    history: list[dict] = field(default_factory=list)

    def transition(self, target: AuditState, reason: str) -> AuditState:
        if target not in _ALLOWED[self.state]:
            raise ValueError(f"Invalid audit transition: {self.state.value} -> {target.value}")
        if not reason.strip():
            raise ValueError("Audit transition reason is required")
        self.history.append({"from": self.state.value, "to": target.value, "reason": reason})
        self.state = target
        return self.state
