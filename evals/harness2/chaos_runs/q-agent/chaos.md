# SQLite crash resilience
Scope: helpdesk.py; preserve public mutations and tests. Route: inline.

## Specs
- S1: Implement `verify_integrity(db_path: str | Path)` with integrity errors, foreign key status, counts, and ordered torn ticket IDs.
- S2: Preserve atomic create/claim transactions and configure WAL concurrent write waiting.
- S3: Do not modify tests. Run `python3 ci_check.py`.

## Tasks
- [ ] T1 (S1-S3): diagnostics and connection configuration; independent concurrency verification.

## Terminal Evidence Gate
- RED: `python3 ci_check.py` exit 1: ImportError importing missing verify_integrity (1 discovery error).

## Log
- Existing create_ticket and claim_ticket already wrap both statements in connection transaction contexts; preserve these.
- Integrity reads will use explicit BEGIN for one consistent snapshot. Connection timeout is bounded, not an unlimited lock guarantee.
- GREEN: python3 ci_check.py exit 0, all 3 crash/burst/WAL tests pass.
- Independent verifier APPROVED: FK/torn diagnostics, audit-failure rollback, lock waiting, 281 consistent snapshots during 250 writes, and exactly one winner among 10 claims.
- Configuration: WAL, busy_timeout=15000ms, synchronous=NORMAL, foreign_keys=ON.
- Native review unavailable: canonical STATUS failed before mutation on read-only filesystem during target freeze. No native approval claimed.
- Risk: item 4 (concurrent snapshots/lock waiting). Timeout is bounded, not an indefinite lock guarantee; NORMAL is not power-loss durability.
- Implementation and independent checks complete; native review proof unavailable. Tests unchanged. No commits or publishing.
- Verifier scratch retained at /tmp/chaos-verify-5PMyAd; cleanup command denied by runtime.
