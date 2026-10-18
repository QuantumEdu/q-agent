# Local task recovery

Use the installed `q-agent` launcher, or `<SKILL_ROOT>/bin/q-agent`, from the
project repository. Python 3.10+, SQLite (stdlib), Git and POSIX process groups
are required. Linux is tested; macOS uses the same POSIX facilities but has not
been validated in the release checks. Native Windows is unsupported. No Cloudroom, model account or
background service is needed. Existing Markdown task logs remain authoritative
for scope, acceptance criteria, reviews and human decisions.

Add `.cache/` to the project's ignore policy before recording verification.
Runtime data lives in `.cache/q-agent-tasks/`: transactional SQLite WAL state
with FULL synchronization and a five-second busy timeout, plus private command
logs. Keep that directory local, back it up with SQLite's backup API or after
closing all task commands, and never commit its database/WAL or logs. Logs and
command arguments can contain private data; never pass credentials as arguments.

```sh
q-agent task add TASK-01 "Implement the accepted local feature"
q-agent task run TASK-01 --request-id implement-01 --timeout 300 -- python3 implement.py
q-agent resume
# Inspect the diff and commit the implementation before commit-bound verification.
q-agent task verify TASK-01 --request-id verify-01 -- python3 -m unittest discover -s tests -v
q-agent task history TASK-01
q-agent task preflight
q-agent capabilities --backend local
```

Commands are argv arrays, not shell strings. Explicit shell scripts are supported
only when intentionally invoked. They run at the Git root, noninteractively, with
stdout/stderr in the reported log path. Timeout defaults to 300 seconds and must
be positive and at most 900 seconds. Commands inherit the caller's permissions;
this utility grants no new authority and is not a sandbox. It is for finite
commands: their remaining process-group descendants are stopped at command end.
Detached descendants that escape the process group are not contained.
SIGINT and SIGTERM request cancellation: the owned process group is stopped,
the child's actual exit code is retained, and the attempt remains `uncertain`.
SIGKILL and a power loss cannot run cleanup and may leave external effects or
children alive; recovery never assumes those effects can be repeated safely.

## Resource admission and bounded diagnostics

Every new `run`/`verify` measures free space on the project filesystem before
dispatch, with a default reserve of 256 MiB. `--min-free-mib N` changes that
reserve (zero still requires a valid measurement). Missing measurements block
dispatch. `preflight` reports current capacity and whether this runner's lock
is busy; it does not inventory unrelated processes, impose RAM/CPU limits or
monitor disk consumption continuously. The execution lock serializes local tasks.

New command logs retain their beginning and end within 8 MiB by default;
`--max-log-mib N` allows 1..64 MiB. Excess bytes are drained rather than blocking
the command, and receipts record `output_bytes`/`output_truncated`. Before a new
dispatch, the seven newest existing recorded logs are retained, so the new log
brings the normal total to eight. Older eligible UUID-named regular logs are
removed; receipt history, unrecognized files, symlinks and hardlinks are preserved.
Historical logs may already exceed the new per-attempt limit. Raw output stays
private and is not automatically redacted; inspect it before sharing.

`diagnostics.jsonl` and one previous file are capped at 256 KiB each. These
best-effort records allow only fixed operation/state names and numeric outcome/
output fields; no command arguments, task titles, IDs, paths or raw output.
Diagnostic failure cannot erase a durable task result. Workflow audit events,
SQLite history and the cockpit's session records are not discarded or rotated.
State schema upgrades add nullable columns and preserve existing receipts.

## Capability contract

`q-agent capabilities` (or `q-agent task capabilities`) probes the local runner
without inference, login checks or account access. `durable_receipts` exercises
SQLite WAL commit/reopen in a temporary directory; `process_group_cancellation`
starts and terminates a fresh owned process group; `bounded_output` exercises the
actual output limiter. These checks do not attest the project's filesystem,
power-loss durability, native model sessions or containment of escaped children.

`--backend codex|claude|pi` checks executable presence only. Native cancellation,
recovery, delegation and isolation remain `unknown` without a verified adapter;
the report never converts installation into protocol support. Local native
conversation resume, delegation, workspace isolation and process containment
are explicitly `unsupported`.

New commands may require a verified local primitive before any receipt/dispatch:

```sh
q-agent task run TASK-01 --request-id implement-03 \
  --require-capability bounded_output --require-capability process_group_cancellation \
  -- python3 implement.py
```

Unsupported, unknown or failed required capabilities block execution. Requirements
and resource/output settings are part of request identity; changing them requires
a new request ID and any applicable retry authority. Capability probes neither
grant permission nor install tools, create workers or contact model providers.

`q-agent task --project /path/to/project add TASK-01 "Title"` targets another
checkout; `q-agent resume --project /path/to/project` inspects it. Each checkout
has independent state. A local file lock serializes command execution and retry
decisions. It does not coordinate other Git writers, other tools or network hosts.

## State and recovery contract

| State | Meaning / next action |
| --- | --- |
| `pending` | Task registered; dispatch only within existing authorization. |
| `running` | A command is active under the runner lock; observe it. |
| `awaiting_verification` | Work command exited zero; commit and verify it. |
| `failed` | Command exited nonzero; inspect its log and effects. |
| `uncertain` | Runner disappeared, execution was interrupted, or verification changed the checkout; inspect before retry. |
| `verified` | Verification exited zero against an unchanged, clean commit; acceptance/review gates still apply. |

`resume` never runs a command. If the runner lock is free, abandoned `running`
attempts become `uncertain`. An active runner is preserved. A crash can leave
children or external effects alive: saved PIDs are informational, never authority
to kill a process. Inspect live processes, logs, Git and external effects first.
Then, only with authority to retry, explicitly record that inspection:

```sh
q-agent task retry TASK-01 --reason "Inspected effects and live processes; retry authorized"
q-agent task run TASK-01 --request-id implement-02 -- python3 implement.py
```

Repeating an existing request ID with identical task, operation, argv and timeout
returns the stored attempt without execution. Conflicting reuse is rejected.
An uncertain or failed task cannot dispatch a new command until explicit retry.
`retry` records a reason; it does not prove authorization or exactly-once external
effects. Never use it to bypass a human gate. All attempts remain inspectable.

Verification stores the full HEAD SHA, argv, timestamps, exit code and log path.
Dirty tracked/untracked files block verification; changes during a check prevent
`verified`. After HEAD or cleanliness changes, `resume` flags existing evidence
as stale. Ignored artifacts, dependencies, environment variables and transient
changes reverted during a check are outside this Git comparison; this is not a
hermetic build attestation. Run meaningful checks and inspect their actual output.
Exit codes: 0 = recorded success/report, 1 = failed/uncertain attempt, 2 = rejected
input, busy runner or storage/Git failure. Stored command exit codes are separate.

## Storage failure checks

The regression suite injects real SQLite trigger failures at receipt creation,
PID persistence and final-result persistence. A failed receipt prevents dispatch;
a failed result cannot become successful verification. If recovery cannot write,
it returns an error until storage is repaired. These tests exercise transaction
failures, not a physical full disk, filesystem corruption or power-loss simulation.

See [the Cloudroom-inspired roadmap](cloudroom-inspired-roadmap.md) for the
implemented features and remaining proposals. No Cloudroom service code is bundled.
