# Attention policy

> The scarce resource is not tokens. It is the operator's attention.

A system that can act for a whole team can also spend a whole team's attention. This
document defines when q-agent is allowed to interrupt a human, and what changes when
it stops interrupting for everything else.

## 1. The rule

Silence is the default. q-agent speaks only when a person must act, or when a result
is ready to be used. Everything else is recorded and stays quiet.

Apply the [communication contract](communication-contract.md) and the
[normative lifecycle crosswalk](../docs/communication-policy.md) to owned messages.
Explicit user status requests are pull responses, not unsolicited interruptions.
P03/P04 always record routine gates/log creation; chat requires a class below or
a status request. P07 always delivers a concise `actionable_result` with checked
facts, linked evidence and limitations. Ask one focused unresolved question, then
STOP; never ask again for already authorized work. Host-owned notices and provider
consent envelopes remain unchanged; this policy cannot intercept external output.

An interruption is legal only in one of three classes. `q_tickets.request_attention`
refuses every other value at the code level, so the policy is not a convention that
depends on a model remembering it:

| Class | When | Example |
| :--- | :--- | :--- |
| `actionable_result` | Work finished and a person can use or ship it | "PR #41 is ready for review; tests green" |
| `blocking_decision` | Progress requires a judgement only a human can make | "Two valid schemas; which one is canonical?" |
| `hard_stop` | Work cannot continue at all | "The deploy credential expired; nothing runs" |

Explicitly **not** permitted: progress updates, "I am still working", permission for
work already authorized, confirmation of an action already permitted, restating a
milestone that was already delivered.

## 2. Why three classes and not a severity scale

A severity scale (`info`, `warn`, `error`) invites the system to classify effort. The
three classes classify **the human's obligation**: use it, decide it, or fix it. If a
message does not fit one of the three, no human obligation exists, therefore no
message.

## 3. What this changes in practice

**3.1 The event log is the audit trail, not a competing task plan.** Record ticket
events through the existing store (SQLite WAL, synchronous FULL), greppable by
ticket. The active living log owns scope, task state and acceptance; reports and
events link evidence to it. Never let a report exist only as a message; write it,
then decide whether it also deserves an interruption.

**3.2 The human role moves from operator to judge.** You stop supervising execution
and start resolving the two things a machine cannot: taste and authority. The failure
mode of the previous model was attention starvation; the failure mode of this model is
being out of the loop on something that mattered. Section 4 addresses it.

**3.3 Pull replaces push.** Monitoring happens through `attention-queue`, `list` and
`show`, on demand, not through notifications. That is the only way the cost stays
sublinear: N tickets with M updates each is N×M interruptions, but one queue read is
one interruption regardless of N.

**3.4 Classification becomes a real design constraint.** The main way this policy
decays is a worker that dresses progress as `blocking_decision` because it wants
company. Mitigation: attention requests must carry a structured question and the
decision it blocks. Free text alone is not a classification.

## 4. Known risks and their mitigations

| Risk | Why it is real | Mitigation |
| :--- | :--- | :--- |
| Silent failure | A stuck ticket that never escalates burns hours invisibly | Supervise **progress**, not liveness: a watchdog compares the last report against expected work, and may escalate `hard_stop`. A process can be healthy and produce nothing. |
| Misclassification inflation | Workers over-escalate to feel safe | Structured question required; a request without a concrete decision is refused |
| Audit gap | Nobody read the log, so nobody knows what happened | `show <ticket>` and `attention-queue` are the first thing a session reads, not the last |
| Over-silence on first contact | Trust is not yet earned | Start with `accept_mode: observe`: the system records what it *would* have done. Widen only after the log looks right |
| Reintroduced noise via digests | "Daily summary" is a push channel in disguise | Digests are pull artifacts written to disk, never messages |

## 5. Relationship to execution authority

Attention is not authorization. A human answering a `blocking_decision` answers a
question; it does not widen a mandate. Widening requires a new ticket with a new
mandate (`execution-authority.md`). This separation is what stops a chat message from
becoming a permission grant.

## 6. Operating checklist

- [ ] `triggers.enabled` is false until `accept_mode: observe` has been read once.
- [ ] `allowed_senders` is a short list of people, never a team-wide scope.
- [ ] Every escalation names its class and the decision it blocks.
- [ ] `attention-queue` is read at the start of a working session.
- [ ] A ticket that has not reported in longer than its expected duration is watched
      for progress, not for a process being alive.
