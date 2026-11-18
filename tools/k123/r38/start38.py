from pathlib import Path
import datetime
import json
import os
import subprocess

SCRATCH = Path('$SCRATCH/bounties-squares')
TAKE = SCRATCH / 'take-k123-r38'
WORK = TAKE / 'work'
PYTHON = str(SCRATCH / 'venv/bin/python')


def launch():
    assert json.loads((WORK / 'controls29.json').read_text())['own756_accepted']
    for host in ['boxE', 'boxD']:
        configuration = WORK if host == 'boxE' else WORK / host
        assert json.loads((configuration / 'control38.json').read_text())['passed']
    subprocess.run(['ssh', 'boxE', 'mkdir -p $SCRATCH/squares-k123/control580'], check=True, timeout=30)
    for source, destination in [(SCRATCH / 'take-k123-r26/580.csv', 'control580/580.csv'), (SCRATCH / 'gate/cand-round25-1114b/details.csv', 'control-details.csv')]:
        subprocess.run(['scp', '-q', str(source), 'boxE:scratch/squares-k123/' + destination], check=True, timeout=60)
    job = {'kind': 'verify', 'tag': 'verify-control26-580', 'out': 'control-verify580', 'source': 'positive control held round25b 580', 'raws': ['control580'], 'details': 'control-details.csv'}
    task = WORK / 'verify-control26-580.json'
    task.write_text(json.dumps(job))
    subprocess.run(['scp', '-q', str(task), 'boxE:scratch/squares-k123/tasks/'], check=True, timeout=60)
    subprocess.run(['scp', '-q', str(WORK / 'third22.py'), 'boxE:scratch/squares-k123/'], check=True, timeout=60)
    for host in ['boxE', 'boxD']:
        configuration = WORK if host == 'boxE' else WORK / host
        config = json.loads((configuration / 'runtime33.json').read_text())
        command = f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {config["python"]} -I box_guard34.py > out/box-guard34.log 2>&1 < /dev/null &'
        subprocess.run(['ssh', host, command], check=True, timeout=30)
    started = []
    environment = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1', PYTHONDONTWRITEBYTECODE='1')
    for name, arguments in [('collect', ['resident25.py', 'collect']), ('stage', ['resident25.py', 'stage']), ('third', ['background29.py', 'third']), ('storage', ['background29.py', 'storage']), ('bridge34', ['bridge34.py'])]:
        with (WORK / (name + '-r38.log')).open('a') as stream:
            process = subprocess.Popen(['nohup', 'nice', '-n', '5', PYTHON, str(WORK / arguments[0]), *arguments[1:]], stdout=stream, stderr=stream, stdin=subprocess.DEVNULL, start_new_session=True, env=environment)
        (WORK / (name + '.pid')).write_text(str(process.pid))
        started.append({'name': name, 'pid': process.pid})
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
    message = timestamp + ' k123 -> all: START round 38 band joins on held 683 and 793, with one wide 1.005 slot. boxE 3, boxD 1. Closed 32452 prior signatures. Both 444 controls and all four live-stop cases passed. Deadline 13:45Z. ' + str(TAKE) + '\n'
    for destination in [TAKE / 'STATE.txt', SCRATCH / 'handoff-r38.log']:
        with destination.open('a') as stream:
            stream.write(message)
    with (TAKE / 'STATE.txt').open('a') as stream:
        stream.write(timestamp + ' boxA START ' + json.dumps(started) + ' logs under work/*-r38.log. Final walks by 12:45Z.\n')
    (WORK / 'started38.json').write_text(json.dumps(started, indent=2))
    print(json.dumps(started))


if __name__ == '__main__':
    launch()
