# Hosted unattended E2E repair

This is an instruction-driven P06 workflow executed by the current agent host.
It does not launch a model, add a CLI controller or enforce permissions in code.
Use it in `autonomous` mode when implementation, testing and bounded corrections
are already authorized. Follow [execution authority](execution-authority.md).
No extra question is needed for covered local repairs. Merge/deploy keep their
separate authority. Missing tools or credentials are not product failures.

Activation: set `runtime.interaction_mode` to `autonomous` in the project's
`.q-agent.json`, or ask the host: "Run P06 using references/unattended-e2e.md;
implement and test within the agreed scope, with at most two correction rounds."
Mode selection alone never authorizes previously unapproved edits or operations.

## Prepare once, before running

1. Record scope, acceptance criteria, allowed source paths, exact E2E command,
   regression command, working directory, environment and finite timeouts in the
   task log. For UI requirements include a real browser: HTTP tests alone cannot
   establish layout, timezone rendering or form behavior. Use synthetic data.
2. Confirm the host can run tests and edit source. Start only owned local services;
   verify readiness functionally and arrange cleanup even on failure. Prefer an
   isolated test database with no external side effects.
3. Freeze acceptance tests and thresholds: record their SHA-256 hashes plus the
   starting commit and diff. Add missing reproductions before correction when
   needed, but never delete/skip/weaken tests or change expected behavior to pass.
   Record new tests with their own hashes. A legitimate acceptance change needs
   separate user authority and a new task, not silent editing during this loop.
4. Set `corrections_used = 0`, `max_corrections = 2` and persist them in the log.
   Initial run is execution 0; corrections 1 and 2 permit executions 1 and 2.
   A correction may fix multiple related defects. Stop early on success.

## Execute, diagnose, repair, verify

- Run the exact E2E command with a finite timeout. Record command, cwd, actual exit
  status, collected/executed/skipped test counts, source commit/diff, test hashes,
  log and screenshots/traces where available. Zero tests, unexpected skips,
  timeout, interrupted execution or missing evidence never count as a pass.
- On failure inspect current logs and side effects. Identify failing acceptance
  criteria and classify product defect versus environment/uncertain outcome.
  Repair an understood, in-scope product defect using `skills/q-ci-fixer`.
- **Before each source-editing correction, increment and persist the counter.**
  Every repair round consumes budget, including unsuccessful fixes and review or
  regression findings. P06, q-ci-fixer and P07 share the SAME task budget; changing
  phase, restarting the host or renaming a command never resets it.
- Rerun the unchanged E2E command after the correction, plus affected regressions;
  preserve every failing run. Do not substitute a smaller passing suite for it.
  Inspect the diff and recheck frozen hashes after each round.
- If execution 2 still fails, emit `BLOCKED: correction_budget_exhausted` with
  remaining failures and stop editing. Do not make correction 3. Report earlier
  when the diagnosis requires an unresolved product decision, missing authority,
  unavailable prerequisites or uncertain external effects. Do not replay an
  interrupted operation blindly.
- When E2E passes, run the full agreed regression command, then dispatch
  `skills/q-adversarial-review` in an isolated reviewer context. Only an explicit
  `APPROVED` with no open R IDs permits completion. A rejection or regression
  consumes remaining correction budget before re-running tests AND review; if
  none remains, stop blocked. If independent review is unavailable, report blocked.
- Always clean up owned services. Write the final report even on a blocked run.

## Durable evidence and resumption

Keep one table in `q-tasks/<feature>.md` (or the active ODD task):

| Execution | Corrections used | Command / timeout | Source commit + diff | Test hashes | Exit / counts | Diagnosis / patch | Evidence |
|---|---|---|---|---|---|---|---|
| 0 | 0 | Exact command | Baseline | SHA-256 | Actual result | Observed failures | Log path |
| 1 | 1 | Same command | Patch 1 | Unchanged | Actual result | Diagnosis and delta | Log path |
| 2 | 2 | Same command | Patch 2 | Unchanged | Actual result | Final result | Log path |

Record only executed rows. Save diagnosis/counter BEFORE editing. On resumption
recover the counter from this same log and inspect the working tree/processes.
If the record is missing or contradictory, stop blocked instead of assuming zero.
With `q-agent task`, register once and use distinct request IDs per execution.
After failure inspect effects, then use `task retry --reason` referencing that
inspection and the existing human authorization before another `task run`.
A retry reason is evidence metadata, never a grant of permission. Commit before
`task verify` and preserve its commit-bound evidence; machine success is separate
from acceptance and review. See [local task recovery](local-task-recovery.md).

Final report: `COMPLETE` or `BLOCKED` with reason, host/backend used, commands and
counts per execution, defects found/fixed, corrections used out of 2, remaining
failures, independent verdict and evidence locations. State whether browser E2E
ran. This proves only the exercised scope and host, not arbitrary backend support.

## Repeatable repair drill

Copy `examples/unattended-e2e/` outside the checkout. It intentionally contains two
application defects and immutable acceptance tests. It is not a usable app.
Run from the copy with the host tool's 30-second timeout:

```sh
python3 -m unittest -v test_clinic
```

Expect three executed HTTP tests: one pass and two failures. Follow the workflow
as the repairing host, inspecting output and source; no scripted answer patches
or fake model callbacks are supplied. Preserve the test hash and log every run.
For an exhaustion drill use a fresh copy and explicitly set an authorized
`allowed source paths = []` constraint: fail the initial suite, report blocked
without edits or retries. To exercise budget exhaustion, record two real repair
rounds in a separate copy that still has a failing assertion; stop after execution
2. Do not call that case successful repair. See the release task evidence for
what was actually executed, including review and limits of the validation.
