Implemented Slice A in `helpdesk.py`.

- Preserved WAL and foreign keys.
- Added parameterized inserts, tenant validation, and SLA deadlines.
- `python3 ci_check.py` passed; additional SQLite probes passed.
- Evidence: `VERIFICATION.md`.
- Tests unchanged; no commits or deployment.

Native review was unavailable because `.git` is read-only.

Risk: none.

## Key Learnings:
1. SQLite connection contexts manage transactions but require explicit closure.