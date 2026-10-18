# Hosted unattended E2E workflow fix

- Release: 2.9.2, 2026-10-18. Status: verified; independent review APPROVED (round 2).
- Scope: close the existing instruction workflow; no new model controller.
- UAC-01: P06 invokes bounded E2E repair and shares two corrections with review/P07.
- UAC-02: Freeze tests, preserve evidence and stop on exhausted/uncertain outcomes.
- UAC-03: Demonstrate real HTTP/SQLite recovery and budget exhaustion using the host.
- UAC-04: Require regression success and independent APPROVED review for completion.

## Evidence

The current human request authorizes this implementation and hosted validation.
The Codex API host diagnosed and edited the disposable app copies; q-agent's
existing task runner executed each command, enforced its 30-second timeout and
stored actual command exits. No user intervention occurred between the attempts.

| Task | Execution 0 | Execution 1 | Execution 2 | Outcome before review |
|---|---|---|---|---|
| Recovery | 3 tests, 2 failures | 3 tests, 1 failure | 3 tests, zero failures | Machine green |
| Negative exhaustion | 3 tests, 2 failures | 3 tests, 1 failure | 3 tests, 1 failure | BLOCKED: correction_budget_exhausted |

All failing commands exited 1; the green command exited 0. Each repair counter
was recorded before editing. Frozen tests match their starting Git content.
The negative case intentionally used inadequate composite uniqueness for its
second repair; it tests the stop branch, not spontaneous model reasoning failure.
No third correction or retry was made in that task. Preliminary exploratory
runs are separate from these bounded drills and are not counted as their evidence.

Raw command logs, host records, SHA-256 and final application patches are in
[the committed evidence](../docs/validation/unattended-e2e-2.9.2.json).
The fixture acceptance suite is also its complete regression suite. These drills
cover HTTP only, not browser layout or general external backend compatibility.
The host follows the stop rule; the task runner itself does not enforce a
two-correction policy or autonomously diagnose/edit code.

Repository verification: `python3 -m unittest discover -s tests -v` exited 0
with 103 tests on Python 3.10.21, 3.11.16 and 3.12.14 (separate Q_COCKPIT_HOME).
Compilation, package JSON, shell syntax, local capabilities and benchmark also
exited 0. GitHub-hosted CI is not included in these local results.

R-01 (P07 mutating formatter bypass) was fixed and independently re-reviewed.
No open R IDs. The repaired app was committed as 809967d and supplemental
commit-bound verification exited 0 (3 tests); its task is verified. That final
verification is separate from the three repair-loop executions and made no edits.
