"""SQLite storage for a multi-tenant support workflow under concurrent execution."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SLA_HOURS = {"CRITICAL": 2, "HIGH": 8, "MEDIUM": 24, "LOW": 72}


def _connection(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(db_path: str | Path) -> None:
    with _connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                tenant_id INTEGER NOT NULL REFERENCES tenants(id),
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                state TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                due_at TEXT NOT NULL,
                assignee TEXT
            );
            CREATE TABLE IF NOT EXISTS ticket_events (
                id INTEGER PRIMARY KEY,
                ticket_id INTEGER NOT NULL REFERENCES tickets(id),
                old_state TEXT NOT NULL,
                new_state TEXT NOT NULL,
                actor_role TEXT NOT NULL
            );
            """
        )


def create_tenant(db_path: str | Path, name: str) -> int:
    with _connection(db_path) as connection:
        return int(connection.execute("INSERT INTO tenants (name) VALUES (?)", (name,)).lastrowid)


def create_ticket(
    db_path: str | Path, tenant_id: int, title: str, priority: str, opened_at: datetime
) -> int:
    if priority not in SLA_HOURS:
        raise ValueError(f"unsupported priority: {priority}")
    due_at = opened_at + timedelta(hours=SLA_HOURS[priority])
    with _connection(db_path) as connection:
        return int(
            connection.execute(
                """
                INSERT INTO tickets (tenant_id, title, priority, state, opened_at, due_at)
                VALUES (?, ?, ?, 'OPEN', ?, ?)
                """,
                (tenant_id, title, priority, opened_at.isoformat(), due_at.isoformat()),
            ).lastrowid
        )


def transition_ticket(
    db_path: str | Path, tenant_id: int, ticket_id: int, actor_role: str, new_state: str
) -> None:
    allowed = {
        ("OPEN", "IN_PROGRESS"): {"support"},
        ("IN_PROGRESS", "RESOLVED"): {"support"},
        ("RESOLVED", "CLOSED"): {"manager"},
    }
    with _connection(db_path) as connection:
        row = connection.execute(
            "SELECT state FROM tickets WHERE id = ? AND tenant_id = ?", (ticket_id, tenant_id)
        ).fetchone()
        if not row:
            raise ValueError("ticket not found for tenant")
        current_state = row["state"]
        edge = (current_state, new_state)
        if edge not in allowed or actor_role not in allowed[edge]:
            raise ValueError(f"invalid transition: {edge} by {actor_role}")
        connection.execute(
            "UPDATE tickets SET state = ? WHERE id = ?", (new_state, ticket_id)
        )
        connection.execute(
            """
            INSERT INTO ticket_events (ticket_id, old_state, new_state, actor_role)
            VALUES (?, ?, ?, ?)
            """,
            (ticket_id, current_state, new_state, actor_role),
        )


def overdue_ticket_ids(db_path: str | Path, tenant_id: int, now: datetime) -> list[int]:
    with _connection(db_path) as connection:
        rows = connection.execute(
            """
            SELECT id FROM tickets
            WHERE tenant_id = ?
              AND due_at < ?
              AND state NOT IN ('RESOLVED', 'CLOSED')
            ORDER BY id
            """,
            (tenant_id, now.isoformat()),
        ).fetchall()
        return [row["id"] for row in rows]
