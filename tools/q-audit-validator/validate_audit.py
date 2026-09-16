#!/usr/bin/env python3
"""
q-audit-validator: Deterministic Output Quality Gate for q-agent Plan C.
Zero external dependencies. Two operating modes:

  --mode legacy   : validates monolithic BLUEPRINT.md deliverables (backward compat)
  --mode manifest : validates individual A{ID}-{slug}.md files against audit-manifest.yml
                    produces AUDIT_GAPS.json for the orchestrator retry loop

Usage:
  python validate_audit.py [--cwd PATH] [--mode legacy|manifest] [--manifest PATH] [--level 0|1|2]
"""

import sys
import re
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


# ── Legacy mode constants ────────────────────────────────────────────────────

MANDATORY_BLUEPRINT_SECTIONS = [
    ("Vision / Scope / Topology", [r"visi[oó]n", r"alcance", r"topolog[ií]a", r"bounded context"]),
    ("Frontend UI/UX", [r"interfaz gr[aá]fica", r"frontend", r"ui/ux", r"design system", r"a11y"]),
    ("DevOps / GitHub CI/CD", [r"devops", r"github", r"ci/cd", r"pipeline", r"workflow"]),
    ("Security / OWASP", [r"seguridad", r"owasp"]),
    ("Endpoints Catalog / Flow", [r"endpoints?", r"cat[aá]logo", r"flujo"]),
    ("Actionable Improvement Plan (P0/P1/P2)", [r"plan de mejora", r"quick wins", r"p0", r"p1", r"p2"]),
]

VALID_SEVERITIES = {"none", "low", "medium", "high", "critical"}
REQUIRED_SECTIONS = ["## Summary", "## Violations", "## Severity", "## EARS Spec"]


# ── Manifest mode helpers ───────────────────────────────────────────────────

def load_manifest(manifest_path: Path) -> dict:
    """Minimal YAML parser for the audit-manifest.yml (no PyYAML dependency)."""
    try:
        import yaml  # type: ignore
        with manifest_path.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        pass

    # Fallback: regex-based extraction of item output paths and IDs
    content = manifest_path.read_text(encoding="utf-8", errors="replace")
    items = []
    id_pattern = re.compile(r'^\s+- id:\s+"?(A\d+)"?', re.MULTILINE)
    slug_pattern = re.compile(r'^\s+slug:\s+"?([^"\n]+)"?', re.MULTILINE)
    level_pattern = re.compile(r'^\s+level:\s+(\d+)', re.MULTILINE)
    output_pattern = re.compile(r'^\s+output:\s+"?([^"\n]+)"?', re.MULTILINE)
    required_sections_block = re.compile(
        r'required_sections:\s*\n((?:\s+- \S+\n?)+)', re.MULTILINE
    )

    ids = id_pattern.findall(content)
    slugs = slug_pattern.findall(content)
    levels = [int(x) for x in level_pattern.findall(content)]
    outputs = output_pattern.findall(content)

    for i, item_id in enumerate(ids):
        items.append({
            "id": item_id,
            "slug": slugs[i] if i < len(slugs) else "unknown",
            "level": levels[i] if i < len(levels) else 0,
            "output": outputs[i].strip() if i < len(outputs) else f"audit/{item_id}.md",
            "required_sections": ["summary", "violations", "severity", "ears_spec"],
        })

    return {"items": items}


def parse_frontmatter(content: str) -> dict:
    """Extract YAML-like frontmatter from markdown between --- delimiters."""
    fm = {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def validate_item_file(item: dict, cwd: Path) -> list[str]:
    """Validate a single audit item file. Returns list of error strings."""
    errors = []
    output_path = cwd / item["output"]

    if not output_path.exists():
        errors.append(
            f"MISSING file: {item['output']} — "
            f"Item {item['id']} ({item['slug']}) was never produced."
        )
        return errors

    content = output_path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(content)

    # Frontmatter checks
    if fm.get("status") != "complete":
        errors.append(
            f"INCOMPLETE {item['output']}: frontmatter 'status' is '{fm.get('status', 'missing')}', "
            f"expected 'complete'."
        )

    severity = fm.get("severity", "").lower()
    if severity not in VALID_SEVERITIES:
        errors.append(
            f"INVALID SEVERITY in {item['output']}: '{severity}' is not one of "
            f"{sorted(VALID_SEVERITIES)}."
        )

    # Required sections check
    for section in REQUIRED_SECTIONS:
        if section.lower() not in content.lower():
            errors.append(
                f"MISSING SECTION '{section}' in {item['output']}."
            )

    return errors


# ── Legacy mode validation ───────────────────────────────────────────────────

def validate_legacy(cwd: Path) -> int:
    errors = []
    warnings = []

    print(f"\n[q-agent] Validating Plan C Audit Deliverables (legacy mode): {cwd.resolve()}\n")

    blueprint_path = cwd / "BLUEPRINT.md"
    if not blueprint_path.exists():
        errors.append("[CRITICAL] BLUEPRINT.md does not exist at project root.")
    else:
        content = blueprint_path.read_text(encoding="utf-8", errors="replace")
        lines = content.splitlines()

        if len(lines) < 80:
            errors.append(
                f"[CRITICAL] BLUEPRINT.md is superficial or truncated ({len(lines)} lines). "
                "A complete q-agent Blueprint requires at least 80 detailed lines."
            )

        for section_name, patterns in MANDATORY_BLUEPRINT_SECTIONS:
            found = any(re.search(p, content, re.IGNORECASE) for p in patterns)
            if not found:
                errors.append(f"[OMISSION] BLUEPRINT.md is missing mandatory section: '{section_name}'.")

    constitution_path = cwd / "CONSTITUTION.md"
    if not constitution_path.exists():
        errors.append("[CRITICAL] CONSTITUTION.md does not exist at project root.")
    else:
        c_content = constitution_path.read_text(encoding="utf-8", errors="replace")
        if "ADR-" not in c_content:
            warnings.append("CONSTITUTION.md contains no ADR table entries.")

    cab_paths = [
        cwd / "audit" / "CAB_RP_AUDIT.md",
        cwd / "audit" / "AUDIT_REPORT.md",
        cwd / "CAB_RP_AUDIT.md",
    ]
    cab_file = next((p for p in cab_paths if p.exists()), None)
    if not cab_file:
        errors.append("[CRITICAL] No CAB-RP report found (audit/CAB_RP_AUDIT.md or audit/AUDIT_REPORT.md).")
    else:
        cab_content = cab_file.read_text(encoding="utf-8", errors="replace")
        if "Release" not in cab_content and "Veredicto" not in cab_content:
            warnings.append("CAB-RP report does not declare a Release Verdict.")

    remediation_paths = [
        cwd / "audit" / "REMEDIATION_ISSUES.md",
        cwd / "REMEDIATION_ISSUES.md",
    ]
    rem_file = next((p for p in remediation_paths if p.exists()), None)
    if not rem_file:
        errors.append("[CRITICAL] REMEDIATION_ISSUES.md not found.")
    else:
        rem_content = rem_file.read_text(encoding="utf-8", errors="replace")
        ears_kws = ["WHEN", "THE SYSTEM SHALL", "SO THAT", "IF"]
        if sum(1 for kw in ears_kws if kw in rem_content.upper()) < 2:
            errors.append("[FORMAT] REMEDIATION_ISSUES.md does not use EARS format.")

    if warnings:
        print("Warnings:")
        for w in warnings:
            print(f"  {w}")
        print()

    if errors:
        print("FAILURES:")
        for e in errors:
            print(f"  {e}")
        print(
            "\nRESULT: REJECTED — Audit closed with critical omissions. "
            "Force agent to complete missing sections before closing the task.\n"
        )
        return 1

    print("RESULT: PASSED — All legacy audit deliverables meet q-agent v1.2 standard.\n")
    return 0


# ── Manifest mode validation ─────────────────────────────────────────────────

def validate_manifest(cwd: Path, manifest_path: Path, level: int) -> int:
    print(
        f"\n[q-agent] Validating Atomic Audit Items (manifest mode)\n"
        f"  Project: {cwd.resolve()}\n"
        f"  Manifest: {manifest_path.resolve()}\n"
        f"  Active level: {level} (includes items level <= {level})\n"
    )

    if not manifest_path.exists():
        print(f"[CRITICAL] Manifest not found: {manifest_path}")
        return 1

    data = load_manifest(manifest_path)
    all_items = data.get("items", [])
    active_items = [item for item in all_items if item.get("level", 0) <= level]

    if not active_items:
        print(f"[WARNING] No items found for level <= {level} in manifest.")
        return 0

    all_errors = {}
    for item in active_items:
        item_errors = validate_item_file(item, cwd)
        if item_errors:
            all_errors[item["id"]] = item_errors

    # Print detailed results
    passed = [item["id"] for item in active_items if item["id"] not in all_errors]
    failed = list(all_errors.keys())

    print(f"Results: {len(passed)}/{len(active_items)} items PASSED\n")

    if passed:
        print(f"  Passed: {', '.join(passed)}")

    if failed:
        print(f"  Failed: {', '.join(failed)}\n")
        for item_id, errors in all_errors.items():
            print(f"  [{item_id}]")
            for err in errors:
                print(f"    - {err}")
        print()

    # Produce AUDIT_GAPS.json for orchestrator retry loop
    audit_dir = cwd / "audit"
    audit_dir.mkdir(exist_ok=True)
    gaps_path = audit_dir / "AUDIT_GAPS.json"

    if all_errors:
        gaps = {
            "level": level,
            "total_active": len(active_items),
            "passed": len(passed),
            "failed": len(failed),
            "gaps": [
                {
                    "id": item_id,
                    "errors": errs,
                    "output": next(
                        (i["output"] for i in active_items if i["id"] == item_id), ""
                    ),
                }
                for item_id, errs in all_errors.items()
            ],
        }
        gaps_path.write_text(json.dumps(gaps, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  AUDIT_GAPS.json written: {gaps_path}")
        print(
            "\nRESULT: REJECTED — Audit items are incomplete. "
            "Orchestrator should retry failed IDs from AUDIT_GAPS.json (max 2 attempts).\n"
        )
        return 1

    # Clean up gaps file if all pass
    if gaps_path.exists():
        gaps_path.unlink()

    print("RESULT: PASSED — All active audit items are complete and valid.\n")
    return 0


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="q-audit-validator: Deterministic audit quality gate for q-agent Plan C"
    )
    parser.add_argument("--cwd", default=".", help="Project root directory")
    parser.add_argument(
        "--mode",
        choices=["legacy", "manifest"],
        default="legacy",
        help="legacy = monolithic BLUEPRINT.md, manifest = individual A*.md files",
    )
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to audit-manifest.yml (required for manifest mode)",
    )
    parser.add_argument(
        "--level",
        type=int,
        default=0,
        help="Audit maturity level (0=MVP, 1=Growth, 2=Maturity)",
    )

    args = parser.parse_args()
    cwd = Path(args.cwd)

    if args.mode == "manifest":
        manifest_path = Path(args.manifest) if args.manifest else (
            Path(__file__).parent.parent.parent / "references" / "audit-manifest.yml"
        )
        sys.exit(validate_manifest(cwd, manifest_path, args.level))
    else:
        sys.exit(validate_legacy(cwd))


if __name__ == "__main__":
    main()
