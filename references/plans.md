# Mapeo de flujo-prompts-github por plan

All paths are relative to the root of this package (`q-agent-v01/`).

---

## Plan A — Greenfield (new system from scratch)

Execute in strict order:

| Step | Prompt file | Artifact produced | Branch |
|------|-------------|-------------------|--------|
| P2 | `prompts/P02_context_engineering.md` | `CONTEXT.md` | `develop` |
| P4 | `prompts/P04_propose.md` | `proposal.md` | `develop` |
| P5 | `prompts/P05_spec.md` | `spec.md` | `feature/<name>` |
| P6 | `prompts/P06_design.md` | `design.md` | `feature/<name>` |
| P7 | `prompts/P07_tasks.md` | `tasks.md` | `feature/<name>` |
| P8 | `prompts/P08_apply_verify.md` | verified implementation | `feature/<name>` |

> P1 MAB-PC does not apply in pure Plan A (no existing code to audit).
> P3 Architectural Evolution does not apply either.

**Mandatory gate:** after P4 `/propose` — show to the user and wait for approval.

---

## Plan B — Brownfield (feature / evolution)

Execute in order:

| Step | Prompt file | Artifact produced | Branch |
|------|-------------|-------------------|--------|
| P1 | `prompts/P01_auditoria_adacg.md` | `BLUEPRINT.md` + `CONSTITUTION.md` | `develop` |
| P2 | `prompts/P02_context_engineering.md` | `CONTEXT.md` | `develop` |
| P3 | `prompts/P03_evolucion_blueprint.md` | `EVOLUTION.md` | `develop` |
| P4 | `prompts/P04_propose.md` | `proposal.md` | `feature/<name>` |
| P5 | `prompts/P05_spec.md` | `spec.md` | `feature/<name>` |
| P6 | `prompts/P06_design.md` | `design.md` | `feature/<name>` |
| P7 | `prompts/P07_tasks.md` | `tasks.md` | `feature/<name>` |
| P8 | `prompts/P08_apply_verify.md` | verified implementation | `feature/<name>` |

**Mandatory gate:** after P4 `/propose`.

**Note P1:** MAB-PC analyzes the existing repo using tags:
- `[OBSERVED]` — exists and works
- `[INFERRED]` — inferred from code
- `[CONFLICT]` — detected inconsistency

**Note P3:** Architectural Evolution reconciles blueprint vs real code using tags:
- `[IMPLEMENTED]` — present in V1
- `[ABSENT-IN-V1]` — in the blueprint but not in code
- `[SIMPLIFIED-IN-V1]` — partially implemented

---

## Plan C — Audit (review and improve)

Execute in order:

| Step | Prompt file | Artifact produced | Branch |
|------|-------------|-------------------|--------|
| P1 | `prompts/P01_auditoria_adacg.md` | `BLUEPRINT.md` + `CONSTITUTION.md` | `audit/<date>` |
| CAB-RP | `prompts/P09_compliance_audit.md` | `AUDIT_REPORT.md` | `audit/<date>` |
| — | Recommendations | Issues per gap found | `fix/<name>` |

**No scope gate in Plan C.** The agent generates the full report and creates
remediation Issues, each labeled with severity.

**CAB-RP audit categories (execute in order):**
- Cat. 0: Base Architecture (Clean + Hexagonal, design patterns, TDD)
- Cat. 1: Telemetry and observability
- Cat. 2: Security (inputs, auth, secrets, dependencies)
- Cat. 3: Code quality and test coverage
- Cat. 4: Usability and interface (invoke UI/UX audit prompt if applicable)
- Cat. 5: Uncovered NFRs

Gaps in Cat. 0 → treated as P0 automatically, Issue with label `priority:critical`.

---

## Templates

| Template | File |
|----------|------|
| Architecture Decision Record | `templates/ADR-template.md` |
| Blueprint | `templates/BLUEPRINT.md` |
| Constitution | `templates/CONSTITUTION.md` |
| Propose scope | `templates/proposal.md` |

---

## Note on the executor

The flujo-prompts-github is tool-agnostic by design.
The executor (Codex / Antigravity / OpenCode / Pi) receives the generated
artifacts (spec.md, design.md, tasks.md) as input context.
There is no executor dependency in the flow prompts.
