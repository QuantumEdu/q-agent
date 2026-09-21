# q-agent development and orchestration recipes
# Zero external runtime dependencies · Uses just runner

# Default recipe: list available recipes
default:
    @just --list

# Link q-agent into all detected AI runtimes (AGY, Codex, Pi, Claude Code, OpenCode)
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

# Launch visual elicitation & mission cockpit (q-cockpit web UI)
cockpit PORT="4242":
    python3 tools/q-cockpit/q_cockpit.py serve --port {{PORT}}

# Run interactive pre-flight architectural decision matrix (CLI TUI)
checklist:
    python3 tools/q-checklist/q_checklist.py
