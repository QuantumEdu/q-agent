# Local Codex CLI Prototype Review

## Scope

This prototype compares a minimal instruction harness with q-agent instructions on the same
SQLite ticket-workflow task. It is not an official Harness2 benchmark: Harness2's Codex substrate
requires a Responses-compatible endpoint, while this run used a locally authenticated Codex CLI.

## Evidence

| Case | Codex rollout | Real tests | Tests modified |
| --- | --- | --- | --- |
| Baseline | Exit 0 | 3/3 passed | No |
| q-agent | Exit 0 | 3/3 passed | No |

The q-agent case produced one functional diff in `ticket_store.py` (28 added lines), preserving
SQLite WAL and using parameterized SQL for the conditional state update. `git diff --check` passed.

## Independent Review

An isolated adversarial review of the final q-agent diff returned `APPROVED`. The earlier review
rejected a generated Python bytecode artifact; the evaluator was corrected to exclude generated
bytecode and agent operational artifacts from the application diff before the final clean run.

## Result

The fixture confirms that both harnesses can complete this task with the local Codex CLI. It does
not demonstrate a q-agent improvement: both achieved the same functional score on a single,
small task. A formal Harness2 experiment still requires a supported Responses endpoint and a
larger, fixed task set.
