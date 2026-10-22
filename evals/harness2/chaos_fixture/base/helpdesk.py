"""SQLite storage for a multi-tenant support workflow under chaos and ungraceful crashes."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

SLA_HOURS = {"CRITICAL": 2, "HIGH": 8, "MEDIUM": 24, "LOW": 72}


def _connection(db_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode = WAL")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(db_path: str | Path) -> None:
    with _connection(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS tenants (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );
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
                actor_role TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )


def create_tenant(db_path: str | Path, name: str) -> int:
    with _connection(db_path) as connection:
        cur = connection.execute("INSERT INTO tenants (name) VALUES (?)", (name,))
        return int(cur.lastrowid)


def create_ticket(
    db_path: str | Path, tenant_id: int, title: str, priority: str, opened_at: datetime
) -> int:
    if priority not in SLA_HOURS:
        raise ValueError(f"unsupported priority: {priority}")
    if opened_at.tzinfo is None:
        opened_at = opened_at.replace(tzinfo=timezone.utc)
    due_at = opened_at + timedelta(hours=SLA_HOURS[priority])

    with _connection(db_path) as connection:
        cur = connection.execute(
            """
            INSERT INTO tickets (tenant_id, title, priority, state, opened_at, due_at)
            VALUES (?, ?, ?, 'OPEN', ?, ?)
            """,
            (tenant_id, title, priority, opened_at.isoformat(), due_at.isoformat()),
        )
        ticket_id = int(cur.lastrowid)
        connection.execute(
            """
            INSERT INTO ticket_events (ticket_id, old_state, new_state, actor_role, created_at)
            VALUES (?, 'NONE', 'OPEN', 'system', ?)
            """,
            (ticket_id, opened_at.isoformat()),
        )
        return ticket_id


def claim_ticket(
    db_path: str | Path, tenant_id: int, ticket_id: int, actor_role: str, assignee: str
) -> None:
    if actor_role != "support":
        raise ValueError(f"invalid actor role for claiming ticket: {actor_role}")
    now = datetime.now(timezone.utc)
    with _connection(db_path) as connection:
        cur = connection.execute(
            """
            UPDATE tickets
            SET state = 'IN_PROGRESS', assignee = ?
            WHERE id = ? AND tenant_id = ? AND state = 'OPEN'
            """,
            (assignee, ticket_id, tenant_id),
        )
        if cur.rowcount != 1:
            raise ValueError(f"cannot claim ticket {ticket_id}: not found or already claimed")
        connection.execute(
            """
            INSERT INTO ticket_events (ticket_id, old_state, new_state, actor_role, created_at)
            VALUES (?, 'OPEN', 'IN_PROGRESS', ?, ?)
            """,
            (ticket_id, actor_role, now.isoformat()),
        )
