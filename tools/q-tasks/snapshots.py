"""Explicit, non-overwriting SQLite snapshots; logs and workspaces remain separate."""
import os
from pathlib import Path
import sqlite3
from contextlib import closing
from process_guard import workload


def sync(path):
    with path.open('rb') as handle:
        os.fsync(handle.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def backup(store, target):
    target = Path(target).resolve()
    with store.lock():
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        try:
            with closing(sqlite3.connect(target)) as destination:
                store.db.backup(destination)
                if destination.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                    raise ValueError('Snapshot integrity check failed')
            sync(target)
        except BaseException:
            target.unlink()
            raise
    return {'snapshot': str(target), 'schema_version': 1, 'includes': 'ledger, workflows, effects; not logs or source'}


def restore(store, source):
    source = Path(source).resolve()
    with store.lock(), workload(store.directory, store.db):
        if store.db.execute('SELECT count(*) FROM tasks').fetchone()[0]:
            raise ValueError('Restore requires an empty ledger; existing history is never overwritten')
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as origin:
            if origin.execute('PRAGMA quick_check').fetchall() != [('ok',)]:
                raise ValueError('Snapshot integrity check failed')
            if origin.execute('PRAGMA user_version').fetchone()[0] != 1:
                raise ValueError('Unsupported snapshot version')
            saved = origin.execute("SELECT value FROM store_meta WHERE key='project'").fetchone()
            if not saved or saved[0] != str(store.root):
                raise ValueError('Snapshot belongs to a different project path; relocation requires explicit migration')
            if origin.execute('SELECT count(*) FROM workflows WHERE version != 1').fetchone()[0]:
                raise ValueError('Unsupported workflow definition version in snapshot')
            origin.backup(store.db)
    return {'restored': str(source), 'recovery': 'inspect with resume; no commands replayed'}
