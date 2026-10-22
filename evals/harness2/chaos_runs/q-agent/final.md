Implemented in `helpdesk.py`:
- Snapshot-consistent integrity, foreign-key, and torn-ticket diagnostics.
- 15-second lock timeout and WAL `synchronous=NORMAL`.
- Preserved atomic create/claim transactions.

All 3 CI tests pass; tests unchanged. Independent verification approved. Evidence: `odd/tasks/chaos.md`.

Native review blocked by read-only filesystem restrictions.

Risk: item 4 — concurrency.

## Key Learnings:
1. Explicit read transactions keep integrity diagnostics snapshot-consistent.