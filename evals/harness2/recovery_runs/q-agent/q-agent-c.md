Fixed the regression: restored CRITICAL SLA from 24 to 2 hours, preserving completed storage and workflow code.

- `python3 ci_check.py`: **3 tests passed**.
- Tests unchanged; no commits or deployment.
- RED/GREEN evidence recorded in `odd/tasks/context-recovery.md`.
- Independent review approved; native review remains unavailable on the read-only filesystem.

Risk: none.

## Key Learnings:
1. The CRITICAL SLA controls both ticket deadlines and overdue detection.