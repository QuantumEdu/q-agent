Implemented Slice B, preserving Slice A.

- Strict transitions with atomic audit events.
- Tenant-isolated overdue lookup using `due_at < now`, excluding RESOLVED/CLOSED.
- CI: all 3 tests passed; independent SQLite checks passed.
- Inspected and updated `VERIFICATION.md`.
- Tests unchanged; no commits or deployment.

Native review blocked by read-only filesystem.

Risk: items 1 and 4 — persisted transitions and concurrency.

## Key Learnings:
1. Atomic audit writes roll back failed transitions.