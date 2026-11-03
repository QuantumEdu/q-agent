"""Durable ticket store for q-agent.

Implements the minimum domain model needed for proactive, resumable work:
Trigger -> Ticket -> Mandate -> Assignment, plus Subscriptions, Attention and an
append-only event log. Every write is transactional under SQLite WAL so a crash
between two agent turns cannot lose or double-apply a decision.

Design constraints from the q-agent constitution:
  - Zero external dependencies (stdlib sqlite3 only).
  - Deterministic: all state transitions are explicit, no inference at write time.
  - Idempotent: a trigger_id can create exactly one ticket.
  - Attention is a budget, not a log: only three classes may request a human.

The store is not a sandbox. It records authority; it does not grant it.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1

TICKET_OPEN = "open"
TICKET_ENDED = "ended"

ASSIGNMENT_PENDING = "pending"
ASSIGNMENT_RUNNING = "running"
ASSIGNMENT_ENDED = "ended"

REPORT_STATES = ("progress", "waiting", "ready", "blocked", "failed", "dropped")

# The only three reasons that may cost a human's attention. Everything else is
# recorded and stays silent. See references/attention-policy.md.
ATTENTION_CLASSES = ("actionable_result", "blocking_decision", "hard_stop")

DEFAULT_DB = Path(".q-agent") / "tickets.db"


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_db(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("Q_AGENT_TICKETS_DB")
    if env:
        return Path(env)
    return DEFAULT_DB


def connect(path: Path) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=FULL")
    db.execute("PRAGMA foreign_keys=ON")
    schema(db)
    return db


def schema(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS mandates (
            id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL,
            policy_version TEXT NOT NULL,
            scope TEXT NOT NULL,
            strength TEXT NOT NULL CHECK (strength IN ('explicit', 'inferred')),
            actor TEXT NOT NULL,
            source TEXT NOT NULL,
            rules TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            trigger_id TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            title TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('open', 'ended')),
            mandate_id TEXT NOT NULL REFERENCES mandates (id),
            stopped_by TEXT,
            stopped_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL REFERENCES tickets (id),
            executor TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('pending', 'running', 'ended')),
            report TEXT,
            summary TEXT,
            evidence TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            ticket_id TEXT NOT NULL REFERENCES tickets (id),
            thread_id TEXT NOT NULL,
            kind TEXT NOT NULL DEFAULT 'work',
            created_at TEXT NOT NULL,
            PRIMARY KEY (ticket_id, thread_id)
        );

        CREATE TABLE IF NOT EXISTS attention (
            id TEXT PRIMARY KEY,
            ticket_id TEXT NOT NULL REFERENCES tickets (id),
            class TEXT NOT NULL CHECK (class IN
                ('actionable_result', 'blocking_decision', 'hard_stop')),
            question TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('open', 'answered', 'withdrawn')),
            answer TEXT,
            created_at TEXT NOT NULL,
            answered_at TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id TEXT,
            thread_id TEXT,
            kind TEXT NOT NULL,
            payload TEXT NOT NULL,
            at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS cursors (
            thread_id TEXT PRIMARY KEY,
            position TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_tickets_state ON tickets (state);
        CREATE INDEX IF NOT EXISTS idx_assignments_ticket ON assignments (ticket_id);
        CREATE INDEX IF NOT EXISTS idx_events_ticket ON events (ticket_id);
        CREATE INDEX IF NOT EXISTS idx_attention_open ON attention (state);
        """
    )
    db.execute(
        "INSERT OR IGNORE INTO meta (key, value) VALUES ('schema_version', ?)",
        (str(SCHEMA_VERSION),),
    )
    db.commit()


def record(db: sqlite3.Connection, kind: str, payload: dict, *, ticket_id=None, thread_id=None) -> None:
    db.execute(
        "INSERT INTO events (ticket_id, thread_id, kind, payload, at) VALUES (?, ?, ?, ?, ?)",
        (ticket_id, thread_id, kind, json.dumps(payload, sort_keys=True), utcnow()),
    )


def next_ticket_id(db: sqlite3.Connection) -> str:
    row = db.execute("SELECT value FROM meta WHERE key = 'ticket_seq'").fetchone()
    seq = int(row["value"]) if row else 0
    seq += 1
    db.execute(
        "INSERT INTO meta (key, value) VALUES ('ticket_seq', ?) "
        "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
        (str(seq),),
    )
    return f"T-{seq:04d}"


def open_ticket(
    db: sqlite3.Connection,
    *,
    trigger_id: str,
    title: str,
    source: str,
    actor: str,
    strength: str = "explicit",
    scope: str = "local-write",
    policy_version: str = "local",
    thread_id: str | None = None,
    rules: dict | None = None,
) -> tuple[str, bool]:
    """Create a ticket, or return the existing one for this trigger.

    Returns (ticket_id, created). A repeated trigger_id is a no-op: accepting the
    same event twice must not produce two tickets.
    """
    existing = db.execute(
        "SELECT id FROM tickets WHERE trigger_id = ?", (trigger_id,)
    ).fetchone()
    if existing:
        return existing["id"], False

    with db:
        ticket_id = next_ticket_id(db)
        mandate_id = f"M-{uuid.uuid4().hex[:12]}"
        now = utcnow()
        db.execute(
            "INSERT INTO mandates (id, ticket_id, policy_version, scope, strength, actor, source, rules, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (mandate_id, ticket_id, policy_version, scope, strength, actor, source,
             json.dumps(rules or {}, sort_keys=True), now),
        )
        db.execute(
            "INSERT INTO tickets (id, trigger_id, source, title, state, mandate_id, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ticket_id, trigger_id, source, title, TICKET_OPEN, mandate_id, now, now),
        )
        if thread_id:
            db.execute(
                "INSERT OR IGNORE INTO subscriptions (ticket_id, thread_id, kind, created_at) VALUES (?, ?, 'work', ?)",
                (ticket_id, thread_id, now),
            )
        record(db, "ticket.opened", {"trigger_id": trigger_id, "strength": strength, "actor": actor},
               ticket_id=ticket_id, thread_id=thread_id)
    return ticket_id, True


def subscribe(db: sqlite3.Connection, ticket_id: str, thread_id: str, kind: str = "work") -> None:
    with db:
        db.execute(
            "INSERT OR IGNORE INTO subscriptions (ticket_id, thread_id, kind, created_at) VALUES (?, ?, ?, ?)",
            (ticket_id, thread_id, kind, utcnow()),
        )
        record(db, "subscription.added", {"thread_id": thread_id, "kind": kind}, ticket_id=ticket_id)


def subscribers(db: sqlite3.Connection, thread_id: str) -> list[str]:
    rows = db.execute(
        "SELECT DISTINCT s.ticket_id FROM subscriptions s "
        "JOIN tickets t ON t.id = s.ticket_id "
        "WHERE s.thread_id = ? AND t.state = 'open' AND t.stopped_by IS NULL",
        (thread_id,),
    ).fetchall()
    return [r["ticket_id"] for r in rows]


def fanout(db: sqlite3.Connection, thread_id: str, text: str) -> list[str]:
    """Deliver a thread message to subscribed tickets as context.

    Fan-out grants no new authority: it only appends context to tickets that
    already hold a mandate.
    """
    targets = subscribers(db, thread_id)
    if not targets:
        return []
    with db:
        for ticket_id in targets:
            record(db, "fanout", {"thread_id": thread_id, "text": text}, ticket_id=ticket_id)
    return targets


def assign(db: sqlite3.Connection, ticket_id: str, executor: str) -> str:
    ticket = require_ticket(db, ticket_id)
    if ticket["state"] == TICKET_ENDED:
        raise SystemExit(f"refused: ticket {ticket_id} is ended; resume it first")
    with db:
        now = utcnow()
        assignment_id = f"A-{uuid.uuid4().hex[:12]}"
        db.execute(
            "INSERT INTO assignments (id, ticket_id, executor, state, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (assignment_id, ticket_id, executor, ASSIGNMENT_PENDING, now, now),
        )
        record(db, "assignment.created", {"executor": executor}, ticket_id=ticket_id)
    return assignment_id


def start(db: sqlite3.Connection, assignment_id: str) -> None:
    with db:
        cur = db.execute(
            "UPDATE assignments SET state = 'running', updated_at = ? "
            "WHERE id = ? AND state = 'pending'",
            (utcnow(), assignment_id),
        )
        if cur.rowcount == 0:
            raise SystemExit(f"refused: assignment {assignment_id} is not pending")
        record(db, "assignment.started", {"assignment_id": assignment_id})


def report(
    db: sqlite3.Connection,
    ticket_id: str,
    assignment_id: str,
    state: str,
    summary: str,
    *,
    evidence: str | None = None,
    end_ticket: bool = False,
) -> str | None:
    """Record an assignment report.

    Returns the attention id when the report escalates, otherwise None. Only
    'ready' (with a human-facing result), 'blocked' and 'failed' escalate; the
    caller decides the class explicitly through request_attention.
    """
    if state not in REPORT_STATES:
        raise SystemExit(f"refused: unknown report state {state!r}")
    require_ticket(db, ticket_id)
    with db:
        terminal = state in ("ready", "blocked", "failed", "dropped")
        cur = db.execute(
            "UPDATE assignments SET state = ?, report = ?, summary = ?, evidence = ?, updated_at = ? WHERE id = ?",
            (ASSIGNMENT_ENDED if terminal else ASSIGNMENT_RUNNING, state, summary, evidence, utcnow(), assignment_id),
        )
        if cur.rowcount == 0:
            raise SystemExit(f"refused: unknown assignment {assignment_id}")
        record(db, "assignment.report",
               {"state": state, "summary": summary, "evidence": evidence}, ticket_id=ticket_id)
        if end_ticket and state in ("ready", "dropped"):
            end(db, ticket_id, reason=f"report:{state}")
    return None


def end(db: sqlite3.Connection, ticket_id: str, *, reason: str) -> None:
    already = db.execute(
        "UPDATE tickets SET state = 'ended', updated_at = ? WHERE id = ? AND state = 'open'",
        (utcnow(), ticket_id),
    )
    if already.rowcount:
        record(db, "ticket.ended", {"reason": reason}, ticket_id=ticket_id)


def stop(db: sqlite3.Connection, ticket_id: str, *, by: str) -> None:
    """A person withdraws the mandate. Only a person may stop a ticket."""
    require_ticket(db, ticket_id)
    with db:
        db.execute(
            "UPDATE tickets SET state = 'ended', stopped_by = ?, stopped_at = ?, updated_at = ? WHERE id = ?",
            (by, utcnow(), utcnow(), ticket_id),
        )
        db.execute(
            "UPDATE attention SET state = 'withdrawn' WHERE ticket_id = ? AND state = 'open'",
            (ticket_id,),
        )
        record(db, "ticket.stopped", {"by": by}, ticket_id=ticket_id)


def resume(db: sqlite3.Connection, ticket_id: str, *, actor: str, policy_version: str) -> None:
    ticket = require_ticket(db, ticket_id)
    if ticket["stopped_by"]:
        raise SystemExit(f"refused: ticket {ticket_id} was stopped by {ticket['stopped_by']}")
    mandate = db.execute("SELECT * FROM mandates WHERE id = ?", (ticket["mandate_id"],)).fetchone()
    if mandate["policy_version"] != policy_version:
        raise SystemExit(
            "refused: mandate was granted under policy "
            f"{mandate['policy_version']}, current policy is {policy_version}; open a new ticket"
        )
    with db:
        db.execute("UPDATE tickets SET state = 'open', updated_at = ? WHERE id = ?", (utcnow(), ticket_id))
        record(db, "ticket.resumed", {"actor": actor}, ticket_id=ticket_id)


def request_attention(db: sqlite3.Connection, ticket_id: str, classification: str, question: str) -> str:
    """Ask a human. Restricted to the three classes the policy allows."""
    if classification not in ATTENTION_CLASSES:
        raise SystemExit(
            f"refused: {classification!r} may not cost human attention; "
            f"allowed: {', '.join(ATTENTION_CLASSES)}"
        )
    require_ticket(db, ticket_id)
    with db:
        attention_id = f"H-{uuid.uuid4().hex[:12]}"
        db.execute(
            "INSERT INTO attention (id, ticket_id, class, question, state, created_at) "
            "VALUES (?, ?, ?, ?, 'open', ?)",
            (attention_id, ticket_id, classification, question, utcnow()),
        )
        record(db, "attention.requested", {"class": classification}, ticket_id=ticket_id)
    return attention_id


def answer(db: sqlite3.Connection, attention_id: str, text: str) -> None:
    with db:
        cur = db.execute(
            "UPDATE attention SET state = 'answered', answer = ?, answered_at = ? "
            "WHERE id = ? AND state = 'open'",
            (text, utcnow(), attention_id),
        )
        if cur.rowcount == 0:
            raise SystemExit(f"refused: attention {attention_id} is not open")
        record(db, "attention.answered", {"attention_id": attention_id})


def require_ticket(db: sqlite3.Connection, ticket_id: str) -> sqlite3.Row:
    row = db.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if not row:
        raise SystemExit(f"refused: unknown ticket {ticket_id}")
    return row


def ticket_view(db: sqlite3.Connection, ticket_id: str) -> dict:
    ticket = dict(require_ticket(db, ticket_id))
    ticket["mandate"] = dict(db.execute(
        "SELECT * FROM mandates WHERE id = ?", (ticket["mandate_id"],)).fetchone())
    ticket["assignments"] = [dict(r) for r in db.execute(
        "SELECT * FROM assignments WHERE ticket_id = ? ORDER BY created_at", (ticket_id,))]
    ticket["subscriptions"] = [dict(r) for r in db.execute(
        "SELECT * FROM subscriptions WHERE ticket_id = ?", (ticket_id,))]
    ticket["attention"] = [dict(r) for r in db.execute(
        "SELECT * FROM attention WHERE ticket_id = ? ORDER BY created_at", (ticket_id,))]
    ticket["events"] = [dict(r) for r in db.execute(
        "SELECT * FROM events WHERE ticket_id = ? ORDER BY id", (ticket_id,))]
    return ticket


def list_tickets(db: sqlite3.Connection, state: str | None = None) -> list[dict]:
    sql = (
        "SELECT t.id, t.title, t.state, t.source, t.created_at, "
        "(SELECT COUNT(*) FROM attention a WHERE a.ticket_id = t.id AND a.state = 'open') AS open_attention "
        "FROM tickets t"
    )
    params: tuple = ()
    if state:
        sql += " WHERE t.state = ?"
        params = (state,)
    sql += " ORDER BY t.created_at DESC"
    return [dict(r) for r in db.execute(sql, params)]


def pending_attention(db: sqlite3.Connection) -> list[dict]:
    rows = db.execute(
        "SELECT a.*, t.title FROM attention a JOIN tickets t ON t.id = a.ticket_id "
        "WHERE a.state = 'open' ORDER BY a.created_at"
    ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Durable ticket store for q-agent")
    parser.add_argument("--db", help="path to the tickets database")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("open", help="open a ticket from a trigger")
    p.add_argument("--trigger-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--source", default="local")
    p.add_argument("--actor", required=True)
    p.add_argument("--strength", default="explicit", choices=("explicit", "inferred"))
    p.add_argument("--scope", default="local-write")
    p.add_argument("--policy-version", default="local")
    p.add_argument("--thread")

    p = sub.add_parser("list", help="list tickets")
    p.add_argument("--state", choices=(TICKET_OPEN, TICKET_ENDED))

    p = sub.add_parser("show", help="show one ticket")
    p.add_argument("ticket")

    p = sub.add_parser("assign", help="assign a ticket to an executor")
    p.add_argument("ticket")
    p.add_argument("--executor", required=True)

    p = sub.add_parser("start", help="start an assignment")
    p.add_argument("assignment")

    p = sub.add_parser("report", help="record an assignment report")
    p.add_argument("ticket")
    p.add_argument("--assignment", required=True)
    p.add_argument("--state", required=True, choices=REPORT_STATES)
    p.add_argument("--summary", required=True)
    p.add_argument("--evidence")
    p.add_argument("--end", action="store_true", help="end the ticket when the report is ready/dropped")

    p = sub.add_parser("attention", help="ask a human (three classes only)")
    p.add_argument("ticket")
    p.add_argument("--class", dest="classification", required=True, choices=ATTENTION_CLASSES)
    p.add_argument("--question", required=True)

    p = sub.add_parser("answer", help="answer a pending attention request")
    p.add_argument("attention")
    p.add_argument("--text", required=True)

    p = sub.add_parser("stop", help="a person withdraws the mandate")
    p.add_argument("ticket")
    p.add_argument("--by", required=True)

    p = sub.add_parser("resume", help="resume an ended ticket under its mandate")
    p.add_argument("ticket")
    p.add_argument("--actor", required=True)
    p.add_argument("--policy-version", default="local")

    p = sub.add_parser("fanout", help="deliver a thread message to subscribed tickets")
    p.add_argument("--thread", required=True)
    p.add_argument("--text", required=True)

    p = sub.add_parser("subscribe", help="subscribe a ticket to a thread")
    p.add_argument("ticket")
    p.add_argument("--thread", required=True)
    p.add_argument("--kind", default="work", choices=("work", "context"))

    sub.add_parser("attention-queue", help="list open attention requests")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    db = connect(resolve_db(args.db))
    try:
        if args.command == "open":
            ticket_id, created = open_ticket(
                db,
                trigger_id=args.trigger_id,
                title=args.title,
                source=args.source,
                actor=args.actor,
                strength=args.strength,
                scope=args.scope,
                policy_version=args.policy_version,
                thread_id=args.thread,
            )
            echo(args, {"ticket": ticket_id, "created": created})
        elif args.command == "list":
            echo(args, list_tickets(db, args.state))
        elif args.command == "show":
            echo(args, ticket_view(db, args.ticket))
        elif args.command == "assign":
            echo(args, {"assignment": assign(db, args.ticket, args.executor)})
        elif args.command == "start":
            start(db, args.assignment)
            echo(args, {"assignment": args.assignment, "state": ASSIGNMENT_RUNNING})
        elif args.command == "report":
            report(db, args.ticket, args.assignment, args.state, args.summary,
                   evidence=args.evidence, end_ticket=args.end)
            echo(args, {"ticket": args.ticket, "report": args.state})
        elif args.command == "attention":
            echo(args, {"attention": request_attention(db, args.ticket, args.classification, args.question)})
        elif args.command == "answer":
            answer(db, args.attention, args.text)
            echo(args, {"attention": args.attention, "state": "answered"})
        elif args.command == "stop":
            stop(db, args.ticket, by=args.by)
            echo(args, {"ticket": args.ticket, "state": TICKET_ENDED, "stopped_by": args.by})
        elif args.command == "resume":
            resume(db, args.ticket, actor=args.actor, policy_version=args.policy_version)
            echo(args, {"ticket": args.ticket, "state": TICKET_OPEN})
        elif args.command == "fanout":
            echo(args, {"delivered_to": fanout(db, args.thread, args.text)})
        elif args.command == "subscribe":
            subscribe(db, args.ticket, args.thread, args.kind)
            echo(args, {"ticket": args.ticket, "thread": args.thread})
        elif args.command == "attention-queue":
            echo(args, pending_attention(db))
        else:  # pragma: no cover - argparse enforces the choices
            raise SystemExit(f"unknown command {args.command}")
    finally:
        db.close()
    return 0


def echo(args: argparse.Namespace, payload) -> None:
    if getattr(args, "json", False):
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, list):
        if not payload:
            print("(empty)")
            return
        for row in payload:
            print("  ".join(f"{key}={row[key]}" for key in list(row)[:5]))
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
