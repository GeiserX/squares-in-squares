from pathlib import Path
import csv
import datetime
import hashlib
import json
import os
import shlex
import signal
import subprocess
import sys
import time

REPOSITORY = Path('$PRIVATE_REPO')
SOURCE = REPOSITORY / 'lanes/squares/tools/k123/r37'
SCRATCH = Path('$SCRATCH/bounties-squares')
TAKE = SCRATCH / 'take-k123-r37'
WORK = TAKE / 'work'
PYTHON = str(SCRATCH / 'venv/bin/python')
sys.path.insert(0, str(WORK))
import finalutil36


def note(message):
    line = datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ') + ' boxA FINAL37 ' + message
    with (TAKE / 'STATE.txt').open('a') as stream:
        stream.write(line + '\n')
    print(line, flush=True)


finalutil36.note = note


def wait_until(hour, minute, second=0):
    deadline = datetime.datetime(2026, 11, 18, hour, minute, second, tzinfo=datetime.timezone.utc).timestamp()
    while time.time() < deadline:
        time.sleep(min(30, deadline - time.time()))


def run(arguments, timeout=180):
    return finalutil36.run(arguments, timeout=timeout)


def stop_local(names):
    for name in names:
        pid_file = WORK / (name + '.pid')
        if not pid_file.exists():
            continue
        pid = int(pid_file.read_text())
        result = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], text=True, capture_output=True)
        if str(WORK) + '/' not in result.stdout:
            continue
        try:
            os.killpg(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        note('STOP ' + name + ' pid=' + str(pid))


def source_stamp():
    from policy27 import lines
    return hashlib.sha256(json.dumps(lines(), sort_keys=True).encode()).hexdigest()


def commit():
    paths = ['lanes/squares/avenues/k123.md', 'lanes/squares/results/k123-r37-2026-11-18.tsv', 'lanes/squares/tools/k123/r37']
    message = 'Record round 37 k123 changed-geometry joins'
    tracked = subprocess.run(['git', 'diff', '--quiet', 'HEAD', '--', *paths], cwd=REPOSITORY)
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '--', *paths], cwd=REPOSITORY, text=True)
    if tracked.returncode == 0 and not untracked.strip():
        return
    command = shlex.join(['git', 'add', '--', *paths]) + ' && ' + shlex.join(['git', 'commit', '--only', '-m', message, '--', *paths])
    result = subprocess.run(['/bin/zsh', '-c', command], cwd=REPOSITORY, capture_output=True, text=True)
    if result.returncode and 'index.lock' in result.stderr + result.stdout:
        time.sleep(3)
        result = subprocess.run(['/bin/zsh', '-c', command], cwd=REPOSITORY, capture_output=True, text=True)
    print(result.stdout + result.stderr, flush=True)
    if result.returncode:
        if 'nothing to commit' in result.stdout:
            return
        raise RuntimeError('Exact-path commit failed')
    revision = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--grep=^' + message + '$'], cwd=REPOSITORY, text=True).strip()
    output = subprocess.check_output(['git', 'show', '--stat', revision], cwd=REPOSITORY, text=True)
    print(output, flush=True)
    changed = subprocess.check_output(['git', 'show', '--pretty=', '--name-only', revision], cwd=REPOSITORY, text=True).splitlines()
    assert all(name in paths[:2] or name.startswith(paths[2] + '/') for name in changed)
    commits = json.loads((WORK / 'commits37.json').read_text()) if (WORK / 'commits37.json').exists() else []
    commits.append(revision)
    (WORK / 'commits37.json').write_text(json.dumps(commits))
    pushed = False
    for attempt in range(2):
        pull = subprocess.run(['git', 'pull', '--rebase', '--autostash', 'origin', 'main'], cwd=REPOSITORY, capture_output=True, text=True, timeout=20)
        print(pull.stdout + pull.stderr, flush=True)
        if pull.returncode:
            break
        push = subprocess.run(['git', 'push', 'origin', 'HEAD:main'], cwd=REPOSITORY, capture_output=True, text=True, timeout=20)
        print(push.stdout + push.stderr, flush=True)
        if push.returncode == 0:
            pushed = True
            break
        if attempt == 0:
            time.sleep(3)
    actual = subprocess.check_output(['git', 'log', '-1', '--format=%H', '--grep=^' + message + '$'], cwd=REPOSITORY, text=True).strip()
    if actual:
        commits[-1] = actual
        (WORK / 'commits37.json').write_text(json.dumps(commits))
    if not pushed:
        (WORK / 'blocked37.json').write_text(json.dumps('not pushed'))
    elif (WORK / 'blocked37.json').exists() and str(json.loads((WORK / 'blocked37.json').read_text())).startswith('not pushed'):
        (WORK / 'blocked37.json').unlink()
    note('COMMIT ' + commits[-1] + (' pushed' if pushed else ' not pushed'))


def main():
    note('START durable finalizer: precopy05:35Z, final walk05:40Z, search drain05:45Z, boxE stop06:20Z, final take06:54:30Z.')
    wait_until(5, 35)
    for host in ['boxD', 'boxE']:
        try:
            finalutil36.archive(host)
        except Exception as error:
            note('PRECOPY ' + host + ' ' + repr(error))
    wait_until(5, 40)
    with (WORK / 'finalwalk37.log').open('a') as stream:
        walk = subprocess.Popen(['nice', '-n', '5', PYTHON, str(WORK / 'finalwalk36.py')], stdout=stream, stderr=stream, start_new_session=True, stdin=subprocess.DEVNULL)
    (WORK / 'finalwalk37.pid').write_text(str(walk.pid))
    note('START final walk pid=' + str(walk.pid))
    wait_until(5, 45)
    stop_local(['stage', 'seed37', 'storage', 'bridge34'])
    (WORK / 'bridge-stop34').touch()
    finalutil36.stopremote('boxD')
    run([PYTHON, str(WORK / 'bridge34.py'), '--once', '--no-export'], timeout=240)
    finalutil36.archive('boxD', True)
    wait_until(6, 20)
    stop_local(['collect', 'third'])
    finalutil36.stopremote('boxE')
    for script, timeout in [('collect22.py', 180), ('near36.py', 240), ('follow37.py', 240), ('peer33.py', 30), ('independent33.py', 180), ('history28.py', 60)]:
        try:
            run([PYTHON, str(WORK / script)], timeout=timeout)
        except Exception as error:
            note('DRAIN ' + script + ' ' + repr(error))
    if (WORK / 'history28.json').exists():
        (WORK / 'history-final37.json').write_bytes((WORK / 'history28.json').read_bytes())
    finalutil36.archive('boxE', True)
    finalutil36.close_connections()
    if walk.poll() is None:
        walk.wait(timeout=max(1, datetime.datetime(2026, 11, 18, 6, 40, tzinfo=datetime.timezone.utc).timestamp() - time.time()))
    try:
        run([PYTHON, str(WORK / 'finalwalk36.py')], timeout=max(1, min(600, datetime.datetime(2026, 11, 18, 6, 44, tzinfo=datetime.timezone.utc).timestamp() - time.time())))
    except Exception as error:
        (WORK / 'blocked37.json').write_text(json.dumps('final source proof incomplete: ' + repr(error)))
        walks = json.loads((WORK / 'finalwalk36.json').read_text()) if (WORK / 'finalwalk36.json').exists() else []
        clean = {str(item['n']) for item in walks if item.get('clean') and not item.get('capped') and item.get('withdrawal_stamp') == source_stamp()}
        with (TAKE / 'take.tsv').open() as stream:
            reader = csv.DictReader(stream, delimiter='\t')
            fields = reader.fieldnames
            retained = [row for row in reader if row['n'] in clean]
        with (TAKE / 'take.tsv.tmp').open('w') as stream:
            writer = csv.DictWriter(stream, fields, delimiter='\t')
            writer.writeheader()
            writer.writerows(retained)
        (TAKE / 'take.tsv.tmp').replace(TAKE / 'take.tsv')
    (WORK / 'cleanup37.json').write_text(json.dumps({'complete': True, 'processes_left': 0, 'time': datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')}))
    run([PYTHON, str(SOURCE / 'report37.py'), '--artifacts'], timeout=60)
    try:
        commit()
    except Exception as error:
        note('CHECKPOINT COMMIT ' + repr(error))
        (WORK / 'blocked37.json').write_text(json.dumps('not pushed: ' + repr(error)))
    wait_until(6, 50)
    marker = WORK / 'retention-withdraw-stamp32'
    if not marker.exists() or marker.read_text() != source_stamp():
        try:
            run([PYTHON, str(WORK / 'retention32.py')], timeout=180)
        except Exception as error:
            note('LATE SOURCE ' + repr(error))
            (WORK / 'blocked37.json').write_text(json.dumps('late source refresh incomplete'))
            (WORK / 'late-unverified37.tsv').write_bytes((TAKE / 'take.tsv').read_bytes())
            (TAKE / 'take.tsv.tmp').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
            (TAKE / 'take.tsv.tmp').replace(TAKE / 'take.tsv')
    while datetime.datetime.now(datetime.timezone.utc) < datetime.datetime(2026, 11, 18, 6, 54, 10, tzinfo=datetime.timezone.utc):
        run([PYTHON, str(WORK / 'peer33.py')], timeout=20)
        time.sleep(20)
    if not marker.exists() or marker.read_text() != source_stamp():
        (WORK / 'late-unverified37.tsv').write_bytes((TAKE / 'take.tsv').read_bytes())
        (TAKE / 'take.tsv.tmp').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
        (TAKE / 'take.tsv.tmp').replace(TAKE / 'take.tsv')
        (WORK / 'blocked37.json').write_text(json.dumps('withdrawal set changed after final source refresh; unverified rows omitted'))
    run([PYTHON, str(WORK / 'peer33.py')], timeout=20)
    run([PYTHON, str(SOURCE / 'report37.py'), '--artifacts'], timeout=30)
    try:
        commit()
    except Exception as error:
        note('FINAL COMMIT ' + repr(error))
        (WORK / 'blocked37.json').write_text(json.dumps('not pushed: ' + repr(error)))
    run([PYTHON, str(SOURCE / 'report37.py'), '--final'], timeout=30)
    (WORK / 'finalize37.done').write_text(json.dumps({'time': datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')}))
    note('FINISH report.json written, take.tsv frozen, processes_left=0.')


if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        note('ERROR ' + repr(error))
        raise
