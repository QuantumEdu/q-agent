from __future__ import annotations

import concurrent.futures
import multiprocessing
import os
import signal
import sqlite3
import sys
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path

from helpdesk import (
    claim_ticket,
    create_tenant,
    create_ticket,
    initialize,
    verify_integrity,
    _connection,
)


def _continuous_writer_worker(db_path: str, tenant_id: int, ready_file: str) -> None:
    """Worker process that writes rapid transactions until killed with SIGKILL."""
    conn = _connection(db_path)
    count = 0
    now = datetime.now(timezone.utc)
    while True:
        try:
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO tickets (tenant_id, title, priority, state, opened_at, due_at)
                    VALUES (?, ?, 'HIGH', 'OPEN', ?, ?)
                    """,
                    (tenant_id, f"Stress Ticket {count}", now.isoformat(), now.isoformat()),
                )
                tid = int(cur.lastrowid)
                conn.execute(
                    """
                    INSERT INTO ticket_events (ticket_id, old_state, new_state, actor_role, created_at)
                    VALUES (?, 'NONE', 'OPEN', 'stress_agent', ?)
                    """,
                    (tid, now.isoformat()),
                )
            count += 1
            if count == 10 and not os.path.exists(ready_file):
                with open(ready_file, "w") as f:
                    f.write("ready")
            time.sleep(0.002)
        except Exception:
            break


class ChaosAndCrashRecoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "chaos_helpdesk.db"
        initialize(self.db_path)
        self.tenant_id = create_tenant(self.db_path, "ChaosTenant")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_sigkill_crash_during_multi_statement_transaction(self) -> None:
        """Kills an active writer process with SIGKILL (kill -9) during transactions.
        Verifies that SQLite WAL cleanly rolls back the interrupted transaction,
        passes PRAGMA integrity_check, PRAGMA foreign_key_check, and leaves no torn writes.
        """
        ready_file = str(Path(self.temp_dir.name) / "writer_ready.flag")
        p = multiprocessing.Process(
            target=_continuous_writer_worker,
            args=(str(self.db_path), self.tenant_id, ready_file),
        )
        p.start()

        # Wait until the worker has actively written at least 10 tickets
        timeout = time.time() + 5.0
        while time.time() < timeout:
            if os.path.exists(ready_file):
                break
            time.sleep(0.05)

        self.assertTrue(os.path.exists(ready_file), "Worker did not signal readiness in time")

        # Hard crash the worker with SIGKILL (cannot run cleanup or rollback)
        os.kill(p.pid, signal.SIGKILL)
        p.join()
        self.assertEqual(p.exitcode, -signal.SIGKILL)

        # Inspect database recovery
        health = verify_integrity(self.db_path)
        self.assertTrue(health["integrity_ok"], f"Database corrupt after SIGKILL: {health['integrity_errors']}")
        self.assertTrue(health["foreign_keys_ok"], "Foreign key integrity violated after SIGKILL")
        self.assertEqual(len(health["torn_tickets"]), 0, f"Found torn transactions: {health['torn_tickets']}")
        self.assertGreaterEqual(health["tickets"], 10, "Expected at least 10 committed tickets before crash")

    def test_post_crash_write_burst_resilience(self) -> None:
        """After an ungraceful crash, new concurrent workers must immediately succeed
        in acquiring locks and writing transactions without 'database is locked' errors.
        """
        # First trigger a crash to leave WAL in an ungracefully terminated state
        ready_file = str(Path(self.temp_dir.name) / "crash_ready.flag")
        p = multiprocessing.Process(
            target=_continuous_writer_worker,
            args=(str(self.db_path), self.tenant_id, ready_file),
        )
        p.start()
        while not os.path.exists(ready_file):
            time.sleep(0.02)
        os.kill(p.pid, signal.SIGKILL)
        p.join()

        # Now launch 10 concurrent workers writing new tickets and claiming them
        now = datetime.now(timezone.utc)
        def worker_task(worker_id: int) -> int:
            tid = create_ticket(
                self.db_path,
                self.tenant_id,
                f"Post-Crash Ticket {worker_id}",
                "MEDIUM",
                now,
            )
            claim_ticket(
                self.db_path,
                self.tenant_id,
                tid,
                actor_role="support",
                assignee=f"agent_{worker_id}",
            )
            return tid

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_task, i) for i in range(20)]
            completed_tids = [f.result(timeout=10.0) for f in futures]

        self.assertEqual(len(completed_tids), 20, "Not all post-crash burst workers completed")
        
        health = verify_integrity(self.db_path)
        self.assertTrue(health["integrity_ok"], "Integrity check failed after post-crash burst")
        self.assertEqual(len(health["torn_tickets"]), 0, "Found torn tickets in post-crash burst")

    def test_torn_wal_trailing_frame_checksum_recovery(self) -> None:
        """Simulate power loss during WAL sector write by appending trailing corrupted bytes.
        SQLite WAL frame checksums must detect the corruption, safely truncate back to the
        last valid commit, and allow new transactions without database corruption.
        """
        now = datetime.now(timezone.utc)
        t1 = create_ticket(self.db_path, self.tenant_id, "Ticket before tear", "LOW", now)

        wal_path = Path(str(self.db_path) + "-wal")
        self.assertTrue(wal_path.exists(), "WAL file does not exist")

        # Inject 128 bytes of corrupt trailing garbage into the WAL file
        with open(wal_path, "ab") as f:
            f.write(b"\xDE\xAD\xBE\xEF" * 32)

        # Reopen database, execute a query and a new write
        t2 = create_ticket(self.db_path, self.tenant_id, "Ticket after tear recovery", "HIGH", now)
        self.assertGreater(t2, t1)

        health = verify_integrity(self.db_path)
        self.assertTrue(health["integrity_ok"], "WAL checksum recovery failed on torn trailing frame")
        self.assertTrue(health["foreign_keys_ok"])


if __name__ == "__main__":
    unittest.main()
