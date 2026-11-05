# Communication provenance contract

Record routine activity; interrupt a person only for an actionable result, a
blocking decision, a hard stop, or an explicit request for status. This contract
applies to q-agent-owned output, not arbitrary host, model or harness messages.

## Actor attribution

An LLM can follow the q-agent workflow inside a host using a separate harness.
These are independent facts, not mutually exclusive identities:

| Field | Meaning |
| --- | --- |
| `emitter.kind` | `llm`, `tool`, `host`, `harness`, or `unknown`. |
| `emitter.name` | Known producer of this record; null when unknown. |
| `workflow` | Procedure actually being followed, distinct from its executor. |
| `executor` | Component that performed the referenced action, if known. |
| `host` | Known conversation/runtime environment; installation is not evidence. |
| `orchestrator` | Known orchestration layer; do not assume Gentle AI is involved. |
| `phase` | Explicit lifecycle phase; never infer it from a heuristic UI highlight. |
| `lifecycle` | `configured`, `loaded`, `invoked`, `executed`, `verified`, or `unknown`. |

Configured availability is not loading; loading instructions is not invocation;
invocation is not completion; execution is not successful verification. A record
being written does not prove its referenced action ran. Current commit-bound proof
can establish verification; stale proof must not be shown as current verification.

Producers own attribution fields and must not let an ordinary event payload
overwrite them. Missing historical metadata remains unknown. Stored attribution is
local recorded evidence, not authenticated identity or an authorization mechanism.
Do not claim interception or control of OpenCode/Gentle AI/provider-owned notices.

## Timestamp and compact display

New native records obtain timezone-aware ISO 8601 timestamps from the real runtime
clock. Preserve valid historical timestamps; absent, malformed or timezone-less
times remain unavailable. A reader must never replace missing event time with now.
Record source as `runtime_clock`, `recorded`, or `unavailable` in `timestamp_source`.
If only receipt time is known, label it receipt time rather than execution time.

Compact human display: `[HH:mm:ss ±HH:mm] [emitter | workflow | phase] message`.
Use an explicit unknown/time-unavailable label when evidence is absent. Full date,
timezone and available correlation remain in the record or detail view. An LLM
must use a host/tool clock or supplied event timestamp, never invent a clock value.
Preserve provider-owned blocking envelopes unchanged rather than rebranding them.

## Additive native record fields

Reuse current timestamps, correlation IDs, JSONL stores and read-only ledger views.
The optional `provenance` object uses the actor fields above; nullable scalar fields
use null, `emitter.kind` and `lifecycle` use `unknown` for unavailable information.
Existing event keys, API fields, CLI stdout/stderr/exit behavior and SQLite formats
remain compatible. Old records lacking this object are accepted, not rewritten.

The optional `telemetry` object contains `tokens` and `cost` measurements. Each has
`status`, `value`, `source`, and `basis`; cost may also carry `currency`:

- `measured`: nonnegative finite value and an actual source.
- `estimated`: nonnegative finite value, identified source and explicit basis.
- `unavailable`: null value, without implying zero or free execution.

No provider token/cost collector is introduced by this feature. Do not infer usage
from command type or successful execution. Existing observed exit/status/time data
remain evidence; uninstrumented provider usage is unavailable even at enterprise
level. Never fabricate metrics to close a report.

## Lifecycle and artifact authority

Use semantic phase names alongside an explicit stage-to-prompt crosswalk. Keep
existing prompt filenames and legacy variants available; do not silently equate
Step N with every file named PN. The active living task log owns scope, task state,
acceptance and decisions. Blueprint, audit, verification and delivery reports are
linked evidence, not competing copies of task state. Explicit large/legacy variants
must identify their authoritative scope document.

P03/P04 record routine gate/log creation without mandatory redundant chat. Present
scope or engine information when a decision/review is needed or status is requested.
P07 delivers a concise checked-facts result with outstanding limitations. Autonomous
mode changes pacing, never authority; a blocking answer does not widen permissions.

## Cockpit boundary

Display compact timestamps and provenance from a bounded public projection, not
raw session JSONL. Do not expose answers, notes, feedback, command arguments/output,
log paths, private receipt contents or arbitrary event payloads. Metadata labels
are bounded text and must never become HTML. Reject event-file symlink escapes and
malformed records safely; GET must not create stores, run tasks or alter records.

Use actual task evidence for execution/verification labels. Skill discovery and
legacy phase fallbacks cannot establish those states. Framework/footer version
comes from the serving package, not the audited project's version or a stale literal.
Legacy events and unsupported host integrations remain visibly unknown. The cockpit
must not display unavailable tokens/cost as zero. Reuse the existing local execution
panel and event stores rather than creating a second ledger or billing system.
