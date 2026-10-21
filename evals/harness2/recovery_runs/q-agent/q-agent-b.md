Implemented Slice B, preserving Slice A.

- Strict transitions with atomic audit events.
- Tenant-isolated overdue lookup with strict deadline comparison and RESOLVED/CLOSED exclusion.
- `python3 ci_check.py`: all 3 tests passed.
- Evidence recorded in `odd/tasks/context-recovery.md`.
- Tests unchanged; no commits or deployment.

Independent review approved. Native review remains blocked by the read-only filesystem.

Risk: items 2 and 4—tenant guards and concurrency, independently verified.

## Key Learnings:
1. Audit insertion failures roll back ticket transitions.
2. UTC normalization preserves strict deadline comparisons.