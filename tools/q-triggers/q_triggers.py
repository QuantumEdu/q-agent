"""GitHub event triggers for q-agent.

Turns external events into candidate work. This is the piece that makes the
orchestrator proactive instead of conversational.

Discipline borrowed from the dsh-superagent design:

  1. The gate is deterministic and runs BEFORE any model. Who may ask, in what
     scope, with what strength. A message can never change policy by asking.
  2. Observe mode records what would have happened without doing it. Trust is
     earned by reading the log, not by reading the prompt.
  3. Every trigger carries a stable id, so a poll that overlaps the previous one
     cannot create a second ticket for the same event.
  4. A Source holds its own cursor: a restart must not replay events.

The gate is a pure function (see `gate`) so its behaviour is testable without a
network, a repository, or a model.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TICKETS_DIR = HERE.parent / "q-tickets"
if str(TICKETS_DIR) not in sys.path:
    sys.path.insert(0, str(TICKETS_DIR))

import q_tickets  # noqa: E402

DEFAULT_CONFIG = Path(".q-agent.json")

# Admission cells, mirroring a conservative default: on-list people may produce
# inferred candidates; off-list people are ignored unless a scope says otherwise.
DEFAULT_ADMISSION = {
    "on_list_not_addressing": "inferred",
    "off_list_addressing": "ignore",
    "off_list_not_addressing": "ignore",
}

POLICY_VERSION_FALLBACK = "1"


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_config(cwd: Path) -> dict:
    path = cwd / DEFAULT_CONFIG
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"refused: {path} is not valid JSON ({exc})")


def source_config(config: dict) -> dict:
    triggers = (config.get("triggers") or {})
    github = ((triggers.get("sources") or {}).get("github") or {})
    admission = dict(DEFAULT_ADMISSION)
    admission.update(github.get("admission") or {})
    return {
        "enabled": bool(triggers.get("enabled")),
        "policy_version": str(triggers.get("policy_version", POLICY_VERSION_FALLBACK)),
        "repo": github.get("repo"),
        "accept_mode": github.get("accept_mode", "observe"),
        "mention": github.get("mention", "@q-agent"),
        "allowed_senders": [s.lower() for s in github.get("allowed_senders") or []],
        "bots": [b.lower() for b in github.get("bots") or []],
        "watch": github.get("watch") or ["issues", "issue_comment", "pull_request", "ci"],
        "admission": admission,
    }


def is_bot(actor: str) -> bool:
    return actor.endswith("[bot]") or actor.lower().endswith("-bot")


def gate(
    *,
    actor: str,
    text: str,
    kind: str,
    cfg: dict,
) -> dict:
    """Decide the strength of one event. Pure: no I/O, no model, no clock.

    Returns {"strength": "explicit"|"inferred"|"not_admitted", "reason": str}.
    """
    actor_l = (actor or "").lower()
    body = text or ""
    addresses_agent = cfg["mention"].lower() in body.lower()

    if kind not in cfg["watch"]:
        return {"strength": "not_admitted", "reason": f"kind {kind!r} not watched"}

    if is_bot(actor):
        if actor_l in cfg["bots"] and addresses_agent:
            return {"strength": "inferred", "reason": "allowlisted bot addressing the agent"}
        return {"strength": "not_admitted", "reason": "bots other than the allowlist"}

    on_list = actor_l in cfg["allowed_senders"]

    if on_list and addresses_agent:
        return {"strength": "explicit", "reason": "allowlisted sender addressing the agent"}

    cell = "on_list_not_addressing" if on_list else (
        "off_list_addressing" if addresses_agent else "off_list_not_addressing"
    )
    decision = cfg["admission"].get(cell, "ignore")
    if decision == "ignore":
        return {"strength": "not_admitted", "reason": f"admission cell {cell} ignores"}
    return {"strength": decision, "reason": f"admission cell {cell} -> {decision}"}


def gh(args: list[str], *, timeout: int = 25) -> object:
    try:
        out = subprocess.run(
            ["gh", *args], capture_output=True, text=True, timeout=timeout, check=False
        )
    except FileNotFoundError:
        raise SystemExit("refused: gh CLI not found on PATH")
    except subprocess.TimeoutExpired:
        raise SystemExit(f"refused: gh {' '.join(args)} timed out after {timeout}s")
    if out.returncode != 0:
        raise SystemExit(f"refused: gh {' '.join(args)} failed: {out.stderr.strip()[:300]}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        raise SystemExit("refused: gh returned non-JSON output")


def fetch_events(repo: str, limit: int) -> list[dict]:
    """Collect a bounded, most-recently-updated slice of repository events.

    Read-only: this function never writes to GitHub.
    """
    events: list[dict] = []
    issues = gh(["api", f"repos/{repo}/issues?state=open&sort=updated&direction=desc&per_page={limit}"])
    for item in issues if isinstance(issues, list) else []:
        kind = "pull_request" if item.get("pull_request") else "issues"
        events.append({
            "trigger_id": f"github:{kind}:{item['id']}",
            "kind": kind,
            "actor": (item.get("user") or {}).get("login", ""),
            "text": f"{item.get('title') or ''}\n{item.get('body') or ''}",
            "number": item.get("number"),
            "url": item.get("html_url"),
            "updated_at": item.get("updated_at"),
            "title": item.get("title") or f"{kind} #{item.get('number')}",
        })

    comments = gh(["api", f"repos/{repo}/issues/comments?sort=updated&direction=desc&per_page={limit}"])
    for item in comments if isinstance(comments, list) else []:
        events.append({
            "trigger_id": f"github:issue_comment:{item['id']}",
            "kind": "issue_comment",
            "actor": (item.get("user") or {}).get("login", ""),
            "text": item.get("body") or "",
            "number": item.get("issue_url", "").rsplit("/", 1)[-1] or None,
            "url": item.get("html_url"),
            "updated_at": item.get("updated_at"),
            "title": f"comment by {(item.get('user') or {}).get('login', '?')}",
        })
    return events


def seen(db, trigger_id: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM events WHERE kind = 'trigger.seen' AND payload LIKE ?",
        (f'%"{trigger_id}"%',),
    ).fetchone()
    return row is not None


def poll(cwd: Path, *, observe: bool, limit: int) -> dict:
    cfg = source_config(load_config(cwd))
    if not cfg["enabled"]:
        return {"status": "disabled", "reason": "triggers.enabled is false or missing"}
    if not cfg["repo"]:
        raise SystemExit("refused: triggers.sources.github.repo is required")
    if not cfg["allowed_senders"]:
        raise SystemExit("refused: triggers.sources.github.allowed_senders is empty; "
                         "an empty allowlist makes every request inadmissible")

    db_path = q_tickets.resolve_db()
    if not db_path.is_absolute():
        db_path = cwd / db_path
    db = q_tickets.connect(db_path)
    accepted, ignored, rejected, duplicates = [], [], 0, 0
    try:
        for event in fetch_events(cfg["repo"], limit):
            decision = gate(actor=event["actor"], text=event["text"], kind=event["kind"], cfg=cfg)
            if decision["strength"] == "not_admitted":
                rejected += 1
                continue
            if seen(db, event["trigger_id"]):
                duplicates += 1
                continue

            with db:
                q_tickets.record(db, "trigger.seen", {
                    "trigger_id": event["trigger_id"],
                    "actor": event["actor"],
                    "strength": decision["strength"],
                    "reason": decision["reason"],
                }, thread_id=f"github:{event['number']}")

            if observe or cfg["accept_mode"] == "observe":
                ignored.append({**event, "strength": decision["strength"], "action": "would_open"})
                continue

            ticket_id, created = q_tickets.open_ticket(
                db,
                trigger_id=event["trigger_id"],
                title=event["title"],
                source="github",
                actor=event["actor"],
                strength=decision["strength"],
                scope="local-write",
                policy_version=cfg["policy_version"],
                thread_id=f"github:{event['number']}",
                rules={"reason": decision["reason"], "url": event["url"]},
            )
            accepted.append({"ticket": ticket_id, "created": created, "trigger_id": event["trigger_id"],
                             "strength": decision["strength"], "title": event["title"]})
    finally:
        db.close()

    return {
        "status": "observed" if (observe or cfg["accept_mode"] == "observe") else "opened",
        "repo": cfg["repo"],
        "policy_version": cfg["policy_version"],
        "accepted": accepted,
        "candidates": ignored,
        "rejected": rejected,
        "duplicates": duplicates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GitHub triggers for q-agent")
    parser.add_argument("--cwd", default=".", help="project root holding .q-agent.json")
    parser.add_argument("--json", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("poll", help="fetch events and apply the gate")
    p.add_argument("--observe", action="store_true", help="record candidates without opening tickets")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("gate", help="evaluate a single event against the policy")
    p.add_argument("--actor", required=True)
    p.add_argument("--text", required=True)
    p.add_argument("--kind", default="issue_comment")

    sub.add_parser("status", help="show the resolved trigger configuration")
    args = parser.parse_args(argv)

    cwd = Path(args.cwd).resolve()
    if args.command == "poll":
        result = poll(cwd, observe=args.observe, limit=args.limit)
    elif args.command == "gate":
        cfg = source_config(load_config(cwd))
        result = gate(actor=args.actor, text=args.text, kind=args.kind, cfg=cfg)
    else:
        cfg = source_config(load_config(cwd))
        cfg["allowed_senders"] = cfg["allowed_senders"]
        result = cfg

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
