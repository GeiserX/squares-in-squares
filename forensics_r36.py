#!/usr/bin/env python3
"""Compose rectangle windows of fresh certificates and changed held rows.

The local scanner walks each source and queues rectangle compositions. Two
boxE slots run the full default and polish loop. Winners receive finesafe
certification and another full loop from the certified file before publication.
The wrapper completes walks up to 100000 files and refuses capped results.
"""
import csv, glob, hashlib, json, math, os, queue, re, shutil, subprocess, sys, threading, time
from pathlib import Path

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE))
ROOT = Path('$SCRATCH/bounties-squares')
TAKE = ROOT / 'take-forensics-r36'
WORK = TAKE / 'work'
PY = str(ROOT / 'venv/bin/python')
HELD = ROOT / 'gather/round35-2026-11-17a.csv'
BAR = ROOT / 'round36-briefs/bar36.tsv'
HANDOFF = ROOT / 'handoff-r36.log'
REMOTE = 'boxE'
RDIR = '$SCRATCH/squares-forensics-r36'
RBASE = '$SCRATCH/squares-base'
DEADLINE = 1794959100.0          # 2026-11-17T23:45:00Z: every numerical job ends here
SCAN_STOP = DEADLINE - 600      # no new scans after 23:35Z, so their starts still get the fq slot
GRACE = 0                      # Compose immediately after certificates appear
SCAN_ARGS = ['--slack', '0.004', '--keep', '8', '--per-n', '8', '--max-mesh', '400', '--strict-single',
             '--skip-ties', '--collide', '0.03']
MIN_GAIN = 1.01e-10                 # never publish a move within the polish noise of the bar
REWALK = 1800                    # a refused file is walked again after 30 min (its producer may fix its record)
PICKS = [803,747,860,861,920,693,812,871,546,549,554,594,653,702,746,790,806,807,808,809,864,865,869,925]
NEAR = 1e-5                      # side gap under which an fq output goes to near/ for the 900 s searches


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def state(line):
    with open(TAKE / 'STATE.txt', 'a') as h:
        h.write(f'{now()} boxA {line}\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def geometry_key(squares):
    """Canonical numeric geometry at a scale below material score changes."""
    import numpy as np
    import forensics_rect as rect
    import forensics_compose as fc
    side, q = fc.frame(squares)
    keys = []
    for _, x in rect.sym8(q, side):
        _, x = fc.frame(x)
        x[:, 2] = np.mod(x[:, 2], math.pi / 2)
        x = np.round(x, 10)
        x[:, 2][np.abs(x[:, 2] - round(math.pi / 2, 10)) < 1e-10] = 0
        x[x == 0] = 0
        x = x[np.lexsort((x[:, 2], x[:, 1], x[:, 0]))]
        keys.append(hashlib.sha256(x.tobytes()).hexdigest())
    return min(keys)


def material_fq(n, receipt):
    return receipt['start'] - receipt['end'] > 2e-10 * math.sqrt(n)


def material_source(path):
    """Close polish-only feedback while retaining certificates and peer sources."""
    path = Path(path)
    if path.parent != TAKE / 'near':
        return True
    try:
        record = json.loads(Path(str(path) + '.json').read_text())
    except (OSError, ValueError):
        return True
    receipt = record.get('fq_receipt')
    return not receipt or material_fq(int(record['n']), receipt)


def atomic(path, text):
    path = Path(path)
    if path.name.endswith(('.csv.json', '.csv.source.json', '.csv.origin.json')) and path.exists():
        if path.read_text() != text:
            raise FileExistsError(f'published ancestry sidecar is immutable: {path}')
        return
    tmp = path.with_name(path.name + '.tmp')
    tmp.write_text(text); os.replace(tmp, path)


def bar_scores():
    return {int(r['n']): float(r['bar']) for r in csv.DictReader(open(BAR), delimiter='\t')}


def live_scores(exclude='forensics'):
    """Lowest new score per n over every other lane's take-*-r36/take.tsv."""
    live = {}
    for t in glob.glob(str(ROOT / 'take-*-r36/take.tsv')):
        if f'take-{exclude}-r36' in t:
            continue
        try:
            for r in csv.DictReader(open(t), delimiter='\t'):
                n, s = int(r['n']), float(r['new'])
                if s < live.get(n, (9, ''))[0]:
                    live[n] = (s, t)
        except Exception:
            continue
    return live


def targets():
    """Side to beat per n: the lower of bar36 and every live r36 take, as score and side."""
    bar = bar_scores(); live = live_scores(); own = read_take()
    out = {}
    for n, b in bar.items():
        s = min(b, live.get(n, (9,))[0], float(own.get(n, {}).get('new', 9)))
        out[n] = (s, (s + 1) * math.sqrt(n))
    return out


def write_details(path):
    t = targets()
    with open(str(path) + '.tmp', 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'L', 'score'])
        for n in sorted(t):
            w.writerow([n, repr(t[n][1]), repr(t[n][0])])
    os.replace(str(path) + '.tmp', path)
    return t


def withdrawn_text():
    if not HANDOFF.exists():
        return ''
    return '\n'.join(l for l in HANDOFF.read_text(errors='replace').splitlines() if 'withdraw' in l.lower())


def held_parts(raw_meta):
    """'held n = N of round 35' for each part cut from a held round 35 a row (quench_walk reads that form)."""
    out = []
    for key in ('A', 'B'):
        part = raw_meta.get(key) or {}
        src = part.get('source') or ['', 0]
        name = Path(str(src[0])).name
        if str(src[0]) == str(HELD) or name.startswith('held-'):
            out.append(f'held n = {int(src[1])} of round 35 (gather/round35-2026-11-17a.csv)')
        elif src[0]:
            orig = Path(str(src[0]) + '.json')
            out.append(f'part n = {int(src[1])} from {src[0]}' + (f' (original {json.loads(orig.read_text()).get("original")})' if orig.exists() else ''))
    return '; '.join(out)


_HELD_PICK_ROWS = None

def held_pick_walk(path):
    """Trace a setup export to its submitted held root by exact numeric rows."""
    global _HELD_PICK_ROWS
    if _HELD_PICK_ROWS is None:
        selected = {n: [] for n in PICKS}
        for row in csv.DictReader(open(HELD)):
            n = int(row['n'])
            if n in selected:
                selected[n].append(tuple(float(row[k].lstrip('s')) for k in ('x', 'y', 'angle')))
        _HELD_PICK_ROWS = {n: sorted(rows) for n, rows in selected.items()}
    rows = list(csv.DictReader(open(path)))
    n = int(rows[0]['n'])
    actual = sorted(tuple(float(row[k].lstrip('s')) for k in ('x', 'y', 'angle')) for row in rows)
    good = len(rows) == n and actual == _HELD_PICK_ROWS.get(n)
    return dict(start=str(path), n=n, clean=good, hits=[] if good else ['held byte-root mismatch'],
                files=2, capped=False, cap=100000, helds=[f'{n}@35'] if good else [],
                pubfirst=False, proof='exact numeric row equality to submitted round35 gather file')


def walk(path):
    """quench_walk.py on the original path (absolute), as one JSON object."""
    if Path(path).parent == WORK / 'held-picks':
        return held_pick_walk(path)
    r = subprocess.run([PY, '-I', str(LANE / 'forensics_walk36.py'), str(path)], capture_output=True, text=True, timeout=900)
    lines = [l for l in r.stdout.splitlines() if l.startswith('{')]
    if not lines:
        return dict(start=str(path), clean=False, hits=['walker printed nothing: ' + r.stderr[-300:]])
    return json.loads(lines[-1])


# ---------------------------------------------------------------- remote fq loop (runs on boxE)

def fqloop(inp, out, target, deadline, collide=False, fq=RBASE + '/fq'):
    import numpy as np
    import forensics_rect as rect, forensics_compose as fc, midm_scan as ms
    sq = next(iter(rect.layouts(inp).values()))
    side, q = fc.frame(sq)
    y = np.column_stack([q[:, 0], q[:, 1], np.degrees(q[:, 2])])
    best, besty = side, None
    steps = []
    tmp = out + '-tmp'; os.makedirs(tmp, exist_ok=True)

    def one(s, x, flags):
        left = deadline - time.time()
        if left < 2:
            return None, None
        e, z = ms.quench(fq, tmp, s, x, flags, timeout=max(1, min(600, left)))
        steps.append(dict(flags=list(flags), start=s, end=e))
        return e, z

    # a colliding start (tag c) is not a layout: only fq outputs count
    cur, cury = (float('inf'), y) if collide else (side, y)
    for rnd in range(3):
        before = cur
        for flags in ((), ms.POLISH):
            e, z = one(side if cur == float('inf') else cur, cury, flags)
            if z is not None and e < cur:
                cur, cury = e, z
        if before != float('inf') and before - cur < 1e-12:
            break
    if cur == float('inf'):
        json.dump(dict(start=side, end=None, target=target, steps=steps), open(out + '.json', 'w')); return
    if cur < side or collide:
        fc.write_csv(out + '.tmp', len(sq), ms.from_fq(cury)); os.replace(out + '.tmp', out)
    else:
        fc.write_csv(out + '.tmp', len(sq), q); os.replace(out + '.tmp', out)
    json.dump(dict(start=side, end=cur if collide else min(cur, side), target=target, steps=steps), open(out + '.json', 'w'))


# ---------------------------------------------------------------- certification and publication

def certify(path, n):
    """border's finesafe.py on a per-n csv; returns (score, rows) or (None, reason)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location('border_finesafe', str(ROOT / 'take-border-r28/work/finesafe.py'))
    fine = importlib.util.module_from_spec(spec); spec.loader.exec_module(fine)
    rows = [r for r in csv.DictReader(open(path)) if int(r['n']) == n]
    if len(rows) != n:
        return None, 'count'
    rows = [dict(n=str(n), square_id=r['square_id'], x=r['x'], y=r['y'], angle=r['angle']) for r in rows]
    _, fr, s, e = fine.work((n, rows))
    if fr is None:
        return None, 'finesafe refused'
    return s, fr


def write_rows(path, rows):
    with open(str(path) + '.tmp', 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle']); w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in ['n', 'square_id', 'x', 'y', 'angle']})
    os.replace(str(path) + '.tmp', path)


TAKE_LOCK = threading.Lock()


def read_take():
    p = TAKE / 'take.tsv'
    return {int(r['n']): r for r in csv.DictReader(open(p), delimiter='\t')} if p.exists() else {}


def write_take(rows):
    p = TAKE / 'take.tsv'
    with open(str(p) + '.tmp', 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t')
        w.writeheader()
        for n in sorted(rows):
            w.writerow(rows[n])
    os.replace(str(p) + '.tmp', p)


def publish(n, cert_csv, score, record):
    bar = bar_scores()[n]
    with TAKE_LOCK:
        rows = read_take()
        if n in rows and float(rows[n]['new']) <= score:
            state(f'KEEP n={n} published {rows[n]["new"]} <= new {score}')
            return False
        if (TAKE / f'{n}.csv.json').exists():
            olddir = WORK / 'superseded' / sha(TAKE / f'{n}.csv')
            olddir.mkdir(parents=True, exist_ok=True)
            for suffix in ('.csv', '.csv.json'):
                os.replace(TAKE / f'{n}{suffix}', olddir / f'{n}{suffix}')
            with open(HANDOFF, 'a') as h:
                h.write(f'{now()} forensics -> all: superseded n={n} previous bytes and unchanged sidecar retained in {olddir}\n')
        shutil.copyfile(cert_csv, TAKE / f'{n}.csv.tmp'); os.replace(TAKE / f'{n}.csv.tmp', TAKE / f'{n}.csv')
        record = dict(record, take_sha256=sha(TAKE / f'{n}.csv'))
        atomic(TAKE / f'{n}.csv.json', json.dumps(record, indent=1))
        src = record['source']
        rows[n] = dict(n=n, held=repr(bar), new=repr(score), gain=repr(bar - score),
                       source=f"forensics r36 rectangle windows of {src['original']} (n={src['n']}, snapshot "
                              f"{src['snapshot']} sha256 {src['sha256']}) with held round35-2026-11-17a parts; "
                              f"parts: {record.get('parts', '')}; quench_walk clean; fq full loop; finesafe 2.2e-11; full fq loop from the certified file. "
                              f"Record {TAKE}/{n}.csv.json",
                       licence='own composition on held round35 rows and walked round36 files; input notice: ' + src.get('licence', 'own held construction'))
        write_take(rows)
    with open(HANDOFF, 'a') as h:
        h.write(f"{now()} forensics -> all: certified n={n} score {score!r} ({bar - score:.3e} below bar36), "
                f"rectangle windows of fresh {src['original']}, walk files={record['walk_at_publish']['files']} capped={record['walk_at_publish']['capped']}, {TAKE}/{n}.csv\n")
    state(f'PUBLISH n={n} score={score!r} gain={bar - score:.3e} source={src["original"]}')
    return True


# ---------------------------------------------------------------- the driver

def ssh(cmd, timeout=900):
    return subprocess.run(['ssh', '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=30', REMOTE, cmd],
                          capture_output=True, text=True, timeout=timeout)


def remote_fq(local_in, target_side, tag, collide=False):
    """Copy a start to boxE, run the full fq loop there, copy the result back; returns (csv, receipt)."""
    while time.time() < DEADLINE - 60:
        guard = ssh("sysctl -n vm.loadavg", timeout=30)
        try:
            load = float(guard.stdout.strip().strip('{} ').split()[0])
        except (ValueError, IndexError):
            load = 99.0
        if load < 16:
            break
        state(f'BOXE-LOAD {load:.2f}, waiting before {tag}')
        time.sleep(20)
    rin = f'{RDIR}/jobs/{tag}.csv'; rout = f'{RDIR}/jobs/{tag}-out.csv'
    subprocess.run(['scp', '-q', str(local_in), f'{REMOTE}:{rin}'], check=True, timeout=120)
    left = DEADLINE - time.time()
    if left < 30:
        return None, None
    r = ssh(f'cd {RDIR}/code && OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 nice -n 5 {RBASE}/venv/bin/python -I '
            f'{RDIR}/code/forensics_r36.py fqloop {rin} {rout} {target_side!r} {DEADLINE!r} {int(collide)}', timeout=left + 60)
    if r.returncode != 0:
        state(f'FQ-ERROR {tag} rc={r.returncode} {r.stderr[-300:]!r}')
        return None, None
    local_out = WORK / 'fq' / f'{tag}-out.csv'
    local_out.parent.mkdir(exist_ok=True)
    subprocess.run(['scp', '-q', f'{REMOTE}:{rout}.json', str(local_out.parent)], check=True, timeout=120)
    if json.loads(Path(str(local_out) + '.json').read_text())['end'] is None:
        ssh(f'rm -f {rin} {rout}.json', timeout=60)
        return None, None
    subprocess.run(['scp', '-q', f'{REMOTE}:{rout}', str(local_out.parent)], check=True, timeout=120)
    ssh(f'rm -f {rin} {rout} {rout}.json', timeout=60)
    return local_out, json.loads(Path(str(local_out) + '.json').read_text())


class Driver:
    def __init__(self):
        import forensics_rect as rect
        self.seen = json.loads((WORK / 'seen.json').read_text()) if (WORK / 'seen.json').exists() else {}
        self.jobs = queue.PriorityQueue()
        self.scan_no = len(list(WORK.glob('scan-*')))
        self.lock = threading.Lock()
        self.active = set()
        self.geometry_jobs = set()
        self.geometry_sources = set()
        cache = WORK / 'windows36.pkl'
        if cache.exists():
            import pickle
            for key, side, q in pickle.load(open(cache, 'rb'))['src']:
                self.geometry_sources.add((key[1], geometry_key(q)))
        done_file = WORK / 'done.json'
        if done_file.exists():
            for name in json.loads(done_file.read_text()):
                if Path(name).exists():
                    for n, q in rect.layouts(name).items():
                        self.geometry_jobs.add((n, geometry_key(q)))

    def save_seen(self):
        with self.lock:
            atomic(WORK / 'seen.json', json.dumps(self.seen, indent=0))

    def fresh_files(self):
        out = []
        for pat in ('take-*-r36/*.csv', 'take-*-r36/near/*.csv', 'take-forensics-r36/work/held-picks/*.csv'):
            for p in glob.glob(str(ROOT / pat)):
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                if time.time() - st.st_mtime < GRACE:
                    continue
                key = f'{p}|{st.st_size}|{st.st_mtime_ns}'
                mark = self.seen.get(key)
                if mark is None and not material_source(p):
                    self.seen[key] = 'closed-polish-feedback'
                    state(f'QUEUE-CLOSED polish-only source {p}')
                    self.save_seen()
                    continue
                if mark is not None and not (mark.startswith('refused@') and time.time() - int(mark[8:]) > REWALK):
                    continue
                out.append(((-100 + PICKS.index(int(Path(p).stem))) if 'held-picks' in p else (-200 if '/near/' not in p else 1), -st.st_mtime, p, key))
        return sorted(out)

    def admit(self, p, key):
        """Snapshot, walk and scan one fresh file; queue its starts."""
        try:
            data = Path(p).read_bytes()
        except OSError:
            return
        digest = hashlib.sha256(data).hexdigest()
        if digest in self.seen.values():
            self.seen[key] = digest; self.save_seen(); return
        import forensics_rect as rect
        snap_dir = WORK / 'feed' / Path(p).parts[-2 if '/near/' not in p else -3]
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap = snap_dir / f'{Path(p).stem}-{digest[:24]}.csv'
        snap.write_bytes(data)
        atomic(str(snap) + '.json', json.dumps(dict(original=p, sha256=digest, note='forensics r36 byte snapshot of the original file')))
        lay = rect.layouts(snap)
        if len(lay) != 1:
            state(f'SKIP {p} layouts={sorted(lay)[:5]} (not one per-n layout)')
            self.seen[key] = digest; self.save_seen(); return
        n0 = next(iter(lay))
        gkey = (n0, geometry_key(lay[n0]))
        if gkey in self.geometry_sources:
            state(f'GEOMETRY-DUP source n={n0} {p}')
            self.seen[key] = digest; self.save_seen(); return
        t0 = time.time(); w = walk(p)
        (WORK / 'walks').mkdir(exist_ok=True)
        atomic(WORK / 'walks' / f'{digest}.json', json.dumps(dict(w, original=p, snapshot=str(snap)), indent=0))
        if sha(p) != digest:
            state(f'SKIP {p} changed during its walk'); return
        if not w.get('clean') or w.get('capped', True):
            state(f'REFUSE n={n0} {p} clean={w.get("clean")} pubfirst={w.get("pubfirst")} hits={str(w.get("hits"))[:300]}')
            self.seen[key] = f'refused@{int(time.time())}'; self.save_seen(); return
        licence = 'own held or constructed packing'
        if w.get('pubfirst'):
            records = []
            for suffix in ('.json', '.origin.json', '.source.json'):
                sidecar = Path(p + suffix)
                if sidecar.exists():
                    records.append(json.loads(sidecar.read_text()))
            table = Path(p).parent / 'take.tsv'
            if table.exists():
                records.extend(r for r in csv.DictReader(open(table), delimiter='\t') if int(r['n']) == n0)
            notices = [str(r.get('licence', r.get('license', ''))) for r in records if isinstance(r, dict)]
            allowed = [v for v in notices if any(t in re.sub('[^a-z0-9]', '', v.lower()) for t in ('apache20', 'ccby40', 'cc0'))]
            if not allowed:
                state(f'REFUSE-PUBLIC-LICENCE n={n0} {p} notices={notices!r}')
                self.seen[key] = digest; self.save_seen(); return
            licence = '; '.join(allowed)
        atomic(str(snap) + '.source.json', json.dumps(dict(n=n0, original=p, licence=licence, records=records if w.get('pubfirst') else [])))
        if time.time() > SCAN_STOP:
            return
        self.scan_no += 1
        sd = WORK / f'scan-{self.scan_no:03d}'; sd.mkdir()
        write_details(sd / 'details.csv')
        cmd = [PY, '-I', str(LANE / 'forensics_rect.py'), str(sd / 'details.csv'), str(sd / 'raw'),
               '--cache', str(WORK / 'windows36.pkl')] + SCAN_ARGS + ['--fresh-only', str(snap)]
        with open(sd / 'rect.log', 'w') as log:
            r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=1200)
        tail = (sd / 'rect.log').read_text().strip().splitlines()[-1:] or ['']
        state(f'SCAN {self.scan_no} n0={n0} walk={time.time() - t0:.0f}s rc={r.returncode} file={p} :: {tail[0][:200]}')
        self.seen[key] = digest; self.save_seen()
        self.geometry_sources.add(gkey)
        tg = targets()
        for c in sorted((sd / 'raw').glob('*.csv')):
            n = int(c.name.split('-')[0])
            try:
                side, _ = __import__('forensics_compose').frame(next(iter(rect.layouts(c).values())))
            except Exception as error:
                state(f'SKIP raw {c} {error!r}'); continue
            margin = side - tg[n][1]
            self.jobs.put((margin, str(c), n, dict(original=p, snapshot=str(snap), sha256=digest, n=n0, licence=licence,
                                                    start_walk_clean=True, start_walk_files=w['files'], start_walk_capped=w['capped'])))  # never a path: the walker reads a report's held-chain notes as gone ancestors
            state(f'QUEUE n={n} margin={margin:.3e} {c.name}')

    def inbox(self):
        """Starts of side scans (work/inbox/*.json: list of [margin, raw csv, n, source record])."""
        for f in sorted((WORK / 'inbox').glob('*.json')):
            for margin, c, n, src in json.loads(f.read_text()):
                self.jobs.put((margin, c, n, src)); state(f'QUEUE n={n} margin={margin:.3e} {Path(c).name} (inbox {f.name})')
            os.replace(f, f.with_suffix('.done'))

    def scanner(self):
        (WORK / 'inbox').mkdir(exist_ok=True)
        while time.time() < SCAN_STOP:
            self.inbox()
            for _, _, p, key in self.fresh_files()[:1]:
                if time.time() > SCAN_STOP:
                    break
                try:
                    self.admit(p, key)
                except Exception as error:
                    state(f'ADMIT-ERROR {p} {error!r}')
                    self.seen[key] = 'error'; self.save_seen()
            time.sleep(2 if self.fresh_files() else 20)
        state('scanner stopped at SCAN_STOP')

    def requeue(self):
        """After a restart: queue the unrun starts of earlier scans that sit within 1e-3 side of the live bar."""
        import re, forensics_rect as rect, forensics_compose as fc
        done = set(json.loads((WORK / 'done.json').read_text())) if (WORK / 'done.json').exists() else set()
        text = (TAKE / 'STATE.txt').read_text()
        scans = {int(m.group(1)): (int(m.group(2)), m.group(3)) for m in re.finditer(r' SCAN (\d+) n0=(\d+) .*?file=(\S+) ', text)}
        walks = {}
        for w in WORK.glob('walks/*.json'):
            d = json.loads(w.read_text()); walks[d['original']] = (w.stem, d, str(w))
        tg = targets(); seen = set(); k = 0
        for sd in sorted(WORK.glob('scan-*')):
            no = int(sd.name[5:])
            if no not in scans or scans[no][1] not in walks:
                continue
            n0, orig = scans[no]; dg, wd, wp = walks[orig]
            for c in sd.glob('raw/*.csv'):
                if str(c) in done:
                    continue
                n = int(c.name.split('-')[0])
                side, _ = fc.frame(next(iter(rect.layouts(c).values())))
                if side - tg[n][1] < 1e-3 and (n, round(side, 9)) not in seen:
                    seen.add((n, round(side, 9))); k += 1
                    self.jobs.put((side - tg[n][1], str(c), n, dict(original=orig, snapshot=wd['snapshot'], sha256=dg, n=n0, start_walk_clean=True, start_walk_files=wd['files'], start_walk_capped=wd['capped'])))
        state(f'REQUEUE {k} unrun starts within 1e-3 side')

    def runner(self):
        import forensics_rect as rect
        (WORK / 'fq').mkdir(exist_ok=True)
        k = 0
        done = set(json.loads((WORK / 'done.json').read_text())) if (WORK / 'done.json').exists() else set()
        while time.time() < DEADLINE - 60:
            try:
                margin, c, n, src = self.jobs.get(timeout=20)
            except queue.Empty:
                continue
            tg = targets()
            if margin > 0.004 * 2 or c in done:
                continue
            if not material_source(src.get('original', '')):
                done.add(c)
                state(f'QUEUE-CLOSED polish-only feedback job n={n} {c}')
                continue
            with self.lock:
                if c in self.active:
                    continue
                gkey = (n, geometry_key(next(iter(rect.layouts(c).values()))))
                if gkey in self.geometry_jobs:
                    state(f'GEOMETRY-DUP job n={n} {c}')
                    continue
                self.active.add(c)
                self.geometry_jobs.add(gkey)
            k += 1; tag = f'{n}-{threading.current_thread().name}-{time.time_ns()}'
            try:
                out, rec = remote_fq(c, tg[n][1], tag, collide=Path(c).name.split('-')[1].startswith('c'))
            except Exception as error:
                state(f'FQ-ERROR {tag} {error!r}')
                with self.lock:
                    self.active.discard(c)
                    self.geometry_jobs.discard(gkey)
                self.jobs.put((margin, c, n, src)); time.sleep(10); continue
            if out is None:
                with self.lock:
                    self.active.discard(c)
                continue
            done.add(c)
            with self.lock:
                all_done = set(json.loads((WORK / 'done.json').read_text())) if (WORK / 'done.json').exists() else set()
                all_done.add(c); atomic(WORK / 'done.json', json.dumps(sorted(all_done)))
            end = rec['end']; gap = end - tg[n][1]
            state(f'FQ {tag} n={n} start={rec["start"]!r} end={end!r} side-gap={gap:.3e} steps={len(rec["steps"])} raw={Path(c).name}')
            if gap > -MIN_GAIN * math.sqrt(n):
                if 0 < gap < NEAR:
                    self.near(n, out, rec, c, src, tag, gap)
                continue
            try:
                self.finish(n, out, rec, c, src, tag)
            except Exception as error:
                state(f'FINISH-ERROR {tag} {error!r}')

    def near(self, n, out, rec, raw, src, tag, gap):
        """A near miss for the fresh 900 s searches (invent reads forensics near files)."""
        if not material_fq(n, rec):
            state(f'QUEUE-CLOSED polish-only endpoint n={n}, score_move={(rec["start"] - rec["end"]) / math.sqrt(n):.3e}')
            return
        d = TAKE / 'near'; d.mkdir(exist_ok=True)
        for old in d.glob(f'{n}-rect36-*.csv.json'):
            if abs(json.loads(old.read_text())['side'] - rec['end']) < 1e-10:
                state(f'NEAR-DUP n={n} side {rec["end"]!r} as {old.name}'); return
        dst = d / f'{n}-rect36-{tag}.csv'
        shutil.copyfile(out, str(dst) + '.tmp'); os.replace(str(dst) + '.tmp', dst)
        meta = json.loads(Path(raw + '.json').read_text()) if Path(raw + '.json').exists() else {}
        atomic(str(dst) + '.json', json.dumps(dict(n=n, side=rec['end'], side_gap_to_live_bar=gap, raw=raw, source=src,
                                                   parts=held_parts(meta), raw_meta=meta,
                                                   fq_receipt=rec, note='fq full loop output, not certified'), indent=1))
        with open(HANDOFF, 'a') as h:
            h.write(f"{now()} forensics -> invent,all: near n={n} side {rec['end']!r} ({gap:+.3e} side over the live bar), "
                    f"fresh rectangle windows, source walked, {dst}\n")
        state(f'NEAR n={n} gap={gap:+.3e} {dst}')

    def finish(self, n, out, rec, raw, src, tag):
        score, rows = certify(out, n)
        tg = targets()
        if score is None or score > tg[n][0] - MIN_GAIN:
            state(f'CERT-FAIL {tag} n={n} score={score} target={tg[n][0]!r} {rows if score is None else ""}')
            return
        cert = WORK / 'certified' / f'{tag}-cert1.csv'; cert.parent.mkdir(exist_ok=True)
        write_rows(cert, rows)
        out2, rec2 = remote_fq(cert, tg[n][1], tag + 'b')
        if out2 is None:
            state(f'NO-REQUENCH {tag} (not published)'); return
        best, best_rows, receipts = score, rows, [rec]
        if out2 is not None:
            receipts.append(rec2)
            s2, r2 = certify(out2, n)
            state(f'REQUENCH {tag} cert1={score!r} loop-end={rec2["end"]!r} cert2={s2!r}')
            if s2 is not None and s2 < best:
                best, best_rows = s2, r2
        cert2 = WORK / 'certified' / f'{tag}-final.csv'
        write_rows(cert2, best_rows)
        tg = targets()
        if best > tg[n][0] - MIN_GAIN:
            state(f'LATE {tag} n={n} best={best!r} live target now {tg[n][0]!r}')
            return
        raw_meta = json.loads(Path(raw + '.json').read_text()) if Path(raw + '.json').exists() else {}
        record = dict(n=n, score=best, parts=held_parts(raw_meta), bar36=bar_scores()[n], source=src, raw=raw, raw_meta=raw_meta,
                      fq_receipts=receipts, cert_first=str(cert), certified=str(cert2),
                      certifier='take-border-r28/work/finesafe.py (2.2e-11, metric direct and pandas)')
        atomic(str(cert2) + '.json', json.dumps(record, indent=1))
        # the walk the assembler runs: on the certified file itself, through its record (held parts, source file)
        w = walk(cert2)
        if not w.get('clean') or w.get('capped', True) or w.get('pubfirst'):
            state(f'REFUSE-AT-PUBLISH n={n} walk of {cert2.name}: pubfirst={w.get("pubfirst")} {str(w.get("hits"))[:300]}')
            return
        publish(n, cert2, best, dict(record, walk_at_publish=dict(clean=w.get('clean'), hits=w.get('hits'), pubfirst=w.get('pubfirst'), helds=w.get('helds'), files=w.get('files'), capped=w.get('capped'))))


def seed_cache():
    """Window table from the held round 35 a rows only (our own submitted layouts)."""
    d = WORK / 'seed'; d.mkdir(exist_ok=True)
    write_details(d / 'details.csv')
    cmd = [PY, '-I', str(LANE / 'forensics_rect.py'), str(d / 'details.csv'), str(d / 'raw'), '--cache',
           str(WORK / 'windows36.pkl'), '--keep', '8', '--only', '2', '--max-mesh', '0', str(HELD), '--exclude-source-n', ','.join(map(str, PICKS))]
    with open(d / 'rect.log', 'w') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)


def finalize():
    """Keep a row only when it is below every live r36 take and its source is not withdrawn."""
    with TAKE_LOCK:
        rows = read_take(); live = live_scores(); wd = withdrawn_text()
        keep = {}
        for n, r in rows.items():
            rec = json.loads((TAKE / f'{n}.csv.json').read_text())
            orig = rec['source']['original']
            if n in live and live[n][0] <= float(r['new']):
                state(f'FINAL drop n={n}: live {live[n][1]} {live[n][0]!r} <= ours {r["new"]}'); continue
            w = walk(TAKE / f'{n}.csv')
            atomic(WORK / 'walks' / f'final-{n}.json', json.dumps(w))
            if not w.get('clean') or w.get('capped', True) or w.get('pubfirst'):
                state(f"FINAL drop n={n}: clean={w.get('clean')} capped={w.get('capped')} hits={w.get('hits')}")
                continue
            keep[n] = r
        for n in set(rows) - set(keep):
            for suffix in ('.csv', '.csv.json'):
                f = TAKE / f'{n}{suffix}'
                if f.exists():
                    (WORK / 'dropped').mkdir(exist_ok=True); os.replace(f, WORK / 'dropped' / f.name)
        write_take(keep)
        state(f'FINAL take rows={sorted(keep)}')


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'fqloop':
        fqloop(sys.argv[2], sys.argv[3], float(sys.argv[4]), float(sys.argv[5]), len(sys.argv) > 6 and sys.argv[6] == '1')
    elif cmd == 'seed':
        seed_cache()
    elif cmd == 'finalize':
        finalize()
    elif cmd == 'driver':
        if not (WORK / 'windows36.pkl').exists():
            seed_cache(); state('SEED window table from held round35-2026-11-17a')
        dr = Driver()
        dr.requeue()
        ts = [threading.Thread(target=dr.scanner, daemon=True), threading.Thread(target=dr.runner, name='fq0', daemon=True), threading.Thread(target=dr.runner, name='fq1', daemon=True)]
        for t in ts:
            t.start()
        while time.time() < DEADLINE and any(t.is_alive() for t in ts):
            time.sleep(10)
        state('driver stopped at deadline')
