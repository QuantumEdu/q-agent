# Local Codex CLI Chaos Engineering & Crash Recovery Review

## Scope

This evaluation tests catastrophic failure modes, atomic transaction boundaries, and SQLite WAL recovery mechanisms under ungraceful termination:
1. **Catastrophic SIGKILL Crash Test (`test_sigkill_crash_during_multi_statement_transaction`):** A high-throughput writer worker is abruptly terminated with hard `SIGKILL` (`kill -9`) mid-transaction. Verifies that SQLite WAL cleanly rolls back incomplete transactions, `PRAGMA integrity_check` returns `['ok']`, `PRAGMA foreign_key_check` finds zero violations, and zero orphaned or torn tickets exist.
2. **Post-Crash Concurrent Burst Resilience (`test_post_crash_write_burst_resilience`):** Immediately following a hard crash, 20 concurrent worker threads execute ticket creation and claiming bursts. Verifies that stale locks are reclaimed cleanly and all workers succeed without raising `sqlite3.OperationalError: database is locked`.
3. **Torn WAL Trailing Frame Recovery (`test_torn_wal_trailing_frame_checksum_recovery`):** Simulates unbuffered power outage during sector write by injecting 128 bytes of corrupt garbage (`0xDEADBEEF`) into `.db-wal`. Verifies SQLite frame checksum detection, automatic frame truncation to the last consistent commit, and successful resumption of write transactions.

## Evidence

| Case | Codex rollout | Real tests | Tests modified | Changed files |
| :--- | :--- | :--- | :--- | :--- |
| Baseline | Exit 0 | 3/3 passed (0.106s) | No | `helpdesk.py` |
| q-agent | Exit 0 | 3/3 passed (0.109s) | No | `helpdesk.py` |

## Implementation & Quality Gates

The `q-agent` run emitted RED/GREEN evidence in `odd/tasks/chaos.md`:
- **RED Stage:** Probed CI gate; failed with `ImportError: cannot import name 'verify_integrity' from 'helpdesk'`.
- **Snapshot Integrity Diagnostics:** Implemented `verify_integrity(db_path)` using an explicit `BEGIN` transaction to guarantee a single read-isolated point-in-time snapshot of `PRAGMA integrity_check`, `PRAGMA foreign_key_check`, total ticket/event counts, and orphan ticket detection.
- **Connection Hygiene:** Configured `_connection` with `PRAGMA journal_mode = WAL`, `PRAGMA foreign_keys = ON`, `PRAGMA busy_timeout = 10000`, `timeout = 15.0`, and `PRAGMA synchronous = NORMAL`.
- **Adversarial & Concurrency Checks:** Independent verifier validated 281 consistent snapshots across 250 writes, zero torn tickets across forced audit rollbacks and hard kills, and single-winner claiming race guarantees.
