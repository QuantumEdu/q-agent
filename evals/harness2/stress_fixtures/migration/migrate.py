"""Migration utilities for a legacy helpdesk database."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SLA_HOURS = {"CRITICAL": 2, "HIGH": 8, "MEDIUM": 24, "LOW": 72}


def initialize_legacy(db_path: str | Path) -> None:
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute(
            """
            CREATE TABLE tickets (
                id INTEGER PRIMARY KEY,
                tenant_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                priority TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                state TEXT NOT NULL
            )
            """
        )


def insert_legacy_ticket(
    db_path: str | Path, tenant_id: int, title: str, priority: str, opened_at: datetime
) -> int:
    with sqlite3.connect(db_path) as connection:
        return int(
            connection.execute(
                """
                INSERT INTO tickets (tenant_id, title, priority, opened_at, state)
                VALUES (?, ?, ?, ?, 'OPEN')
                """,
                (tenant_id, title, priority, opened_at.isoformat()),
            ).lastrowid
        )
