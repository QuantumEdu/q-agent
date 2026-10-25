# Durable workflow controller (2.11)

The host still diagnoses and edits; no model engine or Pi SDK is embedded.
The optional controller records phase checkpoints in the existing SQLite WAL
ledger. Legacy `task run`/`verify` remain available. Register autonomous E2E tasks
so every dispatched repair consumes a durable budget BEFORE the child starts.
Direct edits outside this runner are not metered or sandboxed by this controller.

## Guarantees and boundaries

- Workflow phase is separate from command state. A lost runner yields `uncertain`,
  not success. `resume` returns checkpoints and dispatch-blocking reasons without
  replaying commands. Restart the host and inspect this state to continue.
- Linux uses a pre-execution pipe gate: persist boot/session/start identity before
  releasing the command. A live subreaper supervisor adopts detached descendants,
  holds an inherited exclusion lease and waits for the whole owned tree. It fsyncs
  a completion receipt after reaping every child. No foreign process environments
  are inspected and no persisted PID is signalled. If the supervisor itself is
  lost and its completion cannot be proved, dispatch blocks until explicit
  inspection/reconciliation. This is process supervision, not a hostile-workload
  sandbox; `process_containment` remains unsupported.
- New durable workflow registration requires Linux `/proc`. Legacy POSIX commands
  retain a descriptor lease and conservative uncertainty handling, without a claim
  of verified macOS orphan exclusion. Windows-native execution is unsupported.
- Sequence checks reject stale transitions. Configuration/definition and controller
  fingerprints detect incompatible resumes. Backend/model names are host-declared,
  not provider availability checks. Changing code/config requires explicit migration
  or an authorized replacement task; do not rename tasks to reset budgets.
- Default maximum is two corrections (explicit initial maximum 1..3). Every command
  in `fixing` consumes one round, even if it fails or the host crashes. Duplicate
  request IDs return their original result without dispatch or another increment.
- Baseline tests cannot change in reproduction, but new tests may be added there.
  Advancing to `fixing` freezes the whole declared test surface. Hash drift blocks
  progress. Reproduction must fail; the host must still diagnose genuine RED rather
  than treating a setup/syntax failure as a product defect.
- Verification requires a clean committed checkout, unchanged declared source/tests
  and the correct phase. Generic commands are checked by exit status and hashes;
  adapters/hosts must reject zero-test runs, skips and invalid test setup. Only current verification plus a recorded independent
  APPROVED review permits completion. Review evidence is a local attestation;
  strings cannot prove reviewer identity or create human authorization.

## Register and run

Runtime files belong in ignored `.cache/`. Register after project bootstrap,
with existing acceptance tests. Source and test surfaces must be disjoint;
symlinks and paths outside the project are rejected. Example:

```sh
q-agent task add TASK-01 "Appointment E2E"
q-agent task workflow start TASK-01 --request-id start-01 \
  --source src --tests tests --definition appointments-v1 \
  --max-corrections 2 --backend codex --model YOUR_VERIFIED_MODEL
q-agent task run TASK-01 --request-id red-01 --timeout 120 -- python3 -m unittest discover -s tests
q-agent task workflow show TASK-01
```

Always take the current `sequence` from `workflow show`; `N` below is a placeholder.
After diagnosing RED:

```sh
q-agent task workflow advance TASK-01 --request-id phase-fix-01 \
  --sequence N --phase fixing --evidence "Inspected red-01; reproduction confirmed"
q-agent task run TASK-01 --request-id fix-01 --timeout 300 -- YOUR_REPAIR_COMMAND
q-agent task workflow show TASK-01
q-agent task workflow advance TASK-01 --request-id phase-verify-01 \
  --sequence N --phase verifying --evidence "Inspected fix-01 diff"
```

Commit the candidate, then `task verify ... -- YOUR_FULL_TEST_COMMAND`. Advance to
`review` with the fresh sequence and evidence; dispatch the independent reviewer.
Record its actual outcome:

```sh
q-agent task workflow review TASK-01 --request-id review-01 --sequence N \
  --verdict APPROVED --reviewer ACTUAL_REVIEWER_ID --evidence ACTUAL_REPORT_LOCATOR
```

Read the sequence again, then advance to `complete`, or `awaiting_approval` when an
external operation is needed. A verification/review failure can return to `fixing`
only while budget remains. Rejected evidence or an exhausted budget never resets
that budget. Move to `blocked` to explicitly close a blocked workflow. Formatting
repairs share this budget; a later candidate change invalidates verification/review.
Never enter FIXING for read-only inspection: every run in it is a correction round.

## Crashes and command reconciliation

`task history TASK-01` retains attempts, checkpoint events, effect events and
reconciliations. Inspect processes and effects before continuing. The runner never
kills a saved PID to make recovery pass. A live orphan blocks all dispatch in that
project, including another task. Stop owned work through its actual supervisor or
wait for it, then record the observed outcome:

```sh
q-agent task reconcile TASK-01 --attempt fix-01 --outcome no_effect \
  --evidence "Actual inspection locator: processes exited, inspected diff/target"
q-agent task retry TASK-01 --reason "Inspected reconciliation; retry within existing authority"
```

Outcomes are `completed`, `failed`, `no_effect`. A completed managed repair
atomically updates its source checkpoint without refunding budget; fresh
verification and review remain mandatory. Reconciliation preserves the
original uncertain attempt and never grants verified status. Legacy receipts
without a reliable process identity require explicit reconciliation; a live
ambiguous PID blocks it. The default replay policy is `inspect`. Only an adapter
whose operation is genuinely repeatable should declare `--replay-policy repeatable`;
this skips the reconciliation requirement for explicit retry, not process exclusion
or authority checks. Neither policy automatically replays a command, and declaring
one does not turn arbitrary shell code into a safe operation.

## External effects and approvals

The local ledger has NO remote credentials and executes NO deployment or merge.
A trusted external executor must verify the actual human authorization, destination,
commit and allowed operation and honor the supplied idempotency key. The owner of
this writable ledger can forge its records; this is not an external approval
security boundary. Production approval enforcement remains a separate integration.

In `awaiting_approval`, prepare a JSON payload with nonempty `operation` and exact
`target` fields and any immutable parameters:

```sh
q-agent task effect prepare RELEASE-01 --task TASK-01 --payload .cache/release.json
q-agent task effect approve RELEASE-01 --evidence ACTUAL_HUMAN_AUTHORIZATION_LOCATOR
q-agent task effect claim RELEASE-01
```

`claim` succeeds once, committing `uncertain` BEFORE returning its idempotency key.
If the response is lost, inspect `effect show RELEASE-01`; do not claim or execute
again blindly. Query the real destination using that key, then settle the observed
outcome with `effect settle RELEASE-01 --outcome completed --external-receipt ID
--evidence LOCATOR`. Stale candidates cannot be approved/claimed; outstanding or
failed effects prevent workflow completion. Settling records observations even if
source later changed; it cannot authorize another operation.

## Versioning, backup and restoration

Schema version 1 upgrades old ledgers additively and preserves attempt fields.
Future schema/workflow versions fail closed. New controller fingerprints reject
incompatible execution; there is no automatic migration of a running workflow.

```sh
q-agent task backup /path/to/new-private-snapshot.sqlite3
q-agent task restore /path/to/private-snapshot.sqlite3
```

Backup uses SQLite's backup API, integrity checking, private permissions and fsync.
It refuses to overwrite a destination. Restore requires an EMPTY ledger at the
same project path and validates integrity/versions first; existing history is never
replaced. Restore does not run tasks. Follow with `resume` and reconciliation.
Snapshots include checkpoints, approvals and receipts, not source, logs, review
artifacts or remote state. Credential-store files are not copied, but recorded
commands/evidence can contain sensitive text; keep snapshots private. Back these up separately and keep an
independent disk copy; WAL alone cannot recover a lost disk. Relocation or a new
workflow definition requires an explicit migration, not silently rewriting paths.
