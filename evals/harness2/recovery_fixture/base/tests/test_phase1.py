from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from helpdesk import create_tenant, create_ticket, initialize


class StorageSliceTest(unittest.TestCase):
    def test_wal_tenant_validation_and_due_date(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "helpdesk.db"
            initialize(db_path)
            tenant_id = create_tenant(db_path, "Alpha")
            ticket_id = create_ticket(
                db_path, tenant_id, "Outage", "CRITICAL", datetime(2026, 10, 20, 9, 0)
            )
            with sqlite3.connect(db_path) as connection:
                self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
                self.assertEqual(
                    connection.execute(
                        "SELECT due_at FROM tickets WHERE id = ?", (ticket_id,)
                    ).fetchone()[0],
                    "2026-10-20T11:00:00",
                )
            with self.assertRaises(ValueError):
                create_ticket(db_path, tenant_id + 99, "Other", "LOW", datetime(2026, 10, 20, 9, 0))
