#!/usr/bin/env python3
"""Round 27 worker: worker26.py plus certification on the box.

Round 27 change (20:15-21:13Z measured: one driver step took 1316 s on boxA at load 75-100, 1199 s of it in
floatsafe): at the end of each scan this slot certifies the lowest raw find of that scan with floatsafe.work (2.2e-11,
the same code the driver ran) and writes run/s<k>/cert/<raw stem>.csv and .json (score, dilation, sha256 of the raw
file); a job with self_cert also gets its start certified as run/s<k>/cert/start.csv and .json. The driver uses these
when the sha256 matches and re-certifies every final take row on boxA before the round closes.

Round 26 text:

Changes from worker25.py:
- the base dir (venv and fq) comes from MIDM_BASE, so the same worker runs on boxE and on boxD;
- every job in this box's jobs/ is open to every slot of the box (the boxA driver assigns jobs to boxes);
- a certified-file quench batch (fqin/GO) is claimed by mkdir fqin/CLAIM, so any free slot of the box runs it once;
- a raw-find leg takes its parent's class plus 0.6, capped at 0.45: a leg of a fresh round 26 design runs after the
  fresh first scans and before the saved starts.
Usage: worker26.py SLOT   (run in the box's scratch dir, with files deadline and search-deadline holding epochs)
"""
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

D = Path(__file__).resolve().parent
BASE = Path(os.environ.get('MIDM_BASE', str(Path.home() / 'scratch/squares-base'))).expanduser()
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


def epoch(name):
    return float(Path(name).read_text())


def jobs():
    out = []
    for p in Path('jobs').glob('*.json'):
        if (Path('claims') / p.stem).exists() or (Path('cancel') / p.stem).exists():
            continue
        try:
            j = json.loads(p.read_text())
        except ValueError:
            continue
        out.append((j['priority'], -j['created'], p, j))
    return sorted(out, key=lambda x: x[:2])


def stop_owned_child(child):
    records = {}
    for line in subprocess.check_output(['ps', '-Ao', 'pid=,ppid='], text=True).splitlines():
        pid, parent = map(int, line.split())
        records[pid] = parent
    owned = {child.pid}
    while True:
        added = {pid for pid, parent in records.items() if parent in owned} - owned
        if not added:
            break
        owned |= added
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for pid in owned:
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                pass
        time.sleep(.1)
    return child.wait()


def run_cancelable(cmd, out, marker):
    child = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    while child.poll() is None:
        if Path(marker).exists() or Path('STOP').exists() or time.time() >= epoch('deadline'):
            return stop_owned_child(child)
        time.sleep(.25)
    return child.returncode


def side_of(path):
    import csv
    xs = []
    for r in csv.DictReader(open(path)):
        a = float(r['angle']); h = .5 * (abs(math.cos(a)) + abs(math.sin(a)))
        xs.append((float(r['x']) - h, float(r['x']) + h, float(r['y']) - h, float(r['y']) + h))
    return max(max(x[1] for x in xs) - min(x[0] for x in xs), max(x[3] for x in xs) - min(x[2] for x in xs))


def certify(n, src, stem, outdir):
    """floatsafe.work on one file; writes outdir/cert/<stem>.csv (when it certifies) and .json."""
    import csv, hashlib
    import floatsafe
    cd = Path(outdir) / 'cert'; cd.mkdir(exist_ok=True)
    t = time.time()
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(src))]
    rec = dict(src=str(src), sha=hashlib.sha256(Path(src).read_bytes()).hexdigest(), n=n)
    if len(rows) != n:
        rec.update(ok=False, why='count %d' % len(rows))
    else:
        _, fr, score, e = floatsafe.work((n, rows))
        rec.update(ok=fr is not None, score=score, e=e)
        if fr is not None:
            tmp = cd / ('.%s.tmp' % stem)
            with open(tmp, 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in fr:
                    w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            tmp.replace(cd / ('%s.csv' % stem))
    rec['seconds'] = time.time() - t
    write(cd / ('%s.json' % stem), rec)
    return rec


def quench_batch(slot):
    if not Path('fqin/GO').exists():
        return False
    try:
        Path('fqin/CLAIM').mkdir()
    except (FileExistsError, FileNotFoundError):
        return False
    with open('logs/quench.log', 'a') as out:
        r = run_cancelable([PY, 'midm_fqonce.py', 'fqin', 'fqout', FQ, 'x'], out, 'fqin/CANCEL')
    Path('fqout/DONE' if r == 0 else 'fqout/FAILED').touch()
    Path('fqin/GO').unlink()
    log('QUENCH slot=%d rc=%d' % (slot, r))
    return True


def main():
    os.chdir(D)
    slot = int(sys.argv[1])
    for d in ('claims', 'cancel', 'jobs', 'logs', 'run', 'done'):
        Path(d).mkdir(exist_ok=True)
    log('BEGIN slot=%d base=%s' % (slot, BASE))
    while time.time() < epoch('deadline') - 40 and not Path('STOP').exists():
        if quench_batch(slot):
            continue
        if time.time() >= epoch('search-deadline'):
            time.sleep(5)
            continue
        task = None
        for _, _, p, j in jobs():
            try:
                (Path('claims') / p.stem).mkdir()
            except FileExistsError:
                continue
            task = (p, j)
            break
        if task is None:
            time.sleep(5)
            continue
        p, j = task
        left = epoch('deadline') - time.time() - 30
        secs = min(j['seconds'], left)
        if secs < 20:
            log('SKIP slot=%d k=%d n=%d: %ds left' % (slot, j['k'], j['n'], secs))
            continue
        outdir = 'run/s%d' % j['k']
        Path(outdir).mkdir(parents=True, exist_ok=True)
        cmd = [PY, 'midm_scan.py', '--n', str(j['n']), '--sub', j['sub'], '--out', outdir,
               '--fq', FQ, '--seconds', str(int(secs)), '--seed', str(j['seed']),
               '--modes', 'kick,lkick', '--ref', '0', '--deadline', 'deadline', '--kicks', str(j['sigma']), '--stop6',
               '--bank', 'bank%d.txt' % slot]
        log('START slot=%d %s' % (slot, json.dumps(j, sort_keys=True)))
        begin = time.time()
        with open(outdir + '/worker.log', 'a') as out:
            returncode = run_cancelable(cmd, out, Path('cancel') / p.stem)
        j['elapsed'] = time.time() - begin
        j['returncode'] = returncode
        try:
            if j.get('self_cert') and not j.get('leg', 0) and not (Path(outdir) / 'cert/start.json').exists():
                certify(j['n'], j['sub'], 'start', outdir)
            mine = list(Path(outdir + '/raw').glob('%d-*-%d-*.csv' % (j['n'], j['seed']))) if Path(outdir + '/raw').is_dir() else []
            if mine:
                low = min(mine, key=side_of)
                rec = certify(j['n'], low, low.stem, outdir)
                j['cert'] = dict(raw=low.name, score=rec.get('score'), ok=rec.get('ok'), seconds=rec.get('seconds'))
        except Exception as ex:  # noqa: BLE001
            log('CERT error slot=%d k=%d n=%d %r' % (slot, j['k'], j['n'], ex))
        j['slot_ran'] = slot
        scan = Path(outdir) / ('scan-%d-%d.tsv' % (j['n'], j['seed']))
        end = [l for l in scan.read_text().splitlines() if l.startswith('# END')] if scan.exists() else []
        if end and not (Path('cancel') / p.stem).exists():
            m = re.search(r'finds (\d+) best ([0-9.]+) held ([0-9.]+)', end[-1])
            j['finds'] = int(m[1])
            j['gain'] = (float(m[3]) - float(m[2])) / math.sqrt(j['n'])
            leg = j.get('leg', 0)
            if j['finds'] and j['gain'] >= 1e-6 and time.time() < epoch('search-deadline'):
                raws = list(Path(outdir + '/raw').glob('%d-*-%d-%d.csv' % (j['n'], j['seed'], j['finds'])))
                if raws:
                    new = {k: v for k, v in j.items() if k not in ('gain', 'finds', 'elapsed', 'returncode', 'slot_ran')}
                    new.update(sub=str(raws[0]), seed=j['seed'] + 100, leg=leg + 1,
                               priority=min(j['priority'] + .6, .45), created=time.time())
                    write('jobs/%d-%d-L%d.json' % (j['k'], j['n'], leg + 1), new)
        write('done/' + p.name, j)
        log('END slot=%d k=%d n=%d leg=%d finds=%s gain=%s elapsed=%.1f' % (
            slot, j['k'], j['n'], j.get('leg', 0), j.get('finds'), j.get('gain'), j['elapsed']))
    log('STOP slot=%d' % slot)


if __name__ == '__main__':
    main()
