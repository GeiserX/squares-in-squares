"""boxA feeder for 900 s midm_scan lkick,kick jobs on boxC (border r30, light python; r29 copy with the r30 candidates() below).
Why: round 28 measured that one 900 s midm_scan lkick,kick run of a fresh row or a forensics rectangle at the bar side
moved 684 by 9.0e-5, 748 by 3.1e-5 and 910 by 8.4e-6 (rebuild), while our r28 kfeed (one fq call with --kick, then a
polish) gave nothing past the slack on 36 tries. So the change from r28 is the kick loop itself (midm_scan, 900 s,
lkick and kick modes, keep the best), not more single kicked calls.
What it kicks: near files that rebuild's own follow29.py chose (within 1e-6 of the bar side, not the bar row) but could
not queue ('near skipped (queues full)' in take-rebuild-r34/work/follow.log), plus every fresh near file of another
r29 lane in our LP index within KICK_GAP of the live bar side when nothing of that kind waits. One input per n at a
time, lowest side first, inputs pinned by sha256, each claimed in handoff-r34.log before it runs; inputs that rebuild
or quench queued or claimed (by path or sha256 prefix) are skipped. Every raw find is certified with finesafe and,
when it is below the live bar, gets the certified-file polish fq as a final job with a 'kick' manifest, which the
driver publishes through the same source policy and share test as every other row."""
import os, sys, time, json, csv, math, hashlib, glob, re, subprocess
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent; T = W.parent
src = (W / 'driver.py').read_text()
src = src[:src.index("log('start round34 collector/scanner")]
src = src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)", "")
ns = {'__name__': 'border_kfeed', '__file__': str(W / 'driver.py')}; exec(compile(src, str(W / 'driver.py'), 'exec'), ns)
bs = ns['bs']; floatsafe = ns['floatsafe']; audit = ns['audit']; metadata = ns['metadata']; csvout = ns['csvout']
REMOTE = 'boxC:scratch/squares-border-r34/'
END = float((W / 'deadline').read_text())
KICK_SEC = int(os.environ.get('KICK_SEC', '900')); KICK_SEC1 = int(os.environ.get('KICK_SEC1', '300')); KICK_GAP = float(os.environ.get('KICK_GAP', '1e-6')); PENDING = int(os.environ.get('KICK_PENDING', '2')); KICK_ANY = os.environ.get('KICK_ANY') == '1'
D = W / 'kq'; [(D / x).mkdir(parents=True, exist_ok=True) for x in ('nin', 'jobs', 'nout')]
IX = D / 'index.json'; index = json.load(open(IX)) if IX.exists() else {}
DONE = D / 'done.json'; done = set(json.load(open(DONE))) if DONE.exists() else set()
def save():
    for f, v in ((IX, index), (DONE, sorted(done))):
        tmp = f.with_suffix('.tmp'); tmp.write_text(json.dumps(v)); tmp.replace(f)
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
def side_of(p):
    xs = []
    for r in csv.DictReader(open(p)):
        a = float(r['angle']); h = .5 * (abs(math.cos(a)) + abs(math.sin(a))); xs.append((float(r['x']), float(r['y']), h))
    return len(xs), max(max(x + h for x, y, h in xs) - min(x - h for x, y, h in xs), max(y + h for x, y, h in xs) - min(y - h for x, y, h in xs))
def others_taken():
    """paths and sha256 prefixes that rebuild queued or that any lane claimed for a kick in handoff-r30.log"""
    paths, shas = set(), set()
    try:
        for line in open(S / 'take-rebuild-r34/work/queue-log.tsv'):
            c = line.rstrip('\n').split('\t')
            if len(c) >= 6: paths.add(str(S / c[4]) if not c[4].startswith('/') else c[4]); shas.add(c[5][:12])
            m = re.search(r'-([0-9a-f]{8})$', c[2]) if len(c) > 2 else None
            if m: shas.add(m[1])
    except OSError: pass
    try:
        for line in open(S / 'handoff-r34.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'\bclaim', line, re.I): continue
            paths.update(re.findall(r'(/Volumes/\S+?\.csv)', line))
            shas.update(h[:12] for h in re.findall(r'sha256 ([0-9a-f]{8,64})', line))
            shas.update(h[:12] for h in re.findall(r'-([0-9a-f]{12})(?:\b|,)', line))
    except OSError: pass
    return paths, shas
def rebuild_skipped():
    out = []
    try:
        for line in open(S / 'take-rebuild-r34/work/follow.log'):
            m = re.search(r'near skipped \(queues full\) near-([a-z0-9-]+?)-(\d+)-([0-9a-f]{12})', line)
            if m: out.append((m[1], int(m[2]), m[3]))
    except OSError: pass
    return out
PROBE = int(os.environ.get('KICK_PROBE', '120'))
def reseed(meta, ident, n):
    src = D / 'nin' / f'{ident}_{n}.csv'; cdata = src.read_bytes(); k = meta.get('reseed', 0) + 1
    cid = hashlib.sha256(cdata).hexdigest()[:9] + f'r{k}'; seed2 = (meta['seed'] + 37 * k + 500) % 1000; w = meta.get('w', '2'); sec = meta.get('seconds', KICK_SEC)
    (D / 'nin' / f'{cid}_{n}.csv').write_bytes(cdata)
    (D / 'jobs' / f'{cid}.json').write_text(json.dumps(dict(input=f'nin/{cid}_{n}.csv', out=f'nout/{cid}_{n}', n=n, seconds=sec, seed=seed2, priority=0, w=w, probe=0)))
    line = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {sec} s midm_scan lkick,kick new seed {seed2} (probe 0 s) of n={n} (second unprobed seed of a held row whose first 900 s seed found nothing; lesson 6c: 753 and 998 paid on the second seed), start bytes sha256 {meta["sha256"][:16]}, {meta["path"]}\n'
    if not claim_ok(n, line):
        (D / 'jobs' / f'{cid}.json').unlink(); return
    index[cid] = dict(meta, seed=seed2, t=time.time(), extra=meta['extra'] - 1, probe=0, reseed=k); save()
    subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
    subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
    log(f'KICK seed2 {n}: new seed {seed2} from {meta["path"]} (extra seeds left {meta["extra"] - 1}); {sec} s, no probe, on boxC worker {w}; claimed')
def claim_ok(n, line):
    """r34 (lesson 6f): post the claim line, wait 5 s, re-read handoff-r34.log, and start only if no other lane claimed a
    kick of the same n in the 1200 s before our line (a 900 s job claimed earlier may still run). Otherwise post a release."""
    import datetime
    with open(S / 'handoff-r34.log', 'a') as f: f.write(line)
    time.sleep(5)
    lines = open(S / 'handoff-r34.log', errors='replace').read().splitlines()
    try: i = max(k for k, l in enumerate(lines) if l == line.rstrip('\n'))
    except ValueError: return True
    try: t0 = datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
    except ValueError: t0 = time.time()
    for l in lines[:i]:
        if ' border -> ' in l or not re.search(r'claim', l, re.I) or not re.search(r'kick', l, re.I): continue
        if n not in {int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', l)}: continue
        try: t = datetime.datetime.fromisoformat(l.split()[0].replace('Z', '+00:00')).timestamp()
        except ValueError: continue
        if t0 - t <= 1200:
            with open(S / 'handoff-r34.log', 'a') as f:
                f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: release claim of n={n} (an earlier claim of {l.split()[1]} at {l.split()[0]} names it; lesson 6f)\n')
            log(f'CLAIM lost {n}: earlier claim of {l.split()[1]} at {l.split()[0]}; released, not started'); return False
    return True
STOPPED = set()
def stop_superseded(L):
    """r34 (lesson 6e): a running kick stops as soon as another lane holds a row more than 1e-6 of score lower at its n."""
    (D / 'stop').mkdir(exist_ok=True); new = False
    for ident, meta in index.items():
        if ident in done or ident in STOPPED or meta.get('skipped') or meta.get('control'): continue
        n = meta['n']
        if L.get(n, 1e9) < meta['side'] - 1e-6 * math.sqrt(n):
            (D / 'stop' / ident).write_text('superseded'); STOPPED.add(ident); new = True
            log(f'KICK stop {n} {ident}: a live r34 row is {(meta["side"] - L[n]) / math.sqrt(n):.3e} of score below its start (lesson 6e)')
    if new: subprocess.run(['rsync', '-a', str(D / 'stop') + '/', REMOTE + 'kq/stop/'], check=False)
LASTCHK = [0.0]
def check_workers():
    """r34 (lesson 6g): one worker.py per slot on boxC; restart a dead one (its kick job runs again: its claim dir goes)."""
    if time.time() - LASTCHK[0] < 240: return
    LASTCHK[0] = time.time()
    try:
        out = subprocess.run(['ssh', 'boxC', 'ps -ax -o pid,command | grep "squares-border-r34" | grep "worker.py [12]" | grep -v grep'], capture_output=True, text=True, timeout=60).stdout
    except Exception as e:
        log(f'WORKERS check failed ({e!r})'); return
    for w in ('1', '2'):
        if re.search(rf'worker\.py {w}\b', out): continue
        stale = 'for c in kq/jobs/*.claim final/*.claim; do [ -d "$c" ] || continue; b=${c%.claim}; [ -e "$b.done" ] || rmdir "$c"; done'
        cmd = (f'cd $SCRATCH/squares-border-r34 && {stale}; R=$HOME/scratch/squares-border-r34; nohup nice -n 5 $R/venv/bin/python -I $R/worker.py {w} >> worker{w}.log 2>&1 < /dev/null & echo $! > worker{w}.pid; cat worker{w}.pid')
        r = subprocess.run(['ssh', 'boxC', cmd], capture_output=True, text=True, timeout=60)
        log(f'WORKERS boxC worker {w} was not running: stale claims of unfinished jobs cleared and worker restarted (pid {r.stdout.strip()}; lesson 6g)')
lpix = {}
def lp_paths():
    try:
        for k, v in json.load(open(W / 'lp/index.json')).items(): lpix[v['sha256'][:12]] = v
    except (OSError, ValueError): pass
    return lpix
RECT_GAP = float(os.environ.get('RECT_GAP', '3e-5'))
POLISH_LANES = {'classfill', 'harvest', 'soft', 'border'}
def lane_of(p):
    m = re.search(r'/take-([a-z0-9-]+?)-r34/', str(p)); return m[1] if m else ''
FRESH_WAIT = float(os.environ.get('FRESH_WAIT', '600'))
def r31_claims():
    """sha256 prefixes and (n, time) of every claim or kick line of another lane in handoff-r34.log (round 31 lesson b)"""
    shas, ns = {}, {}
    try:
        import datetime
        for line in open(S / 'handoff-r34.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'kick|claim', line, re.I): continue
            try: t = datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
            except ValueError: t = time.time()
            for h in re.findall(r'sha256[^0-9a-f\n]{0,24}([0-9a-f]{8,64})', line, re.I): shas[h[:12].lower()] = t
            for h in re.findall(r'-([0-9a-f]{12})(?:\b|,)', line): shas.setdefault(h, t)
            for m in re.finditer(r'\bn\s*=\s*(\d+)', line): ns[int(m[1])] = t
    except OSError: pass
    return shas, ns
def candidates(L):
    """r31: (1) fresh take csv of other r31 lanes that no lane claimed within FRESH_WAIT s of their mtime (backlog is the
    follow lane, round 31 lesson b), (2) held rows of the round 30 c file (work/held34/<n>.csv, order.json) that no kick
    or claim line of handoff-r29..r31 names by n, largest board gap first (round 31 lesson a: border's 17 such kicks
    gave 494 and 791 in round 30). Near files are out (round 30: 13 k123 near kicks and 406 near LP inputs, 0 rows)."""
    taken_p, taken_h = others_taken(); out = {}
    c31, n31 = r31_claims()
    for q in glob.glob(str(S / 'take-*-r34/[0-9]*.csv')):
        if not Path(q).stem.isdigit() or '/take-border-r34/' in q: continue
        try: st = Path(q).stat(); data = Path(q).read_bytes()
        except OSError: continue
        if len(data) > 1500000 or time.time() - st.st_mtime < FRESH_WAIT: continue
        h = hashlib.sha256(data).hexdigest(); h12 = h[:12]
        if q in taken_p or h12 in taken_h or h12[:8] in taken_h or h12 in c31: continue
        if any(x['sha256'][:12] == h12 for x in index.values()): continue
        try: m, side = side_of(q); n = int(next(csv.DictReader(open(q)))['n'])
        except Exception: continue
        if m != n or n not in L: continue
        gap = side - L[n]
        if not gap < 1e-9: continue                      # overtaken already
        if any(x.get('n') == n and not x.get('skipped') and x.get('side', 1e9) - 1e-9 <= side for x in index.values()): continue
        out[n] = ((1, 0, -st.st_mtime), q, side, gap, False, data)
    # r31 19:10Z: held34/order_all.json (build_order_all.py): class 0 open rows, 1 rows round 30 c added, 2 rows named
    # in handoff-r29 only, 3 rows named in handoff-r30; largest board gap first within a class.
    try: order = [(c, n, g) for c, n, g in json.load(open(W / 'held34/order_all.json'))]
    except (OSError, ValueError): order = []
    for c, n, g in order:
        p = str(W / 'held34' / f'{n}.csv')
        if n in out or n in n31 or n not in L: continue
        data = Path(p).read_bytes(); h12 = hashlib.sha256(data).hexdigest()[:12]
        if h12 in taken_h or h12 in c31 or h12[:8] in taken_h: continue
        if any(x['sha256'][:12] == h12 or (x.get('n') == n and not x.get('skipped')) for x in index.values()): continue
        m, side = side_of(p); gap = side - L[n]
        if m != n or gap > 1e-9: continue                 # a lane already lowered this n: its take row is the start
        out[n] = ((2, c, -g), p, side, gap, False, data)
    return sorted(out.values(), key=lambda c: c[0])
while time.time() < END - 300:
    try:
        L = {int(k): v for k, v in json.load(open(W / 'bars.json')).items()}
        check_workers(); stop_superseded(L)
        # r29 08:20Z: bfeed29.py writes boundary grow1 entries into index.json; merge them before this pass saves
        try: index.update({k: v for k, v in json.load(open(IX)).items() if k not in index})
        except (OSError, ValueError): pass
        # r31 20:05Z: hand-queued kicks (kq/manual/<name>.json: path, n, seconds, seed, w, probe, modes, why); each is pinned,
        # claimed and indexed like a feed kick, so its result is certified, chained and published by the same code.
        (D / 'manual').mkdir(exist_ok=True)
        for mf in sorted((D / 'manual').glob('*.json')):
            try:
                mj = json.load(open(mf)); data = Path(mj['path']).read_bytes(); digest = hashlib.sha256(data).hexdigest()
                if not mj.get('control') and not audit(Path(mj['path'])):
                    import provenance as _pv
                    log(f'KICK manual {mf.name} refused before the kick (walk: {_pv.last_reason(mj["path"])})'); mf.rename(mf.with_suffix('.refused')); continue
                ident = digest[:9] + 'm' + str(mj['seed']); n = mj['n']; m_, side = side_of(mj['path']); gap = side - L[n]
                (D / 'nin' / f'{ident}_{n}.csv').write_bytes(data)
                job = dict(input=f'nin/{ident}_{n}.csv', out=f'nout/{ident}_{n}', n=n, seconds=mj['seconds'], seed=mj['seed'], priority=mj.get('priority', 0), w=mj['w'], probe=mj.get('probe', 0))
                if mj.get('modes'): job['modes'] = mj['modes']
                if not mj.get('control'):
                    line = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {mj["seconds"]} s midm_scan {mj.get("modes", "lkick,kick")} (seed {mj["seed"]}, probe {mj.get("probe", 0)} s) of n={n}, start bytes sha256 {digest[:16]} ({mj["why"]}; {gap:.3e} of side vs the live bar), {mj["path"]}\n'
                    if not claim_ok(n, line):
                        mf.rename(mf.with_suffix('.lost')); continue
                (D / 'jobs' / f'{ident}.json').write_text(json.dumps(job))
                index[ident] = dict(path=mj['path'], n=n, sha256=digest, side=side, gap=gap, seed=mj['seed'], t=time.time(), w=mj['w'], seconds=mj['seconds'], probe=mj.get('probe', 0), modes=mj.get('modes', 'lkick,kick'), extra=mj.get('extra', 0), root=mj['path'], control=bool(mj.get('control'))); save()
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
                log(f'KICK queue {n} from {mj["path"]} (sha256 {digest[:16]}), side {side:.13f}, {gap:.3e} vs the live bar, {mj["why"]}; {mj["seconds"]} s midm_scan {mj.get("modes", "lkick,kick")} seed {mj["seed"]} probe {mj.get("probe", 0)} on boxC worker {mj["w"]}; claimed (hand-queued)')
                mf.rename(mf.with_suffix('.queued'))
            except Exception as e:
                log(f'KICK manual {mf.name} not queued ({e!r})'); mf.rename(mf.with_suffix('.failed'))
        # r30 12:40Z: two kick slots. Worker 2 runs 900 s kicks back to back; worker 1 runs a 300 s kick only when its LP and
        # fq follows are empty (the follow queue drained in 25 minutes at the round start, and quench r29 measured 5 rows
        # from 40 kicks of 300 s). A worker-1 job carries w='1'; the boxC worker.py r30b reads it.
        for w, sec in [x for x in (('2', KICK_SEC), ('1', KICK_SEC1)) if x[0] in os.environ.get('KICK_WORKERS', '12')]:   # r31 21:30Z: worker 2 takes deepfeed.py jobs
            pend = [i for i, v in index.items() if i not in done]
            sec = int(min(sec, END - time.time() - 600))   # r31: shorter kicks near the end, each still leaves 600 s for its polish fq
            if len([i for i in pend if index[i].get('w', '2') == w]) >= 1 or sec < 300: continue
            busy = {index[i]['n'] for i in pend}
            for rank, p, side, gap, skipped, data in candidates(L):
                n = int(next(csv.DictReader(open(p)))['n'])
                if n in busy: continue
                if w == '1' and rank[0] not in (1, 2): continue   # r30 14:45Z: worker 1 kicks fresh takes; 15:00Z: and held rows (494 paid)
                if not audit(Path(p)): log(f'KICK skip {n} {p}: the walk refuses it'); index['x' + hashlib.sha256(data).hexdigest()[:12]] = dict(path=p, n=n, sha256=hashlib.sha256(data).hexdigest(), skipped=True); done.add('x' + hashlib.sha256(data).hexdigest()[:12]); save(); continue
                digest = hashlib.sha256(data).hexdigest(); ident = digest[:12]
                (D / 'nin' / f'{ident}_{n}.csv').write_bytes(data)
                seed = int(digest[:6], 16) % 1000
                (D / 'jobs' / f'{ident}.json').write_text(json.dumps(dict(input=f'nin/{ident}_{n}.csv', out=f'nout/{ident}_{n}', n=n, seconds=sec, seed=seed, priority=0, w=w, probe=PROBE)))
                index[ident] = dict(path=p, n=n, sha256=digest, side=side, gap=gap, rebuild_skipped=skipped, seed=seed, t=time.time(), w=w, seconds=sec, probe=PROBE, root=p); save()
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
                why = (f'fresh take row of {lane_of(p)} that no lane claimed within {FRESH_WAIT:.0f} s') if rank[0] == 1 else ('held row of the round 30 c file that no kick or claim line of rounds 29 to 31 names' if rank[1] == 0 else 'held row that round 30 c added (no kick of its final bytes)' if rank[1] == 1 else 'held row of the round 30 c file that no r30 or r31 kick line names' if rank[1] == 2 else 'held row of the round 30 c file, no r31 kick line names it')
                with open(S / 'handoff-r34.log', 'a') as f:
                    f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {sec} s midm_scan lkick,kick (seed {seed}, {PROBE} s probe) of n={n}, start bytes sha256 {digest[:16]} ({why}; {gap:.3e} of side vs the live bar), {p}\n')
                log(f'KICK queue {n} from {p} (sha256 {digest[:16]}), side {side:.13f}, {gap:.3e} vs the live bar, {why}; {sec} s midm_scan lkick,kick seed {seed} on boxC worker {w}; claimed in handoff-r34.log; deadline 07:15Z')
                break
        rr = subprocess.run(['rsync', '-a', '--exclude', 'tmp/', REMOTE + 'kq/nout/', str(D / 'nout') + '/'])   # r31: fq tmp dirs vanish mid-copy (rsync 24)
        if rr.returncode not in (0, 24): raise subprocess.CalledProcessError(rr.returncode, 'rsync nout')
        for ident, meta in list(index.items()):
            if ident in done: continue
            n = meta['n']; outdir = D / 'nout' / f'{ident}_{n}'
            if not (outdir / 'DONE').exists(): continue
            done.add(ident); save()
            raws = glob.glob(str(outdir / 'raw/*.csv'))
            scanlog = sorted(glob.glob(str(outdir / 'scan-*.tsv')))
            end = [l for f in scanlog for l in open(f) if l.startswith('# END')]
            if not raws:
                log(f'{"BOUNDARY" if meta.get("boundary") else "KICK"} {n} {ident}: no find below its start side ({end[-1].strip()[:200] if end else "no END line"})')
                # r31: a chain whose first scan gained 1e-5 of score or more gets at least two more seeds (midm r30: 412 seed 777
                # gained 7.0e-6 after seed 103 gained 1.6e-7); a seed with no find starts the next seed from the same file.
                if meta.get('extra', 0) > 0 and time.time() < END - meta.get('seconds', KICK_SEC) - 600:
                    reseed(meta, ident, n)
                continue
            best = min(raws, key=lambda f: side_of(f)[1]); _, braw = side_of(best)
            rr = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(best))]
            _, fr, sc, e = floatsafe.work((n, rr))
            if fr is None: log(f'KICK {n} {ident}: the best find {best} does not certify ({e})'); continue
            sidec = (sc + 1) * math.sqrt(n); gap = sidec - L[n]
            log(f'KICK {n} {ident}: raw find {braw:.13f} ({braw - meta["side"]:.3e} vs its start), certified side {sidec:.13f}, {gap:.3e} vs the live bar; {end[-1].strip()[:160] if end else ""}')
            # r30 13:35Z: chain legs. A kick whose best find moved its start by more than 1e-6 of side and certified within
            # 1e-5 above the live bar gets one more leg of the same length from that certified find, on the same worker
            # (twoshort r29: legs while a leg removes more than 1e-6 gave 3 of its 5 rows; our 378 leg 1 ended 7.2e-8 above).
            big = False  # r32: legs carry no extra seeds (r31: two seeds of 494 leg 2 found nothing)
            # r32 (r31 next item 2): a leg only from a first find that moved more than 1e-5 of side, and the next leg only
            # while the last leg moved 2e-6 or more (r31: 494 leg 1 1.577e-4 then nothing; 864 legs 1.044e-5, 1.224e-6, nothing).
            moved = meta['side'] - braw; legn = meta.get('leg', 0)
            want_leg = (moved > 1e-5) if legn == 0 else (moved >= 2e-6)
            log(f'CHAIN rule {n} {ident}: moved {moved:.3e} of side on leg {legn}; ' + ('a leg follows' if want_leg and gap < 1e-5 else 'no leg (' + ('certified 1e-5 or more above the live bar' if want_leg else 'first find 1e-5 of side or less' if legn == 0 else 'the leg moved less than 2e-6') + ')'))
            if meta.get('control'): log(f'CONTROL {n} {ident}: rule applied in the log only, no leg, no seed, no publish'); continue
            # r32 15:25Z: the reseed and the leg go to boxC after the finals of a publishable find, so the worker that ends
            # the kick takes the certified-file fq first (worker 1 ranks finals before kicks; they used to arrive 1 to 45 s later).
            def _after():
                if legn == 0 and not want_leg and moved < 1e-6 and meta.get('extra', 0) > 0 and time.time() < END - meta.get('seconds', KICK_SEC) - 600:
                    reseed(meta, ident, n)   # r32: a first seed that only polished the certify dilation counts as dry; the row gets its second seed
                if want_leg and gap < 1e-5 and not meta.get('boundary') and time.time() < END - meta.get('seconds', KICK_SEC) - 600:
                    try:
                        leg = meta.get('leg', 0) + 1; cdir = W / 'chain'; cdir.mkdir(exist_ok=True)
                        tmpc = cdir / f'{n}.tmp.csv'; csvout(tmpc, fr); cdata = tmpc.read_bytes(); cdig = hashlib.sha256(cdata).hexdigest()
                        cfile = cdir / f'{n}-leg{leg}-{cdig[:12]}.csv'; tmpc.replace(cfile)
                        pmd = metadata(Path(meta['path'])) or {}
                        rec = dict(n=n, leg=leg, source=f'kick leg {leg}: the certified best find (finesafe) of the {meta.get("seconds", KICK_SEC)} s midm_scan.py lkick,kick (seed {meta["seed"]}) on boxC of the pinned copy {D / "nin" / (ident + "_" + str(n) + ".csv")} (sha256 {meta["sha256"]}) of {meta["path"]}; parent record ' + json.dumps(pmd, sort_keys=True),
                                   licence=(pmd.get('licence') if isinstance(pmd, dict) else None) or 'ours (kick of a layout of another lane)')
                        Path(str(cfile) + '.json').write_text(json.dumps(rec))
                        cid = cdig[:12]; seed2 = (meta['seed'] + 101 * leg) % 1000; w = meta.get('w', '2'); sec = meta.get('seconds', KICK_SEC)
                        extra = 0; pr = 0   # r32: legs run the full 900 s with no probe and no extra seed
                        (D / 'nin' / f'{cid}_{n}.csv').write_bytes(cdata)
                        (D / 'jobs' / f'{cid}.json').write_text(json.dumps(dict(input=f'nin/{cid}_{n}.csv', out=f'nout/{cid}_{n}', n=n, seconds=sec, seed=seed2, priority=0, w=w, probe=pr)))
                        index[cid] = dict(path=str(cfile), n=n, sha256=cdig, side=sidec, gap=gap, seed=seed2, t=time.time(), w=w, seconds=sec, leg=leg, extra=extra, probe=pr, root=meta.get('root', meta['path'])); save()
                        subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
                        subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
                        with open(S / 'handoff-r34.log', 'a') as f:
                            f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {sec} s midm_scan lkick,kick leg {leg} (seed {seed2}) of n={n}, start bytes sha256 {cdig[:16]} (our certified kick find, {gap:.3e} of side vs the live bar), {cfile}\n')
                        log(f'KICK chain {n}: leg {leg} queued from the certified find {cfile.name} ({gap:.3e} vs the live bar, the leg moved {braw - meta["side"]:.3e}); {sec} s seed {seed2} on boxC worker {w}; claimed')
                    except Exception as e:
                        log(f'KICK chain {n}: leg not queued ({e!r})')
            if not gap < 0:
                _after(); continue
            p = Path(meta['path'])
            copy = W / 'donors' / f'{n}-{ident}.csv'
            bd = meta.get('boundary')
            if bd:  # r29: grow1 at the integer band edge (bfeed29.py): the start is our layout of n-1 plus one square
                copy = W / 'donors' / f'{n}-{ident}.donor{bd["donor_n"]}.csv'
                if not copy.exists(): copy.write_bytes((D / 'nin' / f'{ident}_{n}.donors.csv').read_bytes())
                uid = f'{n}-grow-{ident[:8]}-' + hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
                ss, AA = bs.normalize([(float(q['x']), float(q['y']), float(q['angle'])) for q in fr])
                man = dict(id=uid + '-p', kind='kick', donor=str(bd['donor_n']), n=str(n), corner='0', variant='0', dropped='0', near=str(copy), donor_source=bd['source_text'], donor_licence=bd.get('licence') or 'ours', built_L=repr(ss), start_sha256=bd['donor_sha256'],
                           kick=f'{bd["seconds"]} s midm_scan.py --modes grow1 --seed {meta["seed"]} on boxC (the n={bd["donor_n"]} layout plus one square in its widest hole, then fq; raw find {os.path.basename(best)})')
                csvout(W / 'staged' / f'{uid}-p.csv', fr)
                bs.write_txt(str(W / 'final' / f'{uid}-p.input.txt'), ss, AA)
                job = dict(input=f'{uid}-p.input.txt', output=f'{uid}-p.output.txt', n=n, manifest=man, certified_before=sc, flags=list(bs.POLISH),
                           chain={'mode': 'midm_scan grow1, then the certified-file polish fq', 's_start': ss, 'log': []})
                (W / 'final' / f'{uid}-p.job.json').write_text(json.dumps(job))
                log(f'BOUNDARY {n} {ident}: queued certified-file polish fq {uid}-p (certified score {sc:.16g}, {gap:.3e} of side vs the live bar)')
                _after(); continue
            if not copy.exists(): copy.write_bytes((D / 'nin' / f'{ident}_{n}.csv').read_bytes())
            row = meta.get('row')  # r29 09:35Z: a take input carries its take.tsv row as it was when its bytes were pinned
            if row is None and p.stem.isdigit():
                try: row = next((r for r in csv.DictReader(open(p.parent / 'take.tsv'), delimiter='\t') if r['n'] == p.stem), None)
                except OSError: row = None
            dsrc = f'{p}' + (f', from {p.parent}/take.tsv: {row["source"]}' if row else ', ' + bs.near_source(str(p), n, meta['side'], L[n]))
            lic = row.get('licence', 'ours') if row else bs.near_metadata(str(p)).get('licence') or 'ours (near layout of another lane)'
            md = metadata(p)
            if md: dsrc += '; recorded ancestry ' + json.dumps(md, sort_keys=True); lic = md.get('licence') or lic
            uid = f'{n}-kick-{ident[:8]}-' + hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
            ss, AA = bs.normalize([(float(q['x']), float(q['y']), float(q['angle'])) for q in fr])
            man = dict(id=uid + '-p', kind='kick', donor=str(n), n=str(n), corner='0', variant='0', dropped='0', near=str(copy), donor_source=dsrc, donor_licence=lic, built_L=repr(ss), start_sha256=meta['sha256'],
                       kick=f'{meta.get("seconds", KICK_SEC)} s midm_scan.py --modes {meta.get("modes", "lkick,kick")} --seed {meta["seed"]} on boxC (raw find {os.path.basename(best)})')
            csvout(W / 'staged' / f'{uid}-p.csv', fr)
            bs.write_txt(str(W / 'final' / f'{uid}-p.input.txt'), ss, AA)
            # r34 (round 32 lesson e): one job runs the full fq loop of the certified find on boxC (worker.py 'loop': default
            # flags, then polish, up to three rounds while a round gains 3e-9 of side, as midm_fqonce.py), and only its end is
            # published. r32: our polish-only fq of the 864 find left 1.68e-6 of score that quench's loop took.
            job = dict(input=f'{uid}-p.input.txt', output=f'{uid}-p.output.txt', n=n, manifest=man, certified_before=sc, flags=list(bs.POLISH), loop=True,
                       chain={'mode': 'midm_scan lkick,kick, then the certified-file fq loop (default flags, then polish, up to three rounds)', 's_start': ss, 'log': []})
            (W / 'final' / f'{uid}-p.job.json').write_text(json.dumps(job))
            log(f'KICK {n} {ident}: queued certified-file fq loop {uid}-p (default flags then polish, up to three rounds; certified score {sc:.16g}, {gap:.3e} of side vs the live bar)')
            subprocess.run(['rsync', '-a', '--ignore-existing', '--include', '*.input.txt', '--include', '*.job.json', '--exclude', '*', str(W / 'final') + '/', REMOTE + 'final/'], check=True)
            _after()
    except Exception:
        import traceback; traceback.print_exc()
    time.sleep(30)  # r30 14:45Z: 90 -> 30 s, to claim fresh takes first
log('kfeed34 finished by deadline')
