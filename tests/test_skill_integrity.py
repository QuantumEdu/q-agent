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
        self.assertIn("version: 2.2.2", frontmatter)

    def test_version_consistency(self):
        skill_json = json.loads((ROOT_DIR / "skill.json").read_text(encoding="utf-8"))
        skill_md = (ROOT_DIR / "SKILL.md").read_text(encoding="utf-8")
        version = skill_json["version"]
        self.assertEqual(version, "2.2.2")
        self.assertIn(f"version: {version}", skill_md)

    def test_audit_manifest_reference_exists(self):
        manifest_path = ROOT_DIR / "references" / "audit-manifest.yml"
        self.assertTrue(manifest_path.exists(), "references/audit-manifest.yml must exist")

        content = manifest_path.read_text(encoding="utf-8")
        self.assertIn("version:", content)
        self.assertIn("levels:", content)
        self.assertIn("items:", content)
        self.assertIn("A01", content)


if __name__ == "__main__":
    unittest.main()
