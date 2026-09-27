"""
Test suite for validating CLI tools execution, compilation, argument handling,
and security constraints (CORS, path traversal prevention, localhost binding).
"""

import json
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = sys.executable

# Allow importing cockpit module directly
COCKPIT_DIR = ROOT_DIR / "tools" / "q-cockpit"
if str(COCKPIT_DIR) not in sys.path:
    sys.path.insert(0, str(COCKPIT_DIR))

import q_cockpit  # noqa: E402


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

    def test_q_cockpit_help_and_options(self):
        script = ROOT_DIR / "tools" / "q-cockpit" / "q_cockpit.py"
        res = subprocess.run([PYTHON_EXE, str(script), "--help"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"q_cockpit.py --help failed: {res.stderr}")
        self.assertIn("q-cockpit", res.stdout)
        self.assertIn("serve", res.stdout)

        # Verify serve subcommand exposes --host with 127.0.0.1 default
        serve_res = subprocess.run([PYTHON_EXE, str(script), "serve", "--help"], capture_output=True, text=True)
        self.assertEqual(serve_res.returncode, 0, f"q_cockpit.py serve --help failed: {serve_res.stderr}")
        self.assertIn("--host", serve_res.stdout)
        self.assertIn("127.0.0.1", serve_res.stdout)

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


class TestCockpitSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir_obj = tempfile.TemporaryDirectory()
        cls.project_root = Path(cls.temp_dir_obj.name).resolve()

        # Create test files
        cls.valid_file = cls.project_root / "sample.txt"
        cls.valid_file.write_text("secure content", encoding="utf-8")

        # Create a nested file
        nested_dir = cls.project_root / "subdir"
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / "nested.txt").write_text("nested content", encoding="utf-8")

        # Configure handler
        q_cockpit.CockpitHTTPHandler.project_root = cls.project_root
        q_cockpit.CockpitHTTPHandler.session_manager = q_cockpit.SessionManager()
        q_cockpit.CockpitHTTPHandler.active_session_dir = None

        # Start ephemeral test server on loopback
        cls.server = q_cockpit.ThreadedTCPServer(("127.0.0.1", 0), q_cockpit.CockpitHTTPHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.temp_dir_obj.cleanup()

    def test_valid_file_served(self):
        url = f"http://127.0.0.1:{self.port}/api/file?path=sample.txt"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["content"], "secure content")

    def test_path_traversal_parent_rejected(self):
        url = f"http://127.0.0.1:{self.port}/api/file?path=../outside_secret.txt"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url)
        self.assertEqual(ctx.exception.code, 403)

    def test_path_traversal_nested_escape_rejected(self):
        url = f"http://127.0.0.1:{self.port}/api/file?path=subdir/../../outside_secret.txt"
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(url)
        self.assertEqual(ctx.exception.code, 403)

    def test_cors_rejects_external_origins(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/status",
            headers={"Origin": "https://malicious-site.example.com"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertIsNone(resp.headers.get("Access-Control-Allow-Origin"))
            self.assertNotEqual(resp.headers.get("Access-Control-Allow-Origin"), "*")

    def test_cors_allows_localhost_origins(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/status",
            headers={"Origin": "http://localhost:5173"},
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
            self.assertEqual(resp.headers.get("Vary"), "Origin")

    def test_cors_options_preflight(self):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/status",
            headers={"Origin": "http://127.0.0.1:4242"},
            method="OPTIONS",
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 204)
            self.assertEqual(resp.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:4242")
            self.assertIn("GET", resp.headers.get("Access-Control-Allow-Methods", ""))


if __name__ == "__main__":
    unittest.main()
