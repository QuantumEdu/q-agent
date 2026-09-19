"""
Test suite for validating CLI tools execution, compilation, and argument handling.
"""

from pathlib import Path
import py_compile
import subprocess
import sys
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable


class TestToolsExecution(unittest.TestCase):
    def test_all_python_tools_compile(self):
        tools_dir = ROOT_DIR / "tools"
        python_files = list(tools_dir.glob("**/*.py"))
        self.assertGreater(len(python_files), 0, "There should be python tools in tools/")

        for py_file in python_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
            except py_compile.PyCompileError as e:
                self.fail(f"Failed to compile {py_file}: {e}")

    def test_q_cockpit_help(self):
        script = ROOT_DIR / "tools" / "q-cockpit" / "q_cockpit.py"
        res = subprocess.run([PYTHON_EXE, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"q_cockpit.py --help failed: {res.stderr}")
        self.assertIn("q-cockpit", res.stdout)
        self.assertIn("serve", res.stdout)

    def test_q_checklist_help(self):
        script = ROOT_DIR / "tools" / "q-checklist" / "q_checklist.py"
        res = subprocess.run([PYTHON_EXE, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"q_checklist.py --help failed: {res.stderr}")
        self.assertIn("q-checklist", res.stdout)

    def test_generate_report_help(self):
        script = ROOT_DIR / "tools" / "q-audit-aggregator" / "generate_report.py"
        res = subprocess.run([PYTHON_EXE, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"generate_report.py --help failed: {res.stderr}")
        self.assertIn("q-audit-aggregator", res.stdout)

    def test_validate_audit_help(self):
        script = ROOT_DIR / "tools" / "q-audit-validator" / "validate_audit.py"
        res = subprocess.run([PYTHON_EXE, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"validate_audit.py --help failed: {res.stderr}")
        self.assertIn("q-audit-validator", res.stdout)


if __name__ == "__main__":
    unittest.main()
