"""Candidate-bound local effect receipts. Callers supply real human/external evidence.

This ledger holds no remote credentials and is not a security boundary against
its owner. An external executor must enforce authority and honor idempotency keys.
"""
import json
import uuid
from workflow import digest
from process_guard import workload


def schema(db):
    db.execute('''CREATE TABLE IF NOT EXISTS effects (
        id TEXT PRIMARY KEY, task_id TEXT NOT NULL, candidate TEXT NOT NULL,
        payload TEXT NOT NULL, state TEXT NOT NULL, authority TEXT, receipt TEXT)''')
    db.execute('''CREATE TABLE IF NOT EXISTS effect_events (
        effect_id TEXT NOT NULL, action TEXT NOT NULL, data TEXT NOT NULL, at TEXT NOT NULL)''')
    db.execute('''CREATE TABLE IF NOT EXISTS reconciliations (
        request_id TEXT PRIMARY KEY, outcome TEXT NOT NULL, evidence TEXT NOT NULL, at TEXT NOT NULL)''')


class Operations:
    def __init__(self, store):
        self.store, self.db = store, store.db

    def record(self, effect, action):
        self.db.execute('INSERT INTO effect_events VALUES (?, ?, ?, ?)',
                        (effect, action, json.dumps(self.get(effect)), self.store.timestamp()))

    def get(self, effect):
        row = self.db.execute('SELECT * FROM effects WHERE id=?', (effect,)).fetchone()
        if row is None:
            raise ValueError('Unknown effect receipt')
        return dict(row)

    def prepare(self, effect, task, payload):
        with self.store.lock(), workload(self.store.directory, self.db), self.db:
            w = self.store.workflow.get(task)
            if not w or w['phase'] != 'awaiting_approval':
                raise ValueError('Effects require the awaiting_approval checkpoint')
            candidate = self.store.workflow.candidate(w)
            if not w['review'] or w['review']['verdict'] != 'APPROVED' or w['review']['candidate'] != candidate:
                raise ValueError('Effect requires current independent review')
            if not isinstance(payload, dict) or any(not isinstance(payload.get(k), str) or not payload[k].strip() for k in ('operation', 'target')):
                raise ValueError('Effect payload requires operation and exact target')
            encoded = json.dumps(payload, sort_keys=True)
            old = self.db.execute('SELECT * FROM effects WHERE id=?', (effect,)).fetchone()
            if old:
                if (old['task_id'], old['candidate'], old['payload']) != (task, candidate, encoded):
                    raise ValueError('Effect ID conflicts with candidate, task or operation')
                return dict(old)
            self.db.execute('INSERT INTO effects VALUES (?, ?, ?, ?, ?, NULL, NULL)',
                            (effect, task, candidate, encoded, 'prepared'))
            self.record(effect, 'prepared')
            return self.get(effect)

    def approve(self, effect, evidence):
        with self.store.lock(), workload(self.store.directory, self.db), self.db:
            d = self.get(effect)
            if not evidence.strip():
                raise ValueError('Require a locator for the actual human operation authorization')
            w = self.store.workflow.get(d['task_id'])
            if not w or w['phase'] != 'awaiting_approval' or self.store.workflow.candidate(w) != d['candidate']:
                raise ValueError('Candidate or gate changed; approval is stale')
            if d['state'] == 'approved' and d['authority'] == evidence:
                return d
            if d['state'] != 'prepared':
                raise ValueError('Receipt cannot be approved in this state')
            self.db.execute("UPDATE effects SET state='approved', authority=? WHERE id=?", (evidence, effect))
            self.record(effect, 'approved')
            return self.get(effect)

    def claim(self, effect):
        with self.store.lock(), workload(self.store.directory, self.db), self.db:
            d = self.get(effect)
            if d['state'] != 'approved':
                raise ValueError('Effect was not approved or has already been claimed; reconcile it, never replay')
            w = self.store.workflow.get(d['task_id'])
            if not w or w['phase'] != 'awaiting_approval' or self.store.workflow.candidate(w) != d['candidate']:
                raise ValueError('Candidate changed before effect dispatch')
            # Commit uncertainty BEFORE handing control to an external caller.
            key = uuid.uuid4().hex
            self.db.execute("UPDATE effects SET state='uncertain', receipt=? WHERE id=?", (key, effect))
            self.record(effect, 'claimed')
            return self.get(effect)

    def settle(self, effect, outcome, external_receipt, evidence):
        with self.store.lock(), self.db:
            d = self.get(effect)
            record = json.dumps(dict(key=d['receipt'] if d['state'] == 'uncertain' else None,
                                     external_receipt=external_receipt, evidence=evidence), sort_keys=True)
            if d['state'] == outcome:
                old = json.loads(d['receipt'])
                if old['external_receipt'] == external_receipt and old['evidence'] == evidence:
                    return d
                raise ValueError('Conflicting external receipt')
            if d['state'] != 'uncertain' or not external_receipt.strip() or not evidence.strip():
                raise ValueError('Require an uncertain claim and observed external outcome evidence')
            self.db.execute('UPDATE effects SET state=?, receipt=? WHERE id=?', (outcome, record, effect))
            self.record(effect, 'settled')
            return self.get(effect)

    def reconcile(self, task, attempt, outcome, evidence):
        with self.store.lock(), workload(self.store.directory, self.db, legacy=attempt), self.db:
            self.store.recover()
            if not evidence.strip():
                raise ValueError('Require actual inspection evidence, not authorization inferred from a reason')
            row = self.db.execute('SELECT * FROM attempts WHERE request_id=? AND task_id=?', (attempt, task)).fetchone()
            if row is None or row['state'] != 'uncertain':
                raise ValueError('Only an uncertain attempt can be reconciled')
            old = self.db.execute('SELECT * FROM reconciliations WHERE request_id=?', (attempt,)).fetchone()
            if old:
                if (old['outcome'], old['evidence']) != (outcome, evidence):
                    raise ValueError('Conflicting reconciliation')
                return dict(old)
            latest = self.db.execute('SELECT request_id FROM attempts WHERE task_id=? ORDER BY rowid DESC LIMIT 1', (task,)).fetchone()[0]
            if latest != attempt:
                raise ValueError('Reconciliation cannot overwrite a newer attempt')
            w = self.store.workflow.get(task)
            if w and outcome == 'completed':
                self.store.workflow.validate(w)
                if w['phase'] == 'fixing':
                    source_hash = digest(self.store.workflow.files(w['config']['source']))
                    self.db.execute('UPDATE workflows SET source_hash=?, proof=NULL, review=NULL, sequence=sequence+1 WHERE task_id=?', (source_hash, task))
                self.store.workflow.record('reconcile:' + attempt, task, ['reconcile', attempt, outcome, evidence])
            self.db.execute('INSERT INTO reconciliations VALUES (?, ?, ?, ?)', (attempt, outcome, evidence, self.store.timestamp()))
            state = 'awaiting_verification' if outcome == 'completed' else 'failed'
            self.db.execute('UPDATE tasks SET state=? WHERE id=?', (state, task))
            return dict(self.db.execute('SELECT * FROM reconciliations WHERE request_id=?', (attempt,)).fetchone())
