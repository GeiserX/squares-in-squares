#!/usr/bin/env python3
"""Two-slot round 22 worker. Fresh builds precede raw-find legs and frozen starts."""
import csv
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

D = Path(__file__).resolve().parent
BASE = Path.home() / 'scratch/squares-base'
PY = str(BASE / 'venv/bin/python')
FQ = str(BASE / 'fq')


def write(path, obj):
    path = Path(path)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj))
    tmp.replace(path)


def log(s):
    with open('logs/worker.log', 'a') as f:
        f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ ', time.gmtime()) + s + '\n')


def jobs(slot):
    out = []
    for p in Path('jobs').glob('*.json'):
        if (Path('claims') / p.stem).exists() or (Path('cancel') / p.stem).exists():
            continue
        j = json.loads(p.read_text())
        if j.get('slot', slot) != slot:
            continue
        out.append((j['priority'], -j['created'], p, j))
    return sorted(out, key=lambda x: x[:2])


def main():
    os.chdir(D)
    slot = int(sys.argv[1])
    for d in ('claims', 'cancel', 'jobs', 'logs', 'run', 'done'):
        Path(d).mkdir(exist_ok=True)
    while time.time() < float(Path('deadline').read_text()) - 40 and not Path('STOP').exists():
        if slot == 1 and Path('fqin/GO').exists():
            with open('logs/quench.log', 'a') as out:
                r = subprocess.run([PY, 'midm_fqonce.py', 'fqin', 'fqout', FQ, 'x'], stdout=out, stderr=subprocess.STDOUT)
            if r.returncode == 0:
                Path('fqout/DONE').touch()
            else:
                Path('fqout/FAILED').touch()
            Path('fqin/GO').unlink()
            log('QUENCH rc=%d' % r.returncode)
            continue
        task = None
        for _, _, p, j in jobs(slot):
            try:
                (Path('claims') / p.stem).mkdir()
            except FileExistsError:
                continue
            task = j
            break
        if task is None:
            time.sleep(5)
            continue
        j = task
        left = float(Path('deadline').read_text()) - time.time() - 30
        secs = min(j['seconds'], left)
        outdir = 'run/s%d' % j['k']
        Path(outdir).mkdir(parents=True, exist_ok=True)
        cmd = [PY, 'midm_scan.py', '--n', str(j['n']), '--sub', j['sub'], '--out', outdir,
               '--fq', FQ, '--seconds', str(int(secs)), '--seed', str(j['seed']),
               '--modes', 'kick,lkick', '--ref', '0', '--deadline', 'deadline', '--kicks', str(j['sigma']), '--stop6']
        # The A/B has no bank: its sigma and allotted time must stay fixed.
        if not j.get('ab'):
            cmd += ['--bank', 'bank%d.txt' % slot]
        log('START slot=%d %s' % (slot, json.dumps(j, sort_keys=True)))
        begin = time.time()
        with open(outdir + '/worker.log', 'a') as out:
            r = subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT)
        j['elapsed'] = time.time() - begin
        j['returncode'] = r.returncode
        scan = Path(outdir) / ('scan-%d-%d.tsv' % (j['n'], j['seed']))
        end = [l for l in scan.read_text().splitlines() if l.startswith('# END')] if scan.exists() else []
        if end:
            m = re.search(r'finds (\d+) best ([0-9.]+) held ([0-9.]+)', end[-1])
            j['finds'] = int(m[1])
            j['gain'] = (float(m[3]) - float(m[2])) / math.sqrt(j['n'])
            leg = j.get('leg', 0)
            if j['finds'] and (j['gain'] >= 1e-6 or (j['gain'] >= 3e-8 and leg < 2)):
                raws = list(Path(outdir + '/raw').glob('%d-*-%d-%d.csv' % (j['n'], j['seed'], j['finds'])))
                if raws:
                    new = {k: v for k, v in j.items() if k not in ('gain', 'finds', 'elapsed', 'returncode', 'slot', 'ab')}
                    new.update(sub=str(raws[0]), seed=j['seed'] + 100, leg=leg + 1, priority=2, created=time.time())
                    write('jobs/%d-%d-L%d.json' % (j['k'], j['n'], leg + 1), new)
        write('done/' + p.name, j)
        log('END slot=%d k=%d n=%d leg=%d finds=%s gain=%s elapsed=%.1f' % (
            slot, j['k'], j['n'], j.get('leg', 0), j.get('finds'), j.get('gain'), j['elapsed']))
    log('STOP slot=%d' % slot)


if __name__ == '__main__':
    main()
