#!/usr/bin/env bash
# ==============================================================================
# q-agent Universal Runtime Linker
# Links this canonical repository into AGY, Codex, Pi, Claude Code, and OpenCode.
# Single Source of Truth architecture: updates via `git pull` propagate instantly.
# ==============================================================================
set -euo pipefail

SKILL_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ACTION="install"
FORCE_ALL=0

# Colors for terminal output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Runtime definitions: [Name]|ParentDir|SkillTargetDir
RUNTIMES=(
    "Antigravity (AGY)|${HOME}/.gemini|${HOME}/.gemini/config/skills/q-agent"
    "OpenAI Codex|${HOME}/.codex|${HOME}/.codex/skills/q-agent"
    "Pi (Oh My Pi)|${HOME}/.pi|${HOME}/.pi/agent/skills/q-agent"
    "Claude Code|${HOME}/.claude|${HOME}/.claude/skills/q-agent"
    "OpenCode|${HOME}/.config/opencode|${HOME}/.config/opencode/skills/q-agent"
)

usage() {
    echo "Usage: ./install.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all         Link to all supported runtimes, even if parent dir is missing"
    echo "  --check       Verify status of symlinks without making changes"
    echo "  --uninstall   Remove q-agent symlinks from all runtimes"
    echo "  -h, --help    Show this help message"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)
            FORCE_ALL=1
            shift
            ;;
        --check)
            ACTION="check"
            shift
            ;;
        --uninstall|--unlink)
            ACTION="uninstall"
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

echo -e "\n${BLUE}⚡ q-agent Universal Runtime Linker${NC}"
echo -e "   Source Repository: ${GREEN}${SKILL_ROOT}${NC}\n"

case "$ACTION" in
    check)
        echo "Inspecting active runtimes and symlink integrity:"
        for entry in "${RUNTIMES[@]}"; do
            IFS='|' read -r name parent target <<< "$entry"
            if [[ -L "$target" ]]; then
                actual_link="$(readlink "$target")"
                if [[ "$actual_link" == "$SKILL_ROOT" ]]; then
                    echo -e "  [${GREEN}OK${NC}] $name ➜ ${target} (linked to repo)"
                else
                    echo -e "  [${YELLOW}DRIFT${NC}] $name ➜ ${target} (points to ${actual_link})"
                fi
            elif [[ -d "$target" ]]; then
                echo -e "  [${YELLOW}STATIC${NC}] $name ➜ ${target} (static directory, not linked)"
            elif [[ -d "$parent" ]]; then
                echo -e "  [${BLUE}READY${NC}] $name ➜ Runtime installed, skill not yet linked"
            else
                echo -e "  [--] $name ➜ Runtime not present (${parent})"
            fi
        done
        echo ""
        ;;

    uninstall)
        echo "Removing q-agent symlinks from detected runtimes:"
        for entry in "${RUNTIMES[@]}"; do
            IFS='|' read -r name parent target <<< "$entry"
            if [[ -L "$target" ]]; then
                rm -f "$target"
                echo -e "  [${GREEN}REMOVED${NC}] $name symlink removed (${target})"
            fi
        done
        echo -e "\n${GREEN}Unlink completed successfully.${NC}\n"
        ;;

    install)
        linked_count=0
        for entry in "${RUNTIMES[@]}"; do
            IFS='|' read -r name parent target <<< "$entry"
            
            # Check if runtime exists or --all is requested
            if [[ -d "$parent" || $FORCE_ALL -eq 1 ]]; then
                target_parent="$(dirname "$target")"
                mkdir -p "$target_parent"

                # Backup existing static directory if not already a symlink
                if [[ -d "$target" && ! -L "$target" ]]; then
                    backup_dir="${target}.bak.$(date +%s)"
                    echo -e "  [${YELLOW}BACKUP${NC}] Moving static directory to ${backup_dir}"
                    mv "$target" "$backup_dir"
                fi

                # Create idempotent symlink
                ln -sfn "$SKILL_ROOT" "$target"
                echo -e "  [${GREEN}LINKED${NC}] $name ➜ ${target}"
                ((linked_count++))
            else
                echo -e "  [${BLUE}SKIPPED${NC}] $name (Runtime directory ${parent} not present)"
            fi
        done

        echo -e "\n${GREEN}✓ q-agent successfully linked to ${linked_count} runtime(s).${NC}"
        echo -e "Any future 'git pull' in ${SKILL_ROOT} will reflect instantly across all agents.\n"
        ;;
esac
