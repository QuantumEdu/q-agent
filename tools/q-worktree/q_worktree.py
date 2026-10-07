#!/usr/bin/env python3
"""
q_worktree.py - Isolated Git Worktree Manager for q-agent subagents & ODD waves.

Zero external dependencies.
Inspired by the worktree isolation pattern in Super-Board (EricTechPro).

Commands:
  create   Create an isolated worktree for a task/wave in .q-worktrees/<task_id>
  list     List active worktrees and their tracking status
  remove   Safely remove a task's worktree and clean metadata
  merge    Merge task branch into target branch and prune worktree
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def run_git(args, cwd=None):
    """Run a git command and return (returncode, stdout, stderr)."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_repo_root(cwd=None):
    """Resolve git repository root."""
    code, out, _ = run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    if code != 0:
        return None
    return Path(out)


def cmd_create(args):
    repo_root = get_repo_root()
    if not repo_root:
        sys.stderr.write("Error: not inside a git repository.\n")
        return 1

    worktrees_dir = Path(args.worktree_dir) if args.worktree_dir else repo_root / ".q-worktrees"
    target_path = worktrees_dir / f"task-{args.task}"
    branch_name = f"wave/{args.task}"

    if target_path.exists():
        sys.stderr.write(f"Error: worktree path already exists: {target_path}\n")
        return 2

    base_branch = args.base
    if not base_branch:
        code, out, _ = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
        base_branch = out if code == 0 else "main"

    # Create worktree with dedicated branch
    git_args = ["worktree", "add", "-b", branch_name, str(target_path), base_branch]
    code, out, err = run_git(git_args, cwd=repo_root)
    if code != 0:
        # If branch already exists, try without -b
        git_args = ["worktree", "add", str(target_path), branch_name]
        code, out, err = run_git(git_args, cwd=repo_root)
        if code != 0:
            sys.stderr.write(f"Failed to create worktree: {err}\n")
            return 3

    result = {
        "status": "created",
        "task": args.task,
        "branch": branch_name,
        "base": base_branch,
        "path": str(target_path)
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"✅ Worktree created for task '{args.task}':")
        print(f"   Path:   {target_path}")
        print(f"   Branch: {branch_name} (from {base_branch})")

    return 0


def cmd_list(args):
    repo_root = get_repo_root()
    if not repo_root:
        sys.stderr.write("Error: not inside a git repository.\n")
        return 1

    code, out, err = run_git(["worktree", "list", "--porcelain"], cwd=repo_root)
    if code != 0:
        sys.stderr.write(f"Failed to list worktrees: {err}\n")
        return 1

    worktrees = []
    current_entry = {}
    for line in out.splitlines():
        if line.startswith("worktree "):
            if current_entry:
                worktrees.append(current_entry)
            current_entry = {"path": line.split(" ", 1)[1]}
        elif line.startswith("HEAD "):
            current_entry["head"] = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            current_entry["branch"] = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line == "bare":
            current_entry["bare"] = True

    if current_entry:
        worktrees.append(current_entry)

    # Filter to .q-worktrees or show all
    q_worktrees = [
        wt for wt in worktrees
        if ".q-worktrees" in wt.get("path", "")
    ]

    if args.json:
        print(json.dumps(q_worktrees, indent=2))
    else:
        print(f"Active q-agent worktrees ({len(q_worktrees)}):")
        if not q_worktrees:
            print("  (None active)")
        for wt in q_worktrees:
            print(f"  • Path:   {wt.get('path')}")
            print(f"    Branch: {wt.get('branch', 'detached')}")
            print(f"    HEAD:   {wt.get('head', 'unknown')[:8]}")

    return 0


def cmd_remove(args):
    repo_root = get_repo_root()
    if not repo_root:
        sys.stderr.write("Error: not inside a git repository.\n")
        return 1

    worktrees_dir = Path(args.worktree_dir) if args.worktree_dir else repo_root / ".q-worktrees"
    target_path = worktrees_dir / f"task-{args.task}"

    if not target_path.exists():
        sys.stderr.write(f"Worktree not found: {target_path}\n")
        return 1

    git_args = ["worktree", "remove", str(target_path)]
    if args.force:
        git_args.append("--force")

    code, out, err = run_git(git_args, cwd=repo_root)
    if code != 0:
        sys.stderr.write(f"Failed to remove worktree: {err}\n")
        return 2

    # Prune worktree metadata
    run_git(["worktree", "prune"], cwd=repo_root)

    result = {
        "status": "removed",
        "task": args.task,
        "path": str(target_path)
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"🗑️ Worktree removed for task '{args.task}' ({target_path})")

    return 0


def cmd_merge(args):
    repo_root = get_repo_root()
    if not repo_root:
        sys.stderr.write("Error: not inside a git repository.\n")
        return 1

    worktrees_dir = Path(args.worktree_dir) if args.worktree_dir else repo_root / ".q-worktrees"
    target_path = worktrees_dir / f"task-{args.task}"
    branch_name = f"wave/{args.task}"
    target_branch = args.target or "main"

    if not target_path.exists():
        sys.stderr.write(f"Worktree not found: {target_path}\n")
        return 1

    # First checkout target branch in main repo
    code, _, err = run_git(["checkout", target_branch], cwd=repo_root)
    if code != 0:
        sys.stderr.write(f"Cannot checkout target branch '{target_branch}': {err}\n")
        return 2

    # Merge task branch
    code, out, err = run_git(["merge", "--ff-only", branch_name], cwd=repo_root)
    if code != 0:
        # Try standard merge if ff-only is not possible
        code, out, err = run_git(["merge", branch_name, "-m", f"merge: incorporate wave/{args.task}"], cwd=repo_root)
        if code != 0:
            sys.stderr.write(f"Merge conflict or error: {err}\n")
            return 3

    # Remove worktree
    run_git(["worktree", "remove", str(target_path)], cwd=repo_root)
    run_git(["worktree", "prune"], cwd=repo_root)

    # Delete branch if requested
    if args.delete_branch:
        run_git(["branch", "-d", branch_name], cwd=repo_root)

    result = {
        "status": "merged",
        "task": args.task,
        "branch": branch_name,
        "target": target_branch
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"🔀 Task '{args.task}' merged into '{target_branch}' and worktree pruned.")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="q-agent Worktree Manager for subagent isolation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    p_create = subparsers.add_parser("create", help="Create an isolated worktree for a task")
    p_create.add_argument("--task", required=True, help="Task identifier (e.g. TASK-01, slice-auth)")
    p_create.add_argument("--base", help="Base branch (default: current HEAD)")
    p_create.add_argument("--worktree-dir", help="Custom worktree parent directory")
    p_create.add_argument("--json", action="store_true", help="Output JSON format")

    # list
    p_list = subparsers.add_parser("list", help="List active task worktrees")
    p_list.add_argument("--json", action="store_true", help="Output JSON format")

    # remove
    p_remove = subparsers.add_parser("remove", help="Remove an isolated task worktree")
    p_remove.add_argument("--task", required=True, help="Task identifier to remove")
    p_remove.add_argument("--force", action="store_true", help="Force remove worktree")
    p_remove.add_argument("--worktree-dir", help="Custom worktree parent directory")
    p_remove.add_argument("--json", action="store_true", help="Output JSON format")

    # merge
    p_merge = subparsers.add_parser("merge", help="Merge task worktree branch and prune")
    p_merge.add_argument("--task", required=True, help="Task identifier to merge")
    p_merge.add_argument("--target", default="main", help="Target branch (default: main)")
    p_merge.add_argument("--delete-branch", action="store_true", help="Delete task branch after merge")
    p_merge.add_argument("--worktree-dir", help="Custom worktree parent directory")
    p_merge.add_argument("--json", action="store_true", help="Output JSON format")

    args = parser.parse_args()

    if args.command == "create":
        return cmd_create(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "remove":
        return cmd_remove(args)
    elif args.command == "merge":
        return cmd_merge(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
