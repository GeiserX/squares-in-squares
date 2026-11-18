"""r37 feeder (brief items 6b, 6c, 6q, 8): fresh rows of other lanes first, then k123 near donors under rule 6c.
Fresh row = a take-*-r37/<n>.csv of another lane whose take.tsv row is below bar37 by more than 1e-10 and is the lowest live
row of its n. Stage A: a 180 s invent_rest.py lkick follow on the boxA follow worker (kqf, worker 6). Stage B: the first
unprobed 900 s midm_scan lkick,kick seed on a free remote slot, from the lowest live row of the n at queue time. Both count
only claims made after the row appeared (kfeed37 claim_ok since=), so the producer's earlier kick claims do not block them.
Donors (rule 6c, round 36: 1 of 77 donor kicks paid, 698 at held share 0.125): held share at 1e-3 under 0.5 (heldshare37,
the held round 36 b row), room > 0, no seed claimed on the donor's sha by any lane in rounds 36 and 37 (one seed per donor
geometry), no seeded or claimed donor at the n within 1e-9 of score of it (same geometry), no donor kick at the n that fell
back to the bar this round (certified find within 5e-9 of side of the live bar), at least 1e-6 of score above the bar (r36:
12 of 12 donors within 1e-6 fell back), ranked by room * (1 - share). One job per n in flight; no extra seed."""
import csv, glob, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path
W = Path(__file__).parent; T = W.parent; S = T.parent
END = float((W / 'deadline').read_text())
P = str(S / 'venv/bin/python'); LANE = '.'
INST = [('kq', '12'), ('kqs', '3'), ('kqm', '45')]
FOLLOW = ('kqf', '6')
SEC = 900
sys.path.insert(0, str(W)); import heldshare37 as hs
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
def walk(path, sha):
    out = W / 'walks' / f'{sha[:16]}.json'
    if out.exists():
        try: return json.loads(out.read_text())
        except ValueError: pass
    code = f"import sys,json;sys.path.insert(0,{LANE!r});import quench_walk as q;r=q.check({path!r},cap=3000);print(json.dumps(r))"
    r = subprocess.run([P, '-c', code], capture_output=True, text=True, timeout=1800, cwd=LANE)
    try: j = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception: j = {'clean': False, 'error': (r.stderr or '')[-300:]}
    j = {k: j.get(k) for k in ('clean', 'capped', 'files', 'hits', 'error')}
    out.write_text(json.dumps(j)); return j
def pending(D, w):
    try: idx = json.load(open(W / D / 'index.json'))
    except (OSError, ValueError): idx = {}
    try: done = set(json.load(open(W / D / 'done.json')))
    except (OSError, ValueError): done = set()
    busy = [v for k, v in idx.items() if k not in done and not v.get('skipped') and str(v.get('w')) == w]
    queued = [json.load(open(q)) for q in (W / D / 'manual').glob('*.json')] if (W / D / 'manual').exists() else []
    queued = [m for m in queued if str(m.get('w')) == w]
    return busy, queued, idx, done
def seeds_by_sha():
    """sha prefixes named by any 900 s or 180 s claim line of any lane in rounds 36 and 37 (one seed per geometry)."""
    c = {}
    for h in ('handoff-r36.log', 'handoff-r37.log'):
        if not (S / h).exists(): continue
        for line in open(S / h, errors='replace'):
            if not re.search(r'claim', line, re.I) or re.search(r'release', line, re.I): continue
            if not re.search(r'\b900\b|900 s|900s', line): continue
            for sh in set(x[:12] for x in re.findall(r'\b([0-9a-f]{12,64})\b', line)):
                c[sh] = c.get(sh, 0) + 1
    return c
def ts(line):
    import datetime
    try: return datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
    except (ValueError, IndexError): return None
def other_claims(n, since, win=1200):
    """claim lines of other lanes naming n, made after `since` and within the last `win` s"""
    now = time.time(); out = []
    for line in open(S / 'handoff-r37.log', errors='replace'):
        if ' border -> ' in line or not re.search(r'claim', line, re.I): continue
        if re.search(r'release', line, re.I): continue
        t = ts(line)
        if t is None or now - t > win or t < since - 5: continue
        if n in {int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)} or re.search(rf'/{n}\.csv\b|/{n}-', line): out.append(line.rstrip())
    return out
def recent_other_claims(win=1200):
    out = set(); now = time.time()
    for line in open(S / 'handoff-r37.log', errors='replace'):
        if ' border -> ' in line or not re.search(r'claim', line, re.I): continue
        t = ts(line)
        if t is not None and now - t <= win: out |= {int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)}
    return out
def live_rows():
    """n -> (score, path, lane, mtime) of the lowest live take row of each n in every take-*-r37 dir (ours included)."""
    live = {}
    for t in glob.glob(str(S / 'take-*-r37/take.tsv')):
        d = Path(t).parent
        try: rows = list(csv.DictReader(open(t), delimiter='\t'))
        except OSError: continue
        for r in rows:
            try: n = int(r['n']); sc = float(r['new'])
            except (ValueError, KeyError, TypeError): continue
            p = d / f'{n}.csv'
            if not p.exists(): continue
            if n not in live or sc < live[n][0]:
                live[n] = (sc, str(p), d.name.removeprefix('take-').removesuffix('-r37'), p.stat().st_mtime)
    return live
def fellback():
    """n where one of our donor kicks this round ended within 5e-9 of side of the live bar (fell back to the held geometry)."""
    donors = set()
    for D, _ in INST:
        try: donors |= {k[:9] for k, v in json.load(open(W / D / 'index.json')).items() if v.get('donor')}
        except (OSError, ValueError): pass
    out = set()
    try:
        for line in open(T / 'STATE.txt', errors='replace'):
            m = re.search(r' KICK (\d+) ([0-9a-f]{9})\S*: raw find .*?certified side [\d.]+, ([-+\d.e]+) vs the live bar', line)
            if m and m[2] in donors and abs(float(m[3])) < 5e-9: out.add(int(m[1]))
    except OSError: pass
    return out
def queue(D, w, mj, name):
    (W / D / 'manual').mkdir(parents=True, exist_ok=True)
    tmp = W / D / 'manual' / f'.{name}.tmp'; tmp.write_text(json.dumps(mj)); tmp.replace(W / D / 'manual' / f'{name}.json')
FS = W / 'rank' / 'fresh_seen.json'   # r37 04:25Z: kept across restarts (a restart re-followed 793 dcd4f955 twice)
fresh_seen = json.load(open(FS)) if FS.exists() else {}
SH = W / 'rank' / 'share.json'
share = json.load(open(SH)) if SH.exists() else {}
done_shas = set(); last_rank = 0; rows = []
while time.time() < END - 1500:
    try:
        bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / 'round37-briefs/bar37.tsv'), delimiter='\t')}
        live = live_rows(); claims = seeds_by_sha()
        inflight = set(); state = {}
        for D, ws in INST + [FOLLOW]:
            for w in ws:
                busy, man, idx, done = pending(D, w); state[(D, w)] = (busy, man)
                inflight |= {v['n'] for v in busy} | {m['n'] for m in man}
                for v in idx.values(): done_shas.add(v.get('sha256', '')[:12])
        free = [(D, w) for D, ws in INST for w in ws if not state[(D, w)][0] and not state[(D, w)][1]]
        ffree = not state[FOLLOW][0] and not state[FOLLOW][1]
        # ---- fresh rows of other lanes (rule 6b): stage A follow, stage B first 900 s seed
        for n, (sc, path, lane, mt) in sorted(live.items(), key=lambda kv: kv[1][0] - bar.get(kv[0], 9)):
            if lane == 'border' or not sc < bar.get(n, -9) - 1e-10: continue
            data = open(path, 'rb').read(); full = hashlib.sha256(data).hexdigest(); key = f'{n}-{full[:12]}'
            st = fresh_seen.setdefault(key, {'A': None, 'B': None, 't': time.time(), 'mt': mt})
            if st['A'] is None and st['B'] is None and time.time() - st['mt'] > 2400: continue   # r37: by the row's file time
            if st['A'] is None:
                if ffree and n not in inflight:
                    oc = other_claims(n, st['mt'])
                    if oc and any('180' in l or 'follow' in l for l in oc): st['A'] = 'other'; log(f'FRESH {n} {lane} {full[:12]}: follow already claimed by another lane ({oc[0][:90]})')
                    else:
                        wk = walk(path, full)
                        if not wk.get('clean'):
                            # r37 03:15Z: a refusal may come from a record the producer fixes later (quench 683, relative path): retry in 600 s
                            if st.get('wt', 0) == 0: log(f'FRESH skip {n} {lane} {full[:12]}: walk not clean ({str(wk)[:300]}); retry in 600 s')
                            if time.time() - st.get('wt', time.time()) > 600:
                                (W / 'walks' / f'{full[:16]}.json').unlink(missing_ok=True); st['wt'] = time.time()
                            st.setdefault('wt', time.time()); continue
                        queue(*FOLLOW, dict(path=path, n=n, seconds=180, seed=11, w=FOLLOW[1], probe=0, tool='invent_rest', modes='lkick', extra=0, fresh=True, claim_since=st['mt'],
                                            why=f'first 180 s follow of the fresh certified row of {lane} ({bar[n] - sc:.3e} of score below bar37; brief 6b)'), f'{n}-fresh-{full[:12]}-f')
                        st['A'] = 'queued'; ffree = False; inflight.add(n)
                        log(f'FRESH queue follow {n} {lane} {full[:12]} ({bar[n] - sc:.3e} below bar37) -> kqf worker 6, 180 s invent_rest lkick seed 11')
                continue   # stage B waits for stage A (ours or another lane's) to have started
            if st['B'] is None and free and n not in inflight and time.time() < END - 3000:   # no 900 s seed after 05:55Z: its find could not be walked by the take deadline
                if claims.get(full[:12], 0) > 0: st['B'] = 'other'; log(f'FRESH {n} {lane} {full[:12]}: a 900 s seed is already claimed on its sha'); continue
                oc = [l for l in other_claims(n, st['mt']) if '900' in l]
                if oc: st['B'] = 'other'; log(f'FRESH {n} {lane} {full[:12]}: 900 s seed claimed by another lane ({oc[0][:90]})'); continue
                wk = walk(path, full)
                if not wk.get('clean'): st['B'] = 'walk'; continue
                D, w = free.pop(0); seed = (int(full[:6], 16) + 3797) % 10000
                queue(D, w, dict(path=path, n=n, seconds=SEC, seed=seed, w=w, probe=0, extra=0, fresh=True, claim_since=st['mt'],
                                 why=f'first unprobed 900 s seed of the fresh certified row of {lane} ({bar[n] - sc:.3e} of score below bar37; brief 6b), walked clean (quench_walk cap 3000: files {wk.get("files")}, capped {wk.get("capped")})'),
                      f'{n}-fresh-{full[:12]}-s')
                st['B'] = 'queued'; inflight.add(n)
                log(f'FRESH queue seed {n} {lane} {full[:12]} -> {D} worker {w}, 900 s midm_scan lkick,kick seed {seed}')
        FS.write_text(json.dumps(fresh_seen))
        # ---- donors (rule 6c)
        if time.time() - last_rank > 600:
            subprocess.run([P, str(W / 'rank37.py')], check=False, timeout=900); last_rank = time.time()
            rows = list(csv.DictReader(open(W / 'rank/donors.tsv'), delimiter='\t'))
            rows = [r for r in rows if float(r['room']) > 0 and 1e-8 <= float(r['above']) and not (float(r['above']) >= 1e-4 and float(r['room']) < 1e-4)]
            for r in rows:
                if r['sha16'] not in share:
                    try: share[r['sha16']] = hs.share(r['path'], int(r['n']))[1][0]
                    except Exception as e: share[r['sha16']] = 1.0
            SH.write_text(json.dumps(share))
            rows = sorted(rows, key=lambda r: -float(r['room']) * (1 - share.get(r['sha16'], 1.0)))
        if not free: time.sleep(20); continue
        other = recent_other_claims(); fb = fellback()
        geo = {}
        nseeded = {}
        for D_, _ in INST:
            try:
                for v in json.load(open(W / D_ / 'index.json')).values():
                    if v.get('donor'): nseeded[v['n']] = nseeded.get(v['n'], 0) + 1
            except (OSError, ValueError): pass
        for r in rows:
            if claims.get(r['sha16'][:12], 0) > 0 or r['sha16'][:12] in done_shas: geo.setdefault(int(r['n']), []).append(float(r['above']))
        for D, w in (list(free) if time.time() < END - 3000 else []):
            for r in rows:
                room, n, above, sha = float(r['room']), int(r['n']), float(r['above']), r['sha16']
                sh = share.get(sha, 1.0)
                if float(r['above']) < 1e-6 and sh >= 0.3: continue   # r37: near-bar donors only when clearly another geometry (r36: 12 of 12 within 1e-6 fell back)
                if sum(1 for a in geo.get(n, []) if a is not None) >= 2 and sha[:12] not in done_shas and nseeded.get(n, 0) >= 2: continue   # r37 04:40Z: at most two donor geometries per n this round
                if n in (965, 448, 367, 807): continue   # rebuild r36 next 1: strong local minima of the held row (r37: 367 donor b2c71588 fell back)
                if sh >= 0.5 or n in inflight or n in other or n in fb or sha[:12] in done_shas: continue
                if claims.get(sha[:12], 0) > 0: continue
                if any(abs(above - a) < 2e-8 for a in geo.get(n, [])): continue   # r37 04:15Z: 1e-9 -> 2e-8 (910 k123 variants 5e-9 apart are one geometry)
                if n in live and live[n][0] < bar[n] - 1e-6: continue
                path = r['path']; data = open(path, 'rb').read(); full = hashlib.sha256(data).hexdigest()
                wk = walk(path, full)
                if not wk.get('clean'):
                    log(f'DFEED skip {n} {sha}: walk not clean ({str(wk)[:300]})'); done_shas.add(sha[:12]); continue
                seed = (int(full[:6], 16) + 37 * 97) % 10000
                why = (f'near donor under rule 6c: held share at 1e-3 {sh:.3f} (heldshare37 vs the held round 36 b row), room {room:.3e} of score (board gap {float(r["boardgap"]):.3e} minus donor {above:.3e} above bar37), '
                       f'no seed claimed on its sha in rounds 36 and 37, no same-geometry donor seeded at n, no fallback at n this round, walked clean (quench_walk cap 3000: files {wk.get("files")}, capped {wk.get("capped")}); one seed')
                queue(D, w, dict(path=path, n=n, seconds=SEC, seed=seed, w=w, probe=0, why=why, extra=0, donor=True), f'{n}-donor-{sha[:12]}')
                log(f'DFEED queue {n} {sha} share {sh:.3f} room {room:.3e} above {above:.3e} key {room * (1 - sh):.3e} -> {D} worker {w} seed {seed}')
                inflight.add(n); done_shas.add(sha[:12]); geo.setdefault(n, []).append(above); free.remove((D, w)); break
        # ---- idle slots (rule 6d): held rows of round 36 b that no handoff line of rounds 34 to 37 names, not closed form
        # (build_held37 rigid/lattice screens), board gap 3e-6 or more, largest gap first, one 900 s seed each.
        try: idle = json.load(open(W / 'rank' / 'idle_held.json'))
        except (OSError, ValueError): idle = []
        hdone = set(json.load(open(W / 'rank' / 'idle_done.json'))) if (W / 'rank' / 'idle_done.json').exists() else set()
        for D, w in (list(free) if time.time() < END - 3000 else []):
            if (D, w) not in free: continue
            for n in idle:
                if n in hdone or n in inflight or n in other or (n in live and live[n][0] < bar[n] - 1e-10): continue
                if other_claims(n, 0, win=10**7): hdone.add(n); continue   # a claim of any lane this round names it
                path = str(W / 'held37' / f'{n}.csv'); full = hashlib.sha256(open(path, 'rb').read()).hexdigest()
                seed = (int(full[:6], 16) + 3737) % 10000
                queue(D, w, dict(path=path, n=n, seconds=SEC, seed=seed, w=w, probe=0, extra=0,
                                 why='idle slot, rule 6d: held row of round 36 b (our own layout) that no handoff line of rounds 34 to 37 names, not closed form; one seed'), f'{n}-held-{full[:12]}')
                log(f'IDLE queue held {n} {full[:12]} -> {D} worker {w} seed {seed}')
                hdone.add(n); inflight.add(n); free.remove((D, w)); break
        (W / 'rank' / 'idle_done.json').write_text(json.dumps(sorted(hdone)))
    except Exception:
        import traceback; traceback.print_exc()
    time.sleep(20)
log('dfeed37 finished (no new job after the deadline minus 420 s)')
