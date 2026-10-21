Implemented `migrate_add_sla` with idempotent SLA backfill and atomic rollback on unsupported priorities.

- CI: **2 tests passed**; tests unchanged.
- Independent review: **APPROVED**.
- Evidence: `odd/tasks/stress-workspace.md`.
- Native review unavailable: `.git` is read-only.

Risk: item 1 — schema/data migration.

## Key Learnings:
1. Explicit SQLite transactions roll back schema changes and backfill together.