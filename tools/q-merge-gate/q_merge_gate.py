#!/usr/bin/env python3
"""
q_merge_gate.py - Deterministic Merge Policy Gate for q-agent (Deploy Gate Step 8).

Zero external dependencies.
Inspired by the merge policy and gate architecture in Super-Board (EricTechPro).

Exit Codes:
  0: PROCEED                Standard / automated merge allowed.
  7: HUMAN_APPROVAL_REQUIRED Diff touches Money, Auth, or exceeds LOC threshold (>500 LOC).
  8: HUMAN_ACTION_REQUIRED   Diff modifies DB schemas/migrations; requires manual migration/runbook.
  1: ERROR                   Execution or git failure.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Sensitive keywords and path patterns
PATTERNS = {
    "money": [
        r"billing", r"stripe", r"payment", r"pago", r"cobro",
        r"pricing", r"invoice", r"subscription", r"checkout", r"tarifa"
    ],
    "auth": [
        r"auth", r"login", r"password", r"passwd", r"jwt",
        r"token", r"permission", r"session", r"credential", r"oauth", r"rbac"
    ],
    "schema": [
        r"migrations?/", r"schema\.sql", r"alembic", r"flyway",
        r"db/migrate", r"prisma/migrations", r"knex/migrations"
    ]
}


def run_git(args, cwd=None):
    """Run a git command and return (returncode, stdout, stderr)."""
    cmd = ["git"] + args
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def analyze_diff(base="main", head="HEAD", max_loc=500, cwd=None):
    """Analyze diff between base and head for risks and blast radius."""
    # Check changed files
    code, out, err = run_git(["diff", "--name-only", f"{base}...{head}"], cwd=cwd)
    if code != 0:
        # Fallback to direct diff if base...head fails (e.g. initial branch)
        code, out, err = run_git(["diff", "--name-only", base, head], cwd=cwd)
        if code != 0:
            return None, f"Git diff name-only failed: {err}"

    changed_files = [f for f in out.splitlines() if f.strip()]

    # Check stat for lines added/removed
    code, out_stat, _ = run_git(["diff", "--shortstat", f"{base}...{head}"], cwd=cwd)
    if code != 0:
        code, out_stat, _ = run_git(["diff", "--shortstat", base, head], cwd=cwd)

    added = 0
    deleted = 0
    match_add = re.search(r"(\d+) insertion", out_stat)
    match_del = re.search(r"(\d+) deletion", out_stat)
    if match_add:
        added = int(match_add.group(1))
    if match_del:
        deleted = int(match_del.group(1))
    total_loc = added + deleted

    # Evaluate patterns
    matched_money = []
    matched_auth = []
    matched_schema = []

    for path in changed_files:
        path_lower = path.lower()
        for p in PATTERNS["money"]:
            if re.search(p, path_lower):
                matched_money.append((path, p))
                break
        for p in PATTERNS["auth"]:
            if re.search(p, path_lower):
                matched_auth.append((path, p))
                break
        for p in PATTERNS["schema"]:
            if re.search(p, path_lower):
                matched_schema.append((path, p))
                break

    # Determine exit verdict
    reasons = []
    exit_code = 0
    status = "PROCEED"

    if matched_schema:
        exit_code = 8
        status = "HUMAN_ACTION_REQUIRED"
        reasons.append(f"Database schema/migration files touched ({len(matched_schema)} file(s))")

    if matched_money or matched_auth or total_loc > max_loc:
        # If exit_code was already 8 (schema), 8 takes precedence as critical action,
        # but both reasons are documented
        if exit_code != 8:
            exit_code = 7
            status = "HUMAN_APPROVAL_REQUIRED"

        if matched_money:
            reasons.append(f"Financial/Billing domain files touched ({len(matched_money)} file(s))")
        if matched_auth:
            reasons.append(f"Authentication/Security domain files touched ({len(matched_auth)} file(s))")
        if total_loc > max_loc:
            reasons.append(f"Diff blast radius ({total_loc} LOC) exceeds slice limit ({max_loc} LOC)")

    report = {
        "status": status,
        "exit_code": exit_code,
        "base": base,
        "head": head,
        "total_files": len(changed_files),
        "loc_added": added,
        "loc_deleted": deleted,
        "total_loc": total_loc,
        "max_loc_threshold": max_loc,
        "reasons": reasons,
        "findings": {
            "money": [p[0] for p in matched_money],
            "auth": [p[0] for p in matched_auth],
            "schema": [p[0] for p in matched_schema]
        }
    }

    return report, None


def main():
    parser = argparse.ArgumentParser(
        description="q-agent Deterministic Merge Policy Gate"
    )
    parser.add_argument("--base", default="main", help="Base branch for comparison (default: main)")
    parser.add_argument("--head", default="HEAD", help="Head commit/branch to inspect (default: HEAD)")
    parser.add_argument("--max-loc", type=int, default=500, help="Max LOC threshold before requiring approval (default: 500)")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args()

    report, err = analyze_diff(base=args.base, head=args.head, max_loc=args.max_loc)
    if err:
        sys.stderr.write(f"Error: {err}\n")
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        status_icons = {
            "PROCEED": "🟢 [PROCEED]",
            "HUMAN_APPROVAL_REQUIRED": "🟡 [HUMAN APPROVAL REQUIRED - Exit 7]",
            "HUMAN_ACTION_REQUIRED": "🔴 [HUMAN ACTION REQUIRED - Exit 8]"
        }

        print("================================================================================")
        print("🏛️ q-agent Merge Policy Gate (Step 8 Pre-Flight)")
        print(f"Base: {report['base']}  |  Head: {report['head']}")
        print(f"Status: {status_icons.get(report['status'], report['status'])}")
        print(f"Blast Radius: {report['total_files']} files, +{report['loc_added']} -{report['loc_deleted']} ({report['total_loc']} LOC)")
        print("================================================================================")

        if report["reasons"]:
            print("Gate Reasons:")
            for r in report["reasons"]:
                print(f"  ⚠️  {r}")
            print()

        if report["findings"]["schema"]:
            print("Schema/Migration Files:")
            for f in report["findings"]["schema"]:
                print(f"  • {f}")

        if report["findings"]["money"]:
            print("Money/Billing Files:")
            for f in report["findings"]["money"]:
                print(f"  • {f}")

        if report["findings"]["auth"]:
            print("Auth/Security Files:")
            for f in report["findings"]["auth"]:
                print(f"  • {f}")

        if report["exit_code"] == 0:
            print("✅ Clean slice. No restricted domains touched. Ready for automatic merge.")
        elif report["exit_code"] == 7:
            print("✋ Human sign-off required before merge due to blast radius or domain sensitivity.")
        elif report["exit_code"] == 8:
            print("🚨 Database operator action/verification required before applying migration.")

    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
