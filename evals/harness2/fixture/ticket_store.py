"""SQLite storage for a support-ticket workflow."""

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
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                state TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                due_at TEXT NOT NULL
            )
            """
        )


def create_ticket(
    db_path: str | Path, title: str, priority: str, opened_at: datetime
) -> int:
    if priority not in SLA_HOURS:
        raise ValueError(f"unknown priority: {priority}")
    due_at = opened_at + timedelta(hours=SLA_HOURS[priority])
    with _connection(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO tickets (title, priority, state, opened_at, due_at)
            VALUES (?, ?, 'OPEN', ?, ?)
            """,
            (title, priority, opened_at.isoformat(), due_at.isoformat()),
        )
        return int(cursor.lastrowid)
