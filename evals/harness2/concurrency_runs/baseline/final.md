Implemented atomic `claim_ticket` and a 15-second SQLite lock timeout.

- CI: both tests passed.
- Independent checks confirmed single-winner races, rejection guards, and audit rollback.
- Evidence: `odd/tasks/atomic-ticket-claiming.md`.
- Tests unchanged; no commit or deployment.
- Native review blocked by read-only filesystem.

Risk: items 2, 3, 4 — access guards, shared timeout, concurrency.

## Key Learnings:
1. Conditional updates and transactional audits prevent duplicate claims and orphan events.