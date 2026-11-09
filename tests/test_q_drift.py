import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT_DIR / "tools" / "q-drift" / "q_drift.py"


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *args],
        capture_output=True, text=True, cwd=cwd or str(ROOT_DIR),
    )


def build_tree(base, blueprint_refs, extra_files=None):
    """Create a fake repo root: BLUEPRINT.md + the given real files."""
    base = Path(base)
    (base / "BLUEPRINT.md").write_text(
        "# Blueprint\n\n" + "\n".join(blueprint_refs) + "\n", encoding="utf-8"
    )
    for rel in (extra_files or []):
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("real content\n", encoding="utf-8")
    return base


class TestQDriftCLI(unittest.TestCase):
    def test_clean_tree_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_tree(tmp, [
                "See `tools/q-merge-gate/q_merge_gate.py` for the gate.",
                "Docs live in [the skill](skills/q-fuzz/SKILL.md).",
            ], extra_files=[
                "tools/q-merge-gate/q_merge_gate.py",
                "skills/q-fuzz/SKILL.md",
            ])
            proc = run_cli("--root", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["drift_found"], 0)

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_tree(tmp, [
                "See `tools/q-merge-gate/q_merge_gate.py` for the gate.",
                "See `tools/q-does-not-exist/missing.py` for the old plan.",
            ], extra_files=["tools/q-merge-gate/q_merge_gate.py"])
            proc = run_cli("--root", tmp, "--json")
            self.assertEqual(proc.returncode, 2)
            report = json.loads(proc.stdout)
            self.assertEqual(report["drift_found"], 1)
            finding = report["findings"][0]
            self.assertEqual(finding["kind"], "missing-file")
            self.assertEqual(finding["reference"],
                             "tools/q-does-not-exist/missing.py")

    def test_empty_file_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = build_tree(tmp, ["See `docs/empty.md`."],
                              extra_files=["docs/empty.md"])
            (base / "docs" / "empty.md").write_text("", encoding="utf-8")
            proc = run_cli("--root", tmp, "--json")
            self.assertEqual(proc.returncode, 2)
            report = json.loads(proc.stdout)
            self.assertEqual(report["findings"][0]["kind"], "empty-file")

    def test_human_output_lists_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_tree(tmp, ["See `tools/gone.py`."])
            proc = run_cli("--root", tmp)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("DRIFT", proc.stdout)
            self.assertIn("tools/gone.py", proc.stdout)

    def test_missing_doc_path_errors(self):
        proc = run_cli("--root", ".", "--docs", "no-such-doc.md")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("not found", proc.stderr)

    def test_no_docs_in_empty_tree_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli("--root", tmp, "--json")
            self.assertEqual(proc.returncode, 1)
            self.assertIn("error", proc.stderr.lower())

    def test_placeholders_and_ranges_are_not_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_tree(tmp, [
                "Tasks live in `odd/tasks/<feature>.md`.",
                "Dispatches 17 items (`audit/A01-A17.md`) in parallel.",
                "See `tools/q-merge-gate/q_merge_gate.py`.",
            ], extra_files=["tools/q-merge-gate/q_merge_gate.py"])
            proc = run_cli("--root", tmp, "--json")
            self.assertEqual(proc.returncode, 0)
            report = json.loads(proc.stdout)
            self.assertEqual(report["drift_found"], 0)

    def test_external_links_are_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_tree(tmp, [
                "See [EGM](https://github.com/google/elephant-goldfish-model).",
                "See `tools/q-merge-gate/q_merge_gate.py`.",
            ], extra_files=["tools/q-merge-gate/q_merge_gate.py"])
            proc = run_cli("--root", tmp, "--json")
            self.assertEqual(proc.returncode, 0)


if __name__ == "__main__":
    unittest.main()
