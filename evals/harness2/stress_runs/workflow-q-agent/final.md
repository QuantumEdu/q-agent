Implemented both functions in `helpdesk.py`, preserving WAL and parameterized SQL.

- Required `python3 ci_check.py`: **3 tests passed**.
- Tests unchanged; independent review **APPROVED**.
- Evidence: `odd/tasks/stress-workspace.md`.
- Native review unavailable because `.git` is read-only.

Risk: items 2 and 4—tenant authorization and atomic state/audit writes.

## Key Learnings:
1. State changes and audit events roll back together.