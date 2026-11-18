"""r34: held-row deep-kick feeder for both boxC workers, border's class n mod 4 = 0 (round 34 brief items 6c, 6d, 8).
Rows come from held34/lists.json (build_held34.py): list 1 = held rows of the round 33 a file with a board gap of 1e-5 of
score or more and fewer than two unprobed 900 s kicks since their current geometry, largest gap first; list 2 for idle
slots. Each row gets 900 s midm_scan lkick,kick with no probe; a row with no such kick yet gets extra=1 (kfeed34.py gives
it the second seed when the first is dry), a row with one gets one seed. A row is skipped when another lane claimed a
900 s kick of its n this round, or when a live r34 take is below the held side (that take is the lowest live row; lesson
6e). It writes kq/manual/<n>-deep.json for a worker that has no pending job; kfeed34.py claims (lesson 6f), pins, runs,
certifies, chains and publishes it."""
import json, time, re, datetime, math, csv, os
from pathlib import Path
W = Path(__file__).parent; S = W.parent.parent; T = W.parent
END = float((W / 'deadline').read_text())
info = {int(k): v for k, v in json.load(open(W / 'held34/info.json')).items()}
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
import hashlib
HSHA = {int(n): hashlib.sha256((W / 'held34' / f'{n}.csv').read_bytes()).hexdigest()[:12] for n in info}
lists = json.load(open(W / 'held34/lists.json'))
cands = [(1, False, -info[n]['gap'], n) for n in lists['list1'] if n not in SKIP] + [(2, False, -info[n]['gap'], n) for n in lists['list2'] if n not in SKIP]
log(f'DEEP feeder start: {len(cands)} held rows in order, first 12: ' + ' '.join(str(c[3]) for c in cands[:12]))
while time.time() < END - 1500:
    try:
        ix = json.load(open(W / 'kq/index.json')) if (W / 'kq/index.json').exists() else {}
        dn = set(json.load(open(W / 'kq/done.json'))) if (W / 'kq/done.json').exists() else set()
        L = {int(k): v for k, v in json.load(open(W / 'bars.json')).items()}
        recent = set()
        for line in open(S / 'handoff-r34.log', errors='replace'):
            if ' border -> ' in line or not re.search(r'kick|claim', line, re.I): continue
            try: t = datetime.datetime.fromisoformat(line.split()[0].replace('Z', '+00:00')).timestamp()
            except ValueError: continue
            if re.search(r'claim', line, re.I) and re.search(r'\b900\s*s|900s', line):
                # r34 04:15Z: only a claim of the held row itself (its sha256 prefix, its held34 path, or the word held) closes it;
                # invent's 900 s claims of fresh joins at 448 and 492 kept two held rows of border's list idle
                for m in re.finditer(r'\bn\s*=\s*(\d+)', line):
                    k = int(m[1])
                    if k in HSHA and (HSHA[k] in line or f'held34/{k}.csv' in line or re.search(r'\bheld\b', line)): recent.add(k)   # r34: any 900 s claim of the n this round closes it for us
        mine = {v['n'] for v in ix.values()}
        waiting = [json.load(open(m)).get('w') for m in (W / 'kq/manual').glob('*.json')]
        for w in WORKERS:
            pend = [k for k, v in ix.items() if k not in dn and str(v.get('w', '2')) == w]
            if pend or w in waiting: continue
            handed = set(json.load(open(W / 'handed.json'))) if (W / 'handed.json').exists() else set()   # r34 03:10Z: rows handed to classfill
            for full, probed, g, n in cands:
                if n in done or n in mine or n in handed: continue
                if n in recent: continue                      # another lane claimed this n in the last hour; look again later
                p = W / 'held34' / f'{n}.csv'
                if side_of(p) > L[n] + 1e-9:
                    done.add(n); log(f'DEEP skip {n}: a live r34 take is below the held side (that take is the start; backlog follows it)'); continue
                seed = (3400 + 7 * n) % 10000; k = info[n]['unprobed']; extra = 1 if k == 0 else 0
                (W / 'kq/manual' / f'{n}-deep.json').write_text(json.dumps(dict(path=str(p), n=n, seconds=900, seed=seed, w=w, probe=0, modes='lkick,kick', extra=extra,
                    why=f'deep kick of border class n mod 4 = 0 (lesson 6d), list {full}: held row of the round 33 a file, board gap {-g:.2e} of score, {k} unprobed 900 s kick claims since its current geometry (round {info[n]["since"] if info[n]["since"] > 20 else "27 or older"}), not a lattice or closed-form row, no probe, ' + ('a second seed if the first is dry' if extra else 'one seed (its second)'))))
                done.add(n); waiting.append(w); log(f'DEEP queue {n} (board gap {-g:.2e} of score) as kq/manual/{n}-deep.json for worker {w}')
                break
    except Exception as e:
        log(f'DEEP error {e!r}')
    time.sleep(30)
log('deepfeed34 finished (no new first seed after the deadline minus 1500 s)')
