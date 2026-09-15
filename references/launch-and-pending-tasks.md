# Launch Roadmap, Technical Articles & Actionable Checklist

> **Target Package:** `QuantumEdu/q-agent` (v1.2.0)  
> **Purpose:** Distribution playbook, community outreach drafts, and next-session backlog.

---

## 1. Show HN / Dev.to / Substack Article Draft

### Title Options
- **Show HN:** `Show HN: q-agent – Deterministic SDD & TDD orchestrator for AI coding agents`
- **Dev.to / Substack:** `Deconstructing AI Coding Frameworks: Why We Abandoned Spec-Kit and Multi-Agent Swarms for Deterministic SDD`

### Article Body

```markdown
# Deconstructing AI Coding Frameworks: Why We Abandoned Spec-Kit and Multi-Agent Swarms for Deterministic SDD

For the past year, our team benchmarked the leading approaches to AI-assisted software development:
1. **Vibe Coding:** Prompting conversational LLMs directly into source files.
2. **Spec-Driven Development via Spec-Kit:** Generating large Markdown requirements, plans, and tasks before running `/implement`.
3. **Conversational Swarms (BMAD / ChatDev):** Orchestrating multi-agent dialogue loops (PM, Architect, Coder, Reviewer).

The empirical results were sobering:
- **Vibe coding** introduces silent regressions and architectural drift within 3 turns.
- **Spec-Kit** suffers from Big Design Up Front (BDUF) and **Context Rot**. By Phase 5 of implementation, the model loses attention ("Lost in the Middle"), skips acceptance criteria, and falsely declares convergence ([GitHub Spec-Kit Issue #3507](https://github.com/github/spec-kit/issues/3507), [Issue #3752](https://github.com/github/spec-kit/issues/3752)).
- **Multi-agent swarms** consume 3x–5x more tokens in inter-agent chatter, increase latency exponentially, and compound hallucinations without verifiable quality gates.

### What We Built: q-agent

Instead of more prompt engineering or conversational chatter, we designed `q-agent` around **software engineering fundamentals**:

```text
CONCEPTS > CODE  |  DETERMINISM > PROMPT ENGINEERING  |  HUMAN AT THE WHEEL
```

### The 4 Deterministic Pillars

1. **Git Worktree Isolation:** The agent is never permitted to operate on your dirty working tree. Every feature or fix executes in an isolated worktree (`../{repo}-worktrees/{branch}`).
2. **Reproduction-First TDD (RED-First):** Modifying application source code in `src/` is strictly forbidden until an automated unit test reproduces the bug or asserts the missing capability (exit code != 0).
3. **AST Skeleton Indexing:** Instead of feeding 500-line source files into the context window, `q-agent` prunes function bodies and provides Abstract Syntax Tree (AST) skeletons, conserving >70% of tokens.
4. **Zero-Token Local Quality Gates:** Linters, formatters, and test runners execute locally at 0 LLM tokens. The LLM is only invoked for surgical repairs (capped at 2 passes).

### The Competitive Matrix

| Dimension | GitHub Spec-Kit | OpenSpec | BMAD Swarms | **q-agent** |
| :--- | :--- | :--- | :--- | :--- |
| **Architecture** | Waterfall BDUF | Modular, no hard gates | Conversational swarm | **Single Tier-1 Orchestrator + Local Tier-2 Workers** |
| **Aislamiento** | Local tree | Manual | Harness-dependent | **Mandatory Git Worktrees** |
| **Implementation Guarantee** | Prompt trust (`converge`) | Diff review | Agent consensus | **Reproduction-First TDD (RED required)** |
| **Context Window** | Dumps full specs | Injects full files | High chatter burn | **AST Skeleton Compression (>70% savings)** |
| **Observability** | None | None | None | **Flight Recorder + 9-Dimension LLMOps Matrix** |
| **Zero Dependencies** | Python venvs / uv | CLI wrappers | Heavy frameworks | **Pure Python Standard Library (0 external deps)** |

### Try It Out

Install via `skills.sh` in 1 line:
```bash
npx skills add QuantumEdu/q-agent
```

Or explore the open-source repository:
👉 https://github.com/QuantumEdu/q-agent
```

---

## 2. Reddit Community Outreach Templates

### Template A: For `r/ClaudeAI` or `r/ChatGPTCoding`
> **Context:** When users ask: *"Why does Claude/Cursor start hallucinating or breaking existing code on long coding tasks?"*
>
> **Response:**
> "The root cause isn't the model's IQ; it's **context rot** and lack of architectural isolation. If you feed 20+ tasks into a single context window, attention degradation ('Lost in the Middle') causes the model to ignore earlier constraints by step 4 or 5 (this is documented even in GitHub Spec-Kit issues like #3507).
> 
> We resolved this in our workflow using three engineering practices:
> 1. **Git Worktree Isolation:** Run the agent in a detached worktree so your active IDE tree stays 100% clean.
> 2. **AST Skeleton Compression:** Prune method implementations and only feed class signatures/contracts to preserve context window budget.
> 3. **Reproduction-First TDD:** Never let the agent touch source code until it writes a test that fails reproducing the issue.
> 
> We formalized this into an open-source tool called `q-agent` (https://github.com/QuantumEdu/q-agent) with zero external dependencies if you want to inspect the prompt protocols."

---

## 3. Awesome Lists Submission Format

### PR to `awesome-claude-skills` & `awesome-agentic-patterns`
- **File:** `README.md`
- **Section:** `## Architecture & Governance`
- **Entry:**
  ```markdown
  - [q-agent](https://github.com/QuantumEdu/q-agent) - Deterministic SDD orchestrator with Reproduction-First TDD, AST skeleton compression, and isolated Git worktrees. Pure Python standard library with zero external dependencies.
  ```

---

## 4. Actionable Pending Backlog (Next Session)

- [ ] **Ecosystem Tags:** Add GitHub Topics to `QuantumEdu/q-agent` (`specification-driven-development`, `sdd`, `tdd-framework`, `llmops`, `clean-architecture`, `git-worktree`, `ast-parsing`, `claude-code-skill`).
- [ ] **Terminal GIF Demo:** Record a 30–45 second terminal session using `vhs` or `terminalizer` showing:
  1. `q-checklist` pre-flight setup in under 60 seconds.
  2. The agent blocking code modification until `[REPRODUCTION] [RED_FAIL]` is verified.
- [ ] **skills.sh Registry Validation:** Run `npx skills add QuantumEdu/q-agent` in a clean terminal to verify packaging.
- [ ] **Community Distribution:**
  - [ ] Submit PRs to `awesome-claude-skills` and `awesome-agentic-patterns`.
  - [ ] Publish the article on Dev.to / Substack and post to Hacker News (`Show HN`).
- [ ] **MeetSync Dummy Backlog:**
  - [ ] Resolve **Issue #3** (`[CLI] Graceful Error Handling for Unwritable Output Paths`) via isolated worktree, PR #5, and merge.
