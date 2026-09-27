#!/usr/bin/env python3
"""
q-audit-validator: Deterministic Output Quality Gate for q-agent Plan C.
Zero external dependencies. Two operating modes:

  --mode legacy   : validates monolithic BLUEPRINT.md deliverables (backward compat)
  --mode manifest : validates individual A{ID}-{slug}.md files against audit-manifest.yml
                    produces AUDIT_GAPS.json for the orchestrator retry loop
  --mode technical: deterministic zero-dependency gate validating CI, DR, Observability, and API contracts

Usage:
  python validate_audit.py [--cwd PATH] [--mode legacy|manifest|technical|contracts] [--manifest PATH] [--level 0|1|2] [--strict] [--json]
"""

from datetime import datetime, timezone
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
    id_pattern = re.compile(r'^\s+- id:\s+"?([AE]\d+)"?', re.MULTILINE)
    slug_pattern = re.compile(r'^\s+slug:\s+"?([^"\n]+)"?', re.MULTILINE)
    level_pattern = re.compile(r'^\s+level:\s+(\d+)', re.MULTILINE)
    wave_pattern = re.compile(r'^\s+wave:\s+(\d+)', re.MULTILINE)
    output_pattern = re.compile(r'^\s+output:\s+"?([^"\n]+)"?', re.MULTILINE)

    ids = id_pattern.findall(content)
    slugs = slug_pattern.findall(content)
    levels = [int(x) for x in level_pattern.findall(content)]
    waves = [int(x) for x in wave_pattern.findall(content)]
    outputs = output_pattern.findall(content)

    for i, item_id in enumerate(ids):
        items.append({
            "id": item_id,
            "slug": slugs[i] if i < len(slugs) else "unknown",
            "level": levels[i] if i < len(levels) else 0,
            "wave": waves[i] if i < len(waves) else 0,
            "output": outputs[i].strip() if i < len(outputs) else f"audit/{item_id}.md",
            "required_sections": ["summary", "violations", "severity", "ears_spec"],
            "type": "strategic_evolution" if item_id.startswith("E") else "defect_compliance",
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


STRATEGIC_REQUIRED_SECTIONS = [
    "## Summary",
    "## Current Bottlenecks",
    "## Proposed Architecture",
    "## Expected Impact",
]


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

    # Strategic items (E01-E05) vs Defect items (A01-A17)
    is_strategic = item["id"].startswith("E") or item.get("type") == "strategic_evolution"

    if is_strategic:
        for section in STRATEGIC_REQUIRED_SECTIONS:
            if section.lower() not in content.lower():
                errors.append(
                    f"MISSING SECTION '{section}' in strategic item {item['output']}."
                )
    else:
        severity = fm.get("severity", "").lower()
        if severity not in VALID_SEVERITIES:
            errors.append(
                f"INVALID SEVERITY in {item['output']}: '{severity}' is not one of "
                f"{sorted(VALID_SEVERITIES)}."
            )

        # Required sections check for defect items
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

    print("RESULT: PASSED — All legacy audit deliverables meet q-agent v2.5.3 standard.\n")
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


# ── Technical Contracts mode helpers ──────────────────────────────────────────

BASE_IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "dist",
    "build",
    ".idea",
    ".vscode",
    "coverage",
    ".cache",
    ".turbo",
    ".next",
    ".nuxt",
}

DOC_IGNORED_DIRS = BASE_IGNORED_DIRS | {
    "references",
    "docs",
    "prompts",
    "templates",
    "odd",
    "audit",
    "tests",
    "test",
}


def find_files(
    base_dir: Path,
    filter_fn=None,
    max_depth: int = 4,
    ignored_dirs: set[str] = BASE_IGNORED_DIRS,
    current_depth: int = 0,
) -> list[Path]:
    if current_depth > max_depth or not base_dir.exists():
        return []
    results = []
    try:
        for entry in base_dir.iterdir():
            if entry.name in ignored_dirs:
                continue
            if entry.is_dir():
                results.extend(
                    find_files(
                        entry, filter_fn, max_depth, ignored_dirs, current_depth + 1
                    )
                )
            elif entry.is_file():
                if filter_fn is None or filter_fn(entry.name, entry):
                    results.append(entry)
    except (PermissionError, OSError):
        pass
    return results


def safe_read(file_path: Path, max_bytes: int = 131072) -> str:
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as f:
            return f.read(max_bytes)
    except (PermissionError, OSError):
        return ""


def audit_technical_contracts(cwd: Path) -> dict:
    target_dir = cwd.resolve()
    self_path = Path(__file__).resolve()

    report = {
        "target": str(target_dir),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "contracts": {
            "A03_github_ci_integrity": {
                "id": "A03",
                "name": "GitHub & CI Integrity",
                "checks": [],
            },
            "A17_disaster_recovery": {
                "id": "A17",
                "name": "Disaster Recovery Contract",
                "checks": [],
            },
            "A14_observability_telemetry": {
                "id": "A14",
                "name": "Observability & Telemetry",
                "checks": [],
            },
            "A06_api_contracts": {
                "id": "A06",
                "name": "API Contracts Catalog",
                "checks": [],
            },
        },
        "summary": {
            "total": 0,
            "passed": 0,
            "warnings": 0,
            "critical": 0,
            "verdict": "PASSED",
        },
    }

    # Application source code files (avoiding self, sibling audit script, and documentation)
    audit_script_names = {"audit_api_contracts.js", "validate_audit.py"}
    code_files = find_files(
        target_dir,
        lambda name, path: path.resolve() != self_path
        and name not in audit_script_names
        and bool(re.search(r"\.(py|js|ts|jsx|tsx|go|rs|php|rb|java|cs)$", name, re.I)),
        max_depth=5,
        ignored_dirs=DOC_IGNORED_DIRS,
    )

    # ── CONTRACT A03: GitHub & CI Integrity ──────────────────────────────────
    a03 = report["contracts"]["A03_github_ci_integrity"]

    # 1. .gitignore
    gitignore_path = target_dir / ".gitignore"
    if gitignore_path.exists():
        a03["checks"].append({
            "id": "A03-GITIGNORE",
            "name": "VCS Ignore (.gitignore)",
            "status": "PASS",
            "severity": "PASS",
            "message": ".gitignore exists at project root",
        })
    else:
        a03["checks"].append({
            "id": "A03-GITIGNORE",
            "name": "VCS Ignore (.gitignore)",
            "status": "FAIL",
            "severity": "CRITICAL",
            "message": ".gitignore is missing at project root",
        })

    # 2. CI workflows (.github/workflows/*.yml | *.yaml)
    workflows_dir = target_dir / ".github" / "workflows"
    workflow_files = []
    if workflows_dir.exists() and workflows_dir.is_dir():
        workflow_files = [
            f for f in workflows_dir.iterdir()
            if f.is_file() and f.suffix.lower() in (".yml", ".yaml")
        ]

    if workflow_files:
        rel_names = ", ".join(str(f.relative_to(target_dir)) for f in workflow_files)
        a03["checks"].append({
            "id": "A03-WORKFLOWS",
            "name": "CI Workflow Definitions",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Found {len(workflow_files)} CI workflow file(s): {rel_names}",
        })
    else:
        a03["checks"].append({
            "id": "A03-WORKFLOWS",
            "name": "CI Workflow Definitions",
            "status": "FAIL",
            "severity": "CRITICAL",
            "message": "No CI workflow definitions (.yml/.yaml) found in .github/workflows/",
        })

    # 3. Workflow triggers (push, pull_request)
    if workflow_files:
        triggers_found = set()
        trigger_pr_pat = re.compile(
            r"(?:^|\n)\s*(?:pull_request|pull_request_target)\s*:|on:\s*\[?[^\]\n]*pull_request[^\]\n]*\]?",
            re.M,
        )
        trigger_push_pat = re.compile(
            r"(?:^|\n)\s*push\s*:|on:\s*\[?[^\]\n]*push[^\]\n]*\]?",
            re.M,
        )

        for wf in workflow_files:
            content = safe_read(wf)
            if trigger_pr_pat.search(content):
                triggers_found.add("pull_request")
            if trigger_push_pat.search(content):
                triggers_found.add("push")

        if triggers_found:
            a03["checks"].append({
                "id": "A03-TRIGGERS",
                "name": "Workflow Triggers",
                "status": "PASS",
                "severity": "PASS",
                "message": f"CI triggers verified ({', '.join(sorted(triggers_found))})",
            })
        else:
            a03["checks"].append({
                "id": "A03-TRIGGERS",
                "name": "Workflow Triggers",
                "status": "WARN",
                "severity": "WARNING",
                "message": "No push or pull_request triggers found in workflow definitions",
            })

        # 4. Test / Lint job steps
        test_lint_pat = re.compile(
            r"\b(test|lint|py_compile|unittest|pytest|eslint|jest|vitest|npm\s+(?:run\s+)?test|cargo\s+test|go\s+test|mvn\s+test|flake8|mypy|ruff)\b",
            re.I,
        )
        has_test_lint = any(test_lint_pat.search(safe_read(wf)) for wf in workflow_files)
        if has_test_lint:
            a03["checks"].append({
                "id": "A03-TEST-LINT",
                "name": "Automated Test/Lint Gates",
                "status": "PASS",
                "severity": "PASS",
                "message": "Automated test and/or lint steps detected in CI workflows",
            })
        else:
            a03["checks"].append({
                "id": "A03-TEST-LINT",
                "name": "Automated Test/Lint Gates",
                "status": "WARN",
                "severity": "WARNING",
                "message": "No automated test or lint steps identified in CI workflows",
            })
    else:
        a03["checks"].append({
            "id": "A03-TRIGGERS",
            "name": "Workflow Triggers",
            "status": "WARN",
            "severity": "WARNING",
            "message": "Cannot evaluate triggers: no workflow files found",
        })
        a03["checks"].append({
            "id": "A03-TEST-LINT",
            "name": "Automated Test/Lint Gates",
            "status": "WARN",
            "severity": "WARNING",
            "message": "Cannot evaluate test/lint steps: no workflow files found",
        })

    # 5. Dependabot / Renovate
    dependabot_yml = target_dir / ".github" / "dependabot.yml"
    dependabot_yaml = target_dir / ".github" / "dependabot.yaml"
    renovate_candidates = [
        target_dir / "renovate.json",
        target_dir / ".renovaterc",
        target_dir / ".renovaterc.json",
        target_dir / ".github" / "renovate.json",
    ]

    dep_path = None
    if dependabot_yml.exists():
        dep_path = ".github/dependabot.yml"
    elif dependabot_yaml.exists():
        dep_path = ".github/dependabot.yaml"
    else:
        for r_cand in renovate_candidates:
            if r_cand.exists():
                dep_path = str(r_cand.relative_to(target_dir))
                break

    if dep_path:
        a03["checks"].append({
            "id": "A03-DEPENDABOT",
            "name": "Dependency Automation",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Dependency automation configured ({dep_path})",
        })
    else:
        a03["checks"].append({
            "id": "A03-DEPENDABOT",
            "name": "Dependency Automation",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No Dependabot (.github/dependabot.yml) or Renovate configuration found",
        })

    # ── CONTRACT A17: Disaster Recovery Contract ─────────────────────────────
    a17 = report["contracts"]["A17_disaster_recovery"]

    # 1. Backup strategy & runbooks
    backup_regex = re.compile(r"backup|snapshot|pg_dump|mysqldump|\bdr\b|disaster-recovery|mongodump", re.I)
    backup_files = find_files(
        target_dir,
        lambda name, path: (
            path.resolve() != self_path
            and (
                bool(backup_regex.search(name))
                or (
                    any(part.lower() in ("docs", "runbooks", "scripts") for part in path.parts)
                    and bool(backup_regex.search(str(path.relative_to(target_dir)).lower()))
                )
            )
        ),
        max_depth=4,
        ignored_dirs=BASE_IGNORED_DIRS,
    )

    backup_in_workflows = any(backup_regex.search(safe_read(wf)) for wf in workflow_files)

    if backup_files or backup_in_workflows:
        detail = ", ".join(str(f.relative_to(target_dir)) for f in backup_files[:3]) if backup_files else "CI workflow steps"
        a17["checks"].append({
            "id": "A17-BACKUP",
            "name": "Backup Strategy & Runbooks",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Disaster recovery / backup artifacts detected: {detail}",
        })
    else:
        a17["checks"].append({
            "id": "A17-BACKUP",
            "name": "Backup Strategy & Runbooks",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No backup scripts, snapshot configs, or DR runbooks found",
        })

    # 2. Rollback capabilities in deploy workflows/scripts
    rollback_regex = re.compile(r"\b(rollback|canary|revert|blue-green|helm\s+rollback)\b", re.I)
    deploy_candidates = find_files(
        target_dir,
        lambda name, path: (
            path.resolve() != self_path
            and (
                "deploy" in name.lower()
                or any(k in str(path.relative_to(target_dir)).lower() for k in ("k8s", "helm", "terraform"))
                or name.lower().endswith((".sh", ".ps1"))
            )
            and not str(path.relative_to(target_dir)).lower().startswith(("prompts", "references"))
        ),
        max_depth=4,
        ignored_dirs=DOC_IGNORED_DIRS,
    )

    rollback_found = False
    rollback_location = ""
    for f in list(workflow_files) + deploy_candidates:
        content = safe_read(f)
        if rollback_regex.search(content):
            rollback_found = True
            rollback_location = str(f.relative_to(target_dir))
            break

    if rollback_found:
        a17["checks"].append({
            "id": "A17-ROLLBACK",
            "name": "Rollback & Resilience Capabilities",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Rollback or canary deployment mechanisms identified ({rollback_location})",
        })
    else:
        a17["checks"].append({
            "id": "A17-ROLLBACK",
            "name": "Rollback & Resilience Capabilities",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No rollback, canary, or revert mechanisms identified in deploy workflows/scripts",
        })

    # 3. Healthcheck definition
    health_patterns = [
        re.compile(r"(?:^|\n)\s*HEALTHCHECK\b", re.M),
        re.compile(r"(?:^|\n)\s*healthcheck\s*:", re.M),
        re.compile(r"\b(readinessProbe|livenessProbe)\s*:", re.M),
        re.compile(r"['\"]/(?:health|healthz|ping|livez|readyz)['\"]", re.I),
        re.compile(r"path\s*==\s*['\"]/(?:health|healthz|ping)['\"]", re.I),
    ]

    server_candidates = find_files(
        target_dir,
        lambda name, path: (
            path.resolve() != self_path
            and ("docker" in name.lower() or bool(re.search(r"\.(py|js|ts|go|ya?ml)$", name, re.I)))
        ),
        max_depth=4,
        ignored_dirs=DOC_IGNORED_DIRS,
    )

    healthcheck_found = False
    healthcheck_location = ""
    for f in server_candidates:
        content = safe_read(f)
        for pat in health_patterns:
            if pat.search(content):
                healthcheck_found = True
                healthcheck_location = str(f.relative_to(target_dir))
                break
        if healthcheck_found:
            break

    if healthcheck_found:
        a17["checks"].append({
            "id": "A17-HEALTHCHECK",
            "name": "Healthcheck Endpoint",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Healthcheck definition detected ({healthcheck_location})",
        })
    else:
        a17["checks"].append({
            "id": "A17-HEALTHCHECK",
            "name": "Healthcheck Endpoint",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No healthcheck definition (/health, /healthz, /ping, or Docker HEALTHCHECK) found",
        })

    # ── CONTRACT A14: Observability & Telemetry ──────────────────────────────
    a14 = report["contracts"]["A14_observability_telemetry"]

    logging_keywords = [
        "winston", "pino", "loguru", "logging", "sentry", "opentelemetry",
        "prometheus", "datadog", "bunyan", "morgan", "serilog", "structlog",
        "newrelic", "dynatrace", "statsd",
    ]
    logging_regex = re.compile(rf"\b({'|'.join(logging_keywords)})\b", re.I)

    manifest_names = ["package.json", "requirements.txt", "pyproject.toml", "Pipfile", "go.mod", "Cargo.toml", "composer.json"]
    manifest_files = [target_dir / m for m in manifest_names if (target_dir / m).exists()]

    logging_found = False
    detected_logger = ""

    for mf in manifest_files:
        content = safe_read(mf)
        m = logging_regex.search(content)
        if m:
            logging_found = True
            detected_logger = f"{m.group(1)} in {mf.relative_to(target_dir)}"
            break

    if not logging_found:
        code_log_pat = re.compile(
            r"(?:import\s+logging\b|from\s+logging\s+import|require\((\"|')pino(\"|')\)|require\((\"|')winston(\"|')\)|from\s+loguru\s+import|import\s+loguru|@opentelemetry|datadog|prometheus_client)",
            re.I,
        )
        for f in code_files:
            content = safe_read(f)
            if code_log_pat.search(content):
                logging_found = True
                detected_logger = str(f.relative_to(target_dir))
                break

    if logging_found:
        a14["checks"].append({
            "id": "A14-LOGGING",
            "name": "Structured Logging / APM",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Structured logging / APM / metrics configured ({detected_logger})",
        })
    else:
        a14["checks"].append({
            "id": "A14-LOGGING",
            "name": "Structured Logging / APM",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No structured logging (pino/winston/loguru), APM, or metrics libraries detected",
        })

    # 2. Request correlation / tracing middleware
    correlation_regex = re.compile(
        r"\b(correlationId|correlation_id|requestId|request_id|x-request-id|traceparent|tracing|tracer|trace_id|distributed-tracing|X-Correlation-ID)\b",
        re.I,
    )
    correlation_found = False
    correlation_location = ""
    for f in code_files:
        content = safe_read(f)
        if correlation_regex.search(content):
            correlation_found = True
            correlation_location = str(f.relative_to(target_dir))
            break

    if correlation_found:
        a14["checks"].append({
            "id": "A14-TRACING",
            "name": "Request Correlation & Tracing",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Request correlation or tracing detected ({correlation_location})",
        })
    else:
        a14["checks"].append({
            "id": "A14-TRACING",
            "name": "Request Correlation & Tracing",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No request correlation (x-request-id / correlation_id) or tracing middleware detected",
        })

    # ── CONTRACT A06: API Contracts Catalog ──────────────────────────────────
    a06 = report["contracts"]["A06_api_contracts"]

    # 1. OpenAPI / Swagger specs
    spec_files = find_files(
        target_dir,
        lambda name, path: (
            path.resolve() != self_path
            and (
                name.lower().startswith(("openapi.", "swagger."))
                or name.lower() in ("openapi.json", "openapi.yaml", "openapi.yml", "swagger.json", "swagger.yaml", "swagger.yml")
            )
        ),
        max_depth=4,
        ignored_dirs=BASE_IGNORED_DIRS,
    )

    if spec_files:
        rel_specs = ", ".join(str(f.relative_to(target_dir)) for f in spec_files)
        a06["checks"].append({
            "id": "A06-OPENAPI",
            "name": "OpenAPI / Swagger Specs",
            "status": "PASS",
            "severity": "PASS",
            "message": f"OpenAPI/Swagger specification found: {rel_specs}",
        })
    else:
        a06["checks"].append({
            "id": "A06-OPENAPI",
            "name": "OpenAPI / Swagger Specs",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No OpenAPI or Swagger specification files found (openapi.*, swagger.*)",
        })

    # 2. Route definitions / Controller catalog
    routes_found = False
    routes_location = ""

    route_dir_names = {"routes", "controllers", "api", "endpoints"}
    found_route_dirs = []
    try:
        for ent in target_dir.iterdir():
            if ent.is_dir() and ent.name.lower() in route_dir_names:
                found_route_dirs.append(ent.name)
    except (PermissionError, OSError):
        pass

    if found_route_dirs:
        routes_found = True
        routes_location = f"Directory {', '.join(found_route_dirs)}"
    else:
        route_file_names = {
            "routes.py", "router.py", "urls.py", "api.py",
            "routes.js", "routes.ts", "router.js", "router.ts",
        }
        route_files = find_files(
            target_dir,
            lambda name, path: name.lower() in route_file_names,
            max_depth=4,
            ignored_dirs=DOC_IGNORED_DIRS,
        )
        if route_files:
            routes_found = True
            routes_location = str(route_files[0].relative_to(target_dir))
        else:
            route_code_pat = re.compile(
                r"(?:@app\.(?:route|get|post|put|delete|patch)|@router\.(?:get|post|put|delete|patch)|app\.(?:get|post|put|delete|patch)\s*\(|router\.(?:get|post|put|delete|patch)\s*\(|path\s*==\s*['\"]/api/|['\"]/api/[a-zA-Z0-9_\-/]+['\"])"
            )
            for f in code_files:
                content = safe_read(f)
                if route_code_pat.search(content):
                    routes_found = True
                    routes_location = str(f.relative_to(target_dir))
                    break

    if routes_found:
        a06["checks"].append({
            "id": "A06-ROUTES",
            "name": "Route Definitions & Catalog",
            "status": "PASS",
            "severity": "PASS",
            "message": f"Route definitions or controller catalog detected ({routes_location})",
        })
    else:
        a06["checks"].append({
            "id": "A06-ROUTES",
            "name": "Route Definitions & Catalog",
            "status": "WARN",
            "severity": "WARNING",
            "message": "No route definitions, controller directories, or API endpoints detected",
        })

    # ── Summary Calculations ─────────────────────────────────────────────────
    total = 0
    passed = 0
    warnings = 0
    critical = 0

    for contract in report["contracts"].values():
        for check in contract["checks"]:
            total += 1
            if check["severity"] == "CRITICAL" or check["status"] == "FAIL":
                critical += 1
            elif check["severity"] == "WARNING" or check["status"] == "WARN":
                warnings += 1
            else:
                passed += 1

    report["summary"]["total"] = total
    report["summary"]["passed"] = passed
    report["summary"]["warnings"] = warnings
    report["summary"]["critical"] = critical

    return report


def render_terminal_report(report: dict, strict: bool = False) -> tuple[str, bool]:
    lines = []
    lines.append("================================================================================")
    lines.append("TECHNICAL CONTRACTS AUDIT REPORT")
    lines.append(f"Target: {report['target']}")
    lines.append(f"Timestamp: {report['timestamp']}")
    lines.append("Mode: Technical Contracts Gate (Zero-Dependency)")
    lines.append("================================================================================")
    lines.append("")

    for contract in report["contracts"].values():
        lines.append(f"[{contract['id']}] {contract['name']}")
        for check in contract["checks"]:
            if check["severity"] == "CRITICAL" or check["status"] == "FAIL":
                icon = "[FAIL]"
            elif check["severity"] == "WARNING" or check["status"] == "WARN":
                icon = "[WARN]"
            else:
                icon = "[PASS]"
            lines.append(f"  {icon} {check['name']}: {check['message']}")
        lines.append("")

    lines.append("================================================================================")
    lines.append(
        f"Summary: {report['summary']['passed']} passed, {report['summary']['warnings']} warning(s), {report['summary']['critical']} critical failure(s)"
    )

    passed_verdict = False
    if report["summary"]["critical"] > 0:
        lines.append("Result: FAILED (Critical checks failed)")
        passed_verdict = False
    elif strict and report["summary"]["warnings"] > 0:
        lines.append("Result: FAILED (Strict mode: warnings treated as errors)")
        passed_verdict = False
    else:
        lines.append("Result: PASSED (All critical checks satisfied)")
        passed_verdict = True
    lines.append("================================================================================")

    return "\n".join(lines), passed_verdict


def validate_technical(cwd: Path, strict: bool = False, json_output: bool = False) -> int:
    report = audit_technical_contracts(cwd)
    text, passed = render_terminal_report(report, strict=strict)

    if json_output:
        report["summary"]["verdict"] = "PASSED" if passed else "FAILED"
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(text)

    return 0 if passed else 1


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="q-audit-validator: Deterministic audit quality gate for q-agent Plan C"
    )
    parser.add_argument("--cwd", default=".", help="Project root directory")
    parser.add_argument(
        "--mode",
        choices=["legacy", "manifest", "technical", "contracts"],
        default="legacy",
        help="legacy = monolithic BLUEPRINT.md, manifest = individual A*.md files, technical/contracts = deterministic technical contracts gate",
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
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors in technical mode",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON in technical mode",
    )

    args = parser.parse_args()
    cwd = Path(args.cwd)

    if args.mode in ("technical", "contracts"):
        sys.exit(validate_technical(cwd, strict=args.strict, json_output=args.json))
    elif args.mode == "manifest":
        manifest_path = Path(args.manifest) if args.manifest else (
            Path(__file__).parent.parent.parent / "references" / "audit-manifest.yml"
        )
        sys.exit(validate_manifest(cwd, manifest_path, args.level))
    else:
        sys.exit(validate_legacy(cwd))


if __name__ == "__main__":
    main()

