"""Structured, local-only observability for q-cockpit."""

from __future__ import annotations

import json
import math
import os
import re
import stat
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


# Direct-file consumers historically load this helper under either module name.
# Reuse the context itself even when an external loader creates another module.
_existing = sys.modules.get("cockpit_observability") or sys.modules.get("q_cockpit_observability")
_REQUEST_ID: ContextVar[str | None] = getattr(_existing, "_REQUEST_ID", None) or ContextVar(
    "q_cockpit_request_id", default=None)
_RESERVED_FIELDS = frozenset({"request_id", "operation", "outcome", "timestamp",
                              "timestamp_source", "provenance"})


def native_record(fields: dict, *, emitter: str = "q-cockpit") -> dict:
    """Own receipt attribution, not the identity or completion of a referenced action."""
    record = {key: value for key, value in fields.items() if key not in _RESERVED_FIELDS}
    record.update(timestamp=datetime.now(timezone.utc).isoformat(),
                  timestamp_source="runtime_clock",
                  request_id=current_request_id() or new_request_id(), provenance={
                      "emitter": {"kind": "tool", "name": emitter},
                      "workflow": None, "executor": None, "host": None,
                      "orchestrator": None, "phase": None, "lifecycle": "unknown"})
    return record


def _label(value: Any) -> str | None:
    # Labels are not a channel for command output or local filesystem paths.
    if not isinstance(value, str) or not value.strip() or "/" in value or "\\" in value:
        return None
    return " ".join(value.split())[:96]


def _measurement(value: Any) -> dict:
    missing = {"status": "unavailable", "value": None, "source": None, "basis": None}
    if not isinstance(value, dict):
        return missing
    number, status = value.get("value"), value.get("status")
    source, basis = _label(value.get("source")), _label(value.get("basis"))
    if (status not in ("measured", "estimated") or isinstance(number, bool)
            or not isinstance(number, (int, float))
            or (isinstance(number, float) and not math.isfinite(number))
            or number < 0 or not source or (status == "estimated" and not basis)):
        return missing
    result = {"status": status, "value": number, "source": source, "basis": basis}
    if _label(value.get("currency")):
        result["currency"] = _label(value["currency"])
    return result


def public_event(record: Any) -> dict | None:
    """Fixed-field projection of recorded claims; never authentication/authorization."""
    if not isinstance(record, dict):
        return None
    timestamp = record.get("timestamp")
    try:
        parsed = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) and len(timestamp) <= 64 else None
        if parsed is None or parsed.utcoffset() is None:
            timestamp = None
    except ValueError:
        timestamp = None
    raw = record.get("provenance")
    raw = raw if isinstance(raw, dict) else {}
    emitter = raw.get("emitter")
    emitter = emitter if isinstance(emitter, dict) else {}
    provenance = {key: _label(raw.get(key)) for key in
                  ("workflow", "executor", "host", "orchestrator", "phase")}
    kind = emitter.get("kind")
    provenance["emitter"] = {"kind": kind if kind in
        ("llm", "tool", "host", "harness") else "unknown", "name": _label(emitter.get("name"))}
    lifecycle = raw.get("lifecycle")
    provenance["lifecycle"] = lifecycle if lifecycle in (
        "configured", "loaded", "invoked", "executed", "verified") else "unknown"
    telemetry = record.get("telemetry")
    telemetry = telemetry if isinstance(telemetry, dict) else {}
    operation = record.get("operation", record.get("type"))
    operation = operation if isinstance(operation, str) and re.fullmatch(r"[a-zA-Z0-9_.-]{1,64}", operation) else "unknown"
    return {"timestamp": timestamp,
            "timestamp_source": ("runtime_clock" if record.get("timestamp_source") == "runtime_clock"
                                 else "recorded") if timestamp else "unavailable",
            "request_id": _label(record.get("request_id")), "operation": operation,
            "provenance": provenance,
            "telemetry": {key: _measurement(telemetry.get(key)) for key in ("tokens", "cost")}}


def compact_event(record: dict) -> str:
    """Format a public event with its recorded timezone, never a substitute clock."""
    event = public_event(record)
    if event is None:
        return "[time unavailable] [unknown | unknown | unknown] unknown"
    timestamp = event["timestamp"]
    clock = "time unavailable"
    if timestamp:
        parsed = datetime.fromisoformat(timestamp)
        offset = parsed.strftime("%z")
        clock = f"{parsed:%H:%M:%S} {offset[:3]}:{offset[3:]}"
    actor = event["provenance"]
    emitter = actor["emitter"]
    emitter_label = emitter["kind"]
    if emitter["name"] or emitter["kind"] != "unknown":
        emitter_label += f" ({emitter['name'] or 'unknown'})"
    return (f"[{clock}] [{emitter_label} | "
            f"{actor['workflow'] or 'unknown'} | {actor['phase'] or 'unknown'}] {event['operation']}")


def framework_version() -> str | None:
    """Read the serving package, not the audited project's similarly named file."""
    try:
        return _label(json.loads((Path(__file__).resolve().parents[2] / "skill.json").read_text()).get("version"))
    except (OSError, ValueError, AttributeError):
        return None


def communication_snapshot(session: Path | None) -> dict:
    """Read at most 256 KiB/40 complete records; never create or follow links."""
    result = {"status": "absent", "framework_version": framework_version(),
              "events": [], "truncated": False}
    if session is None:
        return result
    directory = Path(os.path.abspath(session))
    try:
        # Walk anchored directory descriptors so ancestor-link replacement cannot
        # redirect the read between validation and open.
        with_dir = os.open(directory.anchor, os.O_RDONLY | os.O_DIRECTORY)
        try:
            for part in directory.parts[1:]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=with_dir)
                os.close(with_dir)
                with_dir = child
            fd = os.open("events.jsonl", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=with_dir)
        finally:
            os.close(with_dir)
        with os.fdopen(fd, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise OSError("Unsafe event file")
            offset = max(0, info.st_size - 256 * 1024)
            handle.seek(offset)
            data = handle.read(256 * 1024)
        lines = data.split(b"\n")
        if offset:
            lines = lines[1:]
        # The last fragment is not a complete JSONL record even when valid JSON.
        lines = lines[:-1]
        events = []
        for line in lines:
            try:
                event = public_event(json.loads(line))
            except (ValueError, UnicodeError, RecursionError):
                continue
            if event is not None:
                event["compact"] = compact_event(event)
                events.append(event)
        result.update(status="available", events=events[-40:],
                      truncated=bool(offset or len(events) > 40))
    except FileNotFoundError:
        pass
    except (OSError, ValueError):
        result["status"] = "unavailable"
    return result


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
        record: dict[str, Any] = native_record(fields or {})
        record.update({
            "request_id": correlation_id,
            "operation": operation,
            "outcome": outcome,
        })
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        return correlation_id
