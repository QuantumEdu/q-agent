# Cloudroom-inspired local reliability roadmap

The Cloudroom Core review (upstream commit `bbb487e1803d12e7b6cf6e4c27da3a74fe631d5c`)
identified complementary runtime capabilities. q-agent remains an independent,
local-first methodology with optional execution tools. This is a status and scope
record, not authorization to implement all proposals or perform remote operations.

## Delivered in the 2.9.0 change set

| Proposal | Status | Evidence / boundary |
| --- | --- | --- |
| Durable task recovery | Implemented | SQLite WAL task/attempt records; abandoned runners become uncertain. No native model-conversation recovery. |
| Explicit execution states | Implemented | Pending, running, awaiting verification, failed, uncertain, verified. Human acceptance remains in the existing review workflow. |
| Evidence bound to a commit | Implemented | Full HEAD SHA, command, timestamps, log and exit code; dirty/changed checkouts cannot verify. Not a hermetic attestation. |
| Request identity and duplicate prevention | Implemented | Same request returns its receipt; conflicting reuse is rejected. Not exactly-once external effects. |
| Durable execution journal | Implemented as attempt records | Transactional local attempts and history, not a full event-sourced runtime or queued scheduler. |
| Signal/storage failure handling | Hardened | Owned-group cancellation for SIGINT/SIGTERM; real SQLite failure-injection tests; SIGKILL remains uncertain. |
| Cockpit/task-ledger integration | Implemented | Read-only live panel with execution state, commit/exit evidence, stale evidence and unavailable-ledger handling. No queue or execution controls added. |
| Bounded diagnostics | Implemented for the task runner | Size-limited private head/tail logs, recorded-log retention and two bounded fixed-field diagnostic files. Durable history and workflow audit events are preserved. |
| Resource admission checks | Implemented locally | Free-space measurement and reservation before dispatch; busy runner detection. Not continuous disk protection or machine-wide resource containment. |
| Capability detection contract | Implemented locally | Local SQLite/output/process-group primitives are probed; required unavailable capabilities block dispatch. External CLI presence is separate from native capabilities, which remain unknown without an adapter. |

## Remaining proposals

| Priority | Proposal | Next deliverable / acceptance criterion |
| --- | --- | --- |
| High for protected operations | External approval enforcement | A controller outside the agent's writable state holds scoped operation credentials; approvals identify a human, operation and commit. Agent text or retry reasons cannot grant authority. |
| High for concurrent workers | Effective isolation checks | Confirm workspace/process isolation before dispatch; reject a required isolation mode if unavailable. Git worktrees alone do not contain processes. |
| Optional remote workflow | Cloudroom backend adapter | Correlate task/session/request/commit IDs; preserve uncertain results, detect capabilities and verify isolation. No Cloudroom dependency is currently required. |

Priorities are conditional on the workflow: a single local user does not need a
remote runtime to benefit from recovery. Protected remote operations and concurrent
workers require their own implementation and verification, not just configuration.

## Release procedure

1. Open a feature/release PR into `main`; never substitute a direct push to `main`.
2. Require the repository's Python 3.10/3.11/3.12 checks and review before merging.
3. Confirm the resulting `main` commit and then create the `v2.9.0` tag/release.

The version declaration and changelog on a branch prepare a release; they do not
prove a PR merged, a tag exists or a release was published. GitHub API access is
required to automate PR/release operations and inspect remote CI.
