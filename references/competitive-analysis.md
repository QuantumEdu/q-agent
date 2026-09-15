# Comparative Analysis & Architectural Rationale: Deterministic SDD

> **Status:** Active Reference / Architectural Decision Record  
> **Topic:** Specification-Driven Development (SDD) frameworks comparison and context isolation.

---

## 1. Problem Statement: The AI Coding Failure Modes

Through rigorous empirical testing and community defect analysis (the "Amarillas" evaluation), three systemic failure modes were identified in mainstream AI development tools:

1. **Vibe Coding Regressions:** Editing code without architectural contracts causes silent regressions, unmaintainable drift, and broken business domain invariants.
2. **Big Design Up Front (BDUF) & Context Rot (Spec-Kit Pattern):** Emitting massive Markdown specifications in a single session saturates the model's context window. By Phase 5, the model suffers attention degradation ("Lost in the Middle"), ignoring instructions and generating hallucinations.
   - *GitHub Spec-Kit [Issue #3507](https://github.com/github/spec-kit/issues/3507):* Context rot acknowledged; late tasks suffer degraded quality.
   - *GitHub Spec-Kit [Issue #3752](https://github.com/github/spec-kit/issues/3752):* `/speckit.converge` falsely emits "converged" without auditable verification of acceptance scenarios.
3. **Conversational Swarm Overhead (BMAD / ChatDev):** Unconstrained multi-agent swarms burn 3x–5x more tokens, introduce high latency, and multiply hallucination risk through chat chatter without verifiable quality gates.

---

## 2. Alternatives Evaluated

| Dimension | GitHub Spec-Kit | OpenSpec | BMAD Method | Superpowers | **q-agent** |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Execution Architecture** | Waterfall BDUF | Modular, lacks deterministic gates | Multi-agent conversational swarm | Fixed prompt chain | **Single Tier-1 Orchestrator + Tier-2 local workers** |
| **Workspace Isolation** | Local working tree | Manual checkout | Harness-dependent | Manual checkout | **Mandatory Git Worktrees (`../{repo}-worktrees/`)** |
| **Implementation Guarantee**| Prompt trust (`converge`) | Subjective diff review | Inter-agent consensus | Direct execution | **Reproduction-First TDD (RED failure required)** |
| **Context Window Hygiene** | Dumps full Markdown | Injects full specification files | High chatter token burn | Rigid templates | **AST Skeleton Compression (Prunes >70% tokens)** |
| **Human-in-the-Loop** | Agent takes control | Agent takes control | Opaque bot dialogues | Agent takes control | **Supervised Gates (P03, P04, P09) + Mentor Mode** |
| **Observability / LLMOps** | None native | None native | None native | Basic logs | **Flight Recorder + 9-Dimension Evaluation Matrix** |
| **Caliber Routing** | One-size-fits-all | Manual branching | Swarm roles | Static scripts | **Calibrated Fast-Track (≤3 files) vs Full SDD vs Plan C** |

---

## 3. The q-agent Architectural Decision

We selected a **Single-Agent Deterministic Orchestrator** governed by four core architectural pillars:

1. **Git Worktree Isolation:** Every feature and fix is executed in a dedicated worktree (`../{repo}-worktrees/{branch}`). The developer's primary workspace remains clean and uninterrupted.
2. **Reproduction-First TDD:** Modifying application source code in `src/` is prohibited until an automated test in `tests/` reproduces the bug or asserts the missing feature (RED phase).
3. **AST Skeleton Indexing:** In larger codebases, full file contents are replaced with pruned Abstract Syntax Tree (AST) skeletons (class signatures, method contracts, type hints), reducing context footprint by >70%.
4. **Zero-Token Local Quality Gates:** Linters, formatters, and unit tests run deterministically on the local host with zero LLM token consumption. The LLM is invoked only when a targeted repair is required (max 2 passes).

---

## 4. Consequences and Tradeoffs

- **Positive:**
  - Zero context rot on large features.
  - Zero working tree pollution; safe concurrent branching.
  - 100% auditable test coverage prior to code modification.
  - Predictable token costs via model tiering (Tier 1 for reasoning, Tier 2 for mechanical patches).
- **Negative / Costs:**
  - Requires git worktree capability and disk space for sibling worktree directories.
  - Requires initial discipline in formulating reproduction tests before code generation.
