from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from migrate import initialize_legacy, insert_legacy_ticket, migrate_add_sla


class MigrationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "legacy.db"
        initialize_legacy(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_migration_is_idempotent_and_preserves_rows(self) -> None:
        critical = insert_legacy_ticket(
            self.db_path, 1, "Outage", "CRITICAL", datetime(2026, 10, 20, 9, 0)
        )
        low = insert_legacy_ticket(self.db_path, 2, "Question", "LOW", datetime(2026, 10, 20, 9, 0))
        migrate_add_sla(self.db_path)
        migrate_add_sla(self.db_path)
        with sqlite3.connect(self.db_path) as connection:
            rows = connection.execute("SELECT id, due_at FROM tickets ORDER BY id").fetchall()
            self.assertEqual(
                rows,
                [
                    (critical, "2026-10-20T11:00:00"),
                    (low, "2026-10-23T09:00:00"),
                ],
            )

    def test_unsupported_priority_rolls_back_schema_and_data_mutation(self) -> None:
        insert_legacy_ticket(
            self.db_path, 1, "Bad legacy row", "UNKNOWN", datetime(2026, 10, 20, 9, 0)
        )
        with self.assertRaises(ValueError):
            migrate_add_sla(self.db_path)
        with sqlite3.connect(self.db_path) as connection:
            columns = [row[1] for row in connection.execute("PRAGMA table_info(tickets)")]
            self.assertNotIn("due_at", columns)
