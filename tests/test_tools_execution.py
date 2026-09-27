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

    def test_q_cockpit_tui_compiles_and_clean_exit(self):
        script = ROOT_DIR / "tools" / "q-cockpit" / "q_cockpit_tui.py"
        self.assertTrue(script.is_file(), f"{script} must exist")

        # Test compilation
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as e:
            self.fail(f"Failed to compile {script}: {e}")

        # Test --help exit 0
        help_res = subprocess.run([PYTHON_EXE, str(script), "--help"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(help_res.returncode, 0, f"q_cockpit_tui.py --help failed: {help_res.stderr}")
        self.assertIn("q-cockpit TUI", help_res.stdout)
        self.assertIn("--view", help_res.stdout)

        # Test --once non-interactive exit 0
        once_res = subprocess.run([PYTHON_EXE, str(script), "--once"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(once_res.returncode, 0, f"q_cockpit_tui.py --once failed: {once_res.stderr}")
        self.assertIn("Q-COCKPIT TUI", once_res.stdout)


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

    def test_diff_api_stats_returned(self):
        url = f"http://127.0.0.1:{self.port}/api/diff"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("diff", data)
            self.assertIn("stats", data)
            self.assertIn("total_loc", data["stats"])
            self.assertIn("files_changed", data["stats"])

    def test_status_api_idle_mode_and_version(self):
        url = f"http://127.0.0.1:{self.port}/api/status"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("project", data)
            self.assertEqual(data["project"]["status"], "idle")
            self.assertIsNone(data["project"]["active_phase"])
            self.assertEqual(data["tasks"], [])
            self.assertIn("version", data["project"])

    def test_serve_visual_blueprint_fallback(self):
        url = f"http://127.0.0.1:{self.port}/visual"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            html_text = resp.read().decode("utf-8")
            self.assertIn("Blueprint de Arquitectura", html_text)
            self.assertIn("Vista Arquitectónica", html_text)

    def test_serve_visual_mermaid_rendering(self):
        readme = self.project_root / "README.md"
        readme.write_text("# Project\n```mermaid\ngraph TD;\nA-->B;\n```\n", encoding="utf-8")
        try:
            url = f"http://127.0.0.1:{self.port}/visual"
            with urllib.request.urlopen(url) as resp:
                self.assertEqual(resp.status, 200)
                html_text = resp.read().decode("utf-8")
                self.assertIn("mermaid", html_text.lower())
                self.assertIn("A--&gt;B", html_text)
                self.assertIn("zoom-btn", html_text)
                self.assertIn("zoomDiagram", html_text)
                self.assertIn("fitDiagram", html_text)
                self.assertIn("toggleFullscreen", html_text)
                self.assertIn("diagram-viewport", html_text)
                self.assertIn("zoom-val-0", html_text)
        finally:
            if readme.exists():
                readme.unlink()

    def test_skillvault_api_disabled_state(self):
        url = f"http://127.0.0.1:{self.port}/api/skillvault"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("enabled", data)
            self.assertIn("status", data)
            self.assertIn("skills", data)
            self.assertFalse(data["enabled"])
            self.assertEqual(data["status"], "disabled")
            self.assertEqual(data["skills"], [])

    def test_skillvault_api_enabled_state(self):
        # Configure .q-agent.json with skillvault enabled in temp project root
        config_file = self.project_root / ".q-agent.json"
        skills_dir = self.project_root / "test_skills" / "demo-skill"
        skills_dir.mkdir(parents=True, exist_ok=True)
        skill_md = skills_dir / "SKILL.md"
        skill_md.write_text(
            "---\n"
            "name: test:demo-skill\n"
            "description: Test skill for SkillVault\n"
            "metadata:\n"
            "  version: '2.1.0'\n"
            "---\n\n"
            "# Demo Skill\n"
            "This is test content.\n",
            encoding="utf-8"
        )

        config_data = {
            "context_retrieval": {
                "providers": {
                    "skillvault": {
                        "enabled": True,
                        "path": "test_skills"
                    }
                }
            }
        }
        config_file.write_text(json.dumps(config_data), encoding="utf-8")

        try:
            url = f"http://127.0.0.1:{self.port}/api/skillvault"
            with urllib.request.urlopen(url) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data["enabled"])
                self.assertEqual(data["status"], "active")
                self.assertEqual(len(data["skills"]), 1)
                sk = data["skills"][0]
                self.assertEqual(sk["name"], "test:demo-skill")
                self.assertEqual(sk["description"], "Test skill for SkillVault")
                self.assertEqual(sk["version"], "2.1.0")
                self.assertIn("test_skills/demo-skill/SKILL.md", sk["path"].replace("\\", "/"))
                self.assertIn("Demo Skill", sk["content"])
        finally:
            if config_file.exists():
                config_file.unlink()
            if skill_md.exists():
                skill_md.unlink()
            if skills_dir.exists():
                skills_dir.rmdir()
            if (self.project_root / "test_skills").exists():
                (self.project_root / "test_skills").rmdir()


class TestCockpitScanner(unittest.TestCase):
    def test_scan_tasks_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            tasks = q_cockpit.ProjectScanner.scan_tasks(tmp_root)
            self.assertEqual(tasks, [], "Empty directory must return empty task list [] without fake mocks")

    def test_scan_tasks_with_odd_bitacora(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            odd_tasks_dir = tmp_root / "odd" / "tasks"
            odd_tasks_dir.mkdir(parents=True)
            task_file = odd_tasks_dir / "cockpit-test.md"
            task_file.write_text(
                "# Bitácora\n"
                "- [ ] TASK-01 Initial setup\n"
                "- [~] TASK-02 In progress feature\n"
                "- [x] TASK-03 Completed task (Commit: abc1234)\n",
                encoding="utf-8"
            )
            tasks = q_cockpit.ProjectScanner.scan_tasks(tmp_root)
            self.assertEqual(len(tasks), 3)
            self.assertEqual(tasks[0]["task_id"], "TASK-01")
            self.assertEqual(tasks[0]["status"], "todo")
            self.assertEqual(tasks[1]["task_id"], "TASK-02")
            self.assertEqual(tasks[1]["status"], "in_progress")
            self.assertEqual(tasks[2]["task_id"], "TASK-03")
            self.assertEqual(tasks[2]["status"], "done")
            self.assertEqual(tasks[2]["commit"], "abc1234")

    def test_scan_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            (tmp_root / "CONSTITUTION.md").write_text("# Constitution", encoding="utf-8")
            (tmp_root / "README.md").write_text("# Readme", encoding="utf-8")
            (tmp_root / "SKILL.md").write_text("# Skill", encoding="utf-8")
            (tmp_root / "CHANGELOG.md").write_text("# Changelog", encoding="utf-8")

            ref_dir = tmp_root / "references"
            ref_dir.mkdir(parents=True)
            (ref_dir / "audit-manifest.yml").write_text("manifest: 1.0", encoding="utf-8")

            odd_tasks_dir = tmp_root / "odd" / "tasks"
            odd_tasks_dir.mkdir(parents=True)
            (odd_tasks_dir / "feature-real.md").write_text("# Feature Real", encoding="utf-8")

            audit_dir = tmp_root / "audit"
            audit_dir.mkdir(parents=True)
            (audit_dir / "A01-arch.md").write_text("# Audit A01", encoding="utf-8")

            docs_dir = tmp_root / "docs" / "architecture"
            docs_dir.mkdir(parents=True)
            (docs_dir / "adr-001.md").write_text("# ADR 001", encoding="utf-8")

            artifacts = q_cockpit.ProjectScanner.scan_artifacts(tmp_root)
            paths = [a["path"] for a in artifacts]

            self.assertIn("CONSTITUTION.md", paths)
            self.assertIn("README.md", paths)
            self.assertIn("SKILL.md", paths)
            self.assertIn("CHANGELOG.md", paths)
            self.assertIn("references/audit-manifest.yml", paths)
            self.assertIn("odd/tasks/feature-real.md", paths)
            self.assertIn("audit/A01-arch.md", paths)
            self.assertIn("docs/architecture/adr-001.md", paths)

            for art in artifacts:
                self.assertIn("name", art)
                self.assertIn("path", art)
                self.assertIn("category", art)
                self.assertIn("size_bytes", art)
                self.assertIn("last_modified", art)
                self.assertGreater(art["size_bytes"], 0)

    def test_scan_skillvault(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_root = Path(tmp_dir)
            # Default empty / disabled
            data_empty = q_cockpit.ProjectScanner.scan_skillvault(tmp_root)
            self.assertFalse(data_empty["enabled"])
            self.assertEqual(data_empty["status"], "disabled")
            self.assertEqual(data_empty["skills"], [])

            # Enabled with configured directory
            cfg_file = tmp_root / ".q-agent.json"
            cfg_file.write_text(json.dumps({
                "context_retrieval": {
                    "providers": {
                        "skillvault": {
                            "enabled": True,
                            "path": "my_skills"
                        }
                    }
                }
            }), encoding="utf-8")

            my_skills = tmp_root / "my_skills" / "sample-agent"
            my_skills.mkdir(parents=True)
            (my_skills / "SKILL.md").write_text(
                "---\nname: sample-agent\ndescription: A sample skill\n---\n# Content\n",
                encoding="utf-8"
            )

            data_enabled = q_cockpit.ProjectScanner.scan_skillvault(tmp_root)
            self.assertTrue(data_enabled["enabled"])
            self.assertEqual(data_enabled["status"], "active")
            self.assertEqual(len(data_enabled["skills"]), 1)
            self.assertEqual(data_enabled["skills"][0]["name"], "sample-agent")


if __name__ == "__main__":
    unittest.main()
