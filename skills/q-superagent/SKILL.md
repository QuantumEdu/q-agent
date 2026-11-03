---
name: q-superagent
description: "Runs q-agent as a durable, proactive operator for one repository: polls triggers, keeps tickets across sessions, dispatches bounded workers, and interrupts a human only when a decision is required."
license: Apache-2.0
metadata:
  version: "1.0.0"
  context_policy: "PROGRESSIVE"
  requires: ["references/attention-policy.md", "references/execution-authority.md"]
  may_call: ["q-delegate-context", "q-adversarial-review", "q-ci-fixer", "q-skill-doctor"]
  produces: ["tickets", "assignments", "attention-queue"]
---

# q-superagent — the router

> Path B of the super-agent design: keep the domain model, drop the dependency.
> State lives in SQLite, not in a chat window.

## 1. The split of responsibility

| Role | Who | Gets |
| :--- | :--- | :--- |
| Router | this skill, in the parent session | the request, the policy, the routing facts. **Never** the investigation. |
| Worker | `q-delegate-context` (native subagent, codex, opencode, antigravity) | one ticket, one directory, its own context |
| Judge | `q-adversarial-review` on a fresh context | the diff only |
| Memory | Engram (decisions) + SkillVault (project knowledge) | explicit reads, never implicit injection |

The router's one rule: **it does not investigate.** Deciding how to fix something is
work; the router decides *who* works and *whether* work is allowed.

## 2. One cycle

```bash
# 0. What already needs a human? Read this FIRST, every session.
python3 tools/q-tickets/q_tickets.py attention-queue

# 1. What work is already in flight?
python3 tools/q-tickets/q_tickets.py list

# 2. Did anything new arrive? Observe first; it opens nothing.
python3 tools/q-triggers/q_triggers.py poll --cwd . --observe --limit 20

# 3. When the observed candidates look right, let it open tickets.
python3 tools/q-triggers/q_triggers.py poll --cwd . --limit 20
```

Configuration lives in `.q-agent.json`:

```json
{
  "triggers": {
    "enabled": true,
    "policy_version": "1",
    "sources": {
      "github": {
        "repo": "owner/name",
        "accept_mode": "observe",
        "mention": "@q-agent",
        "allowed_senders": ["your-login"],
        "bots": ["dependabot[bot]"],
        "watch": ["issues", "issue_comment"]
      }
    }
  }
}
```

## 3. Dispatch

1. `open` a ticket per accepted trigger (idempotent by trigger id).
2. `assign` it to an executor.
3. Hand the worker: the **original trigger text**, the mandate scope, the allowed
   write paths, and the verification command. Not your plan. The worker derives
   requirements from the source.
4. Worker contract is `q-delegate-context` M4: `status`, `summary`, `changed_files`,
   `evidence`, `checks`.
5. Accept only after inspecting the diff and re-running the check yourself.

```bash
python3 tools/q-tickets/q_tickets.py open --trigger-id <id> --title "<original title>" \
  --source github --actor <login> --thread github:<number>
python3 tools/q-tickets/q_tickets.py assign T-0001 --executor codex
python3 tools/q-tickets/q_tickets.py report T-0001 --assignment A-xxxx \
  --state ready --summary "PR #41" --evidence "gh pr view 41 --json state" --end
```

## 4. Interruption

Only three classes may reach a human: `actionable_result`, `blocking_decision`,
`hard_stop`. The store refuses anything else, so restraint does not depend on the
model remembering it. Progress stays in `events`; it is read on demand, never pushed.

## 5. Durability

A crash between two turns must not lose or duplicate work:

- tickets and mandates are in SQLite WAL with `synchronous=FULL`;
- a repeated trigger id returns the existing ticket;
- before acting again after a restart, read `list` and `show` — never assume a
  previous turn finished. If a pull request was already opened, find it, do not open
  a second one.

## 6. Completion gate

- [ ] Every open ticket has an assignment or a stated reason to wait.
- [ ] Every `ready` report was verified by the router, not accepted from the worker's
      own claim.
- [ ] No progress message became an interruption.
- [ ] `attention-queue` is empty or each item names the decision it blocks.
