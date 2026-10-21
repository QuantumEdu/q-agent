# Local Codex CLI Stress Evaluation Review

## Scope

This local prototype compares baseline instructions and q-agent instructions over two independent
SQLite helpdesk tasks. It is not an official Harness2 benchmark because the Codex CLI login is not
a Responses-compatible endpoint.

| Task | Baseline | q-agent | Immutable tests |
| --- | --- | --- | --- |
| Multi-tenant workflow: WAL, tenant isolation, RBAC, audit events, SLA | CI exit 0, 3/3 passed | CI exit 0, 3/3 passed | Unchanged |
| Legacy SLA migration: idempotency, data preservation, rollback | CI exit 0, 2/2 passed | CI exit 0, 2/2 passed | Unchanged |

## q-agent Quality Gates

The q-agent workflow case emitted RED/GREEN ODD evidence and used a second correction round after
an independent reviewer found unsafe comparison of timezone-aware and naive datetimes. The
corrected implementation passed:

- `python3 ci_check.py` (3/3);
- a direct SQLite probe with an aware `opened_at` and a naive `now`;
- `git diff --check`;
- final isolated adversarial review: `APPROVED`.

The migration q-agent diff passed its CI (2/2), `git diff --check`, and isolated adversarial
review on the first pass: `APPROVED`.

## Interpretation

q-agent completed both complex tasks and successfully incorporated a reviewer-discovered defect
within its bounded correction budget. The baseline also completed both tasks. Therefore this
experiment demonstrates q-agent workflow correctness and repair behavior, not a measured
performance advantage. A formal comparison needs a Responses-compatible Harness2 setup and a
fixed, larger task corpus with predeclared aggregate metrics.
