"""Monitor and close the round with verified archives and a frozen take."""
from datetime import datetime, timezone
import hashlib
import fcntl
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

from report38 import REPO
from setup38 import SCRATCH, TAKE, WORK, write_json

HERE = Path(__file__).resolve().parent
PYTHON = str(SCRATCH / 'venv/bin/python')
BOXES = ('boxD', 'boxE')
sys.path.insert(0, str(WORK))
import finalutil36

CONTROLLERS = {
    'collect': ['resident25.py', 'collect'],
    'stage': ['resident25.py', 'stage'],
    'third': ['background29.py', 'third'],
    'storage': ['background29.py', 'storage'],
    'bridge34': ['bridge34.py'],
}


def note(message):
    now = datetime.now(timezone.utc).strftime('%FT%TZ')
    line = f'{now} boxA FINAL38 {message}'
    with (TAKE / 'STATE.txt').open('a') as stream:
        stream.write(line + '\n')
    print(line, flush=True)


finalutil36.note = note


def at(hour, minute, second=0):
    return datetime(2026, 11, 18, hour, minute, second, tzinfo=timezone.utc).timestamp()


def wait_until(deadline):
    while time.time() < deadline:
        time.sleep(min(30, deadline - time.time()))


def run(script, *arguments, timeout=60):
    return finalutil36.run([PYTHON, str(script), *arguments], timeout=timeout)


def owned_pid(name):
    pin = WORK / (name + '.pid')
    if not pin.is_file():
        return None
    pid = int(pin.read_text())
    command = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True).stdout
    return pid if str(WORK) + '/' in command else None


def stop(*names):
    for name in names:
        pid = owned_pid(name)
        if pid is None:
            continue
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            continue
        note(f'STOP {name} pid={pid}.')


def check_controllers():
    for name, args in CONTROLLERS.items():
        if owned_pid(name) is not None:
            continue
        log = WORK / (name + '-r38.log')
        env = dict(
            os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
            VECLIB_MAXIMUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1',
        )
        with log.open('a') as stream:
            process = subprocess.Popen(
                ['nohup', 'nice', '-n', '5', PYTHON, str(WORK / args[0]), *args[1:]],
                stdout=stream, stderr=stream, stdin=subprocess.DEVNULL, start_new_session=True, env=env,
            )
        (WORK / (name + '.pid')).write_text(str(process.pid))
        note(f'RECOVER {name} pid={process.pid}. Log {log}. Deadline 13:45Z.')


def watch_take(timeout=900):
    if timeout < 1:
        return
    try:
        run(WORK / 'finalwalk36.py', timeout=timeout)
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        note(f'Check on current take did not complete. {error!r}')


def source_stamp():
    from policy27 import lines
    return hashlib.sha256(json.dumps(lines(), sort_keys=True).encode()).hexdigest()


def prune_unproved():
    from report38 import rows
    from setup38 import ROW_FIELDS
    import csv
    with (WORK / 'collect.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        proofs_path = WORK / 'finalwalk36.json'
        proofs = json.loads(proofs_path.read_text()) if proofs_path.is_file() else []
        stamp = source_stamp()
        exact = {
            (r['n'], r['sha256'])
            for r in proofs
            if r['clean'] and not r['capped'] and r['withdrawal_stamp'] == stamp
        }
        good = []
        removed = []
        for row in rows(TAKE / 'take.tsv'):
            count = int(row['n'])
            data = (TAKE / f'{count}.csv').read_bytes()
            if (count, hashlib.sha256(data).hexdigest()) in exact:
                good.append(row)
            else:
                removed.append(count)
        if not removed:
            return
        temporary = TAKE / 'take.tsv.tmp'
        with temporary.open('w') as stream:
            writer = csv.DictWriter(stream, ROW_FIELDS, delimiter='\t')
            writer.writeheader()
            writer.writerows(good)
        temporary.replace(TAKE / 'take.tsv')
        message = f'Final source proof unavailable for {removed}.'
        note(message)
        write_json(WORK / 'blocked38.json', message)


def commit():
    paths = [
        'lanes/squares/avenues/k123.md',
        'lanes/squares/results/k123-r38-2026-11-18.tsv',
        *[
            str(path.relative_to(REPO))
            for path in sorted(HERE.rglob('*.py'))
        ],
    ]
    message = 'Record round 38 k123 joins'
    tracked = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=REPO)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', *paths], cwd=REPO, text=True)
    if tracked.returncode and not untracked.strip():
        message = 'Finish round 38 k123 result table'
    if tracked.returncode or untracked.strip():
        command = shlex.join(['git', 'add', '--', *paths]) + ' && ' + shlex.join(['git', 'commit', '--only', '-m', message, '--', *paths])
        result = finalutil36.run(['/bin/zsh', '-c', command], cwd=REPO, timeout=30, check=False)
        if result.returncode and 'index.lock' in result.stdout:
            time.sleep(3)
            result = finalutil36.run(['/bin/zsh', '-c', command], cwd=REPO, timeout=30, check=False)
        if result.returncode:
            raise RuntimeError('Exact-path commit failed')
        revision = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--grep=^' + message + '$'], cwd=REPO, text=True).strip()
        finalutil36.run(['git', 'show', '--stat', revision], cwd=REPO, timeout=20)
        changed = subprocess.check_output(['git', 'show', '--pretty=', '--name-only', revision], cwd=REPO, text=True).splitlines()
        assert changed and set(changed) <= set(paths)
    commits_path = WORK / 'commits38.json'
    messages = ['Record round 38 k123 joins', 'Finish round 38 k123 result table']
    commits = []
    pushed = False
    for attempt in range(2):
        pulled = finalutil36.run(['git', 'pull', '--rebase', '--autostash', 'origin', 'main'], cwd=REPO, timeout=30, check=False)
        for text in messages:
            revision = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--grep=^' + text + '$'], cwd=REPO, text=True).strip()
            if revision:
                commits.append(revision)
        write_json(commits_path, list(dict.fromkeys(commits)))
        commits.clear()
        if pulled.returncode:
            break
        if not finalutil36.run(['git', 'push', 'origin', 'HEAD:main'], cwd=REPO, timeout=30, check=False).returncode:
            pushed = True
            break
        if attempt == 0:
            time.sleep(3)
    if not pushed:
        write_json(WORK / 'blocked38.json', 'not pushed')
    elif (WORK / 'blocked38.json').is_file() and (WORK / 'blocked38.json').read_text().strip() == '"not pushed"':
        (WORK / 'blocked38.json').unlink()
    note(f'COMMIT {commits_path.read_text().strip()} pushed={pushed}.')


def checkpoint():
    run(HERE / 'report38.py', '--artifacts', timeout=45)
    try:
        commit()
    except (RuntimeError, subprocess.TimeoutExpired) as error:
        write_json(WORK / 'blocked38.json', f'not pushed. {error!r}')
        note(f'Commit or push incomplete. {error!r}')


def main():
    note('START durable monitor. Final source walks start by 12:45Z. All long jobs stop by 13:45Z.')
    last_take = None
    while time.time() < at(12, 30):
        check_controllers()
        now = (TAKE / 'take.tsv').stat().st_mtime_ns
        if now != last_take:
            watch_take()
            last_take = now
        wait_until(min(at(12, 30), time.time() + 60))

    for host in BOXES:
        try:
            finalutil36.archive(host)
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            note(f'PRECOPY {host} {error!r}')
    wait_until(at(12, 40))
    with (WORK / 'finalwalk38.log').open('a') as stream:
        walk = subprocess.Popen(
            ['nice', '-n', '5', PYTHON, str(WORK / 'finalwalk36.py')],
            stdout=stream, stderr=stream, stdin=subprocess.DEVNULL, start_new_session=True,
        )
    (WORK / 'finalwalk38.pid').write_text(str(walk.pid))
    note(f'START final walk pid={walk.pid}. Log {WORK / "finalwalk38.log"}.')
    wait_until(at(12, 45))
    stop('stage', 'storage', 'bridge34')
    (WORK / 'bridge-stop34').touch()
    finalutil36.stopremote('boxD')
    run(WORK / 'bridge34.py', '--once', '--no-export', timeout=200)
    finalutil36.archive('boxD', final=True)
    wait_until(at(13, 22))
    stop('third', 'collect')
    finalutil36.stopremote('boxE')
    for script, timeout in [('collect22.py', 180), ('near36.py', 180), ('own_follow38.py', 180), ('history28.py', 45)]:
        try:
            run(WORK / script, timeout=timeout)
        except (RuntimeError, subprocess.TimeoutExpired) as error:
            note(f'DRAIN {script} {error!r}')
    finalutil36.archive('boxE', final=True)
    finalutil36.close_connections()
    if walk.poll() is None:
        stop('finalwalk38')
        walk.wait(timeout=10)
    watch_take(timeout=max(0, min(900, at(13, 44, 30) - time.time())))
    prune_unproved()
    run(WORK / 'peer33.py', timeout=30)
    remaining = [name for name in CONTROLLERS if owned_pid(name) is not None]
    write_json(WORK / 'cleanup38.json', {'processes_left': len(remaining), 'remaining': remaining})
    assert not remaining
    checkpoint()

    wait_until(at(13, 50))
    while time.time() < at(13, 54, 35):
        prune_unproved()
        run(WORK / 'peer33.py', timeout=30)
        wait_until(min(at(13, 54, 35), time.time() + 30))
    note('FREEZE take.tsv for assembly.')
    checkpoint()
    wait_until(at(13, 55))
    run(HERE / 'report38.py', '--final', timeout=30)
    note('FINISH report.json written and owned workers stopped.')


if __name__ == '__main__':
    with (WORK / 'finalize38.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            main()
        except BaseException as error:
            note(f'ERROR {error!r}')
            raise
