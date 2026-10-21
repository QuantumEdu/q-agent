Implemented strict transitions and overdue lookup, preserving WAL and SLA durations. Tests unchanged.

- Real suite: **3 tests passed**
- Evidence: `odd/tasks/ticket-workflow-tests.txt`
- Native review blocked by read-only `.git`

Risk: none.

## Key Learnings:
1. Conditional updates reject invalid transitions without changing persisted state.