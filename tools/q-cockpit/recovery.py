"""Local backup, restore, and health checks for q-cockpit sessions."""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4

MAX_ARCHIVE_MEMBERS = 10_000
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
_MANIFEST_NAME = "backup-manifest.json"


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _source_files(source: Path) -> list[Path]:
    """List regular source files while rejecting links that leave the source."""
    files: list[Path] = []
    for current, directories, names in os.walk(source, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in list(directories):
            path = current_path / name
            if path.is_symlink():
                if not _inside(path.resolve(strict=False), source):
                    raise ValueError(f"Source symlink escapes source tree: {path}")
                # Do not follow symlinked directories; backups contain regular files only.
                directories.remove(name)
        for name in names:
            path = current_path / name
            if path.is_symlink():
                if not _inside(path.resolve(strict=False), source):
                    raise ValueError(f"Source symlink escapes source tree: {path}")
                if path.resolve(strict=False).is_file():
                    files.append(path)
            elif path.is_file():
                files.append(path)
    return sorted(files, key=lambda path: path.relative_to(source).as_posix())


def backup_sessions(source: Path, archive: Path) -> Path:
    source = Path(source).resolve()
    archive = Path(archive).resolve(strict=False)
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"Session directory does not exist: {source}")
    if _inside(archive, source):
        raise ValueError("Backup archive must be outside its source tree")

    files = _source_files(source)
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "format": "q-cockpit-session-backup-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": str(source),
    }
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr(_MANIFEST_NAME, json.dumps(manifest, indent=2) + "\n")
        for path in files:
            relative = path.relative_to(source).as_posix()
            if relative == _MANIFEST_NAME:
                raise ValueError(f"Source contains reserved backup member: {relative}")
            bundle.write(path, relative)
    return archive


def _member_path(name: str, staging: Path) -> str:
    if not name or "\x00" in name or "\\" in name or re.match(r"^[A-Za-z]:", name):
        raise ValueError(f"Unsafe archive path: {name}")
    stripped = name[:-1] if name.endswith("/") else name
    path = PurePosixPath(stripped)
    if path.is_absolute() or not path.parts or any(part in {".", ".."} for part in path.parts):
        raise ValueError(f"Unsafe archive path: {name}")
    normalized = path.as_posix()
    if normalized != stripped:
        raise ValueError(f"Unsafe archive path: {name}")
    target = (staging / normalized).resolve()
    if not _inside(target, staging):
        raise ValueError(f"Unsafe archive path: {name}")
    return normalized


def _validate_archive(bundle: zipfile.ZipFile, staging: Path) -> tuple[list[zipfile.ZipInfo], int]:
    members = bundle.infolist()
    if len(members) > MAX_ARCHIVE_MEMBERS:
        raise ValueError("Backup archive contains too many members")
    seen: set[str] = set()
    regular_members: list[zipfile.ZipInfo] = []
    total_bytes = 0
    manifest: zipfile.ZipInfo | None = None
    for member in members:
        normalized = _member_path(member.filename, staging)
        if normalized in seen:
            raise ValueError(f"Duplicate archive member: {member.filename}")
        seen.add(normalized)
        mode = (member.external_attr >> 16) & 0o170000
        if stat.S_ISLNK(mode):
            raise ValueError(f"Symlink archive member is not allowed: {member.filename}")
        if member.file_size < 0 or member.file_size > MAX_MEMBER_BYTES:
            raise ValueError(f"Archive member exceeds size limit: {member.filename}")
        total_bytes += member.file_size
        if total_bytes > MAX_TOTAL_BYTES:
            raise ValueError("Backup archive exceeds total extraction limit")
        if normalized == _MANIFEST_NAME:
            if member.is_dir():
                raise ValueError("Backup manifest must be a file")
            manifest = member
        elif not member.is_dir():
            regular_members.append(member)
    if manifest is None:
        raise ValueError("Backup manifest is missing")
    raw_manifest = bytearray()
    with bundle.open(manifest) as manifest_stream:
        while True:
            remaining = 64 * 1024 - len(raw_manifest)
            chunk = manifest_stream.read(min(8192, remaining + 1))
            if not chunk:
                break
            raw_manifest.extend(chunk)
            if len(raw_manifest) > 64 * 1024:
                raise ValueError("Backup manifest exceeds size limit")
    try:
        metadata = json.loads(bytes(raw_manifest).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Backup manifest is invalid") from exc
    if metadata.get("format") != "q-cockpit-session-backup-v1":
        raise ValueError("Unsupported backup format")
    return regular_members, total_bytes


def _extract_members(bundle: zipfile.ZipFile, members: list[zipfile.ZipInfo], staging: Path) -> None:
    total_written = 0
    for member in members:
        relative = _member_path(member.filename, staging)
        target = staging / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        written = 0
        with bundle.open(member) as source, target.open("xb") as output:
            while True:
                chunk = source.read(min(1024 * 1024, MAX_MEMBER_BYTES - written))
                if not chunk:
                    break
                written += len(chunk)
                total_written += len(chunk)
                if written > MAX_MEMBER_BYTES or total_written > MAX_TOTAL_BYTES:
                    raise ValueError("Backup extraction limit exceeded")
                output.write(chunk)
        if written != member.file_size:
            raise ValueError(f"Archive member size changed during extraction: {member.filename}")


def _validate_merge_targets(staging: Path, destination: Path, overwrite: bool) -> None:
    for current, directories, files in os.walk(staging, topdown=True, followlinks=False):
        current_path = Path(current)
        for name in directories + files:
            staged = current_path / name
            relative = staged.relative_to(staging)
            target = destination / relative
            cursor = target.parent
            while cursor != destination:
                if cursor.is_symlink():
                    raise ValueError(f"Restore target traverses a symlink: {cursor}")
                cursor = cursor.parent
            if target.is_symlink():
                raise ValueError(f"Restore target is a symlink: {target}")
            if not target.exists():
                continue
            same_kind = staged.is_dir() == target.is_dir()
            if not same_kind or (not staged.is_dir() and not overwrite):
                if not overwrite:
                    raise FileExistsError(f"Restore target exists: {target}")
                raise FileExistsError(f"Restore target type conflicts: {target}")


def _commit_staged(staging: Path, destination: Path, overwrite: bool) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        os.replace(staging, destination)
        return
    if not destination.is_dir():
        raise FileExistsError(f"Restore destination is not a directory: {destination}")
    _validate_merge_targets(staging, destination, overwrite)

    merged = Path(tempfile.mkdtemp(prefix=f".{destination.name}.merge-", dir=destination.parent))
    backup: Path | None = None
    try:
        shutil.copytree(destination, merged, symlinks=True, dirs_exist_ok=True)
        shutil.copytree(staging, merged, symlinks=False, dirs_exist_ok=True)
        backup = destination.parent / f".{destination.name}.previous-{os.getpid()}-{uuid4().hex}"
        os.replace(destination, backup)
        try:
            os.replace(merged, destination)
        except Exception:
            os.replace(backup, destination)
            backup = None
            raise
        shutil.rmtree(backup, ignore_errors=True)
        backup = None
    finally:
        if merged.exists():
            shutil.rmtree(merged, ignore_errors=True)
        if backup is not None and not destination.exists():
            os.replace(backup, destination)


def restore_sessions(archive: Path, destination: Path, *, overwrite: bool = False) -> Path:
    archive = Path(archive).resolve()
    destination = Path(destination).resolve(strict=False)
    if not zipfile.is_zipfile(archive):
        raise ValueError(f"Invalid backup archive: {archive}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".q-cockpit-restore-", dir=destination.parent))
    try:
        with zipfile.ZipFile(archive) as bundle:
            members, _ = _validate_archive(bundle, staging)
            _extract_members(bundle, members, staging)
        _commit_staged(staging, destination, overwrite)
        return destination
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)


def health_report(sessions_root: Path, session_dir: Path | None = None) -> dict[str, Any]:
    root = Path(sessions_root).resolve()
    checks = {
        "sessions_root": root.exists() and root.is_dir(),
        "writable": False,
        "session_state": True,
    }
    if checks["sessions_root"]:
        try:
            with tempfile.NamedTemporaryFile(dir=root, prefix=".health-", delete=True):
                checks["writable"] = True
        except OSError:
            checks["writable"] = False
    if session_dir:
        state = Path(session_dir).resolve() / "state.json"
        checks["session_state"] = state.is_file()
    return {
        "healthy": all(checks.values()),
        "sessions_root": str(root),
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
