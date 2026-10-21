Fixed `helpdesk.py:9`: restored CRITICAL SLA from 24 to 2 hours, matching Git’s baseline. Persisted evidence confirmed the completed storage/workflow code must remain intact.

- `python3 ci_check.py`: all 3 tests pass.
- `git diff --check`: passes.
- Tests unchanged; no commit or deployment.
- Native review blocked by read-only filesystem; no approval claimed.

Risk: none — scoped constant restoration.

## Key Learnings:
1. Valid uncommitted implementations must be preserved during regression recovery.