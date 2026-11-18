"""r36 donor feeder (brief items 6c and 8): keep every border kick slot busy with k123 near donors ranked by board room.
room = (bar36 - board, of score) - (donor - bar36), largest first; board = main-r17/gap-by-n.tsv.
A donor runs only when: room > 0; it is less than 1e-4 of score above bar36, or its room is 1e-4 or more (border r35:
803 sat 2.37e-4 above with room 2.1e-4 and paid 3.7e-4; backlog's 0 of 11 were donors 1e-4 above with less room);
fewer than two 900 s seeds claimed on its sha by any lane in handoff-r35/r36; no live r36 take at its n more than 1e-6
below bar36 (rule 6e); no other lane claimed a kick of its n in the last 1200 s (kfeed36 claim_ok re-checks after 5 s);
quench_walk.check is clean (cap 3000 here; the uncapped walk runs before a find is published). One donor per n in flight.
Jobs go to kq*/manual/ of the kfeed36 instance that owns the free worker; a dry first seed gets its second from kfeed36."""
import csv, glob, hashlib, json, math, os, re, subprocess, sys, time
from pathlib import Path
W = Path(__file__).parent; T = W.parent; S = T.parent
END = float((W / 'deadline').read_text())
P = str(S / 'venv/bin/python'); LANE = '.'
INST = [('kq', '12'), ('kqs', '3'), ('kql', '45')]
SEC = 900
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
    queued = [p for p in (W / D / 'manual').glob('*.json')] if (W / D / 'manual').exists() else []
    return busy, [json.load(open(q)) for q in queued], idx, done
def seeds_by_sha():
    c = {}
    for h in ('handoff-r35.log', 'handoff-r36.log'):
        for line in open(S / h, errors='replace'):
            if not re.search(r'claim', line, re.I) or not re.search(r'900', line): continue
            if re.search(r'release', line, re.I): continue
            for sh in set(x[:12] for x in re.findall(r'\b([0-9a-f]{12,64})\b', line)):
                c[sh] = c.get(sh, 0) + 1
    return c
def recent_other_claims(win=1200):
    import datetime
    out = set(); now = time.time()
    for line in open(S / 'handoff-r36.log', errors='replace'):
        if ' border -> ' in line or not re.search(r'claim', line, re.I) or not re.search(r'kick', line, re.I): continue
        try: t = datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
        except ValueError: continue
        if now - t <= win: out |= {int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)}
    return out
def live_r36():
    live = {}
    for t in glob.glob(str(S / 'take-*-r36/take.tsv')):
        for r in csv.DictReader(open(t), delimiter='\t'):
            try: n = int(r['n']); live[n] = min(live.get(n, 9), float(r['new']))
            except (ValueError, KeyError, TypeError): pass
    return live
done_shas = set(); last_rank = 0; rows = []
while time.time() < END - SEC - 600:
    try:
        if time.time() - last_rank > 600:
            subprocess.run([P, str(W / 'rank36.py')], check=False, timeout=900); last_rank = time.time()
            rows = list(csv.DictReader(open(W / 'rank/donors.tsv'), delimiter='\t'))
            # r36 22:15Z: band donors first (5e-6 to 3e-4 of score above bar36 with room 1e-4 or more: 698 at 3.4e-5 and r35 803 at
            # 2.4e-4 paid; 12 donors within 1e-6 of the bar this round fell back into the held geometry, -8e-10 of side), by room.
            band = lambda r: 5e-6 <= float(r['above']) <= 3e-4 and float(r['room']) >= 1e-4
            rows = [r for r in rows if band(r)] + [r for r in rows if not band(r)]
        bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / 'round36-briefs/bar36.tsv'), delimiter='\t')}
        claims = seeds_by_sha(); live = live_r36(); other = recent_other_claims()
        inflight = set()
        state = {}
        for D, ws in INST:
            for w in ws:
                busy, man, idx, done = pending(D, w); state[(D, w)] = (busy, man)
                inflight |= {v['n'] for v in busy} | {m['n'] for m in man}
                for v in idx.values(): done_shas.add(v.get('sha256', '')[:12])
        # r36 21:10Z: equal-side donors at one n are one geometry (k123 writes many variants): a donor whose side is within
        # 1e-10 of score of a donor we queued or another lane claimed counts as that geometry and is skipped.
        geo = {}
        for r in rows:
            if int(r['claims']) > 0 or r['sha16'][:12] in done_shas: geo.setdefault(int(r['n']), []).append(float(r['above']))
        for (D, w), (busy, man) in state.items():
            if busy or man or any(m.get('w') == w for m in man): continue
            for r in rows:
                room, n, above, sha = float(r['room']), int(r['n']), float(r['above']), r['sha16']
                if room <= 0: continue
                if n in inflight or sha[:12] in done_shas or n in other: continue   # r36 19:45Z: skip an n another lane claimed in the last 1200 s (10 lost claims by 19:40Z)
                if above >= 1e-4 and room < 1e-4: continue
                if above < 1e-8: continue
                if any(abs(above - a) < 1e-10 for a in geo.get(n, [])) and sha[:12] not in done_shas and claims.get(sha[:12], 0) == 0: continue   # r36 21:05Z: a copy of the held geometry (kick outputs at the bar in other near dirs) is a held-row re-kick, not a fresh donor
                used = claims.get(sha[:12], 0)
                if used >= 2: continue
                if n in live and live[n] < bar[n] - 1e-6: continue
                path = r['path']; data = open(path, 'rb').read(); full = hashlib.sha256(data).hexdigest()
                wk = walk(path, full)
                if not wk.get('clean'):
                    log(f'DFEED skip {n} {sha}: walk not clean ({wk})'); done_shas.add(sha[:12]); continue
                seed = (int(full[:6], 16) + 36 * 97 + used * 1009) % 10000
                why = (f'k123 near donor ranked by board room (brief 6c, item 8): room {room:.3e} of score (board gap {float(r["boardgap"]):.3e} minus donor {above:.3e} above bar36), '
                       f'{used} seed(s) claimed on its sha before, walked clean (quench_walk cap 3000: files {wk.get("files")}, capped {wk.get("capped")}), unclaimed n, no live r36 row below bar36; '
                       f'{"two unprobed seeds" if used == 0 else "its second unprobed seed"}')
                mj = dict(path=path, n=n, seconds=SEC, seed=seed, w=w, probe=0, why=why, extra=1 if used == 0 else 0)
                (W / D / 'manual').mkdir(exist_ok=True)
                (W / D / 'manual' / f'{n}-donor-{sha[:12]}.json').write_text(json.dumps(mj))
                log(f'DFEED queue {n} {sha} room {room:.3e} above {above:.3e} seeds-before {used} -> {D} worker {w} seed {seed}')
                inflight.add(n); done_shas.add(sha[:12]); geo.setdefault(n, []).append(above); break
    except Exception:
        import traceback; traceback.print_exc()
    time.sleep(45)
log('dfeed36 finished (no new first seed after the deadline minus 1500 s)')
