"""Structured, local-only observability for q-cockpit."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


_REQUEST_ID: ContextVar[str | None] = ContextVar("q_cockpit_request_id", default=None)
_RESERVED_FIELDS = frozenset({"request_id", "operation", "outcome", "timestamp"})


def new_request_id() -> str:
    return uuid4().hex


def current_request_id() -> str | None:
    """Return the request correlation ID for the current handler context."""
    return _REQUEST_ID.get()


@contextmanager
def request_context(request_id: str | None = None) -> Iterator[str]:
    """Propagate one request ID through legacy handlers without changing their APIs."""
    correlation_id = request_id or new_request_id()
    token = _REQUEST_ID.set(correlation_id)
    try:
        yield correlation_id
    finally:
        _REQUEST_ID.reset(token)


class StructuredEventLogger:
    """Append structured JSONL events without external logging dependencies."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        operation: str,
        fields: dict[str, Any] | None = None,
        *,
        outcome: str = "ok",
        request_id: str | None = None,
    ) -> str:
        correlation_id = request_id or current_request_id() or new_request_id()
        record: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": correlation_id,
            "operation": operation,
            "outcome": outcome,
        }
        if fields:
            record.update({key: value for key, value in fields.items() if key not in _RESERVED_FIELDS})
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return correlation_id
