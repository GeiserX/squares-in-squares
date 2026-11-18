from pathlib import Path
import datetime
import json
import os
import subprocess

SCRATCH = Path('$SCRATCH/bounties-squares')
TAKE = SCRATCH / 'take-k123-r37'
WORK = TAKE / 'work'
PYTHON = str(SCRATCH / 'venv/bin/python')


def launch():
    assert json.loads((WORK / 'controls29.json').read_text())['own756_accepted']
    for host in ['boxE', 'boxD']:
        configuration = WORK if host == 'boxE' else WORK / host
        assert json.loads((configuration / 'control37.json').read_text())['passed']
    subprocess.run(['ssh', 'boxE', 'mkdir -p $SCRATCH/squares-k123/control580'], check=True, timeout=30)
    for source, destination in [(SCRATCH / 'take-k123-r26/580.csv', 'control580/580.csv'), (SCRATCH / 'gate/cand-round25-1114b/details.csv', 'control-details.csv')]:
        subprocess.run(['scp', '-q', str(source), 'boxE:scratch/squares-k123/' + destination], check=True, timeout=60)
    job = {'kind': 'verify', 'tag': 'verify-control26-580', 'out': 'control-verify580', 'source': 'positive control held round25b 580', 'raws': ['control580'], 'details': 'control-details.csv'}
    task = WORK / 'verify-control26-580.json'
    task.write_text(json.dumps(job))
    subprocess.run(['scp', '-q', str(task), 'boxE:scratch/squares-k123/tasks/'], check=True, timeout=60)
    for host in ['boxE', 'boxD']:
        configuration = WORK if host == 'boxE' else WORK / host
        config = json.loads((configuration / 'runtime33.json').read_text())
        command = f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {config["python"]} -I box_guard34.py > out/box-guard34.log 2>&1 < /dev/null &'
        subprocess.run(['ssh', host, command], check=True, timeout=30)
    started = []
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    for name, arguments in [('collect', ['resident25.py', 'collect']), ('stage', ['resident25.py', 'stage']), ('third', ['background29.py', 'third']), ('storage', ['background29.py', 'storage']), ('bridge34', ['bridge34.py']), ('seed37', ['seed37.py'])]:
        with (WORK / (name + '-r37.log')).open('a') as stream:
            process = subprocess.Popen(['nohup', 'nice', '-n', '5', PYTHON, str(WORK / arguments[0]), *arguments[1:]], stdout=stream, stderr=stream, stdin=subprocess.DEVNULL, start_new_session=True, env=environment)
        (WORK / (name + '.pid')).write_text(str(process.pid))
        started.append({'name': name, 'pid': process.pid})
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
    message = timestamp + ' k123 -> all: round37 changed-geometry band joins START. boxE3 boxD:1. Both 444 controls reproduce side21.564693167754. Own756 and changed-producer controls pass. Closed30024 prior geometry signatures. Held36b bar37, no share gate on held or own descendants. Changed793 597 698 812 972 539 692 976 911 first. Source walks cap100000 reject capped. Search stops05:45Z, hard shared search/quench deadline06:45Z. ' + str(TAKE) + '\n'
    for destination in [TAKE / 'STATE.txt', SCRATCH / 'handoff-r37.log']:
        with destination.open('a') as stream:
            stream.write(message)
    with (TAKE / 'STATE.txt').open('a') as stream:
        stream.write(timestamp + ' boxA START ' + json.dumps(started) + ' logs work/*-r37.log. Final walks by05:45Z.\n')
    (WORK / 'started37.json').write_text(json.dumps(started, indent=2))
    print(json.dumps(started))


if __name__ == '__main__':
    launch()
