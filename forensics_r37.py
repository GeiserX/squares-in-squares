#!/usr/bin/env python3
"""Compose rectangle windows of fresh certificates and changed held rows.

The local scanner walks each source and queues rectangle compositions. Two
boxE slots run the full default and polish loop. Winners receive finesafe
certification and another full loop from the certified file before publication.
The wrapper completes walks up to 100000 files and refuses capped results.
"""
import csv, glob, hashlib, json, math, os, queue, re, shutil, subprocess, sys, threading, time
from pathlib import Path

csv.field_size_limit(1 << 30)
sys.dont_write_bytecode = True

LANE = Path(__file__).resolve().parent
sys.path.insert(0, str(LANE))
ROOT = Path('$SCRATCH/bounties-squares')
TAKE = ROOT / 'take-forensics-r37'
WORK = TAKE / 'work'
PY = str(ROOT / 'venv/bin/python')
HELD = ROOT / 'gather/round36-2026-11-18b.csv'
BAR = ROOT / 'round37-briefs/bar37.tsv'
HANDOFF = ROOT / 'handoff-r37.log'
REMOTE = 'boxE'
RDIR = '$SCRATCH/squares-forensics-r37'
RBASE = '$SCRATCH/squares-base'
DEADLINE = 1794984300.0          # 2026-11-18T06:45:00Z: every numerical job ends here
SCAN_STOP = DEADLINE - 600      # no new scans after 06:35Z, so their starts still get the fq slot
GRACE = 0                      # Compose immediately after certificates appear
SCAN_ARGS = ['--slack', '0.004', '--keep', '8', '--per-n', '8', '--max-mesh', '400', '--strict-single',
             '--skip-ties', '--collide', '0.03']
MIN_GAIN = 1.01e-10                 # never publish a move within the polish noise of the bar
REWALK = 1800                    # a refused file is walked again after 30 min (its producer may fix its record)
PICKS = [539,597,692,698,793,812,911,972,976]
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


def stop_for_live(start_side, bar_side, live_side):
    return live_side < min(start_side, bar_side) - 1e-6


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


def approved_notices(licence):
    normalized = re.sub('[^a-z0-9]', '', str(licence).lower())
    return [label for token, label in (('apache20', 'Apache 2.0'), ('ccby40', 'CC BY 4.0'),
                                       ('cc0', 'CC0')) if token in normalized]


def source_notice(licence):
    return '; '.join(approved_notices(licence)) or 'own held or constructed packing'


def clean_notice_fields(value):
    if isinstance(value, dict):
        return {key: source_notice(item) if key in ('licence', 'license') else clean_notice_fields(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [clean_notice_fields(item) for item in value]
    return value


def walk_accepted(result, licence=''):
    if not result.get('clean') or result.get('capped', True):
        return False
    if not result.get('pubfirst'):
        return True
    return bool(approved_notices(licence))


def live_scores(exclude='forensics'):
    """Lowest new score per n over every other lane's take-*-r37/take.tsv."""
    live = {}
    for t in glob.glob(str(ROOT / 'take-*-r37/take.tsv')):
        if f'take-{exclude}-r37' in t:
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
    """Side to beat per n: the lower of bar37 and every live r37 take, as score and side."""
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
    """'held n = N of round 36' for each part cut from a held round 36 a row (quench_walk reads that form)."""
    out = []
    for key in ('A', 'B'):
        part = raw_meta.get(key) or {}
        src = part.get('source') or ['', 0]
        name = Path(str(src[0])).name
        if str(src[0]) == str(HELD) or name.startswith('held-'):
            out.append(f'held n = {int(src[1])} of round 36 (gather/round36-2026-11-18b.csv)')
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
                files=2, capped=False, cap=100000, helds=[f'{n}@36'] if good else [],
                pubfirst=False, proof='exact numeric row equality to submitted round36 gather file')


def walk(path, defer_to_fresh=False):
    """quench_walk.py on the original path (absolute), as one JSON object."""
    if Path(path).parent == WORK / 'held-picks':
        return held_pick_walk(path)
    started = time.time()
    process = subprocess.Popen([PY, '-I', str(LANE / 'forensics_walk37.py'), str(path)],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    while True:
        try:
            output, errors = process.communicate(timeout=3)
            break
        except subprocess.TimeoutExpired:
            fresh = defer_to_fresh and any(Path(candidate).stat().st_mtime > started
                                          for candidate in glob.glob(str(ROOT / 'take-*-r37/*.csv'))
                                          if Path(candidate).exists())
            if fresh or time.time() - started > 900:
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                return dict(start=str(path), clean=False, capped=False, files=0,
                            deferred=bool(fresh), hits=['walk deferred for a fresh certificate' if fresh else 'walk timeout'])
    lines = [l for l in output.splitlines() if l.startswith('{')]
    if not lines:
        return dict(start=str(path), clean=False, hits=['walker printed nothing: ' + errors[-300:]])
    return json.loads(lines[-1])


# ---------------------------------------------------------------- remote fq loop (runs on boxE)

def fqloop(inp, out, target, deadline, collide=False, fq=RBASE + '/fq'):
    import numpy as np
    import forensics_rect as rect, forensics_compose as fc, midm_scan as ms
    deadline_file = Path(__file__).resolve().parents[1] / 'deadline.txt'
    if deadline_file.exists():
        deadline = min(deadline, float(deadline_file.read_text().strip()))
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
        import forensics_watch34 as source_notices
        notices = source_notices.gather_notices(record.get('raw_meta', {}))
        credits = [f"held n={notice['n']} {Path(notice['ledger']).relative_to(LANE)}" for notice in notices]
        original_path = Path(record['source']['original'])
        producer_table = original_path.parent / 'take.tsv'
        if producer_table.exists() and original_path.parent != TAKE:
            credits.append(f"source n={record['source']['n']} {producer_table}")
        record = dict(record, take_sha256=sha(TAKE / f'{n}.csv'), input_credit_tables=credits)
        atomic(TAKE / f'{n}.csv.json', json.dumps(record, indent=1))
        src = record['source']
        method = record.get('method', 'rectangle windows')
        rows[n] = dict(n=n, held=repr(bar), new=repr(score), gain=repr(bar - score),
                       source=f"forensics r37 {method} of {src['original']} ("
                              f"{'pool target' if src['original'] == str(HELD) else 'source n'}={src['n']}, snapshot "
                              f"{src['snapshot']} sha256 {src['sha256']}); "
                              f"parts: {record.get('parts', '')}; quench_walk clean; fq full loop; finesafe 2.2e-11; full fq loop from the certified file. "
                              f"Input credits: {'; '.join(credits) or 'source record and its producer per-count table'}. "
                              f"Record {TAKE}/{n}.csv.json",
                       licence='derived packing; input notice: ' + src.get('licence', 'own held construction'))
        write_take(rows)
    with open(HANDOFF, 'a') as h:
        h.write(f"{now()} forensics -> all: certified n={n} score {score!r} ({bar - score:.3e} below bar37), "
                f"{method} of fresh {src['original']}, walk files={record['walk_at_publish']['files']} capped={record['walk_at_publish']['capped']}, {TAKE}/{n}.csv\n")
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
            f'{RDIR}/code/forensics_r37.py fqloop {rin} {rout} {target_side!r} {DEADLINE!r} {int(collide)}', timeout=left + 60)
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


def fresh_kick(inp, out, count, seconds, seed, target, deadline):
    import forensics_rect as rectangles
    import forensics_compose as composer
    folder = Path(out + '-kick')
    folder.mkdir(exist_ok=True)
    command = [sys.executable, '-I', str(LANE / 'midm_scan.py'), '--n', str(count),
               '--sub', inp, '--out', str(folder), '--fq', RBASE + '/fq',
               '--seconds', str(seconds), '--seed', str(seed), '--modes',
               'lkick' if seconds == 180 else 'lkick,kick', '--deadline',
               str(Path(__file__).resolve().parents[1] / 'deadline.txt'), '--ref', str(target)]
    started = time.time()
    with (folder / 'kick.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                timeout=max(1, min(seconds + 60, deadline - time.time())))
    candidates = [Path(inp)] + list((folder / 'raw').glob('*.csv'))
    best = min(candidates, key=lambda candidate: composer.frame(next(iter(rectangles.layouts(candidate).values())))[0])
    initial = composer.frame(next(iter(rectangles.layouts(inp).values())))[0]
    fqloop(str(best), out, target, deadline)
    receipt_path = Path(out + '.json')
    receipt = json.loads(receipt_path.read_text())
    receipt.update(fq_start=receipt['start'], start=initial,
                   kick=dict(seconds=seconds, elapsed=time.time() - started, seed=seed,
                             returncode=result.returncode, candidates=len(candidates)))
    receipt_path.write_text(json.dumps(receipt))


def remote_kick(local_in, target_side, tag, count, seconds, seed):
    remote_input = f'{RDIR}/jobs/{tag}.csv'
    remote_output = f'{RDIR}/jobs/{tag}-out.csv'
    subprocess.run(['scp', '-q', str(local_in), f'{REMOTE}:{remote_input}'], check=True, timeout=120)
    left = DEADLINE - time.time()
    if left < seconds + 60:
        return None, None
    command = f'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 nice -n 5 {RBASE}/venv/bin/python -I '
    command += f'{RDIR}/code/forensics_r37.py freshkick {remote_input} {remote_output} '
    command += f'{count} {seconds} {seed} {target_side!r} {DEADLINE!r}'
    process = subprocess.Popen(['ssh', '-o', 'ConnectTimeout=20', '-o', 'ServerAliveInterval=30',
                                REMOTE, command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    initial_bar = (bar_scores()[count] + 1) * math.sqrt(count)
    while True:
        try:
            _, errors = process.communicate(timeout=10)
            break
        except subprocess.TimeoutExpired:
            live = targets()[count][1]
            if stop_for_live(target_side, initial_bar, live) or time.time() >= DEADLINE:
                status = ssh('ps -axo pid,command', timeout=30)
                owned = [line.split()[0] for line in status.stdout.splitlines()
                         if f'{RDIR}/jobs/{tag}' in line and line.split()[0].isdigit()]
                if owned:
                    ssh('kill -TERM ' + ' '.join(owned), timeout=30)
                process.terminate()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                state(f'STOP-PEER fresh follow n={count} seconds={seconds} '
                      f'start={target_side!r} live={live!r}; own remote processes stopped={len(owned)}')
                return None, None
    if process.returncode:
        raise RuntimeError(errors[-500:])
    local_output = WORK / 'fq' / f'{tag}-out.csv'
    subprocess.run(['scp', '-q', f'{REMOTE}:{remote_output}', f'{REMOTE}:{remote_output}.json',
                    str(local_output.parent)], check=True, timeout=120)
    ssh(f'rm -f {remote_input} {remote_output} {remote_output}.json', timeout=60)
    return local_output, json.loads(Path(str(local_output) + '.json').read_text())


def save_finish(count, output, receipt, raw, source, tag):
    folder = WORK / 'pending-finishes'
    folder.mkdir(exist_ok=True)
    path = folder / f'{tag}.json'
    atomic(path, json.dumps(dict(n=count, out=str(output), rec=receipt,
                                raw=str(raw), src=source, tag=tag)))
    return path


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
        cache = WORK / 'windows37.pkl'
        if cache.exists():
            import pickle
            for key, side, q in pickle.load(open(cache, 'rb'))['src']:
                
                if str(key[0]) != str(HELD):
                    self.geometry_sources.add((key[1], geometry_key(q)))
        done_file = WORK / 'done.json'
        completed = set(json.loads(done_file.read_text())) if done_file.exists() else set()
        if done_file.exists():
            for name in completed:
                if Path(name).exists():
                    for n, q in rect.layouts(name).items():
                        kind = f'fresh-{Path(name).stem.rsplit("-", 1)[-1]}' if Path(name).parent.name == 'follow-starts' else 'compose'
                        self.geometry_jobs.add((n, geometry_key(q), kind))
        claims_file = WORK / 'follow-claims.json'
        if claims_file.exists():
            for claim, entry in json.loads(claims_file.read_text()).items():
                path = entry['path']
                if path in completed or not Path(path).exists():
                    continue
                metadata = json.loads(Path(path + '.json').read_text())
                seconds = int(claim.rsplit('-', 1)[-1])
                src = dict(metadata['source'], job_kind=f'fresh-{seconds}', follow_seconds=seconds, seed=entry['seed'])
                self.jobs.put((-1000 if seconds == 180 else -999, path, int(metadata['n']), src))
        for inbox_file in sorted((WORK / 'inbox').glob('*.done')):
            for margin, candidate, count, source in json.loads(inbox_file.read_text()):
                if candidate not in completed and Path(candidate).exists():
                    self.jobs.put((margin, candidate, count, source))
        for pending in sorted((WORK / 'pending-finishes').glob('*.json')):
            record = json.loads(pending.read_text())
            if Path(record['out']).is_file() and Path(record['raw']).is_file():
                source = dict(record['src'], resume_finish=str(pending))
                self.jobs.put((-1002, record['raw'], record['n'], source))

    def save_seen(self):
        with self.lock:
            atomic(WORK / 'seen.json', json.dumps(self.seen, indent=0))

    def follow(self, path, count, src, seconds):
        with self.lock:
            return self.follow_locked(path, count, src, seconds)

    def follow_locked(self, path, count, src, seconds):
        import forensics_rect as rectangles
        import forensics_compose as composer
        squares = next(iter(rectangles.layouts(path).values()))
        side, _ = composer.frame(squares)
        if side > targets()[count][1] + 1e-8:
            own = TAKE / f'{count}.csv'
            if seconds == 900 and own.exists():
                own_squares = next(iter(rectangles.layouts(own).values()))
                own_side, _ = composer.frame(own_squares)
                if own_side <= targets()[count][1] + 1e-8:
                    metadata = json.loads(Path(str(own) + '.json').read_text())
                    digest = sha(own)
                    ancestry_digest = sha(Path(str(own) + '.json'))
                    root_folder = WORK / 'follow-roots' / f'{digest}-{ancestry_digest[:16]}-notices'
                    root_folder.mkdir(parents=True, exist_ok=True)
                    root_packing = root_folder / f'{count}.csv'
                    if root_packing.exists():
                        if sha(root_packing) != digest:
                            raise RuntimeError('pinned follow root changed')
                    else:
                        shutil.copyfile(own, root_packing)
                    atomic(str(root_packing) + '.json', json.dumps(clean_notice_fields(metadata), indent=1))
                    path, squares, side = root_packing, own_squares, own_side
                    walked = metadata['walk_at_publish']
                    src = dict(original=str(root_packing), snapshot=str(root_packing), sha256=digest, n=count,
                               licence='own fresh certified construction; input notice: ' +
                                       source_notice(metadata.get('source', {}).get('licence', 'own held construction')),
                               start_walk_clean=True,
                               start_walk_files=walked['files'], start_walk_capped=False)
            if side > targets()[count][1] + 1e-8:
                state(f'FOLLOW-CLOSED n={count} seconds={seconds}: source no longer the lowest live row')
                return
        signature = geometry_key(squares)
        claims_file = WORK / 'follow-claims.json'
        claims = json.loads(claims_file.read_text()) if claims_file.exists() else {}
        claim = f'{count}-{signature}-{seconds}'
        if claim in claims:
            return
        seed = 3700000 + int(signature[:8], 16) % 900000 + seconds
        folder = WORK / 'follow-starts'
        folder.mkdir(exist_ok=True)
        snapshot = folder / f'{claim}.csv'
        shutil.copyfile(path, snapshot)
        atomic(str(snapshot) + '.json', json.dumps(dict(n=count, original=str(path),
                                                       sha256=sha(path), source=src,
                                                       licence=src.get('licence', 'own held construction'))))
        claims[claim] = dict(path=str(snapshot), seed=seed, queued_at=now())
        atomic(claims_file, json.dumps(claims))
        source = dict(src, job_kind=f'fresh-{seconds}', follow_seconds=seconds, seed=seed)
        with open(HANDOFF, 'a') as log:
            log.write(f'{now()} forensics -> all: claim fresh-follow n={count} '
                      f'seconds={seconds} seed={seed} geometry={signature[:16]} sha256={sha(path)}\n')
        time.sleep(5)
        earlier = [line for line in HANDOFF.read_text().splitlines()
                   if f'claim fresh-follow n={count} seconds={seconds} seed={seed} geometry={signature[:16]}' in line]
        if len(earlier) != 1:
            state(f'FOLLOW-CLOSED duplicate claim n={count} seconds={seconds} seed={seed}')
            return
        self.jobs.put((-1000 if seconds == 180 else -999, str(snapshot), count, source))
        state(f'FOLLOW-QUEUE n={count} seconds={seconds} seed={seed} geometry={signature[:16]}')

    def fresh_files(self):
        out = []
        for pat in ('take-*-r37/*.csv', 'take-*-r37/near/*.csv', 'take-forensics-r37/work/held-picks/*.csv'):
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
        fresh_certificate = '/near/' not in p and Path(p).parent.name.startswith('take-') and Path(p).parent != TAKE
        if digest in self.seen.values() and not fresh_certificate:
            self.seen[key] = digest; self.save_seen(); return
        import forensics_rect as rect
        snap_dir = WORK / 'feed' / Path(p).parts[-2 if '/near/' not in p else -3]
        snap_dir.mkdir(parents=True, exist_ok=True)
        snap = snap_dir / f'{Path(p).stem}-{digest[:24]}-notices.csv'
        snap.write_bytes(data)
        atomic(str(snap) + '.json', json.dumps(dict(original=p, sha256=digest, note='forensics r37 byte snapshot of the original file')))
        lay = rect.layouts(snap)
        if len(lay) != 1:
            state(f'SKIP {p} layouts={sorted(lay)[:5]} (not one per-n layout)')
            self.seen[key] = digest; self.save_seen(); return
        n0 = next(iter(lay))
        gkey = (n0, geometry_key(lay[n0]))
        if gkey in self.geometry_sources and not fresh_certificate:
            state(f'GEOMETRY-DUP source n={n0} {p}')
            self.seen[key] = digest; self.save_seen(); return
        t0 = time.time(); w = walk(p, defer_to_fresh='/near/' in p)
        if w.get('deferred'):
            state(f'DEFER source walk for new certificate: {p}')
            return
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
            allowed = sorted({label for notice in notices for label in approved_notices(notice)})
            if not allowed:
                state(f'REFUSE-PUBLIC-LICENCE n={n0} {p} notices={notices!r}')
                self.seen[key] = digest; self.save_seen(); return
            licence = '; '.join(allowed)
        atomic(str(snap) + '.source.json', json.dumps(dict(n=n0, original=p, licence=licence)))
        if fresh_certificate:
            self.follow(snap, n0, dict(original=p, snapshot=str(snap), sha256=digest, n=n0,
                                      licence=licence, start_walk_clean=True,
                                      start_walk_files=w['files'], start_walk_capped=w['capped']), 180)
        if time.time() > SCAN_STOP:
            return
        self.scan_no += 1
        sd = WORK / f'scan-{self.scan_no:03d}'; sd.mkdir()
        write_details(sd / 'details.csv')
        cmd = [PY, '-I', str(LANE / 'forensics_rect.py'), str(sd / 'details.csv'), str(sd / 'raw'),
               '--cache', str(WORK / 'windows37.pkl')] + SCAN_ARGS + ['--fresh-only', str(snap)]
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
        (WORK / 'source-inbox').mkdir(exist_ok=True)
        while time.time() < SCAN_STOP:
            self.inbox()
            pending = self.fresh_files()[:1]
            if not pending:
                requests = sorted((WORK / 'source-inbox').glob('*.json'))
                if requests:
                    request = requests[0]
                    p = json.loads(request.read_text())['source']
                    info = os.stat(p)
                    key = f'{p}|{info.st_size}|{info.st_mtime_ns}'
                    pending = [(0, 0, p, key)]
                    os.replace(request, request.with_suffix('.done'))
            for _, _, p, key in pending:
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
            d = json.loads(w.read_text())
            if 'original' not in d or 'snapshot' not in d:
                continue
            walks[d['original']] = (w.stem, d, str(w))
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
                signature = (n, geometry_key(next(iter(rect.layouts(c).values()))))
                if side - tg[n][1] < 0.008 and signature not in seen:
                    seen.add(signature); k += 1
                    notice_file = Path(wd['snapshot'] + '.source.json')
                    notice = json.loads(notice_file.read_text()).get('licence', '') if notice_file.exists() else ''
                    self.jobs.put((side - tg[n][1], str(c), n, dict(original=orig, snapshot=wd['snapshot'], sha256=dg, n=n0, licence=notice, start_walk_clean=True, start_walk_files=wd['files'], start_walk_capped=wd['capped'])))
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
            if src.get('resume_finish'):
                pending = Path(src['resume_finish'])
                if not pending.exists():
                    continue
                record = json.loads(pending.read_text())
                try:
                    self.finish(record['n'], Path(record['out']), record['rec'],
                                record['raw'], record['src'], record['tag'])
                except Exception as error:
                    state(f'RESUME-FINISH-ERROR {record["tag"]} {error!r}')
                    self.jobs.put((margin, c, n, src))
                    time.sleep(10)
                    continue
                if record['src'].get('follow_seconds') == 180:
                    source = {key: value for key, value in record['src'].items()
                              if key not in ('job_kind', 'follow_seconds', 'seed')}
                    self.follow(record['raw'], n, source, 900)
                state(f'RESUME-FINISH complete {record["tag"]}')
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
                gkey = (n, geometry_key(next(iter(rect.layouts(c).values()))), src.get('job_kind', 'compose'))
                if gkey in self.geometry_jobs:
                    state(f'GEOMETRY-DUP job n={n} {c}')
                    continue
                self.active.add(c)
                self.geometry_jobs.add(gkey)
            k += 1; tag = f'{n}-{threading.current_thread().name}-{time.time_ns()}'
            try:
                if src.get('follow_seconds'):
                    if DEADLINE - time.time() < src['follow_seconds'] + 90:
                        state(f'FOLLOW-CLOSED n={n}: insufficient deadline room')
                        continue
                    side = __import__('forensics_compose').frame(next(iter(rect.layouts(c).values())))[0]
                    if not src.get('donor') and side > tg[n][1] + 1e-8:
                        state(f'FOLLOW-CLOSED n={n}: superseded before dispatch')
                        continue
                    out, rec = remote_kick(c, tg[n][1], tag, n, src['follow_seconds'], src['seed'])
                else:
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
                    self.geometry_jobs.discard(gkey)
                if time.time() < DEADLINE - 90:
                    self.jobs.put((margin, c, n, src))
                    time.sleep(10)
                continue
            if rec['end'] < tg[n][1] - MIN_GAIN * math.sqrt(n):
                save_finish(n, out, rec, c, src, tag)
            done.add(c)
            with self.lock:
                all_done = set(json.loads((WORK / 'done.json').read_text())) if (WORK / 'done.json').exists() else set()
                all_done.add(c); atomic(WORK / 'done.json', json.dumps(sorted(all_done)))
            end = rec['end']; gap = end - tg[n][1]
            state(f'FQ {tag} n={n} start={rec["start"]!r} end={end!r} side-gap={gap:.3e} steps={len(rec["steps"])} raw={Path(c).name}')
            follow_source = {key: value for key, value in src.items()
                             if key not in ('job_kind', 'follow_seconds', 'seed')}
            if gap > -MIN_GAIN * math.sqrt(n):
                if 0 < gap < NEAR:
                    self.near(n, out, rec, c, src, tag, gap)
                if src.get('follow_seconds') == 180:
                    self.follow(c, n, follow_source, 900)
                continue
            try:
                self.finish(n, out, rec, c, src, tag)
            except Exception as error:
                state(f'FINISH-ERROR {tag} {error!r}')
                self.jobs.put((-1002, c, n, dict(src, resume_finish=str(WORK / 'pending-finishes' / f'{tag}.json'))))
                continue
            if src.get('follow_seconds') == 180:
                self.follow(c, n, follow_source, 900)

    def near(self, n, out, rec, raw, src, tag, gap):
        """A near miss for the fresh 900 s searches (invent reads forensics near files)."""
        if not material_fq(n, rec):
            state(f'QUEUE-CLOSED polish-only endpoint n={n}, score_move={(rec["start"] - rec["end"]) / math.sqrt(n):.3e}')
            return
        d = TAKE / 'near'; d.mkdir(exist_ok=True)
        for old in d.glob(f'{n}-rect37-*.csv.json'):
            if abs(json.loads(old.read_text())['side'] - rec['end']) < 1e-10:
                state(f'NEAR-DUP n={n} side {rec["end"]!r} as {old.name}'); return
        dst = d / f'{n}-rect37-{tag}.csv'
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
        pending = save_finish(n, out, rec, raw, src, tag)
        result = self.finish_now(n, out, rec, raw, src, tag)
        pending.unlink(missing_ok=True)
        return result

    def finish_now(self, n, out, rec, raw, src, tag):
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
        record = dict(n=n, score=best, parts=held_parts(raw_meta), bar37=bar_scores()[n], source=src, raw=raw, raw_meta=raw_meta,
                      method=(f"{src['follow_seconds']} s {'donor' if src.get('donor') else 'fresh'} follow"
                              if src.get('follow_seconds') else 'rectangle windows'),
                      fq_receipts=receipts, cert_first=str(cert), certified=str(cert2),
                      certifier='take-border-r28/work/finesafe.py (2.2e-11, metric direct and pandas)')
        record = clean_notice_fields(record)
        atomic(str(cert2) + '.json', json.dumps(record, indent=1))
        # the walk the assembler runs: on the certified file itself, through its record (held parts, source file)
        w = walk(cert2)
        if not walk_accepted(w, src.get('licence', '')):
            state(f'REFUSE-AT-PUBLISH n={n} walk of {cert2.name}: pubfirst={w.get("pubfirst")} {str(w.get("hits"))[:300]}')
            return
        publish(n, cert2, best, dict(record, walk_at_publish=dict(clean=w.get('clean'), hits=w.get('hits'), pubfirst=w.get('pubfirst'), helds=w.get('helds'), files=w.get('files'), capped=w.get('capped'))))


def seed_cache():
    """Window table from the held round 36 a rows only (our own submitted layouts)."""
    d = WORK / 'seed'; d.mkdir(exist_ok=True)
    write_details(d / 'details.csv')
    cmd = [PY, '-I', str(LANE / 'forensics_rect.py'), str(d / 'details.csv'), str(d / 'raw'), '--cache',
           str(WORK / 'windows37.pkl'), '--keep', '8', '--only', '2', '--max-mesh', '0', str(HELD)]
    with open(d / 'rect.log', 'w') as log:
        subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, check=True)


def finalize():
    """Keep a row only when it is below every live r37 take and its source is not withdrawn."""
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
            if not walk_accepted(w, rec.get('source', {}).get('licence', '')):
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
    elif cmd == 'freshkick':
        fresh_kick(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6]),
                   float(sys.argv[7]), float(sys.argv[8]))
    elif cmd == 'seed':
        seed_cache()
    elif cmd == 'finalize':
        finalize()
    elif cmd == 'driver':
        if not (WORK / 'windows37.pkl').exists():
            seed_cache(); state('SEED window table from held round36-2026-11-18b')
        dr = Driver()
        dr.requeue()
        ts = [threading.Thread(target=dr.scanner, daemon=True), threading.Thread(target=dr.runner, name='fq0', daemon=True), threading.Thread(target=dr.runner, name='fq1', daemon=True)]
        for t in ts:
            t.start()
        while time.time() < DEADLINE:
            for index, thread in enumerate(ts):
                if not thread.is_alive() and (index > 0 or time.time() < SCAN_STOP):
                    state(f'HEALTH restarting thread {thread.name}')
                    replacement = threading.Thread(target=dr.scanner if index == 0 else dr.runner,
                                                   name=thread.name, daemon=True)
                    replacement.start()
                    ts[index] = replacement
            time.sleep(10)
        state('driver stopped at deadline')
