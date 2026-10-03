"""Bounded services for q-cockpit strategic improvements."""

from __future__ import annotations

import hashlib
import os
import subprocess
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any

_ACTIONS = (
    {"id": "status", "label": "Status", "description": "Read the current project and session snapshot."},
    {"id": "new_session", "label": "New session", "description": "Create a new elicitation session."},
    {"id": "inspect_artifact", "label": "Inspect artifact", "description": "Open a project artifact in the cockpit."},
    {"id": "approve_gate", "label": "Approve gate", "description": "Record a human gate decision."},
    {"id": "wait", "label": "Wait", "description": "Wait for the next session event."},
)


def action_catalog() -> list[dict[str, str]]:
    return [dict(action) for action in _ACTIONS]


class ProjectSnapshotWorker:
    """Bounded, coalescing snapshot cache for repository scans."""

    def __init__(self, scanner: Any):
        self.scanner = scanner
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="q-cockpit-snapshot")
        self._cache: dict[str, dict[str, Any]] = {}
        self._futures: dict[str, Future[dict[str, Any]]] = {}
        self._lock = Lock()

    @staticmethod
    def _tree_signature(root: Path) -> str:
        """Fingerprint file metadata without reading project contents."""
        digest = hashlib.sha256()
        for current, directories, files in os.walk(root, topdown=True, followlinks=False):
            directories[:] = sorted(name for name in directories if name != ".git")
            for name in sorted(files):
                path = Path(current) / name
                try:
                    stat = path.lstat()
                    relative = path.relative_to(root).as_posix()
                    target = os.readlink(path) if stat.st_mode & 0o170000 == 0o120000 else ""
                except OSError:
                    continue
                digest.update(
                    f"{relative}\0{stat.st_mode}\0{stat.st_size}\0{stat.st_mtime_ns}\0{target}\n".encode()
                )
        return digest.hexdigest()

    @staticmethod
    def _changed_files_signature(root: Path, status: str) -> str:
        digest = hashlib.sha256()
        paths: set[Path] = set()
        for line in status.splitlines():
            if len(line) < 4:
                continue
            name = line[3:]
            if " -> " in name:
                name = name.rsplit(" -> ", 1)[-1]
            name = name.strip().strip('"')
            path = root / name
            if path.is_dir() and not path.is_symlink():
                for current, _, files in os.walk(path, followlinks=False):
                    paths.update(Path(current) / filename for filename in files)
            else:
                paths.add(path)
        for path in sorted(paths, key=lambda candidate: candidate.as_posix()):
            try:
                stat = path.lstat()
                relative = path.relative_to(root).as_posix()
                digest.update(f"{relative}\0{stat.st_size}\0{stat.st_mtime_ns}\0{stat.st_mode}\n".encode())
            except OSError:
                continue
        return digest.hexdigest()

    @classmethod
    def _git_signature(cls, root: Path) -> tuple[str, str, str, str] | None:
        try:
            head = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain=v1", "--untracked-files=all"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout
            index_path = subprocess.run(
                ["git", "rev-parse", "--git-path", "index"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
            index = Path(index_path)
            if not index.is_absolute():
                index = root / index
            stat = index.stat() if index.exists() else None
            index_signature = "missing" if stat is None else f"{stat.st_size}:{stat.st_mtime_ns}"
            return head, status, index_signature, cls._changed_files_signature(root, status)
        except (OSError, subprocess.SubprocessError):
            return None

    @classmethod
    def _signature(cls, root: Path) -> tuple[str, str, str, str]:
        resolved = root.resolve()
        git = cls._git_signature(resolved)
        if git is not None:
            head, status, index, changed_files = git
            status_signature = hashlib.sha256(f"{status}\0{changed_files}".encode()).hexdigest()
            return str(resolved), "git", f"{head}\0{index}", status_signature
        return str(resolved), "filesystem", cls._tree_signature(resolved), ""

    def _scan(self, root: Path) -> dict[str, Any]:
        return {
            "git": self.scanner.scan_git_info(root),
            "tasks": self.scanner.scan_tasks(root),
            "artifacts": self.scanner.scan_artifacts(root),
            "version": self.scanner.get_project_version(root),
        }

    def get(self, root: Path, refresh: bool = False) -> dict[str, Any]:
        signature = self._signature(root)
        key = signature[0]
        with self._lock:
            cached = self._cache.get(key)
            future = self._futures.get(key)
            if future and future.done():
                self._cache[key] = {"data": future.result(), "signature": signature}
                self._futures.pop(key, None)
                cached = self._cache[key]
                future = None
            if cached and not refresh and cached["signature"] == signature and not future:
                return {**cached["data"], "snapshot": {"state": "fresh", "signature": signature}}
            if cached and not future:
                self._futures[key] = self._executor.submit(self._scan, root)
                return {**cached["data"], "snapshot": {"state": "refreshing", "signature": signature}}
            if cached:
                return {**cached["data"], "snapshot": {"state": "stale", "signature": signature}}
        data = self._scan(root)
        with self._lock:
            self._cache[key] = {"data": data, "signature": signature}
        return {**data, "snapshot": {"state": "fresh", "signature": signature}}

    def close(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
