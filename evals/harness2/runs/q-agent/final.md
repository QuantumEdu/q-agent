Implemented strict lifecycle validation and overdue lookup, preserving WAL mode and SLA durations.

- Tests unchanged: **3 passed**.
- Evidence: `odd/tasks/ticket-workflow-tests.txt`
- Log: `odd/tasks/ticket-workflow.md`
- Native review blocked by read-only `.git`; no commits or deployment.

Risk: none.

## Key Learnings:
1. Conditional SQL updates reject invalid transitions without changing persisted state.