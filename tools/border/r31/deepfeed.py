"""r31 21:30Z: depth feeder for boxC worker 2. One unprobed 900 s midm_scan lkick,kick per held row, largest board gap
first (held31/info.json gap, side fraction not shared by 3 or more n, excluded counts out), only where no r31 take is
below the held side (bars.json) and no other lane claimed n in handoff-r31.log in the last 60 minutes. It writes one
kq/manual/<n>-deep.json at a time when worker 2 has no pending job; kfeed31.py pins, claims, runs and publishes it.
Why: 40% of the kicks of rounds 28 to 31 that moved 1e-6 or more of side made their first find after 120 s (a probe
stops them), and the 494 seeds that paid found at 324 s and later."""
import json, time, re, datetime, math, csv
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent; T = W.parent
END = float((W / 'deadline').read_text())
info = {int(k): v for k, v in json.load(open(W / 'held31/info.json')).items()}
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
def side_of(p):
    xs = []
    for r in csv.DictReader(open(p)):
        a = float(r['angle']); h = .5 * (abs(math.cos(a)) + abs(math.sin(a))); xs.append((float(r['x']), float(r['y']), h))
    return max(max(x + h for x, y, h in xs) - min(x - h for x, y, h in xs), max(y + h for x, y, h in xs) - min(y - h for x, y, h in xs))
done = set(); SKIP = {639, 691, 745, 858, 918, 980, 494}
while time.time() < END - 1500:
    try:
        ix = json.load(open(W / 'kq/index.json')); dn = set(json.load(open(W / 'kq/done.json')))
        pend = [k for k, v in ix.items() if k not in dn and str(v.get('w', '2')) == '2']
        if pend or list((W / 'kq/manual').glob('*.json')): time.sleep(30); continue
        L = {int(k): v for k, v in json.load(open(W / 'bars.json')).items()}
        recent = set()
        for line in open(S / 'handoff-r31.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'kick|claim', line, re.I): continue
            try: t = datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
            except ValueError: continue
            if time.time() - t < 3600: recent.update(int(m[1]) for m in re.finditer(r'\bn\s*=\s*(\d+)', line))
        mine = {v['n'] for v in ix.values() if v.get('probe', 1) == 0}
        cands = sorted(((v['gap'], n) for n, v in info.items() if v['gap'] and v['gap'] >= 1e-5 and not v['rigid'] and not v['bad'] and n not in SKIP and n not in done and n not in mine and n not in recent), reverse=True)
        for g, n in cands:
            p = W / 'held31' / f'{n}.csv'
            if side_of(p) > L[n] + 1e-9: done.add(n); continue    # a lane holds a lower row of n: its take is the start, backlog follows it
            seed = 3100 + n
            (W / 'kq/manual' / f'{n}-deep.json').write_text(json.dumps(dict(path=str(p), n=n, seconds=900, seed=seed, w='2', probe=0, modes='lkick,kick', extra=0,
                why=f'depth kick: held row of the round 30 c file, board gap {g:.2e} of score, no probe (40% of paying kicks find after 120 s)')))
            done.add(n); log(f'DEEP queue {n} (board gap {g:.2e} of score) as kq/manual/{n}-deep.json for worker 2')
            break
    except Exception as e:
        log(f'DEEP error {e!r}')
    time.sleep(30)
log('deepfeed finished (no new deep kick after 23:50Z)')
