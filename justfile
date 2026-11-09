# q-agent development and orchestration recipes
# Zero external runtime dependencies · Uses just runner

# Default recipe: list available recipes
default:
    @just --list

# Link q-agent into all detected AI runtimes (AGY, Codex, Pi, Claude Code, OpenCode, GitHub Copilot)
install:
    @./install.sh

# Force link to all runtimes (even if parent directory does not exist yet)
install-all:
    @./install.sh --all

# Check active symlinks and runtime installation status
check:
    @./install.sh --check

# Unlink q-agent from all agent runtimes
uninstall:
    @./install.sh --uninstall

# Run official test suite
test:
    python3 -m unittest discover -s tests

# Launch visual elicitation & mission cockpit (enhanced q-cockpit web UI)
cockpit PORT="4242":
    python3 tools/q-cockpit/q_cockpit_plus.py serve --port {{PORT}}

# Launch the legacy-compatible cockpit entrypoint
cockpit-legacy PORT="4242":
    python3 tools/q-cockpit/q_cockpit.py serve --port {{PORT}}

# Launch enhanced cockpit with snapshots, structured events, and recovery commands
cockpit-plus PORT="4242":
    python3 tools/q-cockpit/q_cockpit_plus.py serve --port {{PORT}}

# Run the shared action catalog
cockpit-actions:
    python3 tools/q-cockpit/q_cockpit_plus.py actions

# Launch interactive Terminal User Interface (q-cockpit TUI)
cockpit-tui:
    python3 tools/q-cockpit/q_cockpit_tui.py

# Run deterministic local performance benchmark
benchmark ITERATIONS="3":
    python3 tools/q-benchmark/benchmark.py --project . --iterations {{ITERATIONS}} --json

# Run lifecycle-aware Plan C audit and evidence index
run-audit LEVEL="2":
    python3 tools/q-audit-runner/run_audit.py --cwd . --level {{LEVEL}}

# Run interactive pre-flight architectural decision matrix (CLI TUI)
checklist:
    python3 tools/q-checklist/q_checklist.py

# Run deterministic technical contracts audit gate (Disaster Recovery, CI, Observability, API)
audit-contracts CWD=".":
    python3 tools/q-audit-validator/validate_audit.py --mode technical --cwd {{CWD}}

# Check cockpit session health
cockpit-health:
    python3 tools/q-cockpit/q_cockpit_plus.py health

# Run deterministic merge policy gate against base branch
merge-gate BASE="main" MAX_LOC="500":
    python3 tools/q-merge-gate/q_merge_gate.py --base {{BASE}} --max-loc {{MAX_LOC}}

# Run bounded seed-driven fuzz on a registered target (advisory; never blocks on "no crash found")
fuzz TARGET="merge-gate-shortstat" SEED="1" BUDGET="60":
    python3 tools/q-fuzz/q_fuzz.py run --target {{TARGET}} --seed {{SEED}} --budget {{BUDGET}}

# List registered fuzz targets
fuzz-targets:
    python3 tools/q-fuzz/q_fuzz.py list-targets

# Report drift between checked-in docs (BLUEPRINT.md, docs/designs) and the real tree
drift:
    python3 tools/q-drift/q_drift.py --root .

# List active subagent git worktrees
worktrees:
    python3 tools/q-worktree/q_worktree.py list

# Aggregate local agent transcripts (codex | agy | opencode | all | <jsonl dir>)
skill-doctor-ingest SOURCE="all" LIMIT="25":
    python3 tools/q-skill-doctor/skill_doctor.py --root . ingest --source {{SOURCE}} --limit {{LIMIT}}

# Score the conversation corpus against the fixed rubric
skill-doctor-score:
    python3 tools/q-skill-doctor/skill_doctor.py --root . score

# Write skill improvement proposals as drafts (never edits a SKILL.md)
skill-doctor-report:
    python3 tools/q-skill-doctor/skill_doctor.py --root . report --out .q-agent/skill-doctor/proposals

# List every ticket in the durable store
tickets:
    python3 tools/q-tickets/q_tickets.py list

# Show what actually needs a human decision right now
attention:
    python3 tools/q-tickets/q_tickets.py attention-queue

# Poll GitHub events in observe mode: records candidates, opens no tickets
triggers-poll LIMIT="20":
    python3 tools/q-triggers/q_triggers.py poll --observe --limit {{LIMIT}}

# Print the resolved trigger policy for the current project
triggers-status:
    python3 tools/q-triggers/q_triggers.py status
