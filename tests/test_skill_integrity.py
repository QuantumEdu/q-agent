"""
Test suite for validating q-agent skill integrity, schemas, and metadata.
"""

import json
from pathlib import Path
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestSkillIntegrity(unittest.TestCase):
    def test_skill_json_exists_and_valid(self):
        skill_json_path = ROOT_DIR / "skill.json"
        self.assertTrue(skill_json_path.exists(), "skill.json must exist in project root")

        with open(skill_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        required_fields = ["name", "version", "description", "author", "license", "entrypoint"]
        for field in required_fields:
            self.assertIn(field, data, f"skill.json is missing required field: {field}")
            self.assertTrue(bool(data[field]), f"skill.json field '{field}' must not be empty")

        self.assertEqual(data["name"], "q-agent")
        self.assertEqual(data["entrypoint"], "SKILL.md")

    def test_skill_md_frontmatter(self):
        skill_md_path = ROOT_DIR / "SKILL.md"
        self.assertTrue(skill_md_path.exists(), "SKILL.md must exist in project root")

        content = skill_md_path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"), "SKILL.md must start with YAML frontmatter delimiter '---'")

        parts = content.split("---", 2)
        self.assertGreaterEqual(len(parts), 3, "SKILL.md frontmatter must be enclosed by two '---' delimiters")

        frontmatter = parts[1]
        self.assertIn("name: q-agent", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("version: 2.4.0", frontmatter)

    def test_version_consistency(self):
        skill_json = json.loads((ROOT_DIR / "skill.json").read_text(encoding="utf-8"))
        skill_md = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
        version = skill_json["version"]
        self.assertEqual(version, "2.4.0")
        self.assertIn(f"version: {version}", skill_md)

    def test_audit_manifest_reference_exists(self):
        manifest_path = ROOT_DIR / "references" / "audit-manifest.yml"
        self.assertTrue(manifest_path.exists(), "references/audit-manifest.yml must exist")

        content = manifest_path.read_text(encoding="utf-8")
        self.assertIn("version:", content)
        self.assertIn("levels:", content)
        self.assertIn("waves:", content)
        self.assertIn("items:", content)

        # Verify all 17 audit items (A01-A17) are defined with wave assignments
        for i in range(1, 18):
            item_id = f"A{i:02d}"
            self.assertIn(f'- id: "{item_id}"', content, f"Missing audit item {item_id}")

        # Verify strategic evolution items (E01-E05)
        for i in range(1, 6):
            item_id = f"E{i:02d}"
            self.assertIn(f'- id: "{item_id}"', content, f"Missing strategic evolution item {item_id}")

        # Verify wave definitions in manifest
        for wave_num in range(1, 6):
            self.assertIn(f'  {wave_num}:', content, f"Missing wave {wave_num} definition")

    def test_bugfix_template_exists_and_valid(self):
        bugfix_path = ROOT_DIR / "templates" / "bugfix-template.md"
        self.assertTrue(bugfix_path.exists(), "templates/bugfix-template.md must exist")
        content = bugfix_path.read_text(encoding="utf-8")
        self.assertIn("DEFECTO OBSERVADO", content)
        self.assertIn("COMPORTAMIENTO ESPERADO", content)
        self.assertIn("INVARIANTES INTACTOS", content)
        self.assertIn("TEST REPRODUCTOR MANDATORIO", content)
        self.assertIn("TERMINAL EVIDENCE GATE", content)

    def test_task_log_template_wave_support(self):
        task_log_path = ROOT_DIR / "templates" / "task-log-template.md"
        self.assertTrue(task_log_path.exists(), "templates/task-log-template.md must exist")
        content = task_log_path.read_text(encoding="utf-8")
        self.assertIn("WAVE-BASED EXECUTION", content)
        self.assertIn("Wave 1", content)
        self.assertIn("Wave 2", content)
        self.assertIn("Wave 3", content)

    def test_q_agent_json_guardrails(self):
        q_agent_json_path = ROOT_DIR / "templates" / "q-agent.json"
        self.assertTrue(q_agent_json_path.exists(), "templates/q-agent.json must exist")
        data = json.loads(q_agent_json_path.read_text(encoding="utf-8"))
        self.assertIn("guardrails", data)
        self.assertIn("fs_write_allowed", data["guardrails"])
        self.assertIn("fs_write_denied", data["guardrails"])
        self.assertIn("shell_denied", data["guardrails"])


if __name__ == "__main__":
    unittest.main()
