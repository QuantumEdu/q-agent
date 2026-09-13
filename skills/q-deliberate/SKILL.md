---
name: q:deliberate
description: "Trigger: /q-deliberate, deliberate, multi-agent debate, stress-test architecture, design deliberation. Multi-agent dialectical interview that deploys Proponent, Adversary, and Synthesizer subagents to rigorously stress-test decisions in frontier rounds, producing validated architectures and ADRs."
license: Apache-2.0
metadata:
  author: QuantumEdu
  version: "1.0.0"
  date: "2026-08-20"
  updated_at: "2026-08-20"
---

# q:deliberate

Multi-agent dialectical deliberation engine. Interrogates, stress-tests, and sharpens architectural decisions by orchestrating three specialized subagent roles before presenting frontier questions to the user.

---

## 1. Core Architecture & Roles

```text
               ┌──────────────────────────────────────┐
               │          User Prompt / Topic         │
               └──────────────────┬───────────────────┘
                                  │
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
    ┌───────────────────────────┐   ┌───────────────────────────┐
    │   Subagent 1: Proponent   │   │    Subagent 2: Adversary  │
    │      (Thesis Agent)       │   │     (Antithesis Agent)    │
    │  - Prompts: proponent.md  │   │  - Prompts: adversary.md  │
    │  - Primary sources & APIs │   │  - Edge cases & risks     │
    └─────────────┬─────────────┘   └─────────────┬─────────────┘
                  │                               │
                  └───────────────┬───────────────┘
                                  │ (Hypotheses & Critiques)
                                  ▼
                    ┌───────────────────────────┐
                    │   Subagent 3: Synthesizer │
                    │     (Arbitrator Agent)    │
                    │  - Prompts: synthesizer.md│
                    │  - Tradeoff evaluation    │
                    │  - Recommendation (➡️)    │
                    └─────────────┬─────────────┘
                                  │
                                  ▼
                    ┌───────────────────────────┐
                    │    Interactive User Round │
                    │   - Frontier Questions    │
                    │   - Dialectical Rationale │
                    │   - Crystallized ADRs     │
                    └───────────────────────────┘
```

---

## 2. Deliberation Workflow

### Phase 1: Chart the Decision Tree
1. Analyze the user's initial idea, problem statement, or design goal.
2. Structure the problem as a **Directed Acyclic Graph (DAG)** of decisions.
3. Identify the **Frontier**: all decisions whose prerequisites are already settled and can be evaluated immediately without guessing future answers.

### Phase 2: Multi-Agent Parallel Exploration
For each open question on the frontier:
1. **Fact Gathering (Orchestrator)**: Never ask the user for facts accessible via tools (codebase, file system, docs). Dispatch read tasks directly.
2. **Proponent Subagent (Thesis)**: Load [`prompts/proponent.md`](./prompts/proponent.md). Build the strongest viability case based on primary sources, benchmarks, and patterns.
3. **Adversary Subagent (Antithesis)**: Load [`prompts/adversary.md`](./prompts/adversary.md). Stress-test the thesis against scale limits, concurrency, maintenance burden, and failure modes.

### Phase 3: Synthesis & Arbitrated Recommendation
1. Pass the outputs of both Proponent and Adversary to the **Synthesizer Subagent** using [`prompts/synthesizer.md`](./prompts/synthesizer.md).
2. The Synthesizer evaluates tradeoffs, eliminates hype or unsubstantiated claims, and formulates the recommended path (`➡️`) along with mandatory mitigations.

### Phase 4: Interactive Round Presentation
1. Format all frontier questions of the current round using [`assets/templates/debate-round-template.md`](./assets/templates/debate-round-template.md).
2. Present the numbered questions with the synthesized recommendation to the user.
3. **STOP and wait** for the user's answers. Never continue or assume responses.

### Phase 5: Tree Reshaping & ADR Crystallization
1. Incorporate the user's answers to close settled nodes on the tree.
2. If a closed decision is **hard to reverse**, **surprising without context**, and **a meaningful tradeoff**:
   - Generate an Architecture Decision Record (ADR) under `docs/adr/000N-<title>.md` using [`assets/templates/adr-template.md`](./assets/templates/adr-template.md).
   - Update `CONTEXT.md` with any newly defined canonical domain terms.
3. Recompute the frontier. If new questions are unblocked, run the next round.
4. **Completion**: The deliberation finishes when the frontier is empty (all branches resolved).

---

## 3. Rules & Invariants

- **Facts vs Decisions**: Finding facts is the agent team's job. Deciding tradeoffs is the user's prerogative.
- **No Unexamined Assumptions**: If a dependency or constraint is unverified, assign the Adversary to challenge it before proceeding.
- **Round Grouping**: Always batch all currently unblocked frontier questions into a single round to minimize turn overhead.
- **Progressive Persistence**: Create `docs/adr/` and `CONTEXT.md` lazily only when genuine architectural commitments are made.

---

## 4. References & Templates

- **Role Prompts**:
  - Proponent: [`prompts/proponent.md`](./prompts/proponent.md)
  - Adversary: [`prompts/adversary.md`](./prompts/adversary.md)
  - Synthesizer: [`prompts/synthesizer.md`](./prompts/synthesizer.md)
- **Output Templates**:
  - Interactive Round: [`assets/templates/debate-round-template.md`](./assets/templates/debate-round-template.md)
  - Architecture Decision Record: [`assets/templates/adr-template.md`](./assets/templates/adr-template.md)
