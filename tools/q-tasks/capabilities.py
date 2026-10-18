"""Probe local runner primitives; never infer native protocol support from a CLI."""
import argparse
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile

from runtime_support import BoundedOutput

CAPABILITIES = ('durable_receipts', 'process_group_cancellation', 'bounded_output',
                'native_conversation_resume', 'delegation', 'workspace_isolation', 'process_containment')
BACKENDS = ('local', 'codex', 'claude', 'pi')


def probe(name):
    if name == 'bounded_output':
        output = io.BytesIO()
        capture = BoundedOutput(output, 1024)
        capture.write(b'head' + b'x' * 4096 + b'tail')
        return len(output.getvalue()) == 1024 and output.getvalue().endswith(b'tail')
    if name == 'durable_receipts':
        with tempfile.TemporaryDirectory(prefix='q-agent-probe-') as temp:
            database = Path(temp) / 'probe.sqlite3'
            db = sqlite3.connect(database)
            try:
                if db.execute('PRAGMA journal_mode=WAL').fetchone()[0] != 'wal':
                    return False
                db.execute('PRAGMA synchronous=FULL')
                db.execute('CREATE TABLE receipt (value TEXT)')
                db.execute("INSERT INTO receipt VALUES ('saved')")
                db.commit()
            finally:
                db.close()
            db = sqlite3.connect(database.as_uri() + '?mode=ro', uri=True)
            try:
                return db.execute('SELECT value FROM receipt').fetchone()[0] == 'saved'
            finally:
                db.close()
    if name == 'process_group_cancellation':
        child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            if os.getpgid(child.pid) != child.pid:
                return False
            os.killpg(child.pid, signal.SIGTERM)
            return child.wait(timeout=2) < 0
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
    return False


def inspect_backend(backend='local', only=None):
    if backend not in BACKENDS:
        raise ValueError('Unknown backend')
    names = [name for name in CAPABILITIES if only is None or name in only]
    capabilities = {}
    for name in names:
        if backend != 'local':
            capabilities[name] = {'status': 'unknown', 'reason': 'no_verified_native_adapter'}
        elif name not in CAPABILITIES[:3]:
            capabilities[name] = {'status': 'unsupported', 'reason': 'not_implemented_by_local_runner'}
        else:
            try:
                verified = probe(name)
            except (OSError, sqlite3.Error, subprocess.SubprocessError, AttributeError):
                verified = False
            capabilities[name] = {'status': 'verified' if verified else 'unavailable',
                                  'reason': 'local_primitive_probe_passed' if verified else 'local_primitive_probe_failed'}
    return {'schema_version': 1, 'backend': backend,
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'availability': 'available' if backend == 'local' else 'installed' if shutil.which(backend) else 'missing',
            'probe_scope': 'temporary_files_and_owned_processes; not project isolation or inference',
            'capabilities': capabilities}


def require_capabilities(required):
    if required:
        report = inspect_backend('local', only=required)
        for name in required:
            if report['capabilities'].get(name, {}).get('status') != 'verified':
                raise ValueError('Required capability unavailable: ' + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend', choices=BACKENDS, default='local')
    args = parser.parse_args()
    print(json.dumps(inspect_backend(args.backend)))


if __name__ == '__main__':
    main()
