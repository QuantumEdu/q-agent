"""
Unit tests for tools/q-worktree/q_worktree.py
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
WORKTREE_DIR = ROOT_DIR / "tools" / "q-worktree"
if str(WORKTREE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKTREE_DIR))

import q_worktree


class TestQWorktree(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_dir = Path(self.test_dir.name)

        # Initialize git repo with initial commit
        q_worktree.run_git(["init", "-b", "main"], cwd=self.repo_dir)
        q_worktree.run_git(["config", "user.name", "Test User"], cwd=self.repo_dir)
        q_worktree.run_git(["config", "user.email", "test@example.com"], cwd=self.repo_dir)

        # Create dummy file and commit
        dummy_file = self.repo_dir / "README.md"
        dummy_file.write_text("# Initial\n", encoding="utf-8")
        q_worktree.run_git(["add", "README.md"], cwd=self.repo_dir)
        q_worktree.run_git(["commit", "-m", "init: initial commit"], cwd=self.repo_dir)

        # Save and switch working directory
        self.orig_cwd = os.getcwd()
        os.chdir(self.repo_dir)

    def tearDown(self):
        os.chdir(self.orig_cwd)
        self.test_dir.cleanup()

    def test_worktree_lifecycle(self):
        # 1. Create worktree
        class ArgsCreate:
            task = "TASK-01"
            base = "main"
            worktree_dir = None
            json = True

        res = q_worktree.cmd_create(ArgsCreate())
        self.assertEqual(res, 0)

        expected_wt = self.repo_dir / ".q-worktrees" / "task-TASK-01"
        self.assertTrue(expected_wt.exists())

        # 2. List worktrees
        class ArgsList:
            json = True

        res_list = q_worktree.cmd_list(ArgsList())
        self.assertEqual(res_list, 0)

        # 3. Add file in worktree
        feature_file = expected_wt / "feature.txt"
        feature_file.write_text("hello wave\n", encoding="utf-8")
        q_worktree.run_git(["add", "feature.txt"], cwd=expected_wt)
        q_worktree.run_git(["commit", "-m", "feat: wave task"], cwd=expected_wt)

        # 4. Merge worktree
        class ArgsMerge:
            task = "TASK-01"
            target = "main"
            delete_branch = True
            worktree_dir = None
            json = True

        res_merge = q_worktree.cmd_merge(ArgsMerge())
        self.assertEqual(res_merge, 0)

        # Verify file is now in main repo
        merged_file = self.repo_dir / "feature.txt"
        self.assertTrue(merged_file.exists())
        self.assertFalse(expected_wt.exists())


if __name__ == "__main__":
    unittest.main()
