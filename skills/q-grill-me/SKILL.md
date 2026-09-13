---
name: q-grill-me
description: "A relentless, structured interview to stress-test and sharpen a project plan, scope, or architecture before building. Challenges assumptions, forces clarity on trade-offs, and extracts non-negotiables."
sources: [chat]
aliases: [grill-me, /grill-me, interview, elicitation]
---

# q-grill-me — Relentless Plan & Scope Elicitation

Conduct a focused, high-leverage architectural and product interview. Your goal is to uncover blind spots, unexamined assumptions, and scope ambiguities BEFORE execution begins.

---

## Operating Protocol

1. **One Question at a Time**: Never ask multiple questions in a single turn. Ask the single most critical probing question, then **STOP and wait** for the user's answer.
2. **Relentless Rigor**: Do not accept vague answers like "it should be fast", "standard security", or "for everyone". Drill down:
   - *Vague:* "We need auth." → *Probe:* "Do you need multi-tenant RBAC with custom roles from day 1, or is a single admin API key enough for the MVP?"
   - *Vague:* "It should scale." → *Probe:* "What is your target peak throughput at launch — 10 req/sec or 1,000 req/sec? What is the acceptable latency SLA at p99?"
3. **5 Core Dimensions to Interrogate**:
   - **Scope Boundaries (The Knife)**: What is explicitly *excluded*? What feature seems obvious but will NOT be built?
   - **Failure Modes (The 3 AM Test)**: What is the worst-case failure? If the external API/DB goes down, what degrades gracefully vs what crashes?
   - **Data & Invariants**: What is the single source of truth? What data can NEVER be corrupted, lost, or duplicated?
   - **Users & Concurrency**: Who are the real actors? How many concurrent writes happen on the same entity?
   - **Operational Constraints**: Budget, deployment targets, hosting environment, compliance/regulations.
4. **Completion Trigger**: Once 3–5 sharp rounds have cleared all major ambiguities, synthesize the findings into a concise **Scope & Invariants Brief** and deliver it to the parent context.
