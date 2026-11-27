#!/usr/bin/env python3
"""
q_merge_gate.py - Deterministic Merge Policy Gate for q-agent (Deploy Gate Step 8).

Zero external dependencies.
Inspired by the merge policy and gate architecture in Super-Board (EricTechPro).

The gate inspects both the changed paths and the changed lines of the diff.
Projects extend or replace the default vocabularies through the ``merge_gate``
section of ``.q-agent.json`` (see ``templates/q-agent.json``).

Exit Codes:
  0: PROCEED                Standard / automated merge allowed.
  7: HUMAN_APPROVAL_REQUIRED Diff touches Money, Auth, or exceeds LOC threshold (>500 LOC).
  8: HUMAN_ACTION_REQUIRED   Diff modifies DB schemas/migrations; requires manual migration/runbook.
  1: ERROR                   Execution, configuration or git failure.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CATEGORIES = ("money", "auth", "schema")

# Path patterns are matched against the lower-cased repository path.
PATTERNS = {
    "money": [
        r"billing", r"stripe", r"payment", r"pago", r"cobro",
        r"pricing", r"invoice", r"subscription", r"checkout", r"tarifa",
        r"refund", r"reembolso", r"ledger", r"wallet", r"factura",
        r"(?<![a-z])sales?(?![a-z])", r"(?<![a-z])ventas?(?![a-z])",
        r"(?<![a-z])cash(?![a-z])", r"(?<![a-z])caja(?![a-z])",
        r"(?<![a-z])credits?(?![a-z])", r"(?<![a-z])abonos?(?![a-z])",
        r"(?<![a-z])prices?(?![a-z])", r"(?<![a-z])precios?(?![a-z])",
    ],
    "auth": [
        r"auth(?!or(?!i[sz]))", r"login", r"password", r"passwd", r"jwt",
        r"token(?!i[sz])", r"permission", r"session", r"credential", r"oauth", r"rbac",
        r"(?<![a-z])security(?![a-z])", r"(?<![a-z])csrf(?![a-z])",
    ],
    "schema": [
        r"migrations?/", r"schema\.sql", r"alembic", r"flyway",
        r"db/migrate", r"prisma/migrations", r"knex/migrations",
        r"schema\.prisma", r"db/schema\.rb",
    ],
}

# Content patterns are matched against added/removed lines of non-excluded files.
CONTENT_PATTERNS = {
    "money": [
        r"\bDecimal\(", r"\bstripe\.", r"\b(?:unit_)?price\b", r"\bamount\b",
        r"\bcurrency\b", r"\brefund\b", r"\bsubtotal\b", r"\bprecio\b", r"\bimporte\b",
    ],
    "auth": [
        r"\bjwt\b", r"\bbcrypt\b", r"\bargon2\b", r"\bpasslib\b", r"\bhashpw\b",
        r"\b(?:check|verify)_password\b", r"\bset_cookie\b", r"\bcsrf\b",
        r"\bpassword_hash\b", r"\boauth\b",
    ],
    "schema": [
        r"(?i)\b(?:CREATE|ALTER|DROP|TRUNCATE)\s+(?:TABLE|INDEX|SCHEMA|VIEW|COLUMN)\b",
        r"\bop\.(?:create_table|drop_table|add_column|drop_column|alter_column|rename_table)\b",
        r"\bmigrations\.(?:AddField|RemoveField|AlterField|CreateModel|DeleteModel)\b",
    ],
}

# Tests, fixtures and docs legitimately mention DDL, prices and passwords.
CONTENT_EXCLUDE = [
    r"(?:^|/)(?:tests?|spec|__tests__|fixtures?)/",
    r"(?:^|/)test_[^/]*$",
    r"_test\.[a-z0-9]+$",
    r"\.(?:spec|test)\.[a-z0-9]+$",
    r"\.(?:md|rst|txt|adoc)$",
]


def parse_shortstat(out_stat):
    """Parse `git diff --shortstat` output into (insertions, deletions).

    Pure function: no I/O, never raises on arbitrary input. Malformed or
    missing counters yield 0. Kept separate so it can serve as a fuzz
    target (see tools/q-fuzz/q_fuzz.py, target ``merge-gate-shortstat``).
    """
    added = 0
    deleted = 0
    match_add = re.search(r"(\d+) insertion", out_stat or "")
    match_del = re.search(r"(\d+) deletion", out_stat or "")
    if match_add:
        added = int(match_add.group(1))
    if match_del:
        deleted = int(match_del.group(1))
    return added, deleted


def parse_unified_diff(diff_text):
    """Map each file of a `git diff -U0` output to its added/removed lines.

    Pure function: deleted files keep their ``a/`` path, renames use the new path.
    """
    changes = {}
    current = None
    old_path = None
    for line in (diff_text or "").splitlines():
        if line.startswith("--- "):
            old_path = line[6:] if line.startswith("--- a/") else None
            continue
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else old_path
            if current is not None:
                changes.setdefault(current, [])
            continue
        if current is not None and line[:1] in ("+", "-"):
            changes[current].append(line[1:])
    return changes


def run_git(args, cwd=None):
    """Run a git command and return (returncode, stdout, stderr)."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _git_diff(extra_args, base, head, cwd):
    """Run `git diff` on base...head, falling back to base head (e.g. unrelated history)."""
    code, out, err = run_git(["diff", *extra_args, f"{base}...{head}"], cwd=cwd)
    if code != 0:
        code, out, err = run_git(["diff", *extra_args, base, head], cwd=cwd)
    return code, out, err


def _default_policy():
    return {
        "patterns": {k: list(v) for k, v in PATTERNS.items()},
        "content_patterns": {k: list(v) for k, v in CONTENT_PATTERNS.items()},
        "content_exclude": list(CONTENT_EXCLUDE),
        "content_scan": True,
        "max_loc": None,
    }


def _is_regex_list(values):
    return isinstance(values, list) and all(isinstance(v, str) for v in values)


def _find_config(cwd):
    code, top, _ = run_git(["rev-parse", "--show-toplevel"], cwd=cwd)
    root = Path(top) if code == 0 and top else Path(cwd or ".")
    candidate = root / ".q-agent.json"
    return candidate if candidate.is_file() else None


def _merge_category_patterns(policy, section, key, replace):
    extra = section.get(key) or {}
    if not isinstance(extra, dict):
        return f"merge_gate.{key} must be an object of category -> [regex]"
    for category in CATEGORIES:
        values = extra.get(category)
        if values is None:
            if replace:
                policy[key][category] = []
            continue
        if not _is_regex_list(values):
            return f"merge_gate.{key}.{category} must be a list of regex strings"
        policy[key][category] = list(values) if replace else policy[key][category] + list(values)
    return None


def _merge_section(policy, section):
    replace = bool(section.get("replace_defaults", False))
    for key in ("patterns", "content_patterns"):
        err = _merge_category_patterns(policy, section, key, replace)
        if err:
            return err
    exclude = section.get("content_exclude")
    if exclude is not None:
        if not _is_regex_list(exclude):
            return "merge_gate.content_exclude must be a list of regex strings"
        policy["content_exclude"] = list(exclude) if replace else policy["content_exclude"] + list(exclude)
    if "content_scan" in section:
        policy["content_scan"] = bool(section["content_scan"])
    if isinstance(section.get("max_loc"), int):
        policy["max_loc"] = section["max_loc"]
    return None


def _invalid_regex(policy):
    for key in ("patterns", "content_patterns"):
        for category in CATEGORIES:
            for regex in policy[key][category]:
                try:
                    re.compile(regex)
                except re.error as exc:
                    return f"Invalid regex in merge_gate.{key}.{category}: {regex!r} ({exc})"
    for regex in policy["content_exclude"]:
        try:
            re.compile(regex)
        except re.error as exc:
            return f"Invalid regex in merge_gate.content_exclude: {regex!r} ({exc})"
    return None


def load_policy(cwd=None, config_path=None):
    """Build the effective policy from defaults and an optional ``merge_gate`` config section.

    Returns (policy, source, error). ``replace_defaults: true`` discards the built-in
    vocabularies; otherwise project patterns extend them.
    """
    policy = _default_policy()
    if config_path is None:
        config_path = _find_config(cwd)
        if config_path is None:
            return policy, None, None
    config_path = Path(config_path)
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, str(config_path), f"Cannot read merge gate config {config_path}: {exc}"
    section = data.get("merge_gate") if isinstance(data, dict) else None
    if not isinstance(section, dict):
        return policy, None, None
    err = _merge_section(policy, section) or _invalid_regex(policy)
    if err:
        return None, str(config_path), err
    return policy, str(config_path), None


def _first_match(patterns, text):
    for pattern in patterns:
        if re.search(pattern, text):
            return pattern
    return None


def match_paths(changed_files, patterns):
    """Return {category: [path, ...]} for paths matching each category's patterns."""
    matched = {category: [] for category in CATEGORIES}
    for path in changed_files:
        path_lower = path.lower()
        for category in CATEGORIES:
            if _first_match(patterns.get(category, []), path_lower):
                matched[category].append(path)
    return matched


def scan_content(changes, content_patterns, exclude):
    """Return {category: [path, ...]} for files whose changed lines match content patterns."""
    matched = {category: [] for category in CATEGORIES}
    for path, lines in changes.items():
        if _first_match(exclude, path.lower()):
            continue
        body = "\n".join(lines)
        for category in CATEGORIES:
            if _first_match(content_patterns.get(category, []), body):
                matched[category].append(path)
    return matched


def decide(findings, total_loc, max_loc):
    """Return (exit_code, status, reasons) for the combined path/content findings."""
    reasons = []
    exit_code, status = 0, "PROCEED"
    if findings["schema"]:
        exit_code, status = 8, "HUMAN_ACTION_REQUIRED"
        reasons.append(f"Database schema/migration changes ({len(findings['schema'])} file(s))")
    needs_approval = findings["money"] or findings["auth"] or total_loc > max_loc
    if needs_approval and exit_code != 8:
        exit_code, status = 7, "HUMAN_APPROVAL_REQUIRED"
    if findings["money"]:
        reasons.append(f"Financial/Billing domain changes ({len(findings['money'])} file(s))")
    if findings["auth"]:
        reasons.append(f"Authentication/Security domain changes ({len(findings['auth'])} file(s))")
    if total_loc > max_loc:
        reasons.append(f"Diff blast radius ({total_loc} LOC) exceeds slice limit ({max_loc} LOC)")
    return exit_code, status, reasons


def analyze_diff(base="main", head="HEAD", max_loc=500, cwd=None, config_path=None, content_scan=None):
    """Analyze diff between base and head for risks and blast radius."""
    policy, config_source, err = load_policy(cwd=cwd, config_path=config_path)
    if err:
        return None, err
    if max_loc is None:
        max_loc = policy["max_loc"] if policy["max_loc"] is not None else 500
    scan = policy["content_scan"] if content_scan is None else content_scan

    code, out, err = _git_diff(["--name-only"], base, head, cwd)
    if code != 0:
        return None, f"Git diff name-only failed: {err}"
    changed_files = [f for f in out.splitlines() if f.strip()]

    code, out_stat, err = _git_diff(["--shortstat"], base, head, cwd)
    if code != 0:
        return None, f"Git diff shortstat failed: {err}"
    added, deleted = parse_shortstat(out_stat)
    total_loc = added + deleted

    path_findings = match_paths(changed_files, policy["patterns"])
    content_findings = {category: [] for category in CATEGORIES}
    if scan:
        code, diff_text, err = _git_diff(
            ["-U0", "--no-color", "--no-ext-diff", "--src-prefix=a/", "--dst-prefix=b/"], base, head, cwd
        )
        if code != 0:
            return None, f"Git diff content failed: {err}"
        content_findings = scan_content(
            parse_unified_diff(diff_text), policy["content_patterns"], policy["content_exclude"]
        )

    findings = {
        category: sorted(set(path_findings[category]) | set(content_findings[category]))
        for category in CATEGORIES
    }
    exit_code, status, reasons = decide(findings, total_loc, max_loc)

    report = {
        "status": status,
        "exit_code": exit_code,
        "base": base,
        "head": head,
        "total_files": len(changed_files),
        "loc_added": added,
        "loc_deleted": deleted,
        "total_loc": total_loc,
        "total_loc_changed": total_loc,
        "max_loc_threshold": max_loc,
        "reasons": reasons,
        "findings": findings,
        "path_findings": path_findings,
        "content_findings": content_findings,
        "content_scan": scan,
        "config": config_source,
    }
    return report, None


def render_text(report):
    status_icons = {
        "PROCEED": "🟢 [PROCEED]",
        "HUMAN_APPROVAL_REQUIRED": "🟡 [HUMAN APPROVAL REQUIRED - Exit 7]",
        "HUMAN_ACTION_REQUIRED": "🔴 [HUMAN ACTION REQUIRED - Exit 8]",
    }
    lines = [
        "================================================================================",
        "🏛️ q-agent Merge Policy Gate (Step 8 Pre-Flight)",
        f"Base: {report['base']}  |  Head: {report['head']}",
        f"Status: {status_icons.get(report['status'], report['status'])}",
        f"Blast Radius: {report['total_files']} files, +{report['loc_added']} -{report['loc_deleted']} ({report['total_loc']} LOC)",
        f"Content scan: {'on' if report['content_scan'] else 'off'}  |  Config: {report['config'] or 'defaults'}",
        "================================================================================",
    ]
    if report["reasons"]:
        lines.append("Gate Reasons:")
        lines.extend(f"  ⚠️  {r}" for r in report["reasons"])
        lines.append("")
    titles = {"schema": "Schema/Migration Files:", "money": "Money/Billing Files:", "auth": "Auth/Security Files:"}
    for category in ("schema", "money", "auth"):
        if report["findings"][category]:
            lines.append(titles[category])
            for f in report["findings"][category]:
                origin = "content" if f not in report["path_findings"][category] else "path"
                lines.append(f"  • {f} ({origin})")
    closing = {
        0: "✅ Clean slice. No restricted domains touched. Ready for automatic merge.",
        7: "✋ Human sign-off required before merge due to blast radius or domain sensitivity.",
        8: "🚨 Database operator action/verification required before applying migration.",
    }
    lines.append(closing[report["exit_code"]])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="q-agent Deterministic Merge Policy Gate"
    )
    parser.add_argument("--base", default="main", help="Base branch for comparison (default: main)")
    parser.add_argument("--head", default="HEAD", help="Head commit/branch to inspect (default: HEAD)")
    parser.add_argument("--max-loc", type=int, default=None,
                        help="Max LOC threshold before requiring approval (default: merge_gate.max_loc or 500)")
    parser.add_argument("--config", default=None,
                        help="Path to a JSON file with a merge_gate section (default: <repo>/.q-agent.json)")
    parser.add_argument("--no-content", action="store_true", help="Only inspect file paths, not changed lines")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    report, err = analyze_diff(
        base=args.base,
        head=args.head,
        max_loc=args.max_loc,
        config_path=args.config,
        content_scan=False if args.no_content else None,
    )
    if err:
        sys.stderr.write(f"Error: {err}\n")
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
