# Local Codex CLI Concurrency & Lock Contention Review

## Scope

This evaluation tests atomic operations and SQLite lock contention handling under high concurrency in WAL mode:
1. **Race Condition Test:** 10 concurrent threads racing to claim 5 open tickets. Exactly 5 must succeed, 5 must fail with `ValueError`, and zero duplicate assignees or phantom audit records may exist.
2. **Lock Contention Test:** 20 concurrent threads executing rapid ticket creation, atomic claiming, and resolution bursts under WAL mode with zero `sqlite3.OperationalError: database is locked` exceptions.

## Evidence

| Case | Codex rollout | Real tests | Tests modified | Changed files |
| :--- | :--- | :--- | :--- | :--- |
| Baseline | Exit 0 | 2/2 passed (0.070s) | No | `helpdesk.py` |
| q-agent | Exit 0 | 2/2 passed (0.041s) | No | `helpdesk.py` |

## Implementation & Quality Gates

The `q-agent` run emitted RED/GREEN evidence in `odd/tasks/concurrency.md`:
- Applied conditional atomic `UPDATE tickets SET state = 'IN_PROGRESS', assignee = ? WHERE id = ? AND tenant_id = ? AND state = 'OPEN'`.
- Validated `claimed.rowcount == 1` before committing the audit event in the same transaction.
- Configured `sqlite3.connect(db_path, timeout=15.0)` to eliminate transient WAL lock contention.
- Isolated adversarial review passed: `APPROVED`. Real SQLite probe confirmed 20-worker race produced exactly 1 winner, 19 `ValueError` losers, and 1 audit event.
