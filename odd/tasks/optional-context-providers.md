# Optional context providers

## Objective and scope
Make q-agent usable without external memory products; define selective optional retrieval and local-first closure. Files: references/context-retrieval.md, templates/q-agent.json, tools/q-checklist/q_checklist.py, skills/q-gbrain-assistant/SKILL.md, SKILL.md, skills/q-session-wrap/SKILL.md, README.md, tests/test_context_retrieval.py.

## Constraints
Instruction-driven contract/configuration only; no remote integrations, credentials probing, installs, push, PR or merge. Preserve legacy integration flags but explicit disabled provider wins. Generated additions English. One coherent rollback boundary: optional retrieval contract/configuration and associated guidance/tests.

## Execution
- Route: delegated direct; trigger: multiple non-trivial files and preparation reads.
- Strict TDD: true; source: user AGENTS.md instructions.
- Runner: C:/Users/iQuantum/AppData/Local/Programs/Python/Python312/python.exe -m unittest discover -s tests -v
- Delivery: ask-on-risk; user-selected chain: feature-branch-chain. Slice 1: 4afc35a + 72d9391 (339 authored lines). Slice 2: T2 follow-up, forecast 320-410 plus tracking; approximately 400 is advisory, no code golf. PR creation remains unauthorized.
- RDD: off/unmanaged; no user opt-in.
- Runtime harness: N/A; repository supplies agent instructions/configuration, not a provider runtime.
- Mirror: odd/optional-context-providers/tasks in runtime-detected project teng; repository locator D:/02-A/code/q-agent/q-agent-v02/odd/tasks/optional-context-providers.md. Target project binding unavailable; mapping disclosed.

## Tasks and acceptance
- [x] T1: Define optional retrieval configuration shared by template/generated config, document need/project/provider/budget gating and local-first persistence, correct GBrain integration claims; verify zero-provider baseline and defaults through generated-output tests.

## Verification and progress
RED: focused unittest runner observed 3 errors (missing context_retrieval/configuration contract), exit 1.
GREEN: focused runner 3/3 passed; full runner 37/37 passed; git diff --check passed. Refactor: shared template defaults and remaining GBrain label corrected; focused checks repeated successfully.
Structural readback: changed config/generator, instructions and new contract reviewed. Tests verify configuration and documentation contracts, not live integrations or runtime enforcement.
Authored count before commit: 336 additions plus deletions including tracking (below 400). RDD disabled/unmanaged; independent parent verification pending.
Work-unit commit: 4afc35a58a3faf2509bc70b6f1ad2c5cf20310eb -- feat(context): make retrieval providers optional and scoped.
Next step: parent independent verification; no push/PR/merge.

## Accepted follow-up
User authorized execution-authority and retrieval corrections and selected feature-branch-chain.
- [x] T2: Define human-scoped execution authority and typed provider activation; distinguish public research, general references and private memory; reconcile onboarding/deliberation/P03 with prior answers and scoped delegated decisions.
Route delegated direct: preparation reads and multiple non-trivial files. Strict TDD remains enabled with the same runner. Rollback: T2 authority/configuration and its entrypoint guidance/tests independently from T1.
Scope: references/context-retrieval.md, references/execution-authority.md, templates/q-agent.json, tools/q-checklist/q_checklist.py if config parity requires, SKILL.md, references/plans.md, skills/q-deliberate/SKILL.md, prompts/P03_gate_metaorquestacion.md, skills/q-gbrain-assistant/SKILL.md, README.md, tests/test_context_retrieval.py.
Checks: focused tests observed RED then GREEN, full suite, diff check, structural consistency and generated configuration parity. No live provider activation or remote/bootstrap operations.
T2 RED: focused runner observed 1 failure + 3 errors (missing authority defaults/document/example and entrypoint link); later contradiction assertion also observed FAIL before correction.
T2 GREEN/REFACTOR: focused 7/7 passed; full suite 41/41 passed, exit 0; git diff --check passed. Fixture audit reports include expected failure text, not a failing suite.
Structural readback: typed activation example/config parity, distinct public/general/private scopes, gate consistency, P03 optional writes and no onboarding authentication probing inspected.
T2 work-unit commit: cab92f405a985fc7a6fb13daf4833382a7a2e433. Parent independent verification pending; no actual provider activation or private/remote access. Runtime enforcement remains outside this instruction/config change.

Slice 2 precommit authored count: 361 additions plus deletions including tracking; accumulated feature count 700. Cached feature-branch-chain separates slices; no PR created.

Slice 2 holds cab92f4 plus its evidence-tracking commit; slice 1 remains 4afc35a + 72d9391. No child PR branches or remote PRs created.
