# Atomic ticket claiming
Scope: helpdesk.py only; tests remain unchanged. No commit or deployment.
Runner: `python3 ci_check.py`.

## Acceptance criteria
- Support may atomically claim an OPEN tenant-owned ticket and set its assignee.
- Exactly one concurrent claimant succeeds; all losers raise ValueError.
- The OPEN → IN_PROGRESS audit event commits with the update or both roll back.
- WAL connections wait up to 15 seconds for transient write contention.
- Existing storage and workflow functions remain available.

## Tasks
- Implementation and CI: verified; independent review pending.

## Terminal Evidence Gate
| Phase | Command | Observed result |
| --- | --- | --- |
| RED | `python3 ci_check.py` | Exit 1; ImportError: cannot import name 'claim_ticket'. |
| GREEN | `python3 ci_check.py` | Exit 0; both race and 20-thread burst tests passed (2 tests, 0.041s). |

## Implementation
One conditional UPDATE includes ticket ID, tenant ID and OPEN state. Its rowcount must equal one before inserting the audit record in the same SQLite transaction. Support authorization is checked before opening the connection. `_connection` retains WAL and foreign keys, with `timeout=15.0`.

## Verification notes
Native assessment currently unavailable: untracked inventory requires explicit selection. Independent concurrency and adversarial verification pending.

Risk: item 4 (concurrent claiming), item 2 (tenant and role guards), item 3 (shared connection timeout).

## Independent verification
APPROVED by isolated adversarial verifier; all five axes passed. Real SQLite probes confirmed invalid role/tenant/missing/non-OPEN rejection without mutation; forced audit failure rolled back state, assignee and events. A simultaneous 20-worker race produced one winner, 19 ValueError losers and one audit event. WAL and busy_timeout=15000 verified.
Native review unavailable: STATUS failed before mutation because target freeze encountered a read-only filesystem. No native approval claimed.
Parent spot check: CI passed both tests again; diff whitespace check passed.
Scratch retained: /tmp/claim-independent-5i60be82 (cleanup command denied).
