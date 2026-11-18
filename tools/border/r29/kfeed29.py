"""boxA feeder for 900 s midm_scan lkick,kick jobs on boxC (border r29, light python).
Why: round 28 measured that one 900 s midm_scan lkick,kick run of a fresh row or a forensics rectangle at the bar side
moved 684 by 9.0e-5, 748 by 3.1e-5 and 910 by 8.4e-6 (rebuild), while our r28 kfeed (one fq call with --kick, then a
polish) gave nothing past the slack on 36 tries. So the change from r28 is the kick loop itself (midm_scan, 900 s,
lkick and kick modes, keep the best), not more single kicked calls.
What it kicks: near files that rebuild's own follow29.py chose (within 1e-6 of the bar side, not the bar row) but could
not queue ('near skipped (queues full)' in take-rebuild-r29/work/follow.log), plus every fresh near file of another
r29 lane in our LP index within KICK_GAP of the live bar side when nothing of that kind waits. One input per n at a
time, lowest side first, inputs pinned by sha256, each claimed in handoff-r29.log before it runs; inputs that rebuild
or quench queued or claimed (by path or sha256 prefix) are skipped. Every raw find is certified with finesafe and,
when it is below the live bar, gets the certified-file polish fq as a final job with a 'kick' manifest, which the
driver publishes through the same source policy and share test as every other row."""
import os, sys, time, json, csv, math, hashlib, glob, re, subprocess
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent; T = W.parent
src = (W / 'driver.py').read_text()
src = src[:src.index("log('start round29 collector/scanner")]
src = src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)", "")
ns = {'__name__': 'border_kfeed', '__file__': str(W / 'driver.py')}; exec(compile(src, str(W / 'driver.py'), 'exec'), ns)
bs = ns['bs']; floatsafe = ns['floatsafe']; audit = ns['audit']; metadata = ns['metadata']; csvout = ns['csvout']
REMOTE = 'boxC:scratch/squares-border-r29/'
END = float((W / 'deadline').read_text())
KICK_SEC = int(os.environ.get('KICK_SEC', '900')); KICK_GAP = float(os.environ.get('KICK_GAP', '1e-6')); PENDING = int(os.environ.get('KICK_PENDING', '2')); KICK_ANY = os.environ.get('KICK_ANY') == '1'
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
    """paths and sha256 prefixes that rebuild queued or that any lane claimed for a kick in handoff-r29.log"""
    paths, shas = set(), set()
    try:
        for line in open(S / 'take-rebuild-r29/work/queue-log.tsv'):
            c = line.rstrip('\n').split('\t')
            if len(c) >= 6: paths.add(str(S / c[4]) if not c[4].startswith('/') else c[4]); shas.add(c[5][:12])
            m = re.search(r'-([0-9a-f]{8})$', c[2]) if len(c) > 2 else None
            if m: shas.add(m[1])
    except OSError: pass
    try:
        for line in open(S / 'handoff-r29.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'\bclaim', line, re.I): continue
            paths.update(re.findall(r'(/Volumes/\S+?\.csv)', line))
            shas.update(h[:12] for h in re.findall(r'sha256 ([0-9a-f]{8,64})', line))
            shas.update(h[:12] for h in re.findall(r'-([0-9a-f]{12})(?:\b|,)', line))
    except OSError: pass
    return paths, shas
def rebuild_skipped():
    out = []
    try:
        for line in open(S / 'take-rebuild-r29/work/follow.log'):
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
def candidates(L):
    lp_paths(); taken_p, taken_h = others_taken(); out = {}
    skipped = {h for _, _, h in rebuild_skipped()}
    for h12, v in lpix.items():
        p = v['path']; n = v['n']
        if '/take-border-r29/' in p or '-r29/' not in p: continue
        if p in taken_p or h12 in taken_h or h12[:8] in taken_h: continue
        if any(x['sha256'][:12] == h12 for x in index.values()): continue
        # r29 07:50Z: one kick per n unless the new input is lower than every input of that n kicked before by 1e-9 of
        # side (the stair-c 814 builds 3f995333 and 81c13e4e sit at the same side 28.9443055223010; the first kick: 20
        # tries, no find)
        if any(x.get('n') == n and not x.get('skipped') and x.get('side', 1e9) - 1e-9 <= float(v.get('side', 1e9)) for x in index.values()): continue
        try: data = Path(p).read_bytes()
        except OSError: continue
        if hashlib.sha256(data).hexdigest()[:12] != h12: continue          # rewritten since the LP feed pinned it
        m, side = side_of(p)
        if m != n or n not in L: continue
        gap = side - L[n]
        if not (gap < KICK_GAP): continue
        if h12 not in skipped and not (KICK_ANY and Path(p).stem.isdigit()): continue   # only rebuild's own picks (share filter applied there), or takes with KICK_ANY
        rank = (0 if h12 in skipped else 1, gap)
        if n not in out or rank < out[n][0]: out[n] = (rank, p, side, gap, h12 in skipped, data)
    return sorted(out.values(), key=lambda c: c[0])
while time.time() < END - 300:
    try:
        L = {int(k): v for k, v in json.load(open(W / 'bars.json')).items()}
        # r29 08:20Z: bfeed29.py writes boundary grow1 entries into index.json; merge them before this pass saves
        try: index.update({k: v for k, v in json.load(open(IX)).items() if k not in index})
        except (OSError, ValueError): pass
        pend = [i for i, v in index.items() if i not in done]
        if len(pend) < PENDING and time.time() < END - KICK_SEC - 600:
            busy = {index[i]['n'] for i in pend}
            for rank, p, side, gap, skipped, data in candidates(L):
                n = int(next(csv.DictReader(open(p)))['n'])
                if n in busy: continue
                if not audit(Path(p)): log(f'KICK skip {n} {p}: the walk refuses it'); index['x' + hashlib.sha256(data).hexdigest()[:12]] = dict(path=p, n=n, sha256=hashlib.sha256(data).hexdigest(), skipped=True); done.add('x' + hashlib.sha256(data).hexdigest()[:12]); save(); continue
                digest = hashlib.sha256(data).hexdigest(); ident = digest[:12]
                (D / 'nin' / f'{ident}_{n}.csv').write_bytes(data)
                seed = int(digest[:6], 16) % 1000
                (D / 'jobs' / f'{ident}.json').write_text(json.dumps(dict(input=f'nin/{ident}_{n}.csv', out=f'nout/{ident}_{n}', n=n, seconds=KICK_SEC, seed=seed, priority=0)))
                index[ident] = dict(path=p, n=n, sha256=digest, side=side, gap=gap, rebuild_skipped=skipped, seed=seed, t=time.time()); save()
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'nin') + '/', REMOTE + 'kq/nin/'], check=True)
                subprocess.run(['rsync', '-a', '--ignore-existing', str(D / 'jobs') + '/', REMOTE + 'kq/jobs/'], check=True)
                why = "rebuild's follow chose it and skipped it with full queues" if skipped else 'fresh near file of another lane in our LP index, nothing rebuild skipped waits'
                with open(S / 'handoff-r29.log', 'a') as f:
                    f.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + f' border -> rebuild, quench, backlog: claim: {KICK_SEC} s midm_scan lkick,kick (seed {seed}) of n={n}, start bytes sha256 {digest[:16]} ({why}; {gap:.3e} of side vs the live bar), {p}\n')
                log(f'KICK queue {n} from {p} (sha256 {digest[:16]}), side {side:.13f}, {gap:.3e} vs the live bar, {why}; {KICK_SEC} s midm_scan lkick,kick seed {seed} on boxC worker 2; claimed in handoff-r29.log; deadline 11:45Z')
                busy.add(n)
                if len([i for i in index if i not in done]) >= PENDING: break
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
    time.sleep(90)
log('kfeed29 finished by deadline')
