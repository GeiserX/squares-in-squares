"""r32: held-row feeder for both boxC workers (r31 next item 1). One unprobed 900 s midm_scan lkick,kick per held row of
the round 31 b file, with extra=1: kfeed32.py gives the row its second seed when the first finds nothing below its
start (or only the certify dilation, under 1e-6 of side). Order: rows that round 31 b changed and rows with no unprobed
900 s r31 kick first, then fewer r31 kick lines, then the largest board gap (held32/info.json; side fraction not shared
by 3 or more n; excluded counts and the exhausted own 494 chain out). A row is skipped when another lane named its n on
a kick or claim line of handoff-r32.log in the last 60 minutes, or when a live r32 take is below the held side (bars.json:
that lane's take is the start now, and backlog is the follow lane). It writes kq/manual/<n>-deep.json for a worker that
has no pending job; kfeed32.py pins, claims, runs, certifies, chains and publishes it.
Why: in round 31, 9 unprobed kicks of held rows (8,277 s) gave 2 n, 73 kicks with the 120 s probe (9,907 s) gave 0, and
in both paying n a second seed paid after a dry first one (494 first find at 324 s, 864 at 117 s)."""
import json, time, re, datetime, math, csv, os
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent; T = W.parent
END = float((W / 'deadline').read_text())
info = {int(k): v for k, v in json.load(open(W / 'held32/info.json')).items()}
SKIP = {639, 691, 745, 858, 918, 980, 494, 626, 677, 678, 730, 731, 842, 843, 901, 902, 962, 963, 964, 785, 786}   # r32 12:47Z main: pure 45-degree lattice rows do not move under a kick
WORKERS = os.environ.get('DEEP_WORKERS', '12')
def log(msg):
    s = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + msg
    print(s, flush=True)
    with open(T / 'STATE.txt', 'a') as f: f.write(s + '\n')
def side_of(p):
    xs = []
    for r in csv.DictReader(open(p)):
        a = float(r['angle']); h = .5 * (abs(math.cos(a)) + abs(math.sin(a))); xs.append((float(r['x']), float(r['y']), h))
    return max(max(x + h for x, y, h in xs) - min(x - h for x, y, h in xs), max(y + h for x, y, h in xs) - min(y - h for x, y, h in xs))
done = set()
cands = sorted(((v['full31'], v['probe31'] > 0, -v['gap'], n) for n, v in info.items()
                if v['gap'] and v['gap'] >= 1e-5 and not v['rigid'] and not v['bad'] and n not in SKIP))
log(f'DEEP feeder start: {len(cands)} held rows in order, first 12: ' + ' '.join(str(c[3]) for c in cands[:12]))
while time.time() < END - 1500:
    try:
        ix = json.load(open(W / 'kq/index.json')) if (W / 'kq/index.json').exists() else {}
        dn = set(json.load(open(W / 'kq/done.json'))) if (W / 'kq/done.json').exists() else set()
        L = {int(k): v for k, v in json.load(open(W / 'bars.json')).items()}
        recent = set()
        for line in open(S / 'handoff-r32.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'kick|claim', line, re.I): continue
            try: t = datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
            except ValueError: continue
            if time.time() - t < 3600: recent.update(int(m[1]) for m in re.finditer(r'\bn\s*=\s*(\d+)', line))
        mine = {v['n'] for v in ix.values()}
        waiting = [json.load(open(m)).get('w') for m in (W / 'kq/manual').glob('*.json')]
        for w in WORKERS:
            pend = [k for k, v in ix.items() if k not in dn and str(v.get('w', '2')) == w]
            if pend or w in waiting: continue
            for full, probed, g, n in cands:
                if n in done or n in mine: continue
                if n in recent: continue                      # another lane claimed this n in the last hour; look again later
                p = W / 'held32' / f'{n}.csv'
                if side_of(p) > L[n] + 1e-9:
                    done.add(n); log(f'DEEP skip {n}: a live r32 take is below the held side (that take is the start; backlog follows it)'); continue
                seed = (3200 + 7 * n) % 10000
                (W / 'kq/manual' / f'{n}-deep.json').write_text(json.dumps(dict(path=str(p), n=n, seconds=900, seed=seed, w=w, probe=0, modes='lkick,kick', extra=1,
                    why=f'depth kick: held row of the round 31 b file, board gap {-g:.2e} of score, unprobed r31 900 s kick lines {full}, ' + ('changed in round 31 b' if info[n]['changed31'] else 'unchanged since round 30 c') + ', no probe, a second seed if the first is dry')))
                done.add(n); waiting.append(w); log(f'DEEP queue {n} (board gap {-g:.2e} of score) as kq/manual/{n}-deep.json for worker {w}')
                break
    except Exception as e:
        log(f'DEEP error {e!r}')
    time.sleep(30)
log('deepfeed32 finished (no new first seed after 16:40Z)')
