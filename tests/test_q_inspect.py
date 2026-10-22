import io
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

TOOL_PATH = Path(__file__).resolve().parent.parent / "tools" / "q-inspect" / "q_inspect.py"

class TestQInspect(unittest.TestCase):
    def test_missing_file(self):
        proc = subprocess.run([sys.executable, str(TOOL_PATH), "non_existent_file.txt"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("File does not exist", proc.stdout)

    def test_empty_file(self):
        with tempfile.NamedTemporaryFile() as tmp:
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("empty or below", proc.stdout)

    def test_placeholder_detected(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w+") as tmp:
            tmp.write("# Title\nTODO: implement this section\n")
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("Unfilled placeholder 'TODO'", proc.stdout)

    def test_valid_markdown(self):
        with tempfile.NamedTemporaryFile(suffix=".md", mode="w+") as tmp:
            tmp.write("# Title\nThis is a complete and valid section with real data.\n")
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("[OK]", proc.stdout)

    def test_empty_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w+") as tmp:
            tmp.write("id,name,status\n")
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("missing data rows", proc.stdout)

    def test_valid_csv(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", mode="w+") as tmp:
            tmp.write("id,name,status\n1,server1,active\n")
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("[OK]", proc.stdout)

    def test_empty_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w+") as tmp:
            tmp.write("{}\n")
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("empty root container", proc.stdout)

    def test_valid_json(self):
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w+") as tmp:
            tmp.write('{"status": "ok", "count": 42}\n')
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("[OK]", proc.stdout)

    def _create_docx(self, path: str, text: str) -> None:
        xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">\n'
            '  <w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body>\n'
            '</w:document>'
        ).encode("utf-8")
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("word/document.xml", xml)

    def test_invalid_docx_not_zip(self):
        with tempfile.NamedTemporaryFile(suffix=".docx", mode="w+") as tmp:
            tmp.write("corrupted plain text content")
            tmp.flush()
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("not a valid ZIP archive", proc.stdout)

    def test_invalid_docx_missing_document_xml(self):
        with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("unrelated.txt", "content")
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("missing 'word/document.xml'", proc.stdout)

    def test_docx_with_placeholder(self):
        with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
            self._create_docx(tmp.name, "Report findings: TODO need to verify clause 4")
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertIn("Unfilled placeholder 'TODO' found in DOCX content", proc.stdout)

    def test_valid_docx(self):
        with tempfile.NamedTemporaryFile(suffix=".docx") as tmp:
            self._create_docx(tmp.name, "Complete cross-border data transfer deviation analysis without placeholders.")
            proc = subprocess.run([sys.executable, str(TOOL_PATH), tmp.name], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0)
            self.assertIn("[OK]", proc.stdout)

if __name__ == "__main__":
    unittest.main()
