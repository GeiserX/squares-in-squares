"""Move a few paused fresh scan tasks into the existing boxD slot."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from setup38 import TAKE, WORK

ROOT = 'scratch/squares-k123'
NB = 'boxD'
BOXE = 'boxE'
HERE = Path(__file__).resolve().parent
HOST_PY = '/Users/boxD/scratch/squares-readers/venv/bin/python'


def remote(host, command, *, check=True, timeout=25):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', host, command],
                          capture_output=True, text=True, timeout=timeout, check=check)


def copy(source, target):
    subprocess.run(['scp', '-q', str(source), str(target)], timeout=45, check=True)


def stamp(message):
    line = f'{datetime.now(timezone.utc):%FT%TZ} boxA {message}'
    print(line, flush=True)
    with (TAKE / 'STATE.txt').open('a') as stream:
        stream.write(line + '\n')


def feed_scan(tag, control=False):
    src = WORK / tag / 'send.tgz'
    folder = f'{ROOT}/scan-on-boxCD38/{tag}'
    remote(NB, f'mkdir -p ~/{folder}')
    copy(src, f'{NB}:{folder}/input.tgz')
    command = (
        f'cd ~/{folder} && tar -xzf input.tgz && cd ~/{ROOT} && '
        'env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 '
        f'nice -n 5 {HOST_PY} -I scan_boxCD38.py {tag}'
    )
    result = remote(NB, command, timeout=60)
    receipt = json.loads(result.stdout.splitlines()[-1])
    dest = WORK / 'routed-boxCD38' / tag
    dest.mkdir(parents=True, exist_ok=True)
    for name in ['recipes.tsv', 'receipt.json', f'scan{tag}.log']:
        copy(f'{NB}:{folder}/{name}', dest / name)
    if control:
        return receipt, dest
    remote(BOXE, f'mkdir -p ~/{ROOT}/routed-boxCD38/{tag}')
    for name in ['recipes.tsv', 'receipt.json']:
        copy(dest / name, f'{BOXE}:{ROOT}/routed-boxCD38/{tag}/{name}')
    remote(BOXE, f'$SCRATCH/squares-base/venv/bin/python -I ~/{ROOT}/scan_boxCD38.py {tag} --install')
    stamp(f'FINISH boxD fresh scan {tag} with {receipt["recipes"]} recipes. Receipt {dest / "receipt.json"}. Deadline 13:45Z.')
    return receipt, dest


def route(tags):
    assert all(re.fullmatch(r'fresh38\d+', tag) for tag in tags)
    load = remote(NB, f'{HOST_PY} -c "import os; print(os.getloadavg()[0])"')
    if float(load.stdout) >= 10:
        print('boxD load guard closed', load.stdout.strip(), flush=True)
        return
    remote(NB, f'cd ~/{ROOT} && touch STOP34 && {HOST_PY} -I stop_remote25.py')
    try:
        helper = HERE / 'runtime' / 'scan_boxCD38.py'
        for host in (NB, BOXE):
            copy(helper, f'{host}:{ROOT}/scan_boxCD38.py')
        control_tag = 'fresh3810002'
        reference = remote(BOXE, f'cd ~/{ROOT} && awk -F "\\t" \'$8 == "{control_tag}"\' queue.tsv').stdout
        dest = WORK / 'routed-boxCD38' / control_tag
        if (dest / 'receipt.json').is_file():
            result = json.loads((dest / 'receipt.json').read_text())
        else:
            result, dest = feed_scan(control_tag, control=True)
        assert result['recipes'] > 0 and set((dest / 'recipes.tsv').read_text().splitlines()) == set(reference.splitlines())
        stamp(f'PASS boxD scan control {control_tag}. It reproduced {result["recipes"]} boxE recipes.')
        for tag in tags:
            load = remote(NB, f'{HOST_PY} -c "import os; print(os.getloadavg()[0])"')
            if float(load.stdout) >= 10:
                stamp(f'PAUSE further boxD scans at load {load.stdout.strip()}.')
                break
            held = remote(BOXE, f'cd ~/{ROOT} && mkdir -p routed38 && mv tasks/{tag}.json routed38/{tag}.json', check=False)
            if held.returncode:
                continue
            stamp(f'START boxD fresh-certificate scan {tag} in its single slot. Deadline 13:45Z.')
            try:
                feed_scan(tag)
            except (OSError, ValueError, subprocess.SubprocessError) as error:
                stamp(f'RECOVER scan {tag} to boxE after boxD error {error!r}.')
                remote(BOXE, f'cd ~/{ROOT} && if test -f routed38/{tag}.json; then mv routed38/{tag}.json tasks/; fi', check=False)
    finally:
        result = remote(NB, f'cd ~/{ROOT} && rm -f STOP34 && {HOST_PY} -I remotehealth36.py')
        stamp(f'RESUME boxD worker after the scan batch. {result.stdout.strip()}')


if __name__ == '__main__':
    route(sys.argv[1:])
