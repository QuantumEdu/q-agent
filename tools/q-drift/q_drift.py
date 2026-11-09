#!/usr/bin/env python3
"""
q_drift.py - Drift report for q-agent: design docs vs. real tree (MVP).

Zero external dependencies (stdlib only, Python >= 3.10).

Idea adapted from the Elephant-Goldfish Model drift-report skill
(Google, Apache-2.0; see ATTRIBUTION.md): a checked-in design document
is only useful while it still describes the code. This tool compares the
file paths referenced in BLUEPRINT.md (and docs/designs/*.md when the
directory exists) against the real filesystem and reports only the
differences. It is a detector, not a judge: it never edits docs or code.

Scope of this MVP (deliberate):
  - Referenced FILE paths that no longer exist on disk (missing-file).
  - Referenced files that exist but are empty (empty-file).
  - NOT in scope yet: symbol-level drift (a function named in a doc but
    renamed in code), and the reverse check (code never mentioned in any
    doc). Both are documented as future work in skills/q-design-review.

Exit codes:
  0: no drift detected.
  2: drift found (findings listed in the report).
  1: usage error (no doc files found / unreadable input).
"""

import argparse
import json
import re
import sys
from pathlib import Path

# A token counts as a "referenced path" when it looks like a repo-relative
# file path: it has a known top-level directory, or a file extension.
KNOWN_TOP_DIRS = (
    "tools/", "skills/", "tests/", "docs/", "references/", "prompts/",
    "templates/", "workflows/", "examples/", "evals/", "odd/", "q-tasks/",
    "bin/", "scripts/", ".github/",
)
PATH_RE = re.compile(r"[A-Za-z0-9_.\-/]+\.[A-Za-z0-9]{1,6}\b")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
CODE_RE = re.compile(r"`([^`\n]+)`")


def _looks_like_path(token):
    token = token.strip().strip(",;:\"'()[]<>")
    if not token or token.startswith(("http://", "https://", "mailto:", "#")):
        return None
    token = token.split("#", 1)[0]
    if token.startswith("./"):
        token = token[2:]
    if token.startswith("/") or ".." in Path(token).parts:
        return None
    # Template placeholders (<feature>, <ID>) and range shorthands
    # (audit/A01-A17.md) are not literal files; skip them, do not report.
    if "<" in token or ">" in token:
        return None
    base = token.rsplit("/", 1)[-1]
    if re.fullmatch(r"[A-Za-z]+\d+-[A-Za-z]+\d+\.[A-Za-z0-9]{1,6}", base):
        return None
    if token.startswith(KNOWN_TOP_DIRS):
        return token
    if PATH_RE.fullmatch(token) and "/" in token:
        return token
    return None


def extract_references(text):
    """Collect repo-relative file paths mentioned in one document."""
    found = []
    seen = set()
    candidates = []
    candidates.extend(LINK_RE.findall(text))
    candidates.extend(CODE_RE.findall(text))
    # Bare tokens, line by line, to avoid matching prose across lines.
    for line in text.splitlines():
        candidates.extend(line.split())
    for raw in candidates:
        path = _looks_like_path(raw)
        if path and path not in seen:
            seen.add(path)
            found.append(path)
    return found


def check_doc(doc_path, root):
    """Return findings for one document: missing or empty referenced files."""
    findings = []
    try:
        text = doc_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [{"doc": str(doc_path), "reference": "", "kind": "unreadable-doc",
                 "detail": str(exc)}]
    for ref in extract_references(text):
        target = root / ref
        if not target.exists():
            findings.append({"doc": str(doc_path), "reference": ref,
                             "kind": "missing-file",
                             "detail": f"referenced in {doc_path.name} but not on disk"})
        elif target.is_file() and target.stat().st_size == 0:
            findings.append({"doc": str(doc_path), "reference": ref,
                             "kind": "empty-file",
                             "detail": f"referenced in {doc_path.name} but 0 bytes on disk"})
    return findings


def collect_docs(root, extra_docs):
    """Default doc set: BLUEPRINT.md + docs/designs/*.md (when present)."""
    docs = []
    for candidate in extra_docs:
        path = Path(candidate)
        if not path.is_absolute():
            path = root / path
        if path.is_dir():
            docs.extend(sorted(path.glob("*.md")))
        elif path.is_file():
            docs.append(path)
        else:
            raise FileNotFoundError(f"doc path not found: {candidate}")
    if not extra_docs:
        blueprint = root / "BLUEPRINT.md"
        if blueprint.is_file():
            docs.append(blueprint)
        designs = root / "docs" / "designs"
        if designs.is_dir():
            docs.extend(sorted(designs.glob("*.md")))
    return docs


def run_drift(root, extra_docs):
    """Run the drift check. Returns the report dict."""
    root = Path(root).resolve()
    try:
        docs = collect_docs(root, extra_docs)
    except FileNotFoundError as exc:
        return {"tool": "q-drift", "root": str(root), "docs_checked": [],
                "references_checked": 0, "findings": [],
                "error": str(exc), "exit_code": 1}
    findings = []
    references_checked = 0
    if not docs:
        return {"tool": "q-drift", "root": str(root), "docs_checked": [],
                "references_checked": 0, "findings": [],
                "error": "no design documents found (expected BLUEPRINT.md "
                         "or docs/designs/*.md; pass --docs explicitly)",
                "exit_code": 1}
    for doc in docs:
        doc_findings = check_doc(doc, root)
        references_checked += len(extract_references(
            doc.read_text(encoding="utf-8", errors="replace")))
        findings.extend(doc_findings)
    return {
        "tool": "q-drift",
        "root": str(root),
        "docs_checked": [str(d) for d in docs],
        "references_checked": references_checked,
        "findings": findings,
        "drift_found": len(findings),
        "exit_code": 2 if findings else 0,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="q-agent drift report: checked-in docs vs. real tree (advisory; never edits)"
    )
    parser.add_argument("--root", default=".",
                        help="Repo root (default: current directory)")
    parser.add_argument("--docs", nargs="*", default=[],
                        help="Doc files/dirs to check (default: BLUEPRINT.md + docs/designs/*.md)")
    parser.add_argument("--json", action="store_true",
                        help="Output machine-readable JSON")
    args = parser.parse_args(argv)

    report = run_drift(args.root, args.docs)
    if "error" in report:
        print(f"Error: {report['error']}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=" * 72)
        print(f"q-drift report — root={report['root']}")
        print(f"Docs checked: {len(report['docs_checked'])} | "
              f"References checked: {report['references_checked']}")
        if not report["findings"]:
            print("No drift detected.")
        else:
            print(f"DRIFT: {report['drift_found']} finding(s)")
            for finding in report["findings"]:
                print(f"  - [{finding['kind']}] {finding['reference']} "
                      f"(in {Path(finding['doc']).name}): {finding['detail']}")
            print("Next step: update the doc, restore the file, or record "
                  "an ADR if the divergence is intentional.")
        print("=" * 72)
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
