"""Linux launch gate, owned process-tree supervision and orphan exclusion."""
from contextlib import contextmanager
import ctypes
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def process(pid):
    try:
        raw = Path(f'/proc/{pid}/stat').read_text()
    except FileNotFoundError:
        return None
    parts = raw[raw.rfind(')') + 2:].split()
    return {'pid': int(pid), 'state': parts[0], 'session': int(parts[3]), 'parent': int(parts[1]), 'start': parts[19]}


def identity(pid, token, receipt):
    if not Path('/proc/sys/kernel/random/boot_id').is_file():
        return {'platform': 'posix', 'pid': pid, 'token': token}
    info = process(pid)
    if info is None:
        raise ValueError('Supervisor disappeared before durable launch admission')
    return {**info, 'token': token, 'receipt': str(receipt),
            'boot': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def surviving(identity_json, reconciled=False):
    saved = json.loads(identity_json)
    if saved.get('platform') == 'posix':
        try:
            os.kill(saved['pid'], 0)
            return True
        except ProcessLookupError:
            return False
    if saved['boot'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        return False
    leader = process(saved['pid'])
    same_session = not leader or leader['start'] == saved['start']
    if same_session:
        for path in Path('/proc').iterdir():
            if path.name.isdigit():
                info = process(path.name)
                if info and info['session'] == saved['session'] and info['state'] not in {'Z', 'X'}:
                    return True
    if saved.get('receipt') and not reconciled:
        try:
            proof = json.loads(Path(saved['receipt']).read_text())
        except FileNotFoundError:
            raise ValueError('Supervisor completion is missing; inspect effects and reconcile explicitly') from None
        if proof.get('token') != saved['token'] or proof.get('children_reaped') is not True:
            raise ValueError('Invalid supervisor completion receipt')
    return False


@contextmanager
def workload(directory, db, legacy=None, require_linux=False):
    if require_linux and not Path('/proc/sys/kernel/random/boot_id').is_file():
        raise ValueError('Guarded workflow requires Linux /proc and subreaper support')
    with (directory / 'workload.lock').open('a') as lease:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Previous workload still holds its lease; inspect before dispatch') from None
        # Only close: LOCK_UN would release the child's inherited lease as well.
        rows = db.execute('SELECT request_id, process_identity, launch_guard, child_pid, state FROM attempts WHERE process_closed IS NOT 1').fetchall()
        for row in rows:
            reconciled = db.execute('SELECT 1 FROM reconciliations WHERE request_id=?', (row['request_id'],)).fetchone()
            inspecting = row['request_id'] == legacy or bool(reconciled)
            if row['process_identity'] and surviving(row['process_identity'], inspecting):
                raise ValueError('Previous process session still has live members; dispatch blocked')
            unsupported = row['process_identity'] and json.loads(row['process_identity']).get('platform') == 'posix'
            if (row['state'] == 'uncertain' and row['child_pid'] and
                    (not row['process_identity'] or unsupported) and row['launch_guard'] != 'prepared'):
                if not inspecting:
                    raise ValueError('Legacy uncertain process requires explicit reconciliation')
                if process(row['child_pid']) and not reconciled:
                    raise ValueError('Legacy process identity is ambiguous and its PID is live')
            # During manual reconciliation, do not cache closure before evidence commits.
            if not (inspecting and not reconciled):
                with db:
                    db.execute('UPDATE attempts SET process_closed=1 WHERE request_id=?', (row['request_id'],))
        yield lease.fileno()


def launch_args(command, read_fd, lease_fd, receipt, token):
    return [sys.executable, str(Path(__file__).resolve()), str(read_fd), str(lease_fd),
            str(receipt), token, json.dumps(command)]


def supervise(command, lease_fd, receipt, token):
    """Adopt orphaned descendants, including setsid children, until all are reaped."""
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0) != 0:  # PR_SET_CHILD_SUBREAPER
        raise OSError(ctypes.get_errno(), 'Subreaper setup failed')
    signal.signal(signal.SIGCHLD, signal.SIG_DFL)  # Retain child PIDs until this supervisor reaps them.
    stopped = []
    for signum in (signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, lambda number, frame: stopped.append(number))
    child = subprocess.Popen(command, pass_fds=(lease_fd,))
    leader_exit = None
    while True:
        if stopped:
            # These are unreaped children of THIS live supervisor. Their PIDs cannot
            # be reused until we wait for them; no saved/historical PID is signalled.
            owned = []
            for entry in Path('/proc').iterdir():
                info = process(entry.name) if entry.name.isdigit() else None
                if info and info['parent'] == os.getpid():
                    owned.append(info['pid'])
            for pid in owned:
                try:
                    os.kill(int(pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
        try:
            pid, status = os.waitpid(-1, os.WNOHANG)
        except ChildProcessError:
            break
        if pid == child.pid:
            leader_exit = os.waitstatus_to_exitcode(status)
            child.returncode = leader_exit
        if pid == 0:
            time.sleep(.01)
    if leader_exit is None:
        raise RuntimeError('Missing command exit status')
    payload = dict(token=token, children_reaped=True, exit_code=leader_exit)
    path = Path(receipt)
    temporary = path.with_suffix('.tmp')
    with temporary.open('x') as output:
        os.chmod(temporary, 0o600)
        json.dump(payload, output)
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    signum = stopped[0] if stopped else -leader_exit if leader_exit < 0 else None
    if signum:
        if signum not in (signal.SIGKILL, signal.SIGSTOP):
            signal.signal(signum, signal.SIG_DFL)
        os.kill(os.getpid(), signum)
    return leader_exit


if __name__ == '__main__':
    read_fd, lease_fd = map(int, sys.argv[1:3])
    allowed = os.read(read_fd, 1)
    os.close(read_fd)
    if allowed != b'1':
        raise SystemExit(125)
    command = json.loads(sys.argv[5])
    os.set_inheritable(lease_fd, True)
    if sys.platform == 'linux':
        raise SystemExit(supervise(command, lease_fd, sys.argv[3], sys.argv[4]))
    os.execvpe(command[0], command, os.environ)
