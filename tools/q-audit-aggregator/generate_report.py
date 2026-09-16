#!/usr/bin/env python3
"""
q-audit-aggregator: Deterministic report & improvement plan generator for q-agent Plan C.
Zero external dependencies.
Reads individual A{ID}-{slug}.md files and assembles:
  1. audit/AUDIT_REPORT.md (Compliance Matrix + Detailed Findings)
  2. audit/PLAN_DE_MEJORA.md (Prioritized P0/P1/P2 Roadmap with EARS specifications)
  3. audit/REMEDIATION_ISSUES.md (Actionable GitHub Issue templates)

The LLM never generates the final report or improvement plan — this script does.

Usage:
  python generate_report.py [--cwd PATH] [--manifest PATH] [--level 0|1|2] [--output PATH]
"""

import sys
import re
import json
from pathlib import Path
from datetime import datetime, timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}
SEVERITY_BADGE = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "none": "NONE",
}
SEVERITY_VERDICT = {
    "critical": "BLOCKED",
    "high": "BLOCKED",
    "medium": "CONDITIONAL",
    "low": "PASS WITH WARNINGS",
    "none": "PASS",
}
PRIORITY_MAP = {
    "critical": "P0 (Inmediato / Bloqueante)",
    "high": "P1 (Corto Plazo / Alto Riesgo)",
    "medium": "P2 (Mediano Plazo / Contratos & Deuda)",
    "low": "P3 (Higiene / Deuda Menor)",
}


def load_manifest(manifest_path: Path) -> list[dict]:
    try:
        import yaml
        with manifest_path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("items", [])
    except ImportError:
        pass

    content = manifest_path.read_text(encoding="utf-8", errors="replace")
    id_pattern = re.compile(r'^\s+- id:\s+"?(A\d+)"?', re.MULTILINE)
    slug_pattern = re.compile(r'^\s+slug:\s+"?([^"\n]+)"?', re.MULTILINE)
    level_pattern = re.compile(r'^\s+level:\s+(\d+)', re.MULTILINE)
    output_pattern = re.compile(r'^\s+output:\s+"?([^"\n]+)"?', re.MULTILINE)
    category_pattern = re.compile(r'^\s+category:\s+"?([^"\n]+)"?', re.MULTILINE)

    ids = id_pattern.findall(content)
    slugs = slug_pattern.findall(content)
    levels = [int(x) for x in level_pattern.findall(content)]
    outputs = output_pattern.findall(content)
    categories = category_pattern.findall(content)

    return [
        {
            "id": item_id,
            "slug": slugs[i] if i < len(slugs) else "unknown",
            "level": levels[i] if i < len(levels) else 0,
            "output": outputs[i].strip() if i < len(outputs) else f"audit/{item_id}.md",
            "category": categories[i] if i < len(categories) else "unknown",
        }
        for i, item_id in enumerate(ids)
    ]


def parse_frontmatter(content: str) -> dict:
    fm = {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return fm
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm


def strip_frontmatter(content: str) -> str:
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return content
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1:])
    return content


def extract_section(body: str, section_title: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(section_title)}\s*\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(body)
    return match.group(1).strip() if match else ""


def build_improvement_plan(cwd: Path, results: list[dict], verdict: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# 🛠️ Plan de Mejora Accionable y Hoja de Ruta — {cwd.name}",
        f"",
        f"> **Framework:** q-agent v1.2 — Generación Determinista de Remediación  ",
        f"> **Fecha:** {now}  ",
        f"> **Veredicto General:** `{verdict}`  ",
        f"> **Objetivo:** Hoja de ruta priorizada para subsanar los hallazgos de auditoría de forma estructurada e incremental.  ",
        f"",
        f"---",
        f"",
        f"## 📌 Matriz de Priorización de Mejoras",
        f"",
        f"| Prioridad | ID | Categoría | Ítem | Foco de Remediación |",
        f"| :---: | :---: | :--- | :--- | :--- |",
    ]

    actionable = [r for r in results if r["severity"] in ("critical", "high", "medium", "low")]
    actionable.sort(key=lambda x: SEVERITY_RANK.get(x["severity"], 99))

    for r in actionable:
        prio_label = r["severity"].upper()
        prio_badge = "🔴 P0" if prio_label == "CRITICAL" else ("🟠 P1" if prio_label == "HIGH" else ("🟡 P2" if prio_label == "MEDIUM" else "🟢 P3"))
        lines.append(
            f"| {prio_badge} | `{r['id']}` | {r.get('category', '-')} | `{r['slug']}` | Ver especificación EARS en sección detallada |"
        )

    lines += [
        f"",
        f"---",
        f"",
        f"## 🚀 Desglose de Fases de Ejecución",
        f"",
    ]

    phases = [
        ("🔴 Fase P0 — Inmediato / Bloqueante", ["critical"]),
        ("🟠 Fase P1 — Corto Plazo / Riesgo Alto", ["high"]),
        ("🟡 Fase P2 — Mediano Plazo / Contratos & Deuda", ["medium"]),
        ("🟢 Fase P3 — Higiene & Mantenimiento Menor", ["low"]),
    ]

    for phase_title, sevs in phases:
        phase_items = [r for r in actionable if r["severity"] in sevs]
        if not phase_items:
            continue

        lines.append(f"### {phase_title}")
        lines.append("")

        for r in phase_items:
            summary = extract_section(r["body"], "Summary")
            violations = extract_section(r["body"], "Violations")
            ears = extract_section(r["body"], "EARS Spec")

            lines.append(f"#### `{r['id']}` — {r['slug']} `[{r['severity'].upper()}]`")
            if summary:
                lines.append(f"**Diagnóstico:** {summary}")
                lines.append("")
            if violations:
                lines.append(f"**Evidencia observada:**")
                lines.append(violations)
                lines.append("")
            if ears and ears.strip() != "N/A — No remediation required.":
                lines.append(f"**Especificación de Requisito EARS:**")
                lines.append("```ears")
                lines.append(ears)
                lines.append("```")
                lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def generate_report(cwd: Path, manifest_path: Path, level: int, output_path: Path) -> int:
    print(
        f"\n[q-agent] Generating Audit Report & Improvement Plan\n"
        f"  Project: {cwd.resolve()}\n"
        f"  Level: {level}\n"
        f"  Output: {output_path}\n"
    )

    all_items = load_manifest(manifest_path)
    active_items = [item for item in all_items if item.get("level", 0) <= level]

    if not active_items:
        print("[WARNING] No active items found for this level.")
        return 0

    results = []
    for item in active_items:
        item_path = cwd / item["output"]
        if not item_path.exists():
            results.append({
                **item,
                "severity": "missing",
                "status": "missing",
                "body": f"## Summary\n\nItem file not found: `{item['output']}`\n",
            })
            continue

        content = item_path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        body = strip_frontmatter(content).strip()
        results.append({
            **item,
            "severity": fm.get("severity", "unknown").lower(),
            "status": fm.get("status", "unknown"),
            "body": body,
        })

    all_severities = [r["severity"] for r in results if r["severity"] in SEVERITY_RANK]
    worst = min(all_severities, key=lambda s: SEVERITY_RANK.get(s, 99)) if all_severities else "none"
    verdict = SEVERITY_VERDICT.get(worst, "UNKNOWN")

    tally = {s: sum(1 for r in results if r["severity"] == s) for s in SEVERITY_RANK}
    tally["missing"] = sum(1 for r in results if r["severity"] == "missing")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [
        f"# AUDIT REPORT — {cwd.name}",
        f"",
        f"> **Framework:** q-agent v1.2 — Plan C Atomic Dispatch  ",
        f"> **Date:** {now}  ",
        f"> **Audit Level:** {level}  ",
        f"> **Items Audited:** {len(active_items)}  ",
        f"> **Overall Verdict:** `{verdict}` (worst severity: {worst.upper()})  ",
        f"> **Plan de Mejora Asociado:** [`PLAN_DE_MEJORA.md`](./PLAN_DE_MEJORA.md)  ",
        f"",
        f"---",
        f"",
        f"## Compliance Matrix",
        f"",
        f"| ID | Category | Slug | Severity | Status |",
        f"| :- | :------- | :--- | :------: | :----: |",
    ]

    for r in sorted(results, key=lambda x: SEVERITY_RANK.get(x["severity"], 99)):
        sev = r["severity"].upper()
        status = r["status"]
        lines.append(
            f"| {r['id']} | {r.get('category', '-')} | {r['slug']} | `{sev}` | {status} |"
        )

    lines += [
        f"",
        f"**Summary:** "
        f"{tally.get('critical', 0)} critical · "
        f"{tally.get('high', 0)} high · "
        f"{tally.get('medium', 0)} medium · "
        f"{tally.get('low', 0)} low · "
        f"{tally.get('none', 0)} pass · "
        f"{tally.get('missing', 0)} missing",
        f"",
        f"---",
        f"",
    ]

    lines.append("## Detailed Findings")
    lines.append("")

    for r in sorted(results, key=lambda x: SEVERITY_RANK.get(x["severity"], 99)):
        sev_badge = SEVERITY_BADGE.get(r["severity"], r["severity"].upper())
        lines.append(f"### {r['id']} — {r['slug']} `[{sev_badge}]`")
        lines.append(f"*Category: {r.get('category', '-')} · Status: {r['status']}*")
        lines.append("")
        lines.append(r["body"])
        lines.append("")
        lines.append("---")
        lines.append("")

    report_content = "\n".join(lines)
    output_path.write_text(report_content, encoding="utf-8")
    print(f"Report written: {output_path} ({len(results)} items, verdict: {verdict})")

    # Generate and Write audit/PLAN_DE_MEJORA.md & audit/REMEDIATION_ISSUES.md
    plan_content = build_improvement_plan(cwd, results, verdict)
    plan_path = output_path.parent / "PLAN_DE_MEJORA.md"
    remediation_path = output_path.parent / "REMEDIATION_ISSUES.md"
    plan_path.write_text(plan_content, encoding="utf-8")
    remediation_path.write_text(plan_content, encoding="utf-8")
    print(f"Improvement Plan written: {plan_path}")
    print(f"Remediation Issues written: {remediation_path}")

    # Write root PLAN_DE_MEJORA.md for immediate project visibility
    root_plan_path = cwd / "PLAN_DE_MEJORA.md"
    root_plan_path.write_text(plan_content, encoding="utf-8")
    print(f"Root Improvement Plan updated: {root_plan_path}")

    # Update AUDIT_GAPS.json
    blocked = [r for r in results if r["severity"] in ("critical", "high", "missing")]
    if blocked:
        gaps_path = cwd / "audit" / "AUDIT_GAPS.json"
        gaps_data = {
            "verdict": verdict,
            "worst_severity": worst,
            "blocked_count": len(blocked),
            "blocked_items": [
                {"id": r["id"], "slug": r["slug"], "severity": r["severity"]}
                for r in blocked
            ],
        }
        gaps_path.parent.mkdir(exist_ok=True)
        gaps_path.write_text(json.dumps(gaps_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"AUDIT_GAPS.json updated: {gaps_path}")

    return 0 if worst in ("none", "low") else 1


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="q-audit-aggregator: Deterministic AUDIT_REPORT.md & PLAN_DE_MEJORA.md generator"
    )
    parser.add_argument("--cwd", default=".", help="Project root directory")
    parser.add_argument(
        "--manifest",
        default=None,
        help="Path to audit-manifest.yml",
    )
    parser.add_argument(
        "--level", type=int, default=0, help="Maturity level to aggregate (0=MVP)"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output path for AUDIT_REPORT.md (default: <cwd>/audit/AUDIT_REPORT.md)",
    )

    args = parser.parse_args()
    cwd = Path(args.cwd)

    manifest_path = (
        Path(args.manifest)
        if args.manifest
        else Path(__file__).parent.parent.parent / "references" / "audit-manifest.yml"
    )
    output_path = Path(args.output) if args.output else cwd / "audit" / "AUDIT_REPORT.md"
    output_path.parent.mkdir(exist_ok=True)

    sys.exit(generate_report(cwd, manifest_path, args.level, output_path))


if __name__ == "__main__":
    main()
