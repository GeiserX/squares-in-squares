"""boxA feeder for 900 s midm_scan lkick,kick jobs on boxC (border r30, light python; r29 copy with the r30 candidates() below).
Why: round 28 measured that one 900 s midm_scan lkick,kick run of a fresh row or a forensics rectangle at the bar side
moved 684 by 9.0e-5, 748 by 3.1e-5 and 910 by 8.4e-6 (rebuild), while our r28 kfeed (one fq call with --kick, then a
polish) gave nothing past the slack on 36 tries. So the change from r28 is the kick loop itself (midm_scan, 900 s,
lkick and kick modes, keep the best), not more single kicked calls.
What it kicks: near files that rebuild's own follow29.py chose (within 1e-6 of the bar side, not the bar row) but could
not queue ('near skipped (queues full)' in take-rebuild-r30/work/follow.log), plus every fresh near file of another
r29 lane in our LP index within KICK_GAP of the live bar side when nothing of that kind waits. One input per n at a
time, lowest side first, inputs pinned by sha256, each claimed in handoff-r30.log before it runs; inputs that rebuild
or quench queued or claimed (by path or sha256 prefix) are skipped. Every raw find is certified with finesafe and,
when it is below the live bar, gets the certified-file polish fq as a final job with a 'kick' manifest, which the
driver publishes through the same source policy and share test as every other row."""
import os, sys, time, json, csv, math, hashlib, glob, re, subprocess
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent; T = W.parent
src = (W / 'driver.py').read_text()
src = src[:src.index("log('start round30 collector/scanner")]
src = src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)", "")
ns = {'__name__': 'border_kfeed', '__file__': str(W / 'driver.py')}; exec(compile(src, str(W / 'driver.py'), 'exec'), ns)
bs = ns['bs']; floatsafe = ns['floatsafe']; audit = ns['audit']; metadata = ns['metadata']; csvout = ns['csvout']
REMOTE = 'boxC:scratch/squares-border-r30/'
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
        for line in open(S / 'take-rebuild-r30/work/queue-log.tsv'):
            c = line.rstrip('\n').split('\t')
            if len(c) >= 6: paths.add(str(S / c[4]) if not c[4].startswith('/') else c[4]); shas.add(c[5][:12])
            m = re.search(r'-([0-9a-f]{8})$', c[2]) if len(c) > 2 else None
            if m: shas.add(m[1])
    except OSError: pass
    try:
        for line in open(S / 'handoff-r30.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'\bclaim', line, re.I): continue
            paths.update(re.findall(r'(/Volumes/\S+?\.csv)', line))
            shas.update(h[:12] for h in re.findall(r'sha256 ([0-9a-f]{8,64})', line))
            shas.update(h[:12] for h in re.findall(r'-([0-9a-f]{12})(?:\b|,)', line))
    except OSError: pass
    return paths, shas
def rebuild_skipped():
    out = []
    try:
        for line in open(S / 'take-rebuild-r30/work/follow.log'):
            m = re.search(r'near skipped \(queues full\) near-([a-z0-9-]+?)-(\d+)-([0-9a-f]{12})', line)
            if m: out.append((m[1], int(m[2]), m[3]))
    except OSError: pass
    return out
lpix = {}
def lp_paths():
    try:
        for k, v in json.load(open(W / 'lp/index.json')).items(): lpix[v['sha256'][:12]] = v
    except (OSError, ValueError): pass
    return lpix
RECT_GAP = float(os.environ.get('RECT_GAP', '3e-5'))
POLISH_LANES = {'classfill', 'harvest', 'soft', 'border'}
def lane_of(p):
    m = re.search(r'/take-([a-z0-9-]+?)-r30/', str(p)); return m[1] if m else ''
def candidates(L):
    """r30: (0) every fresh take csv of another r30 lane (building and kicking lanes before the polishing lanes), newest
    first, and (1) forensics, invent and k123 near rect or join files up to RECT_GAP above the live bar side, lowest gap
    first; anything another lane claimed or queued is skipped. Why: in r29 the 900 s kick of fresh take rows gave rows to
    rebuild (8), midm (8 crossings), twoshort and backlog, and the forensics rect files in the 1e-5 to 3e-5 band gave
    midm 4 moves of 1e-6 or more in 10 scans and its 747 row; rebuild never gave them a slot."""
    lp_paths(); taken_p, taken_h = others_taken(); out = {}
    files = []
    # r30 14:45Z: fresh take csv are read straight from the take dirs (the LP index added a minute or more, and every fresh
    # take was claimed by two or more lanes before we saw it).
    for q in glob.glob(str(S / 'take-*-r30/[0-9]*.csv')):
        if Path(q).stem.isdigit(): files.append((q, None))
    for q in glob.glob(str(S / 'take-*-r30/near/*.csv')):
        if lane_of(q) in ('forensics', 'invent', 'k123') and ('rect' in q or 'join' in q or lane_of(q) != 'forensics'): files.append((q, None))
        elif lane_of(q) in ('modules', 'stair-c') and '-slp-' not in q: files.append((q, None))   # r30 14:50Z: after the others, see rank
    for p, h12 in files:
        if '/take-border-r30/' in p or '-r30/' not in p: continue
        try: data = Path(p).read_bytes()
        except OSError: continue
        if len(data) > 1500000: continue
        h = hashlib.sha256(data).hexdigest()
        if h12 is not None and h[:12] != h12: continue          # rewritten since the LP feed pinned it
        h12 = h[:12]
        if p in taken_p or h12 in taken_h or h12[:8] in taken_h: continue
        if any(x['sha256'][:12] == h12 for x in index.values()): continue
        try: m, side = side_of(p); n = int(next(csv.DictReader(open(p)))['n'])
        except Exception: continue
        if m != n or n not in L: continue
        gap = side - L[n]; take = Path(p).stem.isdigit()
        if any(x.get('n') == n and not x.get('skipped') and x.get('side', 1e9) - 1e-9 <= side for x in index.values()): continue
        if take:
            if not gap < 1e-6: continue
            rank = (0, 1 if lane_of(p) in POLISH_LANES else 0, -Path(p).stat().st_mtime)
        else:
            if not (-3e-9 < gap < RECT_GAP): continue
            # r30 12:15Z: a near file at the bar side ranks last (rebuild r29: 0 of 9 such near files moved; a rect at the
            # bar side is often the bar layout again), files 1e-7 or more above it first, lowest gap first.
            rank = (4 if (gap < 1e-7 or lane_of(p) in ('modules', 'stair-c')) else 3.5, 0, gap)   # r30 17:15Z: k123, forensics and invent near files after the held rows (near kicks: 0 rows of 12; held-row kicks: 2 of 13)   # r30 15:00Z: bar-side, modules and stair-c near files after the held rows
        if n not in out or rank < out[n][0]: out[n] = (rank, p, side, gap, False, data)
    # r30 12:55Z: (2) parked Samanyu-seed held rows of bar30 (quench r29: 5 rows from 40 kicks of 300 s, 1.5e-4) that no
    # kick or claim line of handoff-r29.log or handoff-r30.log names by n, n 300 and up, the largest board gap first;
    # start bytes are the round 28 b rows (work/held30, same coordinates as take-quench-r29/work/held27).
    try: order = {int(k): v for k, v in json.load(open(W / 'held30/order.json')).items()}
    except (OSError, ValueError): order = {}
    named = set()
    for h in ('handoff-r29.log', 'handoff-r30.log'):
        try:
            for line in open(S / h, errors='replace'):
                if ' border -> ' in line or not re.search(r'kick|claim', line, re.I): continue
                named.update(int(m[1]) for m in re.finditer(r'\bn\s*=\s*(\d+)', line))
        except OSError: pass
    for n, g in order.items():
        p = str(W / 'held30' / f'{n}.csv')
        if n in out or n in named or n not in L or g < 1e-7: continue   # at the board side already (628 633 760)
        data = Path(p).read_bytes(); h12 = hashlib.sha256(data).hexdigest()[:12]
        if any(x['sha256'][:12] == h12 or (x.get('n') == n and not x.get('skipped')) for x in index.values()): continue
        m, side = side_of(p); gap = side - L[n]
        if m != n or gap > 1e-9: continue                     # a lane already lowered this n: its take row is the start
        out[n] = ((2, 0, -g), p, side, gap, False, data)
    # r30 14:55Z: (3) other held rows of bar30 that no kick or claim line of handoff-r28..r30 names by n or file name,
    # n 300 and up, our bar 1e-7 or more of score above the 2026-11-09 board, largest gap first (work/held30/order3.json;
    # 639 691 745 858 918 and the 980 rectangle family left out). Why: the parked seed row 494, unkicked since round 27,
    # gave 5.8e-5 of side in one 900 s kick at 14:40Z.
    try: order3 = {int(k): v for k, v in json.load(open(W / 'held30/order3.json')).items()}
    except (OSError, ValueError): order3 = {}
    for n, g in order3.items():
        p = str(W / 'held30' / f'{n}.csv')
        if n in out or n in named or n not in L or n in (639, 691, 745, 858, 918, 980): continue
        data = Path(p).read_bytes(); h12 = hashlib.sha256(data).hexdigest()[:12]
        if any(x['sha256'][:12] == h12 or (x.get('n') == n and not x.get('skipped')) for x in index.values()): continue
        m, side = side_of(p); gap = side - L[n]
        if m != n or gap > 1e-9: continue
        out[n] = ((3, 0, -g), p, side, gap, False, data)
    return sorted(out.values(), key=lambda c: c[0])
while time.time() < END - 300:
    try:
        L = {int(k): v for k, v in json.load(open(W / 'bars.json')).items()}
        # r29 08:20Z: bfeed29.py writes boundary grow1 entries into index.json; merge them before this pass saves
        try: index.update({k: v for k, v in json.load(open(IX)).items() if k not in index})
        except (OSError, ValueError): pass
        # r30 12:40Z: two kick slots. Worker 2 runs 900 s kicks back to back; worker 1 runs a 300 s kick only when its LP and
        # fq follows are empty (the follow queue drained in 25 minutes at the round start, and quench r29 measured 5 rows
        # from 40 kicks of 300 s). A worker-1 job carries w='1'; the boxC worker.py r30b reads it.
        for w, sec in (('2', KICK_SEC), ('1', KICK_SEC1)):
            pend = [i for i, v in index.items() if i not in done]
            if len([i for i in pend if index[i].get('w', '2') == w]) >= 1 or time.time() >= END - sec - 600: continue
            busy = {index[i]['n'] for i in pend}
            for rank, p, side, gap, skipped, data in candidates(L):
                n = int(next(csv.DictReader(open(p)))['n'])
                if n in busy: continue
                if w == '1' and rank[0] not in (0, 2, 3): continue   # r30 14:45Z: worker 1 kicks fresh takes; 15:00Z: and held rows (494 paid)
                if not audit(Path(p)): log(f'KICK skip {n} {p}: the walk refuses it'); index['x' + hashlib.sha256(data).hexdigest()[:12]] = dict(path=p, n=n, sha256=hashlib.sha256(data).hexdigest(), skipped=True); done.add('x' + hashlib.sha256(data).hexdigest()[:12]); save(); continue
                digest = hashlib.sha256(data).hexdigest(); ident = digest[:12]
                (D / 'nin' / f'{ident}_{n}.csv').write_bytes(data)
                seed = int(digest[:6], 16) % 1000
                (D / 'jobs' / f'{ident}.json').write_text(json.dumps(dict(input=f'nin/{ident}_{n}.csv', out=f'nout/{ident}_{n}', n=n, seconds=sec, seed=seed, priority=0, w=w)))
                index[ident] = dict(path=p, n=n, sha256=digest, side=side, gap=gap, rebuild_skipped=skipped, seed=seed, t=time.time(), w=w, seconds=sec); save()
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
                why = ('fresh take row of ' + lane_of(p)) if rank[0] == 0 else ('near file of ' + lane_of(p) + f' within {RECT_GAP:g} of the bar side') if rank[0] in (1, 3.5, 4) else 'parked Samanyu-seed held row of bar30 that no kick line names' if rank[0] == 2 else 'held row of bar30 that no kick line of rounds 28 to 30 names'
                with open(S / 'handoff-r30.log', 'a') as f:
                    f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {sec} s midm_scan lkick,kick (seed {seed}) of n={n}, start bytes sha256 {digest[:16]} ({why}; {gap:.3e} of side vs the live bar), {p}\n')
                log(f'KICK queue {n} from {p} (sha256 {digest[:16]}), side {side:.13f}, {gap:.3e} vs the live bar, {why}; {sec} s midm_scan lkick,kick seed {seed} on boxC worker {w}; claimed in handoff-r30.log; deadline 17:45Z')
                break
        subprocess.run(['rsync', '-a', REMOTE + 'kq/nout/', str(D / 'nout') + '/'], check=True)
        for ident, meta in list(index.items()):
            if ident in done: continue
            n = meta['n']; outdir = D / 'nout' / f'{ident}_{n}'
            if not (outdir / 'DONE').exists(): continue
            done.add(ident); save()
            raws = glob.glob(str(outdir / 'raw/*.csv'))
            scanlog = sorted(glob.glob(str(outdir / 'scan-*.tsv')))
            end = [l for f in scanlog for l in open(f) if l.startswith('# END')]
            if not raws:
                log(f'{"BOUNDARY" if meta.get("boundary") else "KICK"} {n} {ident}: no find below its start side ({end[-1].strip()[:200] if end else "no END line"})'); continue
            best = min(raws, key=lambda f: side_of(f)[1]); _, braw = side_of(best)
            rr = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(best))]
            _, fr, sc, e = floatsafe.work((n, rr))
            if fr is None: log(f'KICK {n} {ident}: the best find {best} does not certify ({e})'); continue
            sidec = (sc + 1) * math.sqrt(n); gap = sidec - L[n]
            log(f'KICK {n} {ident}: raw find {braw:.13f} ({braw - meta["side"]:.3e} vs its start), certified side {sidec:.13f}, {gap:.3e} vs the live bar; {end[-1].strip()[:160] if end else ""}')
            # r30 13:35Z: chain legs. A kick whose best find moved its start by more than 1e-6 of side and certified within
            # 1e-5 above the live bar gets one more leg of the same length from that certified find, on the same worker
            # (twoshort r29: legs while a leg removes more than 1e-6 gave 3 of its 5 rows; our 378 leg 1 ended 7.2e-8 above).
            if braw - meta['side'] < -1e-6 and gap < 1e-5 and not meta.get('boundary') and time.time() < END - meta.get('seconds', KICK_SEC) - 600:
                try:
                    leg = meta.get('leg', 0) + 1; cdir = W / 'chain'; cdir.mkdir(exist_ok=True)
                    tmpc = cdir / f'{n}.tmp.csv'; csvout(tmpc, fr); cdata = tmpc.read_bytes(); cdig = hashlib.sha256(cdata).hexdigest()
                    cfile = cdir / f'{n}-leg{leg}-{cdig[:12]}.csv'; tmpc.replace(cfile)
                    pmd = metadata(Path(meta['path'])) or {}
                    rec = dict(n=n, leg=leg, source=f'kick leg {leg}: the certified best find (finesafe) of the {meta.get("seconds", KICK_SEC)} s midm_scan.py lkick,kick (seed {meta["seed"]}) on boxC of the pinned copy {D / "nin" / (ident + "_" + str(n) + ".csv")} (sha256 {meta["sha256"]}) of {meta["path"]}; parent record ' + json.dumps(pmd, sort_keys=True),
                               licence=(pmd.get('licence') if isinstance(pmd, dict) else None) or 'ours (kick of a layout of another lane)')
                    Path(str(cfile) + '.json').write_text(json.dumps(rec))
                    cid = cdig[:12]; seed2 = (meta['seed'] + 101 * leg) % 1000; w = meta.get('w', '2'); sec = meta.get('seconds', KICK_SEC)
                    (D / 'nin' / f'{cid}_{n}.csv').write_bytes(cdata)
                    (D / 'jobs' / f'{cid}.json').write_text(json.dumps(dict(input=f'nin/{cid}_{n}.csv', out=f'nout/{cid}_{n}', n=n, seconds=sec, seed=seed2, priority=0, w=w)))
                    index[cid] = dict(path=str(cfile), n=n, sha256=cdig, side=sidec, gap=gap, seed=seed2, t=time.time(), w=w, seconds=sec, leg=leg); save()
                    subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
                    subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
                    with open(S / 'handoff-r30.log', 'a') as f:
                        f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> all: claim: {sec} s midm_scan lkick,kick leg {leg} (seed {seed2}) of n={n}, start bytes sha256 {cdig[:16]} (our certified kick find, {gap:.3e} of side vs the live bar), {cfile}\n')
                    log(f'KICK chain {n}: leg {leg} queued from the certified find {cfile.name} ({gap:.3e} vs the live bar, the leg moved {braw - meta["side"]:.3e}); {sec} s seed {seed2} on boxC worker {w}; claimed')
                except Exception as e:
                    log(f'KICK chain {n}: leg not queued ({e!r})')
            if not gap < 0: continue
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
                continue
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
            job = dict(input=f'{uid}-p.input.txt', output=f'{uid}-p.output.txt', n=n, manifest=man, certified_before=sc, flags=list(bs.POLISH),
                       chain={'mode': 'midm_scan lkick,kick, then the certified-file polish fq', 's_start': ss, 'log': []})
            (W / 'final' / f'{uid}-p.job.json').write_text(json.dumps(job))
            log(f'KICK {n} {ident}: queued certified-file polish fq {uid}-p (certified score {sc:.16g}, {gap:.3e} of side vs the live bar)')
    except Exception:
        import traceback; traceback.print_exc()
    time.sleep(30)  # r30 14:45Z: 90 -> 30 s, to claim fresh takes first
log('kfeed30 finished by deadline')
