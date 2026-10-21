"""Staged SQLite helpdesk implementation."""

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
