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


class WorkflowSliceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "helpdesk.db"
        initialize(self.db_path)
        self.alpha = create_tenant(self.db_path, "Alpha")
        self.beta = create_tenant(self.db_path, "Beta")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_resumed_workflow_preserves_tenant_boundaries_and_audit(self) -> None:
        ticket_id = create_ticket(
            self.db_path, self.alpha, "Access", "CRITICAL", datetime(2026, 10, 20, 9, 0)
        )
        with self.assertRaises(ValueError):
            transition_ticket(self.db_path, self.beta, ticket_id, "IN_PROGRESS")
        transition_ticket(self.db_path, self.alpha, ticket_id, "IN_PROGRESS")
        transition_ticket(self.db_path, self.alpha, ticket_id, "RESOLVED")
        transition_ticket(self.db_path, self.alpha, ticket_id, "CLOSED")
        with sqlite3.connect(self.db_path) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT count(*) FROM ticket_events WHERE ticket_id = ?", (ticket_id,)
                ).fetchone()[0],
                3,
            )

    def test_regression_target_uses_critical_sla_after_recovery(self) -> None:
        ticket_id = create_ticket(
            self.db_path, self.alpha, "Outage", "CRITICAL", datetime(2026, 10, 20, 9, 0)
        )
        self.assertEqual(
            overdue_ticket_ids(self.db_path, self.alpha, datetime(2026, 10, 20, 11, 1)),
            [ticket_id],
        )
