---
name: q-skill-doctor
description: "Scores past agent conversations against a fixed rubric and proposes merge-ready skill improvements with evidence. Use when skills feel stale, when the same failure repeats, or before a skill consolidation pass."
license: Apache-2.0
metadata:
  version: "1.0.0"
  context_policy: "COMPACT"
  requires: ["tools/q-skill-doctor/skill_doctor.py"]
  may_call: ["q-improve-loop", "q-session-wrap"]
  produces: ["skill-score-report", "skill-improvement-proposals"]
---

# q-skill-doctor — Measure the agent setup, then improve it

## 1. When this applies

- A skill is suspected of being stale, noisy, or never used.
- The same failure repeats across sessions (re-running an identical command,
  editing without testing).
- Before a consolidation pass that deletes or merges skills.
- Periodically, to check whether an improvement actually moved a number.

**Anti-triggers:** rewriting a skill by taste (use `q-improve-loop` directly), fixing a
broken CI pipeline (use `q-ci-fixer`), auditing code (use `q-audit-readonly`).

## 2. The loop

```text
ingest  -> read real transcripts from local agent runtimes into one corpus
score   -> deterministic rubric per session and per skill
report  -> proposals, each bound to evidence and handed to q-improve-loop
```

The corpus lives at `.q-agent/skill-doctor/corpus.db`. Transcripts never leave the
machine.

## 3. Commands

```bash
# 1. Aggregate (codex | agy | opencode | all | <path to a jsonl dir>)
python3 tools/q-skill-doctor/skill_doctor.py --root . ingest --source all --limit 25

# 2. Score
python3 tools/q-skill-doctor/skill_doctor.py --root . score

# 3. Propose (drafts only, never edits a SKILL.md)
python3 tools/q-skill-doctor/skill_doctor.py --root . report --out .q-agent/skill-doctor/proposals

# Corpus summary
python3 tools/q-skill-doctor/skill_doctor.py --root . status
```

## 4. The rubric

Three sub-scores, 0–100, deterministic and documented so a regression shows up as a
number that moved rather than a feeling:

| Dimension | Signals | Penalty |
| :--- | :--- | :--- |
| **Efficiency** | duplicate tool calls, tool calls per user turn, error ratio | blind retries and thrash |
| **Quality** | writes after the last test command, writes with no test at all, errors | unverified edits |
| **Coverage** | installed skills referenced in real sessions | skills that never fire |

## 5. Hard boundaries

- **Never edit a skill from this tool.** Proposals are drafts. A scorer with write
  access to what it scores is a self-fulfilling loop with no external check.
- **Never send transcripts anywhere.** Local SQLite only.
- **Never present a score as a verdict on a person.** It measures the setup.
- **Do not compare absolute numbers across corpora.** Compare the same repository
  before and after a change.

## 6. Completion gate

- [ ] `status` shows a non-zero session count from at least one real runtime.
- [ ] Each proposal names a target skill, a section, a finding and its evidence.
- [ ] Proposals were applied through `q-improve-loop`, not by hand-editing prose.
- [ ] Re-running `score` after the change shows the intended movement, or the change
      is reverted.
