Implemented both functions in `helpdesk.py`. Tests unchanged; WAL preserved.

`python3 ci_check.py`: **3 tests passed, OK, exit code 0**. Independent verification also passed, including rejection atomicity and audit rollback.

Native review blocked by read-only `.git`.

Risk: items 1–2 (persisted state and tenant/role authorization).

## Key Learnings:
1. State changes and audit events roll back together on failure.