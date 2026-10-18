"""Bounded private output, fixed-field diagnostics and local resource admission."""
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import time

MIB = 1024 * 1024


def resources(root, minimum=256 * MIB):
    try:
        usage = shutil.disk_usage(root)
        return {'admitted': usage.free >= minimum, 'free_bytes': usage.free,
                'required_bytes': minimum, 'reason': 'ok' if usage.free >= minimum else 'low_disk'}
    except OSError:
        return {'admitted': False, 'free_bytes': None, 'required_bytes': minimum,
                'reason': 'measurement_unavailable'}


def runner_active(directory):
    path = Path(directory) / 'runner.lock'
    if not path.exists():
        return False
    with path.open('r') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(handle, fcntl.LOCK_UN)
            return False
        except BlockingIOError:
            return True


class BoundedOutput:
    def __init__(self, output, limit):
        self.output, self.limit, self.total = output, limit, 0
        self.tail_size = min(65536, limit // 2)
        self.head_size, self.head_written = limit - self.tail_size, 0
        self.tail = bytearray()

    def write(self, data):
        self.total += len(data)
        head = data[:max(0, self.head_size - self.head_written)]
        if head:
            self.output.seek(self.head_written)
            self.output.write(head)
            self.head_written += len(head)
        self.tail.extend(data[len(head):])
        if len(self.tail) > self.tail_size:
            del self.tail[:-self.tail_size]
        self.output.seek(self.head_written)
        self.output.write(self.tail)
        self.output.truncate()
        self.output.flush()


def capture_command(child, timeout, received, capture):
    """Drain pipes without retaining unbounded output or waiting on escaped writers."""
    deadline = time.monotonic() + timeout
    pipe = child.stdout
    os.set_blocking(pipe.fileno(), False)
    with selectors.DefaultSelector() as selector:
        selector.register(pipe, selectors.EVENT_READ)
        while True:
            if received:
                return 'terminated' if received[0] == 15 else 'interrupted'
            if time.monotonic() >= deadline:
                return 'timeout'
            for key, _ in selector.select(.05):
                data = os.read(key.fd, 65536)
                if data:
                    capture.write(data)
                else:
                    selector.unregister(pipe)
            if child.poll() is not None:
                # The exiting leader cannot have more than a bounded pipe buffer left.
                for _ in range(16):
                    try:
                        data = os.read(pipe.fileno(), 65536)
                    except BlockingIOError:
                        break
                    if not data:
                        break
                    capture.write(data)
                return None


def prune_logs(directory, recorded_paths, keep=7):
    eligible = []
    for name in recorded_paths:
        path = Path(name)
        if path.parent != directory or not re.fullmatch(r'[0-9a-f]{32}\.log', path.name):
            continue
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            continue
        eligible.append(path)
    for path in eligible[keep:]:
        path.unlink()


def diagnostic(directory, fields, limit=256 * 1024):
    # Intentionally omit task titles, IDs, arguments, raw output, paths and error strings.
    record = {'timestamp': datetime.now(timezone.utc).isoformat()}
    for key, choices in {'operation': {'run', 'verify'}, 'state': {
            'failed', 'uncertain', 'awaiting_verification', 'verified'}}.items():
        if fields.get(key) in choices:
            record[key] = fields[key]
    for key in ('exit_code', 'output_bytes', 'output_truncated'):
        if isinstance(fields.get(key), (int, bool)):
            record[key] = fields[key]
    data = (json.dumps(record) + '\n').encode()
    current, previous = Path(directory) / 'diagnostics.jsonl', Path(directory) / 'diagnostics.previous.jsonl'
    for path in (current, previous):
        if path.is_symlink() or (path.exists() and (not path.is_file() or path.stat().st_nlink != 1)):
            raise OSError('Unsafe diagnostic file')
    if current.exists() and current.stat().st_size + len(data) > limit:
        current.replace(previous)
    with current.open('ab') as handle:
        os.chmod(current, 0o600)
        handle.write(data)
