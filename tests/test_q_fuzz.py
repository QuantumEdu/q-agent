import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
TOOL_PATH = ROOT_DIR / "tools" / "q-fuzz" / "q_fuzz.py"
MERGE_GATE_DIR = ROOT_DIR / "tools" / "q-merge-gate"

sys.path.insert(0, str(MERGE_GATE_DIR))
import q_merge_gate  # noqa: E402


def load_q_fuzz():
    spec = importlib.util.spec_from_file_location("q_fuzz", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(TOOL_PATH), *args],
        capture_output=True, text=True, cwd=str(ROOT_DIR),
    )


class TestParseShortstatTarget(unittest.TestCase):
    def test_well_formed(self):
        self.assertEqual(
            q_merge_gate.parse_shortstat(" 3 files changed, 10 insertions(+), 2 deletions(-)"),
            (10, 2),
        )
        self.assertEqual(
            q_merge_gate.parse_shortstat(" 1 file changed, 1 insertion(+)"),
            (1, 0),
        )
        self.assertEqual(
            q_merge_gate.parse_shortstat(" 1 file changed, 1 deletion(-)"),
            (0, 1),
        )
        self.assertEqual(q_merge_gate.parse_shortstat(""), (0, 0))

    def test_garbage_never_raises(self):
        garbage = [
            "", " ", "insertions", "99999999999999999999 insertions(+)",
            "abc 12 insertions(+) 34 deletions(-) xyz",
            "1 insertion(+) 1 insertion(+) 2 deletions(-)",
            "\x00\xff\u00e9\U0001f600", "10 insertions(+) deletions(-)",
            "3 files changed, -5 insertions(+)",
        ]
        for value in garbage:
            with self.subTest(value=value):
                result = q_merge_gate.parse_shortstat(value)
                self.assertIsInstance(result, tuple)
                self.assertEqual(len(result), 2)
                self.assertTrue(all(isinstance(n, int) and n >= 0 for n in result))


class TestQFuzzCLI(unittest.TestCase):
    def test_list_targets(self):
        proc = run_cli("list-targets")
        self.assertEqual(proc.returncode, 0)
        self.assertIn("merge-gate-shortstat", proc.stdout)

    def test_unknown_target_errors(self):
        proc = run_cli("run", "--target", "no-such-target", "--iterations", "1")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("unknown target", proc.stderr)

    def test_fixed_seed_is_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            reports = []
            for _ in range(2):
                proc = run_cli("run", "--target", "merge-gate-shortstat",
                               "--seed", "7", "--iterations", "50", "--json",
                               "--corpus-dir", tmp + "/corpus",
                               "--repro-dir", tmp + "/repro")
                self.assertEqual(proc.returncode, 0)
                reports.append(json.loads(proc.stdout))
            self.assertEqual(reports[0]["inputs_sha256"], reports[1]["inputs_sha256"])
            self.assertEqual(reports[0]["inputs_tried"], 50)
            self.assertEqual(reports[0]["crashes_found"], 0)

    def test_budget_is_respected(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli("run", "--target", "merge-gate-shortstat",
                           "--seed", "1", "--budget", "0.3",
                           "--iterations", "1000000", "--json",
                           "--corpus-dir", tmp + "/corpus",
                           "--repro-dir", tmp + "/repro")
            self.assertIn(proc.returncode, (0, 2))
            report = json.loads(proc.stdout)
            self.assertLess(report["elapsed_seconds"], 10)
            self.assertLess(report["inputs_tried"], 1000000)

    def test_corpus_is_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            corpus = Path(tmp) / "corpus"
            proc = run_cli("run", "--target", "merge-gate-shortstat",
                           "--seed", "3", "--iterations", "20", "--json",
                           "--corpus-dir", str(corpus),
                           "--repro-dir", tmp + "/repro")
            self.assertEqual(proc.returncode, 0)
            run_file = corpus / "merge-gate-shortstat" / "run-seed-3.jsonl"
            self.assertTrue(run_file.is_file())
            lines = run_file.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 20)
            self.assertIn("input", json.loads(lines[0]))


class TestQFuzzCrashCycle(unittest.TestCase):
    """Full RED cycle with an injected fault (no real bug is fabricated)."""

    def test_injected_fault_found_deduped_and_reproduced_red(self):
        q_fuzz = load_q_fuzz()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            faulty = tmp_path / "faulty_target.py"
            faulty.write_text(
                "def explode(value):\n"
                "    if 'BOOM' in value:\n"
                "        raise ValueError('injected fault: BOOM input')\n"
                "    return (0, 0)\n",
                encoding="utf-8",
            )
            q_fuzz.TARGETS["test-faulty"] = {
                "description": "test-only injected fault",
                "loader": lambda: _load_faulty(faulty),
                "func_name": "explode",
                "check": lambda r: None,
                "seeds": ["BOOM", "ok"],
                "func_ref": f"{faulty}:explode",
            }
            try:
                report = q_fuzz.run_fuzz(
                    "test-faulty", seed=1, budget=60.0, iterations=10,
                    corpus_dir=str(tmp_path / "corpus"),
                    repro_dir=str(tmp_path / "repro"),
                )
            finally:
                q_fuzz.TARGETS.pop("test-faulty", None)
            self.assertEqual(report["exit_code"], 2)
            self.assertEqual(report["crashes_found"], 1)
            crash = report["crashes"][0]
            self.assertEqual(crash["exception"], "ValueError")
            self.assertIn("BOOM", crash["input"])
            repro = Path(crash["repro_file"])
            self.assertTrue(repro.is_file())
            # The reproducer must fail (RED) while the fault exists.
            proc = subprocess.run([sys.executable, str(repro)],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 2)
            self.assertIn("RED", proc.stdout)
            # Same seed => same crash signature (dedup is deterministic).
            q_fuzz.TARGETS["test-faulty"] = {
                "description": "test-only injected fault",
                "loader": lambda: _load_faulty(faulty),
                "func_name": "explode",
                "check": lambda r: None,
                "seeds": ["BOOM", "ok"],
                "func_ref": f"{faulty}:explode",
            }
            try:
                report2 = q_fuzz.run_fuzz(
                    "test-faulty", seed=1, budget=60.0, iterations=10,
                    corpus_dir=str(tmp_path / "corpus2"),
                    repro_dir=str(tmp_path / "repro2"),
                )
            finally:
                q_fuzz.TARGETS.pop("test-faulty", None)
            self.assertEqual(report2["crashes"][0]["signature"],
                             crash["signature"])


def _load_faulty(path):
    spec = importlib.util.spec_from_file_location("faulty_target", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    unittest.main()
