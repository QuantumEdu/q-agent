#!/usr/bin/env python3
"""
q_inspect.py - Structural Deliverable & Artifact Linter for q-agent.

Verifies that deliverables physically exist, are non-empty, and free of
unfilled sentinel placeholders (TODO, FIXME, NaN, undefined, empty tables).

Usage:
    python3 tools/q-inspect/q_inspect.py file1.csv file2.html file3.rules
    python3 tools/q-inspect/q_inspect.py --forbid-placeholders doc.docx report.md
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

# Tokens indicating unfulfilled mock or placeholder content
DEFAULT_PLACEHOLDERS = [
    r"\bTODO\b",
    r"\bFIXME\b",
    r"\bTBD\b",
    r"\[INSERT\s+[^\]]+\]",
    r"\[PLACEHOLDER[^\]]*\]",
    r"\bundefined\b",
    r"\bNaN\b",
]

# `undefined` and `NaN` are legitimate tokens in source code; they only signal an
# unfilled value inside documents and data deliverables.
CODE_EXTENSIONS = {".py", ".ts", ".js", ".go"}
CODE_ONLY_ALLOWED = {r"\bundefined\b", r"\bNaN\b"}
TEXT_EXTENSIONS = {".md", ".html", ".htm", ".txt", ".csv", ".json", ".rules", ".conf", ".sql"} | CODE_EXTENSIONS
EXCEL_ERRORS = {"#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NULL!", "#NAME?"}


def _fail(result: dict[str, Any], message: str) -> dict[str, Any]:
    result["valid"] = False
    result["errors"].append(message)
    return result


def _xml_texts(root: ET.Element) -> list[str]:
    return [elem.text for elem in root.iter() if elem.tag.endswith("}t") and elem.text]


def _placeholder_patterns(suffix: str) -> list[str]:
    if suffix in CODE_EXTENSIONS:
        return [p for p in DEFAULT_PLACEHOLDERS if p not in CODE_ONLY_ALLOWED]
    return DEFAULT_PLACEHOLDERS


def _check_placeholders(result: dict[str, Any], text: str, label: str) -> None:
    for pat in DEFAULT_PLACEHOLDERS:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            _fail(result, f"Unfilled placeholder '{match.group()}' found in {label} content")


def _inspect_docx(file_path: Path, result: dict[str, Any], forbid_placeholders: bool) -> dict[str, Any]:
    if not zipfile.is_zipfile(file_path):
        return _fail(result, "Invalid DOCX deliverable: not a valid ZIP archive")
    with zipfile.ZipFile(file_path, "r") as zf:
        if "word/document.xml" not in zf.namelist():
            return _fail(result, "Invalid DOCX deliverable: missing 'word/document.xml' in package")
        extracted_text = " ".join(_xml_texts(ET.fromstring(zf.read("word/document.xml")))).strip()
    if not extracted_text:
        return _fail(result, "DOCX deliverable contains empty body or no text runs ('w:t')")
    if forbid_placeholders:
        _check_placeholders(result, extracted_text, "DOCX")
    return result


def _sheet_cells(s_root: ET.Element, s_file: str, all_texts: list[str], found_errors: list[str]) -> None:
    for cell in s_root.iter():
        if not cell.tag.endswith("}c"):
            continue
        all_texts.extend(_xml_texts(cell))
        for val_node in cell.iter():
            if not (val_node.tag.endswith("}v") and val_node.text):
                continue
            val_text = val_node.text.strip()
            if val_text in EXCEL_ERRORS:
                found_errors.append(f"Spreadsheet error '{val_text}' found in {s_file}")
            if cell.attrib.get("t", "") != "s":
                all_texts.append(val_text)


def _inspect_xlsx(file_path: Path, result: dict[str, Any], forbid_placeholders: bool) -> dict[str, Any]:
    if not zipfile.is_zipfile(file_path):
        return _fail(result, "Invalid XLSX deliverable: not a valid ZIP archive")
    all_texts: list[str] = []
    found_errors: list[str] = []
    has_rows = False
    with zipfile.ZipFile(file_path, "r") as zf:
        namelist = zf.namelist()
        if "xl/workbook.xml" not in namelist:
            return _fail(result, "Invalid XLSX deliverable: missing 'xl/workbook.xml' in package")
        sheet_files = [n for n in namelist if n.startswith("xl/worksheets/") and n.endswith(".xml")]
        if not sheet_files:
            return _fail(result, "Invalid XLSX deliverable: no worksheets found under 'xl/worksheets/'")
        if "xl/sharedStrings.xml" in namelist:
            try:
                all_texts.extend(_xml_texts(ET.fromstring(zf.read("xl/sharedStrings.xml"))))
            except ET.ParseError:
                pass
        for s_file in sheet_files:
            s_root = ET.fromstring(zf.read(s_file))
            has_rows = has_rows or any(elem.tag.endswith("}row") for elem in s_root.iter())
            _sheet_cells(s_root, s_file, all_texts, found_errors)
    if not has_rows:
        _fail(result, "XLSX deliverable contains empty worksheets without data rows")
    for error in found_errors[:3]:
        _fail(result, error)
    if forbid_placeholders and all_texts:
        _check_placeholders(result, " ".join(all_texts), "XLSX")
    return result


def _check_format(result: dict[str, Any], suffix: str, content: str) -> None:
    if suffix == ".csv":
        if len([line for line in content.splitlines() if line.strip()]) < 2:
            _fail(result, "CSV deliverable contains only headers or is missing data rows")
    elif suffix == ".json":
        try:
            if json.loads(content) in ({}, []):
                _fail(result, "JSON deliverable contains empty root container ({}) or ([])")
        except json.JSONDecodeError as e:
            _fail(result, f"Invalid JSON syntax: {e}")


def _inspect_text(file_path: Path, result: dict[str, Any], forbid_placeholders: bool) -> dict[str, Any]:
    suffix = file_path.suffix.lower()
    content = file_path.read_text(encoding="utf-8", errors="replace")
    if forbid_placeholders:
        for pat in _placeholder_patterns(suffix):
            matches = list(re.finditer(pat, content, re.IGNORECASE))
            if matches:
                lines = [content[:m.start()].count("\n") + 1 for m in matches[:3]]
                _fail(result, f"Unfilled placeholder '{matches[0].group()}' found on line(s) {lines}")
    _check_format(result, suffix, content)
    return result


def check_file(file_path: Path, forbid_placeholders: bool = True, min_bytes: int = 1) -> dict:
    result: dict[str, Any] = {
        "path": str(file_path),
        "exists": False,
        "size": 0,
        "valid": True,
        "errors": []
    }
    if not file_path.exists():
        return _fail(result, f"File does not exist: {file_path}")

    result["exists"] = True
    size = file_path.stat().st_size
    result["size"] = size
    if size < min_bytes:
        return _fail(result, f"File is empty or below {min_bytes} bytes (got {size} bytes)")

    inspectors = {".docx": ("DOCX file", _inspect_docx), ".xlsx": ("XLSX file", _inspect_xlsx)}
    suffix = file_path.suffix.lower()
    label, inspector = inspectors.get(suffix, ("file", _inspect_text))
    if inspector is _inspect_text and suffix not in TEXT_EXTENSIONS:
        return result
    try:
        return inspector(file_path, result, forbid_placeholders)
    except Exception as e:
        verb = "inspect" if suffix in inspectors else "read"
        return _fail(result, f"Failed to {verb} {label}: {e}")

def main() -> int:
    parser = argparse.ArgumentParser(description="Structural Deliverable Linter for q-agent")
    parser.add_argument("files", nargs="+", help="Files to inspect")
    parser.add_argument("--min-bytes", type=int, default=1, help="Minimum file size in bytes (default: 1)")
    parser.add_argument("--allow-placeholders", action="store_true", help="Allow TODO/NaN sentinel tokens")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    overall_valid = True
    results = []

    for file_str in args.files:
        p = Path(file_str)
        res = check_file(p, forbid_placeholders=not args.allow_placeholders, min_bytes=args.min_bytes)
        results.append(res)
        if not res["valid"]:
            overall_valid = False

    if args.json:
        print(json.dumps({"valid": overall_valid, "results": results}, indent=2))
    else:
        for r in results:
            if r["valid"]:
                print(f"[OK] {r['path']} ({r['size']} bytes)")
            else:
                print(f"[FAIL] {r['path']} ({r['size']} bytes)")
                for err in r["errors"]:
                    print(f"       -> {err}")

    return 0 if overall_valid else 1

if __name__ == "__main__":
    sys.exit(main())
