# Discriminating harness eval — design (pending)

Status: **pending**. Nothing in this document has been run.

## Why

The five local evaluators in `evals/harness2/` end with baseline and q-agent at the
same score (their own `REVIEW.md` files say so). The JobBench/LAB numbers in
`docs/validation/harness2-evaluation.md` compare a Harness² refined harness (`agg1`)
against Harness²'s own base harness, and their raw artifacts (`summary.json`,
`judged.json`, the base `harness.yaml`) are not committed in this repository or in
the Harness² fork (`/runs/` is git-ignored there). Neither result shows whether the
q-agent instructions change outcomes.

## Before running anything new

1. Commit the existing JobBench/LAB artifacts under `docs/validation/harness2-jobbench/`
   with the Harness² commit SHA, executor, model and the exact base harness used.
2. State explicitly whether the base harness contained q-agent's `SKILL.md`.

## Task sources (q-agent only, no external projects)

- **History replay**: pick q-agent commits that fixed a bug and added a regression test
  (e.g. merge-gate, audit validator, checklist fixes in `CHANGELOG.md`). Revert the fix,
  hide the regression test, give the agent the original issue text. Pass = hidden test
  green and visible tests untouched.
- **Spec-gap fixtures**: new fixtures under `evals/harness2/` whose visible tests are
  incomplete and whose hidden tests check invariants stated only in the spec
  (rejected commands leave the DB hash unchanged, exact error strings, boundary inputs).
  These target what q-agent claims to add: spec-derived probes (Fase A.5) and
  invariant checks.

## Protocol

- Arms: `baseline` (task text only) vs `q-agent` (task text + q-agent skill loaded).
- Same executor, model, seed list and budget per arm; k ≥ 3 rollouts per task per arm.
- Freeze visible and hidden tests by SHA-256; any change marks the rollout `tampered`.
- Hidden tests run only by the evaluator, never exposed to the agent.

## Metrics (predeclared)

| Metric | Definition |
|---|---|
| Hidden pass rate | Fraction of rollouts where all hidden tests pass |
| Tamper rate | Fraction of rollouts that modified frozen tests |
| Invariant violations | Hidden invariant tests failed per rollout |
| Review findings | Open `R-xx` findings from an isolated reviewer on the final diff |
| Cost | Tokens and wall time per rollout, when the executor reports them |

Decision rule: report per-task and aggregate results with all rollouts; a q-agent
advantage is claimed only if the hidden pass rate difference holds across tasks, not
from a single task.

## Requirements

A Codex (or other) executor with API access, and a token budget for
2 arms × tasks × k rollouts.
