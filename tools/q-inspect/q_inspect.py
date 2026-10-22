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
import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

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

def check_file(file_path: Path, forbid_placeholders: bool = True, min_bytes: int = 1) -> dict:
    result = {
        "path": str(file_path),
        "exists": False,
        "size": 0,
        "valid": True,
        "errors": []
    }

    if not file_path.exists():
        result["valid"] = False
        result["errors"].append(f"File does not exist: {file_path}")
        return result

    result["exists"] = True
    size = file_path.stat().st_size
    result["size"] = size

    if size < min_bytes:
        result["valid"] = False
        result["errors"].append(f"File is empty or below {min_bytes} bytes (got {size} bytes)")
        return result

    # OpenXML DOCX container and text inspection (zero-dependency)
    if file_path.suffix.lower() == ".docx":
        try:
            if not zipfile.is_zipfile(file_path):
                result["valid"] = False
                result["errors"].append("Invalid DOCX deliverable: not a valid ZIP archive")
                return result

            with zipfile.ZipFile(file_path, "r") as zf:
                if "word/document.xml" not in zf.namelist():
                    result["valid"] = False
                    result["errors"].append("Invalid DOCX deliverable: missing 'word/document.xml' in package")
                    return result

                doc_xml = zf.read("word/document.xml")
                root = ET.fromstring(doc_xml)

                text_nodes = [elem.text for elem in root.iter() if elem.tag.endswith("}t") and elem.text]
                extracted_text = " ".join(text_nodes).strip()

                if not extracted_text:
                    result["valid"] = False
                    result["errors"].append("DOCX deliverable contains empty body or no text runs ('w:t')")
                elif forbid_placeholders:
                    for pat in DEFAULT_PLACEHOLDERS:
                        matches = list(re.finditer(pat, extracted_text, re.IGNORECASE))
                        if matches:
                            result["valid"] = False
                            result["errors"].append(
                                f"Unfilled placeholder '{matches[0].group()}' found in DOCX content"
                            )
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Failed to inspect DOCX file: {e}")
        return result

    # OpenXML XLSX spreadsheet container and text/formula inspection (zero-dependency)
    if file_path.suffix.lower() == ".xlsx":
        try:
            if not zipfile.is_zipfile(file_path):
                result["valid"] = False
                result["errors"].append("Invalid XLSX deliverable: not a valid ZIP archive")
                return result

            with zipfile.ZipFile(file_path, "r") as zf:
                namelist = zf.namelist()
                if "xl/workbook.xml" not in namelist:
                    result["valid"] = False
                    result["errors"].append("Invalid XLSX deliverable: missing 'xl/workbook.xml' in package")
                    return result

                sheet_files = [name for name in namelist if name.startswith("xl/worksheets/") and name.endswith(".xml")]
                if not sheet_files:
                    result["valid"] = False
                    result["errors"].append("Invalid XLSX deliverable: no worksheets found under 'xl/worksheets/'")
                    return result

                all_texts = []
                if "xl/sharedStrings.xml" in namelist:
                    try:
                        ss_xml = zf.read("xl/sharedStrings.xml")
                        ss_root = ET.fromstring(ss_xml)
                        all_texts.extend([elem.text for elem in ss_root.iter() if elem.tag.endswith("}t") and elem.text])
                    except Exception:
                        pass

                has_rows = False
                excel_errors = {"#N/A", "#REF!", "#VALUE!", "#DIV/0!", "#NULL!", "#NAME?"}
                found_errors = []

                for s_file in sheet_files:
                    s_xml = zf.read(s_file)
                    s_root = ET.fromstring(s_xml)
                    rows = [elem for elem in s_root.iter() if elem.tag.endswith("}row")]
                    if rows:
                        has_rows = True
                    for cell in s_root.iter():
                        if cell.tag.endswith("}c"):
                            c_type = cell.attrib.get("t", "")
                            inline_texts = [elem.text for elem in cell.iter() if elem.tag.endswith("}t") and elem.text]
                            all_texts.extend(inline_texts)
                            for val_node in cell.iter():
                                if val_node.tag.endswith("}v") and val_node.text:
                                    val_text = val_node.text.strip()
                                    if val_text in excel_errors:
                                        found_errors.append(f"Spreadsheet error '{val_text}' found in {s_file}")
                                    if c_type != "s":
                                        all_texts.append(val_text)

                if not has_rows:
                    result["valid"] = False
                    result["errors"].append("XLSX deliverable contains empty worksheets without data rows")

                if found_errors:
                    result["valid"] = False
                    result["errors"].extend(found_errors[:3])

                if forbid_placeholders and all_texts:
                    joined_text = " ".join(all_texts)
                    for pat in DEFAULT_PLACEHOLDERS:
                        matches = list(re.finditer(pat, joined_text, re.IGNORECASE))
                        if matches:
                            result["valid"] = False
                            result["errors"].append(
                                f"Unfilled placeholder '{matches[0].group()}' found in XLSX content"
                            )
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Failed to inspect XLSX file: {e}")
        return result

    # Text content inspection for supported file types
    text_extensions = {".md", ".html", ".htm", ".txt", ".csv", ".json", ".rules", ".conf", ".sql", ".py", ".ts", ".js", ".go"}
    if file_path.suffix.lower() in text_extensions:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            
            # Check for placeholder tokens
            if forbid_placeholders:
                for pat in DEFAULT_PLACEHOLDERS:
                    matches = list(re.finditer(pat, content, re.IGNORECASE))
                    if matches:
                        lines = [content[:m.start()].count("\n") + 1 for m in matches[:3]]
                        result["valid"] = False
                        result["errors"].append(
                            f"Unfilled placeholder '{matches[0].group()}' found on line(s) {lines}"
                        )

            # Specific format checks
            ext = file_path.suffix.lower()
            if ext == ".csv":
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                if len(lines) < 2:
                    result["valid"] = False
                    result["errors"].append("CSV deliverable contains only headers or is missing data rows")
            elif ext == ".json":
                try:
                    parsed = json.loads(content)
                    if parsed in ({}, []):
                        result["valid"] = False
                        result["errors"].append("JSON deliverable contains empty root container ({}) or ([])")
                except json.JSONDecodeError as e:
                    result["valid"] = False
                    result["errors"].append(f"Invalid JSON syntax: {e}")

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Failed to read file: {e}")

    return result

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
