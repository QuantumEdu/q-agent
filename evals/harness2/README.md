# q-agent Harness2 local prototype

This repository evaluates a local Codex CLI session against the same SQLite ticket-workflow task
with two instruction harnesses:

1. a minimal baseline;
2. q-agent instructions copied from the installed q-agent repository.

It is a local prototype, not an official Harness2 benchmark. Harness2's supported Codex substrate
requires a Responses-compatible endpoint; a ChatGPT-authenticated Codex CLI does not meet that
contract. The runner preserves the experimental discipline that matters for this prototype:
identical fixture copies, immutable tests, real SQLite verification, captured trajectories, and
separate baseline and q-agent result records.

Run the evaluator with:

```bash
python3 evaluator.py
```

Results are written below `runs/`. The evaluator exits nonzero unless both agent runs produce a
passing, untampered implementation. This makes a failed or incomplete rollout explicit rather than
recording it as a score.
