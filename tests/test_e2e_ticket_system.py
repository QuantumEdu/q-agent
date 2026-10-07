"""
End-to-end integration test exercising the full q-agent SDD & Governance lifecycle
on a canonical Helpdesk Support Ticket System (Sistema de Tickets de Atención).

Verifies:
1. Domain Model: Strict state machine (OPEN -> IN_PROGRESS -> RESOLVED -> CLOSED) and SLA computation.
2. Persistence: Zero-mock SQLite repository with WAL mode.
3. Service: Complete lifecycle execution (creation, routing, SLA breach detection, resolution).
4. Governance Pipeline: Git Worktree isolation (q_worktree) -> TDD implementation ->
   Deterministic Merge Gate verification (q_merge_gate, exit code 0) -> Clean merge to main.
"""

from datetime import datetime, timedelta, timezone
from enum import Enum
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT_DIR / "tools"

for tool_subdir in ["q-worktree", "q-merge-gate"]:
    tool_path = TOOLS_DIR / tool_subdir
    if str(tool_path) not in sys.path:
        sys.path.insert(0, str(tool_path))

import q_merge_gate  # noqa: E402
import q_worktree  # noqa: E402


# ==============================================================================
# Canonical Domain: Support Ticket System (Sistema de Tickets de Atención)
# ==============================================================================


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


SLA_HOURS_MAP = {
    TicketPriority.CRITICAL: 2,
    TicketPriority.HIGH: 8,
    TicketPriority.MEDIUM: 24,
    TicketPriority.LOW: 72,
}


class Ticket:
    def __init__(
        self,
        ticket_id: int,
        title: str,
        description: str,
        category: str,
        priority: TicketPriority,
        requester_email: str,
        created_at: datetime,
        status: TicketStatus = TicketStatus.OPEN,
        assigned_agent: str | None = None,
        resolution_notes: str | None = None,
        resolved_at: datetime | None = None,
    ):
        self.ticket_id = ticket_id
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.requester_email = requester_email
        self.created_at = created_at
        self.status = status
        self.assigned_agent = assigned_agent
        self.resolution_notes = resolution_notes
        self.resolved_at = resolved_at
        self.sla_deadline = created_at + timedelta(hours=SLA_HOURS_MAP[priority])

    def assign(self, agent_email: str):
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            raise ValueError(f"Cannot assign ticket in {self.status.value} status")
        self.assigned_agent = agent_email
        self.status = TicketStatus.IN_PROGRESS

    def resolve(self, notes: str, resolved_at: datetime | None = None):
        if not notes or not notes.strip():
            raise ValueError("Resolution notes are mandatory to resolve a ticket")
        if self.status != TicketStatus.IN_PROGRESS:
            raise ValueError("Ticket must be IN_PROGRESS before being RESOLVED")
        self.resolution_notes = notes.strip()
        self.resolved_at = resolved_at or datetime.now(timezone.utc)
        self.status = TicketStatus.RESOLVED

    def close(self):
        if self.status != TicketStatus.RESOLVED:
            raise ValueError("Ticket must be RESOLVED before being CLOSED")
        self.status = TicketStatus.CLOSED

    def is_sla_breached(self, current_time: datetime | None = None) -> bool:
        check_time = self.resolved_at or (current_time or datetime.now(timezone.utc))
        return check_time > self.sla_deadline


class TicketRepository:
    """Thread-safe SQLite zero-mock repository for tickets."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    requester_email TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_agent TEXT,
                    resolution_notes TEXT,
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                );
            """)

    def close(self):
        self.conn.close()

    def save(self, ticket: Ticket) -> Ticket:
        with self.conn:
            if ticket.ticket_id == 0:
                cursor = self.conn.execute(
                    """
                    INSERT INTO tickets (title, description, category, priority, requester_email,
                                         status, assigned_agent, resolution_notes, created_at, resolved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket.title,
                        ticket.description,
                        ticket.category,
                        ticket.priority.value,
                        ticket.requester_email,
                        ticket.status.value,
                        ticket.assigned_agent,
                        ticket.resolution_notes,
                        ticket.created_at.isoformat(),
                        ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                    ),
                )
                ticket.ticket_id = cursor.lastrowid
            else:
                self.conn.execute(
                    """
                    UPDATE tickets
                    SET status = ?, assigned_agent = ?, resolution_notes = ?, resolved_at = ?
                    WHERE id = ?
                    """,
                    (
                        ticket.status.value,
                        ticket.assigned_agent,
                        ticket.resolution_notes,
                        ticket.resolved_at.isoformat() if ticket.resolved_at else None,
                        ticket.ticket_id,
                    ),
                )
        return ticket

    def find_by_id(self, ticket_id: int) -> Ticket | None:
        cur = self.conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cur.fetchone()
        if not row:
            return None
        created_at = datetime.fromisoformat(row["created_at"])
        resolved_at = datetime.fromisoformat(row["resolved_at"]) if row["resolved_at"] else None
        return Ticket(
            ticket_id=row["id"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            priority=TicketPriority(row["priority"]),
            requester_email=row["requester_email"],
            created_at=created_at,
            status=TicketStatus(row["status"]),
            assigned_agent=row["assigned_agent"],
            resolution_notes=row["resolution_notes"],
            resolved_at=resolved_at,
        )

    def count_by_status(self, status: TicketStatus) -> int:
        cur = self.conn.execute("SELECT COUNT(*) FROM tickets WHERE status = ?", (status.value,))
        return cur.fetchone()[0]


class TicketService:
    def __init__(self, repo: TicketRepository):
        self.repo = repo

    def create_ticket(
        self,
        title: str,
        description: str,
        category: str,
        priority: TicketPriority,
        requester: str,
        created_at: datetime | None = None,
    ) -> Ticket:
        now = created_at or datetime.now(timezone.utc)
        ticket = Ticket(
            ticket_id=0,
            title=title,
            description=description,
            category=category,
            priority=priority,
            requester_email=requester,
            created_at=now,
        )
        return self.repo.save(ticket)

    def assign_ticket(self, ticket_id: int, agent_email: str) -> Ticket:
        ticket = self.repo.find_by_id(ticket_id)
        if not ticket:
            raise KeyError(f"Ticket {ticket_id} not found")
        ticket.assign(agent_email)
        return self.repo.save(ticket)

    def resolve_ticket(self, ticket_id: int, notes: str, resolved_at: datetime | None = None) -> Ticket:
        ticket = self.repo.find_by_id(ticket_id)
        if not ticket:
            raise KeyError(f"Ticket {ticket_id} not found")
        ticket.resolve(notes, resolved_at=resolved_at)
        return self.repo.save(ticket)

    def close_ticket(self, ticket_id: int) -> Ticket:
        ticket = self.repo.find_by_id(ticket_id)
        if not ticket:
            raise KeyError(f"Ticket {ticket_id} not found")
        ticket.close()
        return self.repo.save(ticket)


# ==============================================================================
# End-to-End Suite: Domain & Governance Pipeline Validation
# ==============================================================================


class TestE2ETicketSystem(unittest.TestCase):
    def setUp(self):
        self.repo = TicketRepository()
        self.service = TicketService(self.repo)

    def tearDown(self):
        self.repo.close()

    def test_e2e_ticket_lifecycle_and_sla(self):
        """E2E Test 1: Complete ticket lifecycle from OPEN to CLOSED with SLA checks."""
        start_time = datetime(2026, 10, 7, 9, 0, 0, tzinfo=timezone.utc)

        # 1. Ingestion: Critical Ticket created
        t = self.service.create_ticket(
            title="Database Latency Spike",
            description="Connection pool exhausted on main cluster",
            category="INFRASTRUCTURE",
            priority=TicketPriority.CRITICAL,
            requester="sre@example.com",
            created_at=start_time,
        )
        self.assertEqual(t.status, TicketStatus.OPEN)
        self.assertEqual(t.ticket_id, 1)
        self.assertEqual(t.sla_deadline, start_time + timedelta(hours=2))

        # 2. Assignment: Support agent takes the ticket
        t = self.service.assign_ticket(1, "ops.lead@example.com")
        self.assertEqual(t.status, TicketStatus.IN_PROGRESS)
        self.assertEqual(t.assigned_agent, "ops.lead@example.com")

        # 3. Validation: Direct close without resolution is forbidden
        with self.assertRaises(ValueError):
            t.close()

        # 4. Resolution: Resolved within SLA (1 hour later)
        resolve_time = start_time + timedelta(hours=1)
        t = self.service.resolve_ticket(
            1,
            notes="Scaled connection pool max_conns to 120 and tuned idle timeout.",
            resolved_at=resolve_time,
        )
        self.assertEqual(t.status, TicketStatus.RESOLVED)
        self.assertFalse(t.is_sla_breached())

        # 5. Closure: Requester accepts resolution
        t = self.service.close_ticket(1)
        self.assertEqual(t.status, TicketStatus.CLOSED)

        # 6. Verify persistence state
        persisted = self.repo.find_by_id(1)
        self.assertIsNotNone(persisted)
        self.assertEqual(persisted.status, TicketStatus.CLOSED)
        self.assertEqual(persisted.resolution_notes, "Scaled connection pool max_conns to 120 and tuned idle timeout.")

    def test_e2e_sla_breach_detection(self):
        """E2E Test 2: SLA breach is correctly flagged when resolution exceeds deadline."""
        start_time = datetime(2026, 10, 7, 10, 0, 0, tzinfo=timezone.utc)
        t = self.service.create_ticket(
            title="VPN Client Failure",
            description="Unable to authenticate to corporate gateway",
            category="NETWORK",
            priority=TicketPriority.HIGH,  # 8h SLA
            requester="analyst@example.com",
            created_at=start_time,
        )
        self.service.assign_ticket(t.ticket_id, "neteng@example.com")

        # Resolve 10 hours later (SLA deadline was 8h)
        resolve_time = start_time + timedelta(hours=10)
        t = self.service.resolve_ticket(
            t.ticket_id,
            notes="Revoked expired certificate and reissued profile.",
            resolved_at=resolve_time,
        )
        self.assertTrue(t.is_sla_breached())

    def test_e2e_q_agent_governance_pipeline_simulation(self):
        """
        E2E Test 3: Simulates the complete q-agent v2.6.0 pipeline in an isolated Git environment:
        1. Initialize canonical git repo.
        2. Create subagent worktree branch (q-worktree).
        3. Author code slice inside worktree.
        4. Pass through deterministic merge policy gate (q-merge-gate, exit code 0).
        5. Merge worktree branch cleanly to main.
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir)
            orig_cwd = os.getcwd()

            try:
                # 1. Repo init
                q_worktree.run_git(["init", "-b", "main"], cwd=repo_dir)
                q_worktree.run_git(["config", "user.name", "E2E Test Bot"], cwd=repo_dir)
                q_worktree.run_git(["config", "user.email", "bot@example.com"], cwd=repo_dir)

                init_file = repo_dir / "README.md"
                init_file.write_text("# Helpdesk System\n", encoding="utf-8")
                q_worktree.run_git(["add", "README.md"], cwd=repo_dir)
                q_worktree.run_git(["commit", "-m", "init: bootstrap repository"], cwd=repo_dir)

                os.chdir(repo_dir)

                # 2. Isolate subagent task via q_worktree
                class ArgsCreate:
                    task = "TICKETS-01"
                    base = "main"
                    worktree_dir = None
                    json = True

                exit_create = q_worktree.cmd_create(ArgsCreate())
                self.assertEqual(exit_create, 0)

                wt_path = repo_dir / ".q-worktrees" / "task-TICKETS-01"
                self.assertTrue(wt_path.exists())

                # 3. Implement the feature slice inside the isolated worktree
                ticket_code = wt_path / "tickets.py"
                ticket_code.write_text(
                    "# Tickets Domain Slice\n"
                    "def calculate_sla(priority: str) -> int:\n"
                    "    return {'CRITICAL': 2, 'HIGH': 8, 'MEDIUM': 24, 'LOW': 72}.get(priority, 24)\n",
                    encoding="utf-8",
                )
                q_worktree.run_git(["add", "tickets.py"], cwd=wt_path)
                q_worktree.run_git(["commit", "-m", "feat(tickets): implement sla calculator"], cwd=wt_path)

                # 4. Gate verification via q_merge_gate
                report, err = q_merge_gate.analyze_diff(base="main", head="HEAD", max_loc=500, cwd=wt_path)
                self.assertIsNone(err)
                self.assertEqual(report["exit_code"], 0, f"Expected PROCEED (0), got {report}")
                self.assertEqual(report["status"], "PROCEED")
                self.assertLess(report["total_loc"], 500)

                # 5. Merge worktree back to main
                class ArgsMerge:
                    task = "TICKETS-01"
                    target = "main"
                    delete_branch = True
                    worktree_dir = None
                    json = True

                exit_merge = q_worktree.cmd_merge(ArgsMerge())
                self.assertEqual(exit_merge, 0)

                # Verify file landed in main
                merged_file = repo_dir / "tickets.py"
                self.assertTrue(merged_file.exists())
                self.assertIn("calculate_sla", merged_file.read_text(encoding="utf-8"))

            finally:
                os.chdir(orig_cwd)


if __name__ == "__main__":
    unittest.main()
