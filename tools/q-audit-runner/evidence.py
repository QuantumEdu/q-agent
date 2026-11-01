"""Canonical, hash-addressed evidence index for audit reports."""

from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _base_commit(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def build_evidence_index(
    root: Path,
    manifest: Path,
    items: Iterable[Path],
    *,
    base_commit: str | None = None,
    validator_version: str = "q-agent-v2.5.4",
) -> dict[str, Any]:
    root = Path(root).resolve()
    manifest = Path(manifest).resolve()
    records = []
    for item in sorted((Path(path).resolve() for path in items), key=lambda path: path.as_posix()):
        records.append({
            "path": item.relative_to(root).as_posix() if item.is_relative_to(root) else str(item),
            "sha256": sha256_file(item),
        })
    return {
        "format": "q-agent-audit-evidence-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": root.name,
        "base_commit": base_commit or _base_commit(root),
        "manifest": manifest.relative_to(root).as_posix() if manifest.is_relative_to(root) else str(manifest),
        "manifest_sha256": sha256_file(manifest),
        "validator_version": validator_version,
        "items": records,
    }


def sign_evidence_index(index: dict[str, Any], private_key: Path) -> str:
    """Sign canonical evidence JSON when optional cryptography is installed."""
    try:
        serialization = importlib.import_module("cryptography.hazmat.primitives.serialization")
    except ImportError as exc:
        raise RuntimeError("Ed25519 signing requires the optional 'cryptography' package") from exc
    payload = json.dumps(index, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    key_data = Path(private_key).read_bytes()
    key = serialization.load_pem_private_key(key_data, password=None)
    return key.sign(payload).hex()


def write_evidence_index(index: dict[str, Any], output: Path) -> Path:
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    return output
