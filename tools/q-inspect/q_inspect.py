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
