"""Keep the round driver healthy and audit changed published bytes promptly."""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_r37 as lane


def running(filename, marker):
    try:
        process_id = int(filename.read_text())
    except (OSError, ValueError):
        return False
    status = subprocess.run(['ps', '-p', str(process_id), '-o', 'command='], capture_output=True, text=True)
    return marker in status.stdout


def remote_workers():
    status = lane.ssh('ps -axo pid,command', timeout=30)
    if status.returncode:
        raise RuntimeError(status.stderr)
    return [line for line in status.stdout.splitlines()
            if lane.RDIR + '/' in line and line.split()[0].isdigit()]


def start_driver():
    owned = remote_workers()
    if owned:
        lane.ssh('kill -TERM ' + ' '.join(line.split()[0] for line in owned), timeout=30)
    with (lane.WORK / 'driver.log').open('a') as output:
        process = subprocess.Popen(['nohup', 'nice', '-n', '5', lane.PY, '-I',
                                    str(lane.LANE / 'forensics_r37.py'), 'driver'],
                                   stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
    (lane.WORK / 'driver.pid').write_text(str(process.pid) + '\n')
    time.sleep(2)
    if process.poll() is not None:
        raise RuntimeError('new driver exited before its first health check')
    lane.state(f'HEALTH started verified driver group{process.pid}; stopped old remote processes={len(owned)}')


def audited(count, digest):
    for filename in (lane.WORK / 'final-audit').glob(f'{count}-{digest[:16]}-*.json'):
        result = json.loads(filename.read_text())
        if result.get('ok') and result.get('csv_sha256') == digest:
            return True
    return False


def main():
    audit_process = None
    final_walk_started = (lane.WORK / 'final-walk-started.json').exists()
    last_heartbeat = 0
    while time.time() < lane.DEADLINE:
        try:
            if not running(lane.WORK / 'driver.pid', 'forensics_r37.py driver'):
                start_driver()
            owned = remote_workers()
            rows = lane.read_take()
            missing = [count for count in rows
                       if not audited(count, lane.sha(lane.TAKE / f'{count}.csv'))]
            final_due = time.time() >= lane.DEADLINE - 3600 and not final_walk_started
            if audit_process is not None and audit_process.poll() is not None:
                lane.state(f'AUDIT worker group{audit_process.pid} ended rc={audit_process.returncode}')
                audit_process = None
            if rows and (missing or final_due) and audit_process is None:
                with (lane.WORK / 'audit.log').open('a') as output:
                    selected = [] if final_due else [str(count) for count in missing]
                    audit_process = subprocess.Popen(['nohup', 'nice', '-n', '5', lane.PY, '-I',
                                                      str(lane.LANE / 'forensics_manage37.py'), 'audit'] + selected,
                                                     stdout=output, stderr=subprocess.STDOUT,
                                                     start_new_session=True)
                (lane.WORK / 'audit.pid').write_text(str(audit_process.pid) + '\n')
                lane.state(f'START uncapped direct-and-pandas audit group{audit_process.pid} '
                           f'counts={sorted(rows) if final_due else missing}; log work/audit.log')
                if final_due:
                    final_walk_started = True
                    lane.atomic(lane.WORK / 'final-walk-started.json', json.dumps(dict(at=lane.now())))
            if time.time() - last_heartbeat >= 300:
                logical = [line for line in owned if '/code/forensics_r37.py fqloop ' in line or
                           '/code/forensics_r37.py freshkick ' in line]
                lane.state(f'HEALTH driver alive; boxE slots={len(logical)}/2; '
                           f'take={sorted(rows)}; pending audits={missing}; audit_pid='
                           f'{audit_process.pid if audit_process is not None else None}')
                if len(logical) > 2:
                    raise RuntimeError('boxE numerical slot budget exceeded')
                last_heartbeat = time.time()
        except Exception as error:
            lane.state(f'HEALTH error {error!r}')
        time.sleep(min(20, max(1, lane.DEADLINE - time.time())))
    lane.state('STOP health watcher at common06:45Z deadline')


if __name__ == '__main__':
    main()
