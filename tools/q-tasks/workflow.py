"""Versioned, transactional workflow checkpoints for the local command runner."""
import hashlib
import json
from pathlib import Path
from process_guard import workload

VERSION = 1
PHASES = {
    'reproducing': {'fixing', 'blocked'}, 'fixing': {'verifying', 'blocked'},
    'verifying': {'fixing', 'review', 'blocked'},
    'review': {'fixing', 'awaiting_approval', 'complete', 'blocked'},
    'awaiting_approval': {'fixing', 'complete', 'blocked'}, 'complete': set(), 'blocked': set(),
}


def controller_identity():
    root = Path(__file__).parent
    return digest({name: (root / name).read_text() for name in
                   ('q_tasks.py', 'workflow.py', 'process_guard.py', 'operations.py')})


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS workflows (
        task_id TEXT PRIMARY KEY, version INTEGER NOT NULL, phase TEXT NOT NULL,
        sequence INTEGER NOT NULL, corrections INTEGER NOT NULL, maximum INTEGER NOT NULL,
        config TEXT NOT NULL, tests TEXT NOT NULL, source_hash TEXT NOT NULL,
        proof TEXT, review TEXT)''')
    db.execute('''CREATE TABLE IF NOT EXISTS workflow_events (
        request_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, signature TEXT NOT NULL,
        result TEXT NOT NULL, at TEXT NOT NULL, input TEXT NOT NULL)''')


class Workflow:
    def __init__(self, store):
        self.store, self.db = store, store.db

    def get(self, task):
        row = self.db.execute('SELECT * FROM workflows WHERE task_id=?', (task,)).fetchone()
        if row is None:
            return None
        d = dict(row)
        if d['version'] != VERSION:
            raise ValueError('Unsupported workflow version; inspect/migrate explicitly')
        for field in ('config', 'tests', 'proof', 'review'):
            d[field] = json.loads(d[field]) if d[field] else None
        return d

    def files(self, roots):
        files = {}
        for name in roots:
            rel = Path(name)
            if (not name or rel.is_absolute() or '..' in rel.parts or
                    rel.parts[0] in {'.git', '.cache'} or name == '.'):
                raise ValueError('Use explicit project-relative source/test paths outside runtime state')
            path = self.store.root / rel
            if path.is_symlink() or not path.resolve().is_relative_to(self.store.root):
                raise ValueError('Workflow path escapes project or is a symlink')
            candidates = [path] if not path.is_dir() else sorted(path.rglob('*'))
            for entry in candidates:
                if '__pycache__' in entry.parts or entry.suffix == '.pyc':
                    continue
                if entry.is_symlink():
                    raise ValueError('Symlink in workflow surface')
                if entry.is_file():
                    files[str(entry.relative_to(self.store.root))] = hashlib.sha256(entry.read_bytes()).hexdigest()
        return files

    def candidate(self, w):
        head, clean = self.store.checkout()
        if not clean:
            raise ValueError('Commit the candidate and exclude runtime artifacts first')
        self.validate(w)
        return digest({'commit': head, 'source': self.files(w['config']['source']),
                       'tests': self.files(w['config']['tests']), 'config': w['config']})

    def validate(self, w):
        if w['config'].get('controller') != controller_identity():
            raise ValueError('Workflow controller changed; explicit migration/new authorization required')
        if self.files(w['config']['harness']) != w['config']['harness_hashes']:
            raise ValueError('Harness configuration changed; explicit migration/new authorization required')
        current = self.files(w['config']['tests'])
        if w['phase'] == 'reproducing':
            if any(current.get(k) != v for k, v in w['tests'].items()):
                raise ValueError('Existing acceptance tests changed during reproduction')
        elif current != w['tests']:
            raise ValueError('Frozen acceptance tests changed')

    def cached(self, request, signature):
        row = self.db.execute('SELECT signature, result FROM workflow_events WHERE request_id=?', (request,)).fetchone()
        if row:
            if row['signature'] != digest(signature):
                raise ValueError('Workflow request ID conflicts with previous arguments')
            return json.loads(row['result'])
        return None

    def record(self, request, task, signature):
        result = self.get(task)
        self.db.execute('INSERT INTO workflow_events VALUES (?, ?, ?, ?, ?, ?)',
                        (request, task, digest(signature), json.dumps(result), self.store.timestamp(), json.dumps(signature)))
        return result

    def start(self, task, request, source, tests, maximum, definition, backend, model, harness):
        signature = ['start', task, source, tests, maximum, definition, backend, model, harness]
        with self.store.lock(), workload(self.store.directory, self.db, require_linux=True), self.db:
            old = self.cached(request, signature)
            if old is not None:
                return old
            self.store.task(task)
            if self.get(task):
                raise ValueError('Workflow already exists; its correction budget cannot be reset')
            if not 1 <= maximum <= 3 or not definition.strip():
                raise ValueError('Require a definition version and correction budget in 1..3')
            source_files, test_files = self.files(source), self.files(tests)
            if not test_files or set(source_files) & set(test_files):
                raise ValueError('Require frozen baseline tests and disjoint source/test paths')
            config = dict(controller=controller_identity(), source=source, tests=tests, definition=definition, backend=backend,
                          model=model, harness=harness, harness_hashes=self.files(harness))
            self.db.execute('INSERT INTO workflows VALUES (?, ?, ?, 0, 0, ?, ?, ?, ?, NULL, NULL)',
                            (task, VERSION, 'reproducing', maximum, json.dumps(config),
                             json.dumps(test_files), digest(source_files)))
            return self.record(request, task, signature)

    def advance(self, task, request, sequence, phase, evidence):
        signature = ['advance', task, sequence, phase, evidence]
        with self.store.lock(), workload(self.store.directory, self.db), self.db:
            old = self.cached(request, signature)
            if old is not None:
                return old
            w = self.get(task)
            if not w or w['sequence'] != sequence or phase not in PHASES[w['phase']]:
                raise ValueError('Stale checkpoint or invalid phase transition')
            if not evidence.strip() or self.store.task(task)['state'] in {'running', 'uncertain'}:
                raise ValueError('Require inspection evidence and settled execution before transition')
            self.validate(w)
            last = self.db.execute('SELECT * FROM attempts WHERE task_id=? ORDER BY rowid DESC LIMIT 1', (task,)).fetchone()
            if phase == 'fixing':
                if w['corrections'] >= w['maximum']:
                    raise ValueError('Correction budget exhausted; workflow remains blocked for further edits')
                if w['phase'] == 'reproducing':
                    dispatch = self.db.execute('SELECT result FROM workflow_events WHERE request_id=? AND task_id=?',
                        ('dispatch:' + last['request_id'], task)).fetchone() if last else None
                    bound = json.loads(dispatch['result']) if dispatch else None
                    if (not last or last['exit_code'] in (None, 0) or last['error'] or not bound or
                            bound['phase'] != 'reproducing' or bound['config'] != w['config'] or
                            bound['source_hash'] != w['source_hash']):
                        raise ValueError('Require a settled failing reproduction bound to this workflow')
            if phase == 'verifying':
                reconciliation = self.db.execute('SELECT outcome FROM reconciliations WHERE request_id=?',
                    (last['request_id'],)).fetchone() if last else None
                completed = last and (last['state'] == 'awaiting_verification' or
                    reconciliation and reconciliation['outcome'] == 'completed')
                if not w['corrections'] or not completed:
                    raise ValueError('Require a completed correction before verification')
            if phase in {'review', 'awaiting_approval', 'complete'}:
                if not w['proof'] or w['proof']['candidate'] != self.candidate(w):
                    raise ValueError('Require current commit-bound verification')
            if phase in {'awaiting_approval', 'complete'}:
                if not w['review'] or w['review']['verdict'] != 'APPROVED' or w['review']['candidate'] != self.candidate(w):
                    raise ValueError('Require independent APPROVED review for this candidate')
            if phase == 'complete' and self.db.execute(
                    "SELECT count(*) FROM effects WHERE task_id=? AND state NOT IN ('completed', 'no_effect')", (task,)).fetchone()[0]:
                raise ValueError('Outstanding external effects must be reconciled before completion')
            frozen = self.files(w['config']['tests'])
            changed = self.db.execute('UPDATE workflows SET phase=?, sequence=sequence+1, tests=? WHERE task_id=? AND sequence=? AND phase=?',
                            (phase, json.dumps(frozen), task, sequence, w['phase'])).rowcount
            if changed != 1:
                raise ValueError('Checkpoint changed concurrently')
            if phase in {'fixing', 'verifying'}:
                self.db.execute("UPDATE tasks SET state='pending' WHERE id=?", (task,))
            return self.record(request, task, signature)

    def review(self, task, request, sequence, verdict, reviewer, evidence):
        signature = ['review', task, sequence, verdict, reviewer, evidence]
        with self.store.lock(), workload(self.store.directory, self.db), self.db:
            old = self.cached(request, signature)
            if old is not None:
                return old
            w = self.get(task)
            if not w or w['phase'] != 'review' or sequence != w['sequence']:
                raise ValueError('Review requires the current review checkpoint')
            candidate = self.candidate(w)
            if not evidence.strip() or not reviewer.strip() or not w['proof'] or w['proof']['candidate'] != candidate:
                raise ValueError('Require reviewer, evidence and current verification')
            review = dict(verdict=verdict, reviewer=reviewer, evidence=evidence, candidate=candidate)
            changed = self.db.execute("UPDATE workflows SET review=?, sequence=sequence+1 WHERE task_id=? AND sequence=? AND phase='review'", (json.dumps(review), task, sequence)).rowcount
            if changed != 1:
                raise ValueError('Review checkpoint changed concurrently')
            return self.record(request, task, signature)

    def prepare(self, task, request, operation):
        """Called INSIDE the attempt transaction, before any child is released."""
        w = self.get(task)
        if not w:
            return
        self.validate(w)
        if w['phase'] in {'blocked', 'complete', 'review', 'awaiting_approval'}:
            raise ValueError('Workflow phase does not permit command dispatch')
        if operation == 'verify' and w['phase'] != 'verifying':
            raise ValueError('Verification requires the verifying phase')
        if w['phase'] == 'verifying':
            self.db.execute('UPDATE workflows SET proof=NULL, review=NULL WHERE task_id=?', (task,))
        if w['phase'] == 'fixing':
            if w['corrections'] >= w['maximum']:
                raise ValueError('Correction budget exhausted')
            changed = self.db.execute("UPDATE workflows SET corrections=corrections+1, sequence=sequence+1, proof=NULL, review=NULL WHERE task_id=? AND sequence=? AND corrections < maximum AND phase='fixing'", (task, w['sequence'])).rowcount
            if changed != 1:
                raise ValueError('Correction budget/checkpoint changed concurrently')
        self.record('dispatch:' + request, task, ['dispatch', task, request, operation])

    def finish(self, task, request, operation, state):
        w = self.get(task)
        if not w:
            return state
        try:
            self.validate(w)
            if w['phase'] == 'reproducing' and digest(self.files(w['config']['source'])) != w['source_hash']:
                raise ValueError('Source changed before reproduction completed')
            if w['phase'] == 'verifying' and digest(self.files(w['config']['source'])) != w['source_hash']:
                raise ValueError('Verification modified source')
            if state == 'verified':
                proof = dict(candidate=self.candidate(w), request_id=request)
                self.db.execute('UPDATE workflows SET proof=? WHERE task_id=?', (json.dumps(proof), task))
            if w['phase'] == 'fixing':
                self.db.execute('UPDATE workflows SET source_hash=? WHERE task_id=?',
                                (digest(self.files(w['config']['source'])), task))
        except ValueError:
            state = 'uncertain'
            self.db.execute("UPDATE workflows SET phase='blocked', proof=NULL, review=NULL WHERE task_id=?", (task,))
        self.db.execute('UPDATE workflows SET sequence=sequence+1 WHERE task_id=?', (task,))
        self.record('finish:' + request, task, ['finish', task, request, state])
        return state
