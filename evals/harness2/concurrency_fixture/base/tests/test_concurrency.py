from __future__ import annotations

import concurrent.futures
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from helpdesk import (
    claim_ticket,
    create_tenant,
    create_ticket,
    initialize,
    transition_ticket,
)


class ConcurrencyAndLockContentionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "helpdesk_concurrent.db"
        initialize(self.db_path)
        self.tenant_id = create_tenant(self.db_path, "AcmeCorp")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_atomic_ticket_claim_under_race_condition(self) -> None:
        """10 concurrent workers race to claim 5 open tickets.
        Exactly 5 claims must succeed, and 5 must fail with ValueError.
        No ticket may have more than one assignee or duplicate claim audit event.
        """
        opened = datetime(2026, 10, 21, 9, 0)
        tickets = [
            create_ticket(self.db_path, self.tenant_id, f"Ticket {i}", "HIGH", opened)
            for i in range(5)
        ]

        def worker(worker_id: int) -> tuple[int, bool, str]:
            target_ticket = tickets[worker_id % 5]
            try:
                claim_ticket(
                    self.db_path,
                    self.tenant_id,
                    target_ticket,
                    actor_role="support",
                    assignee=f"agent_{worker_id}",
                )
                return (target_ticket, True, f"agent_{worker_id}")
            except ValueError:
                return (target_ticket, False, f"agent_{worker_id}")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(worker, range(10)))

        successes = [r for r in results if r[1] is True]
        failures = [r for r in results if r[1] is False]

        self.assertEqual(len(successes), 5, f"Expected 5 successful claims, got {len(successes)}")
        self.assertEqual(len(failures), 5, f"Expected 5 rejected claims, got {len(failures)}")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT id, state, assignee FROM tickets WHERE tenant_id = ? ORDER BY id",
                (self.tenant_id,),
            ).fetchall()
            self.assertEqual(len(rows), 5)
            for row in rows:
                self.assertEqual(row["state"], "IN_PROGRESS")
                self.assertTrue(str(row["assignee"]).startswith("agent_"))

            events = conn.execute(
                "SELECT count(*) FROM ticket_events WHERE new_state = 'IN_PROGRESS'"
            ).fetchone()[0]
            self.assertEqual(events, 5)

    def test_high_concurrency_write_burst_under_wal(self) -> None:
        """20 concurrent threads performing rapid ticket creation, claim and resolution.
        All 20 burst operations must complete with zero 'database is locked' errors.
        """
        def writer_task(worker_id: int) -> int:
            t_id = create_ticket(
                self.db_path,
                self.tenant_id,
                f"Burst ticket from worker {worker_id}",
                "MEDIUM",
                datetime(2026, 10, 21, 10, 0),
            )
            claim_ticket(
                self.db_path, self.tenant_id, t_id, "support", f"worker_{worker_id}"
            )
            transition_ticket(self.db_path, self.tenant_id, t_id, "support", "RESOLVED")
            return t_id

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            created_ids = list(executor.map(writer_task, range(20)))

        self.assertEqual(len(created_ids), 20)
        with sqlite3.connect(self.db_path) as conn:
            total_resolved = conn.execute(
                "SELECT count(*) FROM tickets WHERE state = 'RESOLVED' AND tenant_id = ?",
                (self.tenant_id,),
            ).fetchone()[0]
            self.assertEqual(total_resolved, 20)
            total_events = conn.execute(
                "SELECT count(*) FROM ticket_events WHERE new_state = 'RESOLVED'"
            ).fetchone()[0]
            self.assertEqual(total_events, 20)
