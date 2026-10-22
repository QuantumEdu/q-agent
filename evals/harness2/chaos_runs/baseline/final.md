Implemented integrity checks, snapshot-consistent diagnostics, and WAL contention settings. Preserved atomic create/claim transactions.

- CI: all 3 tests passed.
- Independent crash/concurrency verification passed.
- Evidence: `odd/tasks/chaos-recovery.md`.
- Tests unchanged; no commits or deployment.
- Native review unavailable due to read-only storage.

Risk: item 4 (concurrency).

## Key Learnings:
1. Explicit `BEGIN` keeps integrity queries within one consistent snapshot.