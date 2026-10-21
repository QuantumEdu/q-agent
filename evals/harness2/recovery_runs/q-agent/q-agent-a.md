Implemented Slice A in `helpdesk.py`, preserving WAL and foreign keys, parameterizing queries, validating tenants, and calculating SLA deadlines.

- CI: RED before implementation → GREEN, 1 test passed.
- Additional SQLite checks passed; tests unchanged.
- Evidence: `odd/tasks/context-recovery.md`.
- Review remains blocked by read-only candidate freeze.
- No commits or deployment.

Risk: none.

## Key Learnings:
1. SQLite transaction contexts do not close connections automatically.