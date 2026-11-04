# Traceable communication and lifecycle

Normative guide for q-agent-owned instructions. Use the [communication contract](../references/communication-contract.md)
for field definitions and this crosswalk for the current flow. Step N is not a PN filename:
the same numbered legacy prompt may serve a different semantic phase.

## Canonical crosswalk

Paths are package-relative. Stages 0–2 use the root skill as their entry point;
supporting prompts are named explicitly, not inferred from stage numbers.

| Stage | Semantic phase | Current primary prompt / entry | Inputs | Outputs | Advance condition |
| --- | --- | --- | --- | --- | --- |
| 0 | Plan selection | `SKILL.md` — Paso 0 | Request and existing mandate | A/B/F/C plan | Plan resolved; ask only if missing |
| 1 | Context | `prompts/P02_context_engineering.md` | Plan, problem, constraints | Bounded context | Required context known |
| 2 | Elicitation and deliberation | `SKILL.md` — Paso 2 | Context and unresolved tradeoffs | Decisions and acceptance intent | Product choices resolved or explicitly delegated |
| 3 | Engine and constitution gate | `prompts/P03_gate_metaorquestacion.md` | Local tool evidence, constitution | Recorded engine, log path, gate evidence | Constitution valid and required authority present |
| 4 | Living log | `prompts/P04_odd_feature_log.md` | Authorized scope and acceptance intent | One living log with tasks and UAC | Scope/acceptance settled; missing decision answered |
| 5 | Implementation | `prompts/P05_vertical_slice_apply.md` | Living log and allowed files | Slice and tests | Implementation ready for verification; no completion claim |
| 6 | Verification | `prompts/P06_terminal_evidence_gate.md` | Slice, tests and acceptance | Terminal evidence and independent review | Observed passing checks and APPROVED review |
| 7 | Hygiene and delivery | `prompts/P07_hygiene_and_blueprint.md` | Verified tasks and remaining limitations | Updated blueprint, log, concise delivery | Checked facts delivered; unresolved limits explicit |
| 8 | Deployment authorization | `prompts/P08_deploy_gate.md` | Verification, delivery and blast radius | REVIEW.md and human decision | Explicit human deployment authority; never implied by mode |
| 9 | Operations to ODD | `prompts/P10_ops_to_odd.md` | Actual incident evidence | Reproduction and bounded correction log | RED observed before fix; return through verification |

Brownfield discovery and Plan C retain `prompts/P01_auditoria_mab_pc.md`;
explicit architectural evolution retains `prompts/P03_evolucion_blueprint.md`.
`prompts/P09_compliance_audit.md` is a release/Plan C audit, not stage 9 operations.
Stages describe meaning, not an obligation to run every prompt for every plan.

## Artifact authority and compatibility

The active living log (`odd/tasks/<feature>.md` or `q-tasks/<feature>.md`) owns
scope, task state, acceptance and decisions. BLUEPRINT.md, audit, verification and
delivery reports link evidence back to it; they do not create competing task states.

Keep all legacy filenames. Only use these separate-artifact variants when explicitly
invoked; their compatibility headers identify the active log and scope authority:

| Variant | Meaning in the canonical flow | Artifact handling |
| --- | --- | --- |
| `prompts/P04_propose.md` | Scope elaboration at stage 4 | OpenSpec proposal linked from living log |
| `prompts/P05_spec.md` | Acceptance elaboration at stage 4 | OpenSpec specs linked, not stage 5 execution |
| `prompts/P06_design.md` | Design before stage 5 | OpenSpec design, not stage 6 verification |
| `prompts/P07_tasks.md` | Task planning at stage 4 | OpenSpec task detail linked; active state stays in log |
| `prompts/P08_apply_verify.md` | Execution and verification at stages 5–6 | OpenSpec verification evidence, not deployment authority |
| A-L in `references/plans.md` | Explicit large-project detail | Log identifies intent.md/spec.md as scoped detail; acceptance changes reconcile in log |

Do not rename, remove or silently migrate legacy artifacts. Preserve CONSTITUTION.md
and [execution authority](../references/execution-authority.md); this guide changes
communication, not independent authorization, merge, remote-write or deploy gates.

## When to speak

Record routine gate evaluation and log creation even when chat stays silent. Speak
only for `actionable_result`, `blocking_decision`, `hard_stop`, or a user's explicit
status request. P03/P04 announce scope/engine only when useful to a decision or
requested review. Reuse existing approvals: one focused unresolved question, then
STOP. Interactive mode may explain on request; autonomous mode grants no authority.
P07 always delivers concise checked facts, evidence links and outstanding limitations.
Never substitute a successful linter for acceptance, independent review or deploy consent.

## Who is speaking, and when

New LLM messages owned by q-agent use the compact prefix:
`[HH:mm:ss ±HH:mm] [emitter | workflow | phase] message`.
Use a real host/tool clock or supplied event timestamp with timezone; retain full
date and available correlation in the record. If not available, visibly write
`[time-unavailable] [llm | q-agent | unknown]` instead of inventing a clock value.
Missing execution time is never replaced with receipt time or the current time.

The emitter of model narration is `llm`, even when workflow is `q-agent`. Separately
record known executor, host and orchestrator; unknown values stay unknown/null.
Instructions being loaded do not prove a CLI was invoked, executed or verified.
Tool invocation and results establish only the lifecycle they actually evidence.
A prose prefix is not native tool proof, authenticated identity or consent.
Do not rewrite provider-owned consent menus, host notices or blocking envelopes.
q-agent cannot intercept all host outputs or attribute arbitrary external messages.

## Honest evidence and telemetry

Keep observed commands, test results, exit codes, status and time. Tokens/cost are
optional without provider instrumentation, including enterprise evaluation. Each
metric carries status/value/source/basis: `measured` needs an actual source;
`estimated` also needs explicit assumptions; `unavailable` has value `null`.
Unknown is neither zero nor free. Totals cannot silently omit unknown portions.
Do not infer billing from local command type, success, skill loading or silence.
Use existing log/event writers and stores; no competing ledger is required.
