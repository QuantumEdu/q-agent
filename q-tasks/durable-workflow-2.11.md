# Durable workflow controller

- Release: 2.11.0. Execution: standalone Python/SQLite, no Pi SDK.
- Human scope: implement the durability/state improvements from the code review.
- Status: VERIFIED; independent review APPROVED, no open R IDs.

## Acceptance and implementation

- UAC-01: A child cannot execute before its identity is committed. Supervisor loss
  must not permit conflicting dispatch while a cooperative child/descendant lives.
- UAC-02: Persist workflow phase separately from execution state; compare sequence
  numbers, freeze tests/config and reject incompatible controller/definition state.
- UAC-03: Consume correction budget transactionally before dispatch; survive
  SIGKILL and duplicate request IDs; refuse correction three at the default limit.
- UAC-04: Bind verification/review/effect receipts to a committed candidate, retain
  approval evidence, and reconcile claimed effects without a second claim.
- UAC-05: Preserve phase/event history and support private SQLite snapshots with
  integrity/version/project checks; refuse to overwrite history on restoration.

## Architecture

`process_guard.py`: inherited lease, launch gate and Linux subreaper supervision/completion
receipts, never signals persisted PIDs. `workflow.py`: versioned phase/checkpoint and
budget transactions. `operations.py`: local reconciliation and effect receipts.
`snapshots.py`: SQLite backup/empty-ledger restoration. `q_tasks.py`: CLI and command
integration. Existing runner tests remain unchanged; new tests use real Git,
SQLite, processes, SIGKILL and actual unittest commands.

The first regression reproduced the old overlap: retry succeeded with a surviving
child. The new behavior blocks it. The suite also exercises detached descendants,
PID-write failure before launch, crash during repair, frozen-test drift, stale
candidate approvals, lost claim responses, failed reverification, legacy receipt
migration and invalid snapshot/version rejection.

## Trust and limits

The host supplies reasoning and commands. Registration makes the runner enforce
phase/budget contracts on its dispatches; direct edits outside it are not metered.
Local review/approval fields are evidence records, not cryptographic identities.
The effect ledger runs no production operation and holds no remote credentials;
external authority enforcement stays with a trusted executor. There is no native
conversation recovery or kernel containment. Linux checks cover cooperative
workloads; hostile workloads require external containment.

The user previously authorized direct pushes to main. Changes remain on a feature
branch until verification/review. No production deployment is authorized here.

## Terminal evidence gate

| Check | Exit | Observed outcome |
|---|---|---|
| Full suite, Python 3.10.21 | 0 | 139 tests passed |
| Full suite, Python 3.11.16 | 0 | 139 tests passed |
| Full suite, Python 3.12.14 | 0 | 139 tests passed |
| Original runner suite | 0 | 13 tests, including SIGTERM/SIGINT |
| Independent durability suite | 0 | 17 tests passed |
| Compilation, shell syntax, package JSON, CLI and benchmark smoke | 0 | Passed |

The three complete suites ran concurrently. Initial matrix failures exposed
cross-process environment-inspection interference; replaced that approach with
subreaper supervision. A kernel without `/proc/.../children` exposed a shutdown
failure; ownership enumeration now uses current parent IDs, with SIGCHLD reset so
owned PIDs remain reserved until reaped. Original signal regressions then passed.
Review R-01/R-02 are FIXED; no blockers remain. Raw log hashes and the controller
fingerprint are in [release evidence](../docs/validation/durable-workflow-2.11.json).
Remote GitHub CI is separate from these local checks.
