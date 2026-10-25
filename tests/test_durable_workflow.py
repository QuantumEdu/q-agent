"""Crash and state-machine regressions using real Git, SQLite and child processes."""
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

CLI = Path(__file__).resolve().parents[1] / 'tools/q-tasks/q_tasks.py'


class DurableWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for args in (['init', '-q'], ['config', 'user.name', 'Test'],
                     ['config', 'user.email', 'test@example.invalid']):
            self.git(*args)
        (self.root / '.gitignore').write_text('.cache/\n__pycache__/\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture')
        self.cli('add', 'T', 'Durable task')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], text=True).strip()

    def cli(self, *args, code=0):
        r = subprocess.run([sys.executable, str(CLI), '--project', str(self.root), *args],
                           text=True, capture_output=True, timeout=15,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return json.loads(r.stdout)

    def wait_file(self, path):
        deadline = time.monotonic() + 5
        while not path.exists() and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(path.exists())

    def test_sigkill_survivor_blocks_retry_and_other_tasks_until_exit(self):
        release = self.root / '.cache/release'
        command = [sys.executable, '-c',
                   "from pathlib import Path; import time; Path('.cache/ready').touch(); "
                   "\nwhile not Path('.cache/release').exists(): time.sleep(.02)"]
        runner = subprocess.Popen([sys.executable, str(CLI), '--project', str(self.root),
                                   'run', 'T', '--request-id', 'crash', '--', *command],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.wait_file(self.root / '.cache/ready')
            runner.kill(); runner.wait(timeout=3)
            self.assertEqual(self.cli('resume')['tasks'][0]['state'], 'uncertain')
            self.cli('retry', 'T', '--reason', 'Inspected synthetic effects', code=2)
            self.cli('add', 'OTHER', 'Other task')
            self.cli('run', 'OTHER', '--request-id', 'conflict', '--', sys.executable,
                     '-c', "from pathlib import Path; Path('.cache/overlap').touch()", code=2)
            self.assertFalse((self.root / '.cache/overlap').exists())
            release.touch()
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                r = subprocess.run([sys.executable, str(CLI), '--project', str(self.root),
                                    'reconcile', 'T', '--attempt', 'crash', '--outcome', 'no_effect', '--evidence', 'Observed probe child exit; only synthetic ready marker was written'],
                                   capture_output=True, text=True)
                if r.returncode == 0:
                    break
                time.sleep(.05)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.cli('retry', 'T', '--reason', 'Reconciled isolated probe; authorized retry')
        finally:
            release.touch()
            if runner.poll() is None:
                runner.kill(); runner.wait(timeout=3)

    def seed_workflow(self):
        (self.root / 'calc.py').write_text('def value(): return 0\n')
        (self.root / 'tests').mkdir()
        (self.root / 'tests/test_calc.py').write_text(
            'import unittest\nfrom calc import value\nclass Check(unittest.TestCase):\n'
            ' def test_value(self): self.assertEqual(value(), 1)\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'failing acceptance')
        return self.cli('workflow', 'start', 'T', '--request-id', 'start',
                        '--source', 'calc.py', '--tests', 'tests', '--definition', 'calc-v1')

    def status(self):
        return self.cli('workflow', 'show', 'T')

    def advance(self, phase, request, code=0):
        return self.cli('workflow', 'advance', 'T', '--request-id', request,
                        '--sequence', str(self.status()['sequence']), '--phase', phase,
                        '--evidence', 'Observed command and inspected checkout', code=code)

    def reproduce(self):
        self.cli('run', 'T', '--request-id', 'red', '--', sys.executable,
                 '-m', 'unittest', 'discover', '-s', 'tests', code=1)
        self.advance('fixing', 'to-fix')

    def test_checkpoint_budget_idempotence_and_completion_require_real_proof_and_review(self):
        self.seed_workflow()
        self.reproduce()
        patch = [sys.executable, '-c',
                 "from pathlib import Path; Path('calc.py').write_text('def value(): return 1\\n')"]
        self.cli('run', 'T', '--request-id', 'fix', '--', *patch)
        self.cli('run', 'T', '--request-id', 'fix', '--', *patch)
        self.assertEqual(self.status()['corrections'], 1)
        self.advance('verifying', 'to-verify')
        self.advance('review', 'premature-review', code=2)
        self.git('add', 'calc.py'); self.git('commit', '-qm', 'fix')
        self.cli('verify', 'T', '--request-id', 'green', '--', sys.executable,
                 '-m', 'unittest', 'discover', '-s', 'tests')
        self.advance('review', 'to-review')
        self.advance('complete', 'no-review', code=2)
        self.cli('workflow', 'review', 'T', '--request-id', 'review', '--sequence',
                 str(self.status()['sequence']), '--verdict', 'APPROVED',
                 '--reviewer', 'independent-test-reviewer', '--evidence', 'review.md#round-1')
        self.assertEqual(self.advance('complete', 'done')['phase'], 'complete')
        self.assertGreater(len(self.cli('history', 'T')['workflow_events']), 5)

    def test_third_fix_is_refused_across_cli_restarts_and_cannot_reset_budget(self):
        self.seed_workflow(); self.reproduce()
        for index in (1, 2):
            self.cli('run', 'T', '--request-id', f'fix-{index}', '--', sys.executable, '-c', 'pass')
            self.cli('retry', 'T', '--reason', 'Inspected unsuccessful correction')
        self.cli('run', 'T', '--request-id', 'fix-3', '--', sys.executable,
                 '-c', "from pathlib import Path; Path('.cache/third').touch()", code=2)
        self.assertFalse((self.root / '.cache/third').exists())
        self.assertEqual(self.status()['corrections'], 2)
        self.cli('workflow', 'start', 'T', '--request-id', 'reset', '--source', 'calc.py',
                 '--tests', 'tests', '--definition', 'calc-v1', code=2)

    def test_frozen_test_change_blocks_dispatch_and_stale_transition_is_rejected(self):
        start = self.seed_workflow(); self.reproduce()
        self.cli('workflow', 'advance', 'T', '--request-id', 'stale', '--sequence',
                 str(start['sequence']), '--phase', 'verifying', '--evidence', 'stale', code=2)
        (self.root / 'tests/test_calc.py').write_text('raise SystemExit(0)\n')
        self.cli('run', 'T', '--request-id', 'tampered', '--', sys.executable, '-c', 'pass', code=2)
        self.assertEqual(self.status()['corrections'], 0)

    def reviewed_candidate(self):
        self.seed_workflow(); self.reproduce()
        self.cli('run', 'T', '--request-id', 'fix', '--', sys.executable, '-c',
                 "from pathlib import Path; Path('calc.py').write_text('def value(): return 1\\n')")
        self.advance('verifying', 'to-verify')
        self.git('add', 'calc.py'); self.git('commit', '-qm', 'fixed candidate')
        self.cli('verify', 'T', '--request-id', 'green', '--', sys.executable,
                 '-m', 'unittest', 'discover', '-s', 'tests')
        self.advance('review', 'to-review')
        self.cli('workflow', 'review', 'T', '--request-id', 'review', '--sequence',
                 str(self.status()['sequence']), '--verdict', 'APPROVED',
                 '--reviewer', 'independent-test-reviewer', '--evidence', 'review.md')
        self.advance('awaiting_approval', 'to-approval')

    def test_effect_claim_lost_response_requires_reconciliation_not_redispatch(self):
        self.reviewed_candidate()
        payload = self.root / '.cache/effect.json'
        payload.write_text(json.dumps({'operation': 'deploy', 'target': 'synthetic/local'}))
        self.cli('effect', 'prepare', 'deploy-1', '--task', 'T', '--payload', str(payload))
        self.cli('effect', 'claim', 'deploy-1', code=2)
        self.cli('effect', 'approve', 'deploy-1', '--evidence', 'human-chat:deploy-synthetic')
        claim = self.cli('effect', 'claim', 'deploy-1')
        self.assertEqual(claim['state'], 'uncertain')
        self.cli('effect', 'claim', 'deploy-1', code=2)
        self.advance('complete', 'unresolved', code=2)
        settled = self.cli('effect', 'settle', 'deploy-1', '--outcome', 'completed',
                           '--external-receipt', 'observed-synthetic-operation-1', '--evidence', 'inspected synthetic target')
        self.assertEqual(settled['state'], 'completed')
        self.assertEqual(self.advance('complete', 'done')['phase'], 'complete')

    def test_approved_effect_cannot_dispatch_after_candidate_commit_changes(self):
        self.reviewed_candidate()
        payload = self.root / '.cache/effect.json'
        payload.write_text(json.dumps({'operation': 'merge', 'target': 'synthetic/main'}))
        self.cli('effect', 'prepare', 'merge-1', '--task', 'T', '--payload', str(payload))
        self.cli('effect', 'approve', 'merge-1', '--evidence', 'human-chat:merge-synthetic')
        self.git('commit', '--allow-empty', '-qm', 'changed candidate')
        self.cli('effect', 'claim', 'merge-1', code=2)

    def test_snapshot_preserves_checkpoint_and_refuses_overwrite_or_downgrade(self):
        import shutil
        self.seed_workflow(); self.reproduce()
        snapshot = self.root / '.cache/snapshot.sqlite3'
        self.cli('backup', str(snapshot))
        self.cli('backup', str(snapshot), code=2)
        self.cli('restore', str(snapshot), code=2)
        saved = self.root / 'snapshot.sqlite3'
        shutil.copyfile(snapshot, saved)
        before = self.status()
        shutil.rmtree(self.root / '.cache')
        self.cli('restore', str(saved))
        self.assertEqual(self.status(), before)
        saved.unlink()
        with sqlite3.connect(self.root / '.cache/q-agent-tasks/tasks.sqlite3') as db:
            db.execute('PRAGMA user_version=99')
        self.cli('resume', code=2)

    def test_launch_gate_prevents_effect_if_identity_commit_fails(self):
        db_path = self.root / '.cache/q-agent-tasks/tasks.sqlite3'
        with sqlite3.connect(db_path) as db:
            db.execute("CREATE TRIGGER reject_identity BEFORE UPDATE OF child_pid ON attempts "
                       "BEGIN SELECT RAISE(ABORT, 'no identity'); END")
        self.cli('run', 'T', '--request-id', 'no-identity', '--', sys.executable, '-c',
                 "from pathlib import Path; Path('.cache/effect').touch()", code=2)
        self.assertFalse((self.root / '.cache/effect').exists())

    def test_detached_descendant_is_owned_by_supervisor_after_runner_sigkill(self):
        child = ("from pathlib import Path; import time; Path('.cache/daemon').touch(); "
                 "\nwhile not Path('.cache/release').exists(): time.sleep(.02)\n"
                 "Path('.cache/daemon-done').touch()")
        parent = "import subprocess,sys; subprocess.Popen([sys.executable,'-c'," + repr(child) + "],start_new_session=True)"
        runner = subprocess.Popen([sys.executable, str(CLI), '--project', str(self.root),
            'run', 'T', '--request-id', 'daemon', '--', sys.executable, '-c', parent],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.wait_file(self.root / '.cache/daemon')
            runner.kill(); runner.wait(timeout=3)
            self.cli('resume')
            self.cli('retry', 'T', '--reason', 'Inspect detached child', code=2)
            self.cli('add', 'OTHER', 'Other work')
            self.cli('run', 'OTHER', '--request-id', 'overlap', '--', sys.executable, '-c', 'pass', code=2)
        finally:
            (self.root / '.cache/release').touch()
            self.wait_file(self.root / '.cache/daemon-done')
            if runner.poll() is None:
                runner.kill(); runner.wait(timeout=3)

    def test_sigkill_during_fix_preserves_spent_budget(self):
        self.seed_workflow(); self.reproduce()
        cmd = "from pathlib import Path; import time; Path('.cache/fixing').touch(); \nwhile not Path('.cache/release').exists(): time.sleep(.02)"
        runner = subprocess.Popen([sys.executable, str(CLI), '--project', str(self.root),
                                   'run', 'T', '--request-id', 'interrupted-fix', '--', sys.executable, '-c', cmd],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.wait_file(self.root / '.cache/fixing')
            runner.kill(); runner.wait(timeout=3)
            self.cli('resume')
            self.assertEqual(self.status()['corrections'], 1)
            self.cli('retry', 'T', '--reason', 'Unreconciled failure', code=2)
            (self.root / '.cache/release').touch()
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                result = subprocess.run([sys.executable, str(CLI), '--project', str(self.root),
                    'reconcile', 'T', '--attempt', 'interrupted-fix', '--outcome', 'no_effect',
                    '--evidence', 'Observed finite child exit and unchanged source'], capture_output=True, text=True)
                if result.returncode == 0:
                    break
                time.sleep(.03)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.cli('retry', 'T', '--reason', 'Reconciled; remaining repair authorized')
            self.cli('run', 'T', '--request-id', 'second-fix', '--', sys.executable, '-c', 'pass')
            self.assertEqual(self.status()['corrections'], 2)
            self.cli('retry', 'T', '--reason', 'Inspect final failed correction')
            self.cli('run', 'T', '--request-id', 'third-fix', '--', sys.executable, '-c', 'pass', code=2)
        finally:
            (self.root / '.cache/release').touch()
            if runner.poll() is None:
                runner.kill(); runner.wait(timeout=3)

    def test_future_workflow_and_corrupt_snapshot_are_rejected_without_reset(self):
        self.seed_workflow()
        snapshot = self.root / '.cache/corrupt.sqlite3'
        snapshot.write_bytes(b'not sqlite')
        self.cli('restore', str(snapshot), code=2)
        with sqlite3.connect(self.root / '.cache/q-agent-tasks/tasks.sqlite3') as db:
            db.execute('UPDATE workflows SET version=99 WHERE task_id=\'T\'')
        self.cli('workflow', 'show', 'T', code=2)

    def test_failed_reverification_invalidates_previous_green_candidate(self):
        self.seed_workflow(); self.reproduce()
        self.cli('run', 'T', '--request-id', 'fix', '--', sys.executable, '-c',
                 "from pathlib import Path; Path('calc.py').write_text('def value(): return 1\\n')")
        self.advance('verifying', 'to-verify')
        self.git('add', 'calc.py'); self.git('commit', '-qm', 'fixed')
        self.cli('verify', 'T', '--request-id', 'green', '--', sys.executable,
                 '-m', 'unittest', 'discover', '-s', 'tests')
        self.cli('verify', 'T', '--request-id', 'regression-failed', '--', sys.executable,
                 '-c', 'raise SystemExit(1)', code=1)
        self.assertIsNone(self.status()['proof'])
        self.advance('review', 'stale-green', code=2)
        events = self.cli('history', 'T')['workflow_events']
        self.assertTrue(any('Observed command' in row['input'] for row in events))

    def test_legacy_database_migrates_without_rewriting_historical_receipt(self):
        import shutil
        shutil.rmtree(self.root / '.cache')
        directory = self.root / '.cache/q-agent-tasks'
        directory.mkdir(parents=True)
        with sqlite3.connect(directory / 'tasks.sqlite3') as db:
            db.executescript("""
                CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    state TEXT NOT NULL, retry_reason TEXT);
                CREATE TABLE attempts (request_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                    operation TEXT NOT NULL, command TEXT NOT NULL, timeout REAL NOT NULL,
                    state TEXT NOT NULL, commit_sha TEXT NOT NULL, started_at TEXT NOT NULL,
                    finished_at TEXT, exit_code INTEGER, child_pid INTEGER,
                    checkout_matches INTEGER, error TEXT, log_path TEXT NOT NULL);
                INSERT INTO tasks VALUES ('T', 'Legacy', 'verified', NULL);
                INSERT INTO attempts VALUES ('legacy', 'T', 'verify', '[]', 10, 'verified',
                    'historical-sha', 'historical-start', 'historical-end', 0, NULL, 1, NULL, 'old.log');
            """)
        old = self.cli('history', 'T')['attempts'][0]
        self.assertEqual((old['commit_sha'], old['started_at'], old['exit_code']),
                         ('historical-sha', 'historical-start', 0))
        self.assertEqual(self.cli('resume')['tasks'][0]['state'], 'verified')

    def test_pre_registration_failure_is_not_reproduction_for_new_workflow(self):
        self.cli('run', 'T', '--request-id', 'historical-failure', '--', sys.executable,
                 '-c', 'raise SystemExit(7)', code=1)
        self.seed_workflow()
        self.advance('fixing', 'reuse-old-failure', code=2)
        self.assertEqual(self.status()['corrections'], 0)
        self.cli('retry', 'T', '--reason', 'Inspected historical failure; start actual reproduction')
        self.reproduce()
        self.assertEqual(self.status()['phase'], 'fixing')

    def test_completed_repair_reconciles_checkpoint_after_sigkill_without_refunding_budget(self):
        self.seed_workflow(); self.reproduce()
        command = ("from pathlib import Path; import time; "
                   "Path('calc.py').write_text('def value(): return 1\\n'); "
                   "Path('.cache/repaired').touch(); "
                   "\nwhile not Path('.cache/release').exists(): time.sleep(.02)")
        runner = subprocess.Popen([sys.executable, str(CLI), '--project', str(self.root),
            'run', 'T', '--request-id', 'crashed-repair', '--', sys.executable, '-c', command],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.wait_file(self.root / '.cache/repaired')
            runner.kill(); runner.wait(timeout=3)
            self.cli('resume')
            (self.root / '.cache/release').touch()
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                r = subprocess.run([sys.executable, str(CLI), '--project', str(self.root),
                    'reconcile', 'T', '--attempt', 'crashed-repair', '--outcome', 'completed',
                    '--evidence', 'Observed finished child and inspected corrected source'],
                    capture_output=True, text=True)
                if r.returncode == 0:
                    break
                time.sleep(.03)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.assertEqual(self.status()['corrections'], 1)
            self.assertIsNone(self.status()['proof'])
            self.advance('verifying', 'recovered-to-verify')
            self.git('add', 'calc.py'); self.git('commit', '-qm', 'reconciled correction')
            proof = self.cli('verify', 'T', '--request-id', 'fresh-verification', '--',
                sys.executable, '-m', 'unittest', 'discover', '-s', 'tests')
            self.assertEqual(proof['state'], 'verified')
            self.assertEqual(self.status()['corrections'], 1)
        finally:
            (self.root / '.cache/release').touch()
            if runner.poll() is None:
                runner.kill(); runner.wait(timeout=3)

    def test_actual_command_signal_exit_is_preserved_by_supervisor(self):
        proof = self.cli('run', 'T', '--request-id', 'self-kill', '--', sys.executable,
                         '-c', 'import os,signal; os.kill(os.getpid(), signal.SIGKILL)', code=1)
        self.assertEqual(proof['exit_code'], -signal.SIGKILL)
        self.assertEqual(proof['process_closed'], 1)

    def test_lost_supervisor_requires_explicit_reconciliation_after_child_exit(self):
        command = "from pathlib import Path; import time; Path('.cache/ready').touch(); \nwhile not Path('.cache/release').exists(): time.sleep(.02)\nPath('.cache/done').touch()"
        runner = subprocess.Popen([sys.executable, str(CLI), '--project', str(self.root),
            'run', 'T', '--request-id', 'lost-supervisor', '--', sys.executable, '-c', command],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            self.wait_file(self.root / '.cache/ready')
            supervisor = self.cli('history', 'T')['attempts'][0]['child_pid']
            # This supervisor is still waiting on our controlled child; a pidfd pins it.
            descriptor = os.pidfd_open(supervisor)
            try:
                runner.kill(); runner.wait(timeout=3)
                signal.pidfd_send_signal(descriptor, signal.SIGKILL)
            finally:
                os.close(descriptor)
            self.cli('resume')
            (self.root / '.cache/release').touch()
            self.wait_file(self.root / '.cache/done')
            self.cli('add', 'OTHER', 'Other task')
            self.cli('run', 'OTHER', '--request-id', 'unproven', '--', sys.executable, '-c', 'pass', code=2)
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline:
                r = subprocess.run([sys.executable, str(CLI), '--project', str(self.root),
                    'reconcile', 'T', '--attempt', 'lost-supervisor', '--outcome', 'no_effect',
                    '--evidence', 'Controlled child exited; inspected markers and source'],
                    capture_output=True, text=True)
                if r.returncode == 0:
                    break
                time.sleep(.03)
            self.assertEqual(r.returncode, 0, r.stdout)
            self.cli('run', 'OTHER', '--request-id', 'now-safe', '--', sys.executable, '-c', 'pass')
        finally:
            (self.root / '.cache/release').touch()
            if runner.poll() is None:
                runner.kill(); runner.wait(timeout=3)


if __name__ == '__main__':
    unittest.main()
