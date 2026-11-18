#!/usr/bin/env python3
"""Round 32 worker: worker31.py with a 1105 share gate before the legs of a public-first scan.

Round 32 change (midm round 31 next item 2, round 32 override 6c): a job with a "ref" file (the driver ships the
harvested prvsiyan 1105 rows of n that are not our own layout) has the share of its best find measured with the frozen
assembler measure (share31.py from take-assemble-r31/scripts, shipped beside this file: bounding-box centring on
centres and corners, 8 symmetries, median-offset ICP, at 1e-3 and 1e-2). At 0.4 or more at either tolerance the scan
writes no leg and no sibling (round 31: a 972 find read 0.460 and its legs held a slot to a row that could never
publish; at 911 a leg read 0.429 where its root read 0.341).

Round 31 text: worker30.py with a probe, a wider leg rule and sibling seeds (round 31 brief items 6a and 6c).

Round 31 changes (measured on 615 midm scans of rounds 22 to 30 before the change, /tmp/probe_measure.py in STATE.txt):
  - probe: a scan whose finds have not moved the side 1e-8 below its start after PROBE seconds (120) stops (a held
    row re-found at its undilated side, 1.2e-9 lower, is not a find). On the 615 old scans this keeps 88 per cent of
    the side gain in 44 per cent of the slot time (gain per slot second x2.01);
  - a leg follows every scan whose best find moved the side by more than 1e-6 (was: score gain 1e-6), and it runs
    before new first scans (priority 0.03);
  - a scan whose find gained 1e-5 of score or more also gets a sibling leg from the same find with another seed
    (round 30: 412 seeds 103, 777, 877 and 1999 from one find gained 1.6e-7, 7.0e-6, 7e-11 and 0);
  - a probe-stopped scan has no "# END" line: its finds and gain come from its FIND lines.

Round 30 text: worker29.py with the certified-file quench of fqonce30.py (fq rounds, contact LP, polish fq).

Round 29 text: worker27.py with two changes.

Round 29 changes (round 29 brief item 6, measured in round 28):
  - certification on the box is border's finesafe.work (floatsafe with a bisected dilation, tools/border/r28/finesafe.py
    shipped beside this file): border measured 3e-10 to 8e-10 of side lower than the floatsafe ladder on 19 fq outputs;
  - every scan ends 600 s before the deadline (the certified-file quench needs a free slot after the last scan), and a
    job's seconds may be 900 (round 28: 300 s rect scans gained about their margin and were still finding at the cap).

Round 27 text: worker26.py plus certification on the box.

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


PROBE = 120.0
PROBE_EPS = 1e-8   # a held row comes back about 1.2e-9 of side under its certified (dilated) side: not a find


def finds_of(scan):
    """(finds, best side, held side) from the FIND lines and header of a scan file (no END line needed)."""
    held = best = None; finds = 0
    if not Path(scan).exists():
        return 0, None, None
    for line in Path(scan).read_text().splitlines():
        if line.startswith('# n='):
            m = re.search(r'held=([0-9.]+)', line)
            held = float(m[1]) if m else None
        elif line.startswith('# FIND'):
            m = re.search(r' side ([0-9.]+)', line)
            if m:
                finds += 1; best = float(m[1])
    return finds, best, held


def run_cancelable(cmd, out, marker, probe_scan=None, end_by=None):
    child = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
    t0 = time.time(); probed = False
    while child.poll() is None:
        if Path(marker).exists() or Path('STOP').exists() or time.time() >= epoch('deadline') or (end_by and time.time() >= end_by):
            return stop_owned_child(child)
        if probe_scan and not probed and time.time() - t0 >= PROBE:
            probed = True
            _, best, held = finds_of(probe_scan)
            if best is None or held is None or held - best <= PROBE_EPS:
                Path(str(probe_scan) + '.probe-stop').write_text('%.0f\n' % (time.time() - t0))
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
    import finesafe as floatsafe
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


def find_share(j, outdir, finds):
    """Max share (1e-3 and 1e-2) of the scan's best find against every shipped non-own 1105 row of n."""
    import csv
    import numpy as np
    import share31
    raws = list(Path(outdir + '/raw').glob('%d-*-%d-%d.csv' % (j['n'], j['seed'], finds)))
    if not raws:
        return 0.0
    P = np.array([[float(r['x']), float(r['y']), float(r['angle'])] for r in csv.DictReader(open(raws[0]))])
    best = 0.0
    for label, ref in json.loads(Path(j['ref']).read_text()):
        sh = share31.share(P, np.array(ref))
        best = max(best, max(sh.values()))
    return best


def quench_batch(slot):
    if not Path('fqin/GO').exists():
        return False
    try:
        Path('fqin/CLAIM').mkdir()
    except (FileExistsError, FileNotFoundError):
        return False
    with open('logs/quench.log', 'a') as out:
        r = run_cancelable([PY, 'fqonce30.py', 'fqin', 'fqout', FQ, 'x'], out, 'fqin/CANCEL')
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
        left = epoch('deadline') - time.time() - 600
        secs = min(j['seconds'], left)
        if secs < 20:
            log('SKIP slot=%d k=%d n=%d: %ds left' % (slot, j['k'], j['n'], secs))
            continue
        outdir = 'run/s%d' % j['k']
        Path(outdir).mkdir(parents=True, exist_ok=True)
        scan = Path(outdir) / ('scan-%d-%d.tsv' % (j['n'], j['seed']))
        cmd = [PY, 'midm_scan.py', '--n', str(j['n']), '--sub', j['sub'], '--out', outdir,
               '--fq', FQ, '--seconds', str(int(secs)), '--seed', str(j['seed']),
               '--modes', j.get('modes', 'kick,lkick'), '--ref', '0', '--deadline', 'deadline', '--kicks', str(j['sigma']),
               '--bank', 'bank%d.txt' % slot] + (['--stop6'] if not (j.get('donors') or j.get('noprobe')) else []) + (
               ['--donors', j['donors']] if j.get('donors') else [])
        # round 32, 12:00Z: a noprobe job (held-gap2, border's unprobed 900 s kick) runs without --stop6 too; with it the
        # first 16 held-gap2 scans ended in 8 to 25 s (3 of 6 tries back at the start side), border's run the full 900 s
        log('START slot=%d %s' % (slot, json.dumps(j, sort_keys=True)))
        begin = time.time()
        with open(outdir + '/worker.log', 'a') as out:
            returncode = run_cancelable(cmd, out, Path('cancel') / p.stem, probe_scan=scan if not j.get('noprobe') else None,
                                        end_by=epoch('deadline') - 600)
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
        j['probe_stop'] = Path(str(scan) + '.probe-stop').exists()
        if not (Path('cancel') / p.stem).exists():
            finds, best, held = finds_of(scan)
            j['finds'] = finds
            j['side_gain'] = (held - best) if (finds and best is not None and held is not None) else 0.0
            j['gain'] = j['side_gain'] / math.sqrt(j['n'])
            leg = j.get('leg', 0)
            if finds and j.get('ref'):
                try:
                    j['find_share'] = find_share(j, outdir, finds)
                except Exception as ex:  # noqa: BLE001
                    j['find_share'] = 1.0; log('SHARE error slot=%d k=%d n=%d %r' % (slot, j['k'], j['n'], ex))
            if finds and j.get('ref') and j['find_share'] >= 0.4:
                log('SHARE-STOP slot=%d k=%d n=%d: best find 1105 share %.3f, no leg' % (slot, j['k'], j['n'], j['find_share']))
            elif finds and j['side_gain'] > 1e-6 and time.time() < epoch('search-deadline'):
                raws = list(Path(outdir + '/raw').glob('%d-*-%d-%d.csv' % (j['n'], j['seed'], finds)))
                if raws:
                    new = {k: v for k, v in j.items() if k not in ('gain', 'side_gain', 'finds', 'elapsed', 'returncode',
                                                                   'slot_ran', 'probe_stop', 'cert', 'sib')}
                    new.update(sub=str(raws[0]), seed=j['seed'] + 100, leg=leg + 1, priority=0.03, created=time.time())
                    new.pop('donors', None); new.pop('noprobe', None); new.pop('find_share', None)
                    new['modes'] = 'kick,lkick'   # a leg kicks its find (a public-first leg keeps its ref file)
                    write('jobs/%d-%d-L%d.json' % (j['k'], j['n'], leg + 1), new)
                    if j['gain'] >= 1e-5:
                        sib = dict(new, seed=j['seed'] + 7000 + 100 * leg, sib=True, created=time.time() + 1)
                        write('jobs/%d-%d-L%d.json' % (j['k'], j['n'], leg + 51), sib)
        write('done/' + p.name, j)
        log('END slot=%d k=%d n=%d leg=%d finds=%s gain=%s probe_stop=%s elapsed=%.1f' % (
            slot, j['k'], j['n'], j.get('leg', 0), j.get('finds'), j.get('gain'), j.get('probe_stop'), j['elapsed']))
    log('STOP slot=%d' % slot)


if __name__ == '__main__':
    main()
