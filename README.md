# q-agent — Master Project Orchestrator

> **Hermetic deployment package v01** · Tool-agnostic · Greenfield · Brownfield · Audit

---

## What is q-agent?

`q-agent` is a master orchestrator for full software development cycles. It is NOT a code generator — it is a **conductor**: it guides the user through the right questions, makes architectural decisions using specialized skills, and delegates technical execution to the correct runtime.

Every decision is **traceable as a GitHub Issue** in the project repository. Every step produces a documented artifact.

### Compatible runtimes
| Runtime | How to activate |
|---------|----------------|
| **Pi** | `pi chat --skill q-agent` or say "start agent" |
| **Antigravity CLI** | Load skill, then say "start agent" |
| **Claude Code** | SKILL.md is auto-detected via frontmatter |
| **OpenCode** | Load skill directory |

---

## The 3 Plans

q-agent operates under one of three plans, selected at the start of every cycle:

| Plan | Use case | Pipeline |
|------|----------|---------|
| **A — Greenfield** | New system from scratch | P2 → P4 → P5 → P6 → P7 → P8 |
| **B — Brownfield** | Feature or evolution on existing code | P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 |
| **C — Audit** | Review, audit and improve existing code | P1 → P9 (CAB-RP) |

---

## Operating Modes

```
Steps 0–3  → GUIDED mode      (agent asks, user responds — 1 question at a time)
Steps 4–7  → AUTONOMOUS mode  (agent executes, interrupts only at critical gates)
```

### The 3 ONLY reasons to interrupt after Step 3
1. The `/propose` scope (P4) needs explicit approval before continuing
2. An architectural decision has two symmetric tradeoffs (no clear winner)
3. A blocking error that requires context the agent doesn't have

Everything else → the agent decides, records the rationale in a GitHub Issue, and continues.

---

## Step-by-step Walkthrough

### Step 0 — Plan Identification
The agent presents the 3 plans and waits for the user's choice.
Loads `references/plans.md` to configure the exact pipeline for the selected plan.

---

### Step 1 — Initial Context (Guided)
The agent asks questions one at a time:

**All plans:**
1. Project / system name
2. Core problem it solves (1–3 lines)
3. Known technical constraints (stack, integrations, platform)

**Plan A adds:**
4. End user and main use case
5. Hardest constraint (what breaks at 3am?)
6. What is explicitly OUT of MVP scope

**Plan B adds:**
4. Repository URL or local path
5. Specific feature or change needed

**Plan C adds:**
4. Repository URL or local path
5. Specific audit criteria (or general review)

---

### Step 2 — Research (Skills invoked)

#### 2a. `q-deliberate` — Architectural Deliberation (all plans)
Multi-agent dialectical debate. Deploys 3 sub-roles internally:
- **Proponent** — builds the strongest case for each option
- **Adversary** — stress-tests risks, edge cases, failure modes
- **Synthesizer** — arbitrates and produces the recommended decision + ADR

Output: architectural brief with evaluated alternatives. Presented to user for confirmation.

#### 2b. `q-gbrain-assistant` — Historical Knowledge Query (optional, all plans)
Queries 3 knowledge sources in parallel via MCP:
- **Engram** — previous architectural decisions, similar past projects
- **GBrain** — accumulated knowledge on stacks and patterns
- **SkillVault** (`QuantumEdu/kbs`) — skills and prompts used in similar contexts

Results synthesized into a `## Historical context` block in `PROJECT_CONTEXT.md`.

#### 2c. `grill-me` — Deep Elicitation (Plan A only)
A relentless structured interview to sharpen the plan scope. Surfaces assumptions the user hasn't considered yet.

All Step 2 outputs are synthesized into an internal `PROJECT_CONTEXT.md` (not delivered to user — used as context for all subsequent steps).

---

### Step 3 — Meta-Orchestration Gate (Last guided step)
The agent decides and presents:
- Single-agent or multi-agent execution?
- Recommended executor runtime (Codex CLI / Antigravity CLI / OpenCode / Pi)
- Rationale for the decision

User confirms → **autonomous mode begins**.

---

### Step 4 — Infrastructure Setup (Autonomous)

Delegates heavy sub-tasks via `delegate-context-work` (FirstMate pattern) to keep the orchestrator main thread clean.

**Plan A:**
1. Create private GitHub repository
2. Create `CLAUDE.md` at repo root (from `references/claude-md-template.md`)
3. Verify subsystems (SkillVault, Telemetry, SDDinit + Engram)
4. Create initial Issues: `[SETUP]`, `[ADR-001]`, `[SCOPE] MVP`

**Plan B:**
1. Clone / verify access to existing repo
2. Verify subsystems
3. Create Issue `[FEATURE] description`
4. Create branch `feature/<name>`

**Plan C:**
1. Clone / verify access to repo to audit
2. Create Issue `[AUDIT] start`
3. Create branch `audit/<date>-<project>`

---

### Step 5 — Main Pipeline Flow (Autonomous)

Executes the SDD pipeline prompts in the order defined by `references/plans.md`.

After each prompt that produces an artifact:
```bash
git add <artifact>
git commit -m "feat: <artifact description>"
git push origin <active-branch>
```

**Mandatory P4 gate (Plans A & B):** After `/propose`, the `proposal.md` is presented to the user with full IN/OUT scope. The user must approve before continuing.

#### SDD Pipeline Prompts

| Prompt | File | What it produces |
|--------|------|-----------------|
| **P00** | `prompts/P00_constitution_template.md` | Constitutional rules for the project |
| **P01** | `prompts/P01_auditoria_adacg.md` | MAB-PC audit: `BLUEPRINT.md` + `CONSTITUTION.md` |
| **P02** | `prompts/P02_context_engineering.md` | `CONTEXT.md` — structured project context |
| **P03** | `prompts/P03_evolucion_blueprint.md` | `EVOLUTION.md` — blueprint vs real code reconciliation |
| **P04** | `prompts/P04_propose.md` | `proposal.md` — IN/OUT scope gate |
| **P05** | `prompts/P05_spec.md` | `spec.md` — BDD specification (Given/When/Then) |
| **P06** | `prompts/P06_design.md` | `design.md` — architectural design |
| **P07** | `prompts/P07_tasks.md` | `tasks.md` — atomic task breakdown |
| **P08** | `prompts/P08_apply_verify.md` | Verified TDD implementation |
| **P09** | `prompts/P09_compliance_audit.md` | `AUDIT_REPORT.md` — CAB-RP compliance audit |

---

### Step 6 — Implementation with Hygiene Control (Autonomous)

#### Sub-phase A — Code implementation
Standard git workflow per feature/fix:
1. Create Issue with label `type:feature` or `type:fix`
2. Create branch from `develop`
3. Implement with descriptive commits
4. Open PR → `develop` referencing the Issue (`Closes #N`)
5. Merge on quality pass, close Issue via PR

Branch naming:
- `main` → stable production
- `develop` → continuous integration
- `feature/<name>` → new features (Plans A/B)
- `fix/<name>` → bugs
- `audit/<date>-<name>` → audits (Plan C)

#### Sub-phase B — Hygiene (SwarmForge pattern)
After each implementation unit, in order:

1. **Deterministic local check (0 tokens):** Run linters/formatters/type checks locally.
   - Exit 0 → proceed. No tokens consumed.
2. **Surgical CI repair — only if exit ≠ 0:** Invoke `q-ci-fixer` on `git diff` files ONLY.
   - Never on the full codebase. Never for cosmetic changes.
   - **Hard cap: maximum 2 passes.** If still failing → create Issue `[CI-BLOCK]` with `priority:high` and continue.

---

### Step 7 — Closure & Delivery (Autonomous)

#### 7a. `q-audit-readonly` — Pre-delivery audit
Non-mutating inspection. Checks:
- SDD contract compliance (`spec.md` vs `tasks.md` completion)
- API surface (auth middleware, RBAC, exception handling)
- Frontend hygiene (no fake preloaded data, validation handling)
- Outputs: `AUDIT_REPORT.md` with verdict `PASS / FAIL / PASS WITH OBSERVATIONS`

Issues created for each gap: label `type:nfr-gap` + severity.

#### 7b. Retrospective Issue
Created in the project repo with label `type:retrospective`:
- Decisions made and rationale
- Skills invoked
- Artifacts generated
- Gaps detected
- Executor used
- Recommended next action

#### 7c. `q-session-wrap` — Session persistence
- Saves session memory to **Engram** (`mem_session_summary`)
- Catalogs artifacts in **SkillVault**
- Creates atomic SQLite snapshot (`VACUUM INTO`)

#### 7d. Final report
Compact summary delivered in chat:
- What was done
- Key decisions
- Open Issues
- Retrospective Issue URL
- Next step

---

## Skills Reference

### `grill-me`
**Step 2c — Plan A only**
A relentless structured interview to sharpen scope. Surfaces hidden assumptions and requirements before any code is written.
- Activates with: `/grill-me`, "grill me", "interview me"
- Output: refined scope and elicited requirements

### `q-deliberate`
**Step 2a — All plans**
Multi-agent dialectical debate engine. Three internal sub-roles (Proponent, Adversary, Synthesizer) stress-test architectural decisions before presenting frontier questions to the user.
- Proponent: builds the strongest case for each option using primary sources
- Adversary: attacks scale limits, concurrency, failure modes, maintenance burden
- Synthesizer: arbitrates, eliminates hype, produces recommended decision + ADR
- Never asks for facts the agent can fetch itself
- Output: architectural brief + ADRs in `docs/adr/`

### `delegate-context-work`
**Steps 4 & 5 — All plans**
Keeps the orchestrator main thread clean by delegating heavy sub-tasks to isolated sub-contexts (FirstMate pattern). Selects executor, model, and effort automatically or explicitly.
- Modes: auto / explicit / off
- Budgets: read ≤180s, web research ≤600s, implementation ≤900s
- Hard cap: 2 correction rounds per task
- Compatible executors: native subagents, Antigravity CLI, Codex CLI

### `q-gbrain-assistant`
**Step 2b — All plans (optional)**
Structured gateway to GBrain (Personal + Multi-Agent Knowledge Graph). Queries Engram, GBrain, and SkillVault in parallel to surface historical decisions, patterns, and lessons learned.
- Hybrid query (RRF + semantic expansion)
- Key intents: context briefing, historical decision retrieval, knowledge registration, gap analysis, health check
- CLI: `gbrain query`, `gbrain remember`, `gbrain link`, `gbrain doctor`

### `q-audit-readonly` _(part of q-session-quality-suite)_
**Step 7a — All plans**
Deep technical audit with **absolute zero disk mutations**. Checks SDD contract compliance, frontend hygiene, API security surface.
- Invariant: `git status -s` must be identical before and after
- Uses CodeGraph for call-path and blast-radius analysis before text search
- Output: executive report (PASS / FAIL / PASS WITH OBSERVATIONS), P1 critical + P2 medium findings

### `q-ci-fixer` _(part of q-session-quality-suite)_
**Step 6 Sub-phase B — All plans**
Surgical CI/CD pipeline repair. Operates only on `git diff` files. Never weakens quality rules.
- 4-layer protocol: Format/Lint → Static Types → Business Logic Assertions → Coverage Gate
- PROHIBITED: editing `ci.yml` to lower coverage thresholds, blanket `# noqa` / `# type: ignore` suppressors
- Blast radius minimum: only essential lines to resolve the error
- Always verifies with local command before declaring done

### `q-session-wrap` _(part of q-session-quality-suite)_
**Step 7c — All plans**
Ordered session closure. Persists operational memory so the next session starts with full context.
- Engram: `mem_session_summary` with Goal / Instructions / Discoveries / Accomplished / Next Steps / Relevant Files
- SkillVault: `skillvault add-entry --type session` + `save-artifact` for relevant documents
- SQLite: `VACUUM INTO` atomic snapshot in `~/.skillvault/exports/`
- Invariant: internal backup never replaces the visible user-facing final report

---

## Artifact Templates

| Template | File | Purpose |
|----------|------|---------|
| ADR | `templates/ADR-template.md` | Architecture Decision Record |
| Blueprint | `templates/BLUEPRINT.md` | System architecture map |
| Constitution | `templates/CONSTITUTION.md` | Non-negotiable rules and principles |
| Proposal | `templates/proposal.md` | `/propose` scope gate structure |

---

## References

| File | Purpose |
|------|---------|
| `references/plans.md` | Exact prompt mapping per plan A/B/C with file paths |
| `references/claude-md-template.md` | CLAUDE.md template for new repositories |
| `references/issue-labels.md` | Complete GitHub Issue label taxonomy |

---

## Installation

### Pi (recommended)
```bash
cp -r q-agent-v01 ~/.pi/agent/skills/q-agent
pi skills list | grep q-agent
```

Activate: say **"start agent"** or **"/q-agent"** in any Pi session.

### Antigravity CLI
```bash
cp -r q-agent-v01 ~/.gemini/antigravity-cli/skills/q-agent
```

### Claude Code / OpenCode
Copy `q-agent-v01/` to your agent's skills directory. The `SKILL.md` frontmatter (`name`, `aliases`) is auto-detected.

---

## Activation Triggers

Say any of these in a session with q-agent loaded:

```
start agent · /q-agent · iniciar agente · new project
new feature · audit code · I want to build a system
```

---

## Version

`v01` — Initial hermetic package.  
Author: QuantumEdu  
License: Apache-2.0
