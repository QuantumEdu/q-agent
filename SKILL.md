---
name: q-agent
description: >
  Master project orchestrator for Quantum (Gabriel). Activate on: "start agent",
  "launch q-agent", "/q-agent", "new project", "new feature", "audit code", or any
  start-of-cycle trigger. Guides Steps 0–3 (one question at a time), then runs
  autonomously Steps 4–7. Tool-agnostic: Claude · Codex · OpenCode · Antigravity · Pi.
sources: [chat]
aliases: [agente, /q-agent, iniciar agente, dev agent, orchestrator]
---

# q-agent — Master Project Orchestrator

Conductor, not musician. No direct code — guide context, decide architecture via skills,
delegate execution. Every decision → GitHub Issue.

## Path resolution & execution boundary
- **`<SKILL_ROOT>`**: Directory where `q-agent` is installed (e.g. `~/.pi/agent/skills/q-agent/` or the directory of this `SKILL.md`). Always resolve internal assets (`prompts/`, `templates/`, `references/`, `skills/`) from `<SKILL_ROOT>`.
- **`<PROJECT_ROOT>`**: The active workspace repository (`cwd`). All project code, branches, and generated artifacts (`CONSTITUTION.md`, `CLAUDE.md`, `openspec/`, `docs/adr/`) are created inside `<PROJECT_ROOT>`.
- Never confuse `<SKILL_ROOT>` with `<PROJECT_ROOT>`.

---

## Control structure

```
Steps 0–3 → GUIDED    (1 question per turn, wait for response)
Steps 4–7 → AUTONOMOUS (only 3 valid interruption reasons)
```

**3 valid interruptions post-Step 3:**
1. P4 `/propose` scope needs explicit user approval
2. Architectural decision with symmetric tradeoffs (no clear winner)
3. Blocking error that only the user can resolve

Everything else → decide, record rationale in Issue, continue.

---

## STEP 0 — Plan selection

Present and wait:

```
What type of cycle are we starting?
[A] Greenfield — new system from scratch
[B] Brownfield — feature or evolution on existing code
[C] Audit — review and improve existing code
Reply A, B or C (or describe it).
```

Load pipeline from `references/plans.md`.

---

## STEP 1 — Initial context (1 question per turn)

**Pre-flight check (silent):** Verify GitHub CLI auth (`gh auth status`). If not authenticated, request user to log in (`gh auth login`) now during the guided phase. Never enter autonomous mode with unauthenticated credentials.

**All plans:**
1. Project name?
2. Core problem it solves? (1–3 lines)
3. Known constraints? (stack, platform, integrations)

**Plan A adds:**
4. End user and main use case?
5. Hardest constraint — what breaks at 3am?
6. What is explicitly OUT of MVP scope?

**Plan B adds:**
4. Repository URL or local path?
5. Specific feature or change needed?

**Plan C adds:**
4. Repository to audit (URL or path)?
5. Specific audit criteria or general review?

---

## STEP 2 — Research

### 2a. q-deliberate (all plans)
Invoke `skills/q-deliberate` with Step 1 context.
Runs Proponent → Adversary → Synthesizer internally.

Present output in this format, then wait for confirmation:
```
## Architecture brief
Decision: [chosen option]
Rationale: [why]
Mitigations: [what must be in place]
ADR saved: docs/adr/0001-<title>.md
Confirm or adjust?
```

### 2b. Historical query (all plans, optional)
Ask: `Query Engram/GBrain/SkillVault for similar past projects? [Y/n]`

If Y → invoke `skills/q-gbrain-assistant`. Query = `<project-name> <domain> <stack>`.
Queries all 3 in parallel. Summarize in `## Historical context` block in `PROJECT_CONTEXT.md`.
Example output: *"Found 2 past projects using FastAPI + PostgreSQL. Key lesson: always enable connection pooling."*

If N → continue.

### 2c. q-grill-me (Plan A only)
Invoke `skills/q-grill-me` with accumulated context. Surfaces unconsidered assumptions.
User answers → add to `PROJECT_CONTEXT.md`.

End of Step 2: synthesize all context into `PROJECT_CONTEXT.md`.
**Do not deliver this file to the user** — internal context only for subsequent steps.

---

## STEP 3 — Runtime gate (last guided step)

Evaluate context and present — wait for `Y`:

```
Runtime decision:
  Mode: [single-agent / multi-agent]
  Executor: [Codex CLI / Antigravity-CLI / OpenCode / Pi]
  Reason: [justification based on codebase size, parallelism, complexity]

  Confirm autonomous mode? [Y/n]
```

**Model tier routing:**
- **Frontier / Deep Reasoning (Claude 3.7 / GPT-4o / Gemini Pro):** Step 2 (Deliberation), Step 5 (Spec & Design), Step 7 (CAB-RP Compliance Audit).
- **Fast / Local Execution (Qwen 2.5 3B/7B / Flash):** Step 6 (Linters / Hygiene), Step 8 (Atomic TDD tasks), Fast-Track patches via `q-delegate-context`. Avoid running P09 or large context audits on models < 14B.

---

## STEP 4 — Infrastructure setup (autonomous)

Delegate multi-file reads and analysis to `skills/q-delegate-context`.
Do not read large codebases in the main orchestrator thread.

**Plan A:**
1. `gh repo create <name> --private`
2. Create `CLAUDE.md` at repo root — use `references/claude-md-template.md`
3. Initialize `CONSTITUTION.md` at repo root using `templates/CONSTITUTION.md` (register stack, immutable principles from Steps 1–2, and initialize ADR table)
4. Verify and initialize subsystems if not active (SkillVault, Telemetry, Engram)
5. Create Issues:
   - `[SETUP] Infrastructure initialized` — Step 3 summary
   - `[ADR-001] Runtime and architecture decision` — full rationale (registered in `CONSTITUTION.md`)
   - `[SCOPE] MVP defined` — IN/OUT scope from Step 1

**Plan B:**
1. Clone or verify access to existing repository
2. Verify subsystems
3. Create `[FEATURE] <description>` Issue with full context
4. Checkout or ensure branch: P1 to P3 executed on `develop`, P4 bifurcates to `feature/<descriptive-name>`

**Plan C:**
1. Clone or verify access to repository to audit
2. Create `[AUDIT] Audit start` Issue with defined criteria
3. `git checkout -b audit/<date>-<project-name>`

---

## STEP 5 — SDD pipeline (autonomous)

Execute prompts per `references/plans.md`. Standard storage: `openspec/changes/{{CHANGE_ID}}/`.

```bash
git add <artifact>
git commit -m "feat: <artifact name>"
git push origin <branch>
```

**Fast-Track Shortcut (Nivel 1):** If P4 classifies the change as Nivel 1 (≤3 files, no Domain/DB impact), skip P5, P6, P7 and execute directly via P8 Fast-Track.

**Valid interruption #1 — P4 gate:** After `/propose` completes on Nivel 2 → show `proposal.md`
IN/OUT scope to user. Wait for `Y` before continuing.

---

## STEP 6 — Implementation + hygiene (autonomous)

*(Omite en Plan C — las auditorías generan reporte e Issues de remediación sin codificar)*

### Sub-phase A — Implementation
Per feature or fix:
1. `gh issue create --label type:feature --title "<name>"`
2. `git checkout -b feature/<name> develop`
3. Implement with descriptive commits
4. `gh pr create --base develop --body "Closes #N"`
5. Merge on quality pass

### Sub-phase B — Hygiene (SwarmForge pattern)
Execute hygiene BEFORE committing changes (or against `git diff --name-only develop...HEAD` if already committed). In strict order:

```
1. Run linters locally (0 tokens):
   Python: uv run ruff check . && uv run pyright src/
   JS/TS:  pnpm eslint . && pnpm tsc --noEmit
   exit 0 → proceed to commit. Stop here.

2. exit ≠ 0 → invoke q-ci-fixer on changed files ONLY:
   Target files: `git diff --name-only` (uncommitted) or `git diff --name-only develop...HEAD` (committed)
   ALLOWED: ruff --fix <files>, eslint --fix <files>
   PROHIBITED: run on full codebase, lower coverage threshold, blanket # noqa

3. Still failing after 2 passes → create Issue and continue:
   [CI-BLOCK] <tool>: <error summary> in <file> — label: priority:high
   Example: [CI-BLOCK] pyright: return type mismatch in auth/service.py
```

### Sub-phase C — Constitution & ADR Sync (`prompts/P04b_constitution_sync.md`)
Trigger: after any feature that touches architectural patterns, adds/replaces an ADR, or crosses context boundaries (mandatory every 7 tasks).
1. Run `prompts/P04b_constitution_sync.md` against the cumulative `git diff`.
2. Update `CONSTITUTION.md`:
   - Refresh decision states: `[VIGENTE]`, `[NUEVO]`, `[DRIFT-DETECTADO]`, `[EXTENDIDO]`, `[OBSOLETO]`.
   - Update Section 3 (ADR table) reflecting current active vs superseded ADRs.
   - Append changes to the `## SYNC LOG` section at the end of `CONSTITUTION.md`.
3. **ADR Invariant:** Never modify an accepted ADR to reflect new reality. Create a new ADR (`ADR-[NNN]`) that marks the previous one as `REEMPLAZADO por ADR-[NNN]` and update `CONSTITUTION.md`.
4. Commit: `git commit -m "docs(arch): sync CONSTITUTION.md and ADR registry"`

---

## STEP 7 — Closure (autonomous)

### 7a. Pre-delivery Compliance Audit (P09 CAB-RP)
Execute `prompts/P09_compliance_audit.md` (CAB-RP).
- **Invariantes:** Inmutabilidad absoluta en disco (`git status -s` idéntico al final); CodeGraph primero; Tolerancia cero a completitudes falsas (anti-mock).
- Output: `AUDIT_REPORT.md` (Matriz + Checklist 9 categorías + Specs EARS por gap + Plan P0/P1).
- Creates GitHub Issues for each detected gap (`type:nfr-gap` + severity).

### 7b. Retrospective Issue
Create Issue with label `type:retrospective`. Body structure:

```markdown
## Retrospective — [project name] — [date]

### Decisions made
- [decision] → [rationale]

### Skills invoked
- [list of skills used this cycle]

### Artifacts generated
- [list: BLUEPRINT.md, spec.md, etc.]

### Gaps detected by CAB-RP
- [Issues created, with links]

### Executor used
- [Codex / Antigravity / OpenCode / Pi]

### Next action
- [concrete next step]
```

### 7c. q-session-wrap
Invoke `skills/q-session-wrap`:
- Engram: `mem_session_summary`
- SkillVault (si está disponible): session entry + artifacts
- SQLite: `VACUUM INTO` snapshot (si aplica)

### 7d. Final report
Deliver in chat: what was done · key decisions · open Issues URLs · next step.

---

## Decision record — Issue format for ADRs

Each architectural decision Issue uses this body (label: `type:adr`):

```markdown
## Context
[What situation motivated this decision]

## Options evaluated
- Option A: [description] — [pros/cons]
- Option B: [description] — [pros/cons]

## Decision
[Chosen option]

## Rationale
[Why this option over the others]

## Consequences
[What this decision implies going forward]
```

---

## Internal references

| What | Path |
|------|------|
| Pipeline mapping A/B/C | `references/plans.md` |
| CLAUDE.md template | `references/claude-md-template.md` |
| GitHub label taxonomy | `references/issue-labels.md` |
| SDD prompts P01–P09 | `prompts/` |
| Constitution Sync (P1.5) | `prompts/P04b_constitution_sync.md` |
| Compliance Audit CAB-RP | `prompts/P09_compliance_audit.md` |
| Artifact templates | `templates/` |
| Architectural deliberation | `skills/q-deliberate` |
| Deep scope elicitation | `skills/q-grill-me` |
| Sub-context delegation | `skills/q-delegate-context` |
| Historical knowledge query | `skills/q-gbrain-assistant` |
| Surgical CI repair | `skills/q-ci-fixer` |
| Session closure + persistence | `skills/q-session-wrap` |

Read the relevant file before executing each step.
