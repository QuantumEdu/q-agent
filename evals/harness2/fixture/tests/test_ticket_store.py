from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ticket_store import create_ticket, initialize, overdue_ticket_ids, transition_ticket


class TicketStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "tickets.db"
        initialize(self.db_path)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sqlite_uses_wal_mode(self) -> None:
        with sqlite3.connect(self.db_path) as connection:
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")

    def test_ticket_lifecycle_rejects_invalid_transition_without_mutating_state(self) -> None:
        ticket_id = create_ticket(
            self.db_path, "Restore customer access", "HIGH", datetime(2026, 10, 20, 9, 0)
        )
        transition_ticket(self.db_path, ticket_id, "IN_PROGRESS")
        transition_ticket(self.db_path, ticket_id, "RESOLVED")
        transition_ticket(self.db_path, ticket_id, "CLOSED")
        with self.assertRaises(ValueError):
            transition_ticket(self.db_path, ticket_id, "OPEN")
        with sqlite3.connect(self.db_path) as connection:
            state = connection.execute(
                "SELECT state FROM tickets WHERE id = ?", (ticket_id,)
            ).fetchone()[0]
        self.assertEqual(state, "CLOSED")

    def test_overdue_excludes_resolved_and_closed_tickets(self) -> None:
        opened_at = datetime(2026, 10, 20, 9, 0)
        overdue = create_ticket(self.db_path, "Page outage", "CRITICAL", opened_at)
        resolved = create_ticket(self.db_path, "Import error", "CRITICAL", opened_at)
        closed = create_ticket(self.db_path, "Report typo", "CRITICAL", opened_at)
        transition_ticket(self.db_path, resolved, "IN_PROGRESS")
        transition_ticket(self.db_path, resolved, "RESOLVED")
        transition_ticket(self.db_path, closed, "IN_PROGRESS")
        transition_ticket(self.db_path, closed, "RESOLVED")
        transition_ticket(self.db_path, closed, "CLOSED")
        self.assertEqual(
            overdue_ticket_ids(self.db_path, datetime(2026, 10, 20, 11, 1)), [overdue]
        )


if __name__ == "__main__":
    unittest.main()
