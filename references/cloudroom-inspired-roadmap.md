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

## Remaining proposals

| Priority | Proposal | Next deliverable / acceptance criterion |
| --- | --- | --- |
| High for protected operations | External approval enforcement | A controller outside the agent's writable state holds scoped operation credentials; approvals identify a human, operation and commit. Agent text or retry reasons cannot grant authority. |
| High for concurrent workers | Effective isolation checks | Confirm workspace/process isolation before dispatch; reject a required isolation mode if unavailable. Git worktrees alone do not contain processes. |
| Medium | Backend capability detection | Report verified cancellation, recovery, delegation and isolation capabilities; missing capabilities cannot silently become enabled. |
| Medium | Bounded/redacted diagnostics | Bound disk use and separate ordinary diagnostics from private command output; retention and redaction tests required. Current logs are private, not size-bounded. |
| Conditional on heavy local work | Resource admission checks | Check free space and active workloads before costly commands; distinguish unavailable measurements from safe capacity. No cgroup/disk enforcement is currently delivered. |
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
