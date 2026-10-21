Implemented `migrate_add_sla` in `migrate.py`: idempotent SLA backfill, row preservation, and atomic rollback with `ValueError` for unsupported priorities. Tests unchanged.

`python3 ci_check.py`: **2 tests passed, OK**, exit 0. Independent verification also passed.

Native review unavailable: `.git` is read-only.

Risk: item 1 (persisted schema/data migration).

## Key Learnings:
1. Explicit SQLite transactions roll back schema changes and data updates together.