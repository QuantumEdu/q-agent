# Optional context providers

## Objective and scope
Make q-agent usable without external memory products; define selective optional retrieval and local-first closure. Files: references/context-retrieval.md, templates/q-agent.json, tools/q-checklist/q_checklist.py, skills/q-gbrain-assistant/SKILL.md, SKILL.md, skills/q-session-wrap/SKILL.md, README.md, tests/test_context_retrieval.py.

## Constraints
Instruction-driven contract/configuration only; no remote integrations, credentials probing, installs, push, PR or merge. Preserve legacy integration flags but explicit disabled provider wins. Generated additions English. One coherent rollback boundary: optional retrieval contract/configuration and associated guidance/tests.

## Execution
- Route: delegated direct; trigger: multiple non-trivial files and preparation reads.
- Strict TDD: true; source: user AGENTS.md instructions.
- Runner: C:/Users/iQuantum/AppData/Local/Programs/Python/Python312/python.exe -m unittest discover -s tests -v
- Delivery: ask-on-risk; forecast: 300-390 authored lines plus tracking; stop before commit if above approximately 400.
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
Next step: work-unit commit; commit identity pending.
