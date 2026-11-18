#!/usr/bin/env python3
"""Two-slot round 25 worker. Fresh builds precede raw-find legs and frozen starts."""
import csv
import json
import math
import os
from pathlib import Path
import re
import subprocess
import signal
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
    visited = {int(p.name.split('-')[1]) for p in Path('claims').iterdir() if '-' in p.name and not (Path('cancel')/p.name).exists()}
    for p in Path('jobs').glob('*.json'):
        if (Path('claims') / p.stem).exists() or (Path('cancel') / p.stem).exists():
            continue
        j = json.loads(p.read_text())
        if j.get('raw_design') and j['n'] not in visited and .55 < j['priority'] <= .9:
            j = dict(j, priority=.55)
        if j.get('slot', slot) != slot:
            if slot != 2 or j.get('public'):
                continue
            j = dict(j, priority=j['priority']+10)
        out.append((j['priority'], -j['created'], p, j))
    return sorted(out, key=lambda x: x[:2])



def stop_owned_child(child):
    records = {}
    for line in subprocess.check_output(['ps','-Ao','pid=,ppid='],text=True).splitlines():
        pid,parent = map(int,line.split());records[pid]=parent
    owned = {child.pid}
    while True:
        added = {pid for pid,parent in records.items() if parent in owned}-owned
        if not added:break
        owned |= added
    for sig in (signal.SIGTERM,signal.SIGKILL):
        for pid in owned:
            try:os.kill(pid,sig)
            except ProcessLookupError:pass
        time.sleep(.1)
    return child.wait()


def run_cancelable(cmd, out, marker):
    child = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    while child.poll() is None:
        if Path(marker).exists() or Path('STOP').exists() or time.time() >= float(Path('deadline').read_text()):
            return stop_owned_child(child)
        time.sleep(.25)
    return child.returncode


def main():
    os.chdir(D)
    slot = int(sys.argv[1])
    for d in ('claims', 'cancel', 'jobs', 'logs', 'run', 'done'):
        Path(d).mkdir(exist_ok=True)
    while time.time() < float(Path('deadline').read_text()) - 40 and not Path('STOP').exists():
        marker=Path('RELOAD%d'%slot)
        if marker.exists():
            marker.unlink();os.execv(PY,[PY,str(D/'worker25.py'),str(slot)])
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
        if time.time() >= float(Path('search-deadline').read_text()):
            time.sleep(5)
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
            returncode = run_cancelable(cmd, out, Path('cancel')/p.stem)
        j['elapsed'] = time.time() - begin
        j['returncode'] = returncode
        scan = Path(outdir) / ('scan-%d-%d.tsv' % (j['n'], j['seed']))
        end = [l for l in scan.read_text().splitlines() if l.startswith('# END')] if scan.exists() else []
        if end and not (Path('cancel')/p.stem).exists():
            m = re.search(r'finds (\d+) best ([0-9.]+) held ([0-9.]+)', end[-1])
            j['finds'] = int(m[1])
            j['gain'] = (float(m[3]) - float(m[2])) / math.sqrt(j['n'])
            leg = j.get('leg', 0)
            if j['finds'] and j['gain'] >= 1e-6 and time.time() < float(Path('search-deadline').read_text()):
                raws = list(Path(outdir + '/raw').glob('%d-*-%d-%d.csv' % (j['n'], j['seed'], j['finds'])))
                if raws:
                    new = {k: v for k, v in j.items() if k not in ('gain', 'finds', 'elapsed', 'returncode', 'ab')}
                    new.update(sub=str(raws[0]), seed=j['seed'] + 100, leg=leg + 1, slot=1, priority=0.4 if j['gain'] >= 1e-6 and j['n'] < 640 else (0.5 if j['n'] < 640 else 1.6), created=time.time())
                    write('jobs/%d-%d-L%d.json' % (j['k'], j['n'], leg + 1), new)
        write('done/' + p.name, j)
        log('END slot=%d k=%d n=%d leg=%d finds=%s gain=%s elapsed=%.1f' % (
            slot, j['k'], j['n'], j.get('leg', 0), j.get('finds'), j.get('gain'), j['elapsed']))
    log('STOP slot=%d' % slot)


if __name__ == '__main__':
    main()
