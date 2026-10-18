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
