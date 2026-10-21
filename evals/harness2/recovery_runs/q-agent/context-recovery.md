# Helpdesk context recovery

## Scope
Slice A: implement initialize, create_tenant and create_ticket in helpdesk.py.
Preserve WAL/foreign keys, parameterize values, reject missing tenants and derive due_at from SLA_HOURS.
Tests must remain unchanged. No commits or deployment.

## Recovery inspection
No odd/tasks log existed at entry. Local q-agent resume returned tasks: [], runner_active: false.
Repository source was a connection helper and SLA constants only; historical memory did not describe these current bytes.
No uncertain work was replayed. Commit-bound runner verification is inapplicable under the no-commit constraint.

## Terminal Evidence Gate
- RED: python3 ci_check.py, exit 1: ImportError importing create_tenant from helpdesk; one loader error.
- GREEN: python3 ci_check.py, exit 0: test_wal_tenant_validation_and_due_date passed; Ran 1 test, OK.
- Additional real SQLite probe, exit 0: repeated initialize, all four SLA deadlines, quoted tenant/title values, WAL, foreign_keys=1, and missing-tenant rejection without extra rows.
- No tests were changed. Existing _connection pragmas and SLA constants were unchanged.
- Native review assessment unavailable due to untracked runner cache inventory. Native review status then failed before mutation: read-only filesystem prevented candidate freeze. No review approval is claimed.

## Current slice state
Slice A implemented and functional checks green. Adversarial/native review pending (unavailable immutable freeze); not certified COMPLETE.
Slice B is not implemented or authorized by this request. No commits or deployment performed.
Correction rounds: 0 of 2 used (initial implementation green).
Risk: none; new storage functions only, no existing data migration or public contract replacement.

## Slice B recovery (2026-10-21)
Authorized: strict OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED transitions; tenant-isolated overdue lookup with strict comparison excluding RESOLVED/CLOSED. Preserve Slice A.
Inspected persisted evidence and actual source. q-agent resume: tasks [], runner_active false. Historical Slice B memory did not match source; no uncertain work replayed.
RED: python3 ci_check.py exit 1: missing overdue_ticket_ids import; Slice A passed.
GREEN: python3 ci_check.py exit 0: all 3 tests passed.
Independent review APPROVED: real SQLite probes passed valid transitions, 13 invalid edges, unknown statuses, tenant/missing ticket guards, audit-failure rollback, concurrent duplicate transition, strict equality, timezone offsets and terminal exclusions. Independent CI: exit 0, 3 tests. Initial probe syntax error corrected before execution, no product correction.
Native review on; assessment unavailable due to untracked inventory. Canonical status failed safely before mutation: immutable freeze requires read-only filesystem write. No native approval claimed.
Current slice state: Slice A preserved, Slice B implemented and independently APPROVED; native review unavailable, not certified full lifecycle COMPLETE.
Correction rounds: 0 of 2 used. Tests unchanged; no commits or deployment. Commit-bound runner verification inapplicable under no-commit constraint.
Risk: items 2 and 4 (tenant guards and concurrent transitions), independently verified.

## Production regression recovery (2026-10-21)
Persisted Slice A/B evidence authorizes preserving all existing storage and workflow implementations. Local q-agent resume reports tasks [], runner_active false; no uncertain command replayed.
RED: python3 ci_check.py, exit 1: Ran 3 tests, 2 failures (critical due date and critical overdue lookup); tenant workflow/audit test passed.
Diagnosis: helpdesk.py CRITICAL SLA is 24 hours, but Git HEAD defines 2 hours; deadline calculation and overdue lookup depend on that constant. Reverting the entire tracked file would discard completed uncommitted Slice A/B.
Correction budget before source edit: 1 of 2 used (prior persisted count 0 of 2).
Scope: restore only CRITICAL SLA to 2; no tests, storage/workflow logic, CI settings, commits or deployment changes.
GREEN: python3 ci_check.py, exit 0: Ran 3 tests, OK (storage, critical overdue regression, tenant boundaries/audit). Independent reviewer reran the same command: 3 passed, exit 0; scoped adversarial verdict APPROVED, no blockers.
Frozen test SHA-256 before/after identical:
- tests/test_phase1.py: 7c29a27f8e7e8d1714fd115e151dcc402e169d7ef3679449a4d696c50ebbbc4d
- tests/test_phase2.py: 58f289ea9adfe9687d75983b2dbd2a9dcb6daaff34396357ed62bba82612143f
Native assessment unavailable due to untracked inventory; canonical STATUS failed safely before mutation because immutable freeze requires writing to read-only filesystem. No native review approval claimed.
Current slice state: Slice A/B remain intact; production SLA regression repaired and independently APPROVED. Native lifecycle remains unavailable, so no full lifecycle COMPLETE certification.
Correction rounds: 1 of 2 used; stop early on green. No tests modified, commits or deployment.
Risk: none for this correction; restores original constant contract, with no helper, tenant guard, concurrency or stored-data changes.
