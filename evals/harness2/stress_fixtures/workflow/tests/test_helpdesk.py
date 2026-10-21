from __future__ import annotations

import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from helpdesk import (
    create_tenant,
    create_ticket,
    initialize,
    overdue_ticket_ids,
    transition_ticket,
)


class HelpdeskWorkflowTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "helpdesk.db"
        initialize(self.db_path)
        self.alpha = create_tenant(self.db_path, "Alpha")
        self.beta = create_tenant(self.db_path, "Beta")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_wal_and_tenant_scoped_overdue_tickets(self) -> None:
        opened = datetime(2026, 10, 20, 9, 0)
        alpha_ticket = create_ticket(self.db_path, self.alpha, "Outage", "CRITICAL", opened)
        create_ticket(self.db_path, self.beta, "Other tenant", "CRITICAL", opened)
        with sqlite3.connect(self.db_path) as connection:
            self.assertEqual(connection.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(
            overdue_ticket_ids(self.db_path, self.alpha, datetime(2026, 10, 20, 11, 1)),
            [alpha_ticket],
        )

    def test_roles_transitions_and_audit_are_atomic(self) -> None:
        ticket_id = create_ticket(
            self.db_path, self.alpha, "Access request", "HIGH", datetime(2026, 10, 20, 9, 0)
        )
        with self.assertRaises(ValueError):
            transition_ticket(self.db_path, self.beta, ticket_id, "support", "IN_PROGRESS")
        with self.assertRaises(ValueError):
            transition_ticket(self.db_path, self.alpha, ticket_id, "manager", "RESOLVED")
        transition_ticket(self.db_path, self.alpha, ticket_id, "support", "IN_PROGRESS")
        transition_ticket(self.db_path, self.alpha, ticket_id, "support", "RESOLVED")
        with self.assertRaises(ValueError):
            transition_ticket(self.db_path, self.alpha, ticket_id, "support", "CLOSED")
        transition_ticket(self.db_path, self.alpha, ticket_id, "manager", "CLOSED")
        with sqlite3.connect(self.db_path) as connection:
            self.assertEqual(
                connection.execute("SELECT state FROM tickets WHERE id = ?", (ticket_id,)).fetchone()[0],
                "CLOSED",
            )
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM ticket_events WHERE ticket_id = ?", (ticket_id,)
                ).fetchone()[0],
                3,
            )

    def test_overdue_excludes_resolved_tickets(self) -> None:
        opened = datetime(2026, 10, 20, 9, 0)
        active = create_ticket(self.db_path, self.alpha, "Active", "CRITICAL", opened)
        resolved = create_ticket(self.db_path, self.alpha, "Resolved", "CRITICAL", opened)
        transition_ticket(self.db_path, self.alpha, resolved, "support", "IN_PROGRESS")
        transition_ticket(self.db_path, self.alpha, resolved, "support", "RESOLVED")
        self.assertEqual(
            overdue_ticket_ids(self.db_path, self.alpha, datetime(2026, 10, 20, 11, 1)), [active]
        )
