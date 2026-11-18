"""Round 35 twoshort deep-kick screen (override 6c, 6d and 8): held rows of the round 34 a file in class n mod 4 = 1,
with the number of unprobed 900 s kicks since their current geometry.

Changes from sel34.py + sel34b.py (one script now):
 - held file round 34 a, bars 30..35, geometry change rounds 30..34, kick lines of handoff-r28..r35.
 - seeds: a line naming 'seeds [a, b]' or 'seeds a and b' counts each seed (sel34 counted such a line once).
 - twoshort's own round 34 kicks come from take-twoshort-r34/STATE.txt DONE lines that ran to the end (a claim line
   named two seeds where only one ran); twoshort lines of handoff-r34 are not read.
 - byte check (sel34b): a line counts only when a csv it names holds the held round 34 a geometry of n, or when it
   names no readable csv.
Order (lesson 6c): rows with exactly one unprobed kick since their geometry first (one seed, their second), then rows
with none (two seeds), each by board gap. Rows with two or more are done. Writes sel35.json."""
import csv, json, math, re, sys
from pathlib import Path
csv.field_size_limit(1 << 30)
B = Path('$SCRATCH/bounties-squares')
R = Path('results')
bars = {}
for k in (30, 31, 32, 33, 34, 35):
    bars[k] = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(B / f'round{k}-briefs/bar{k}.tsv'), delimiter='\t')}
bar = bars[35]
OUT = {639, 691, 745, 858, 918, 980}
LATTICE = {626, 677, 678, 730, 731, 785, 786, 842, 843, 901, 902, 962, 963, 964}
HELD = B / 'gather/round34-2026-11-17a.csv'
rows = {}
for r in csv.DictReader(open(HELD)):
    rows.setdefault(int(r['n']), []).append(r)
def tkey(p):
    return int(re.match(r'round(\d+)', p.name)[1])
last = {}
for t in sorted(R.glob('round*-best-*.tsv'), key=tkey):
    for r in csv.DictReader(open(t), delimiter='\t'):
        try: last[int(r['n'])] = (t.name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError, TypeError): pass
gap = {}
for r in csv.DictReader(open(B / 'main-r17/gap-by-n.tsv'), delimiter='\t'):
    n = int(r['n']); gap[n] = ((bar[n] + 1) * math.sqrt(n) - float(r['board_L'])) / math.sqrt(n)
fr = {}
for n, b in bar.items():
    s = (b + 1) * math.sqrt(n); fr.setdefault(round(s - math.floor(s), 8), []).append(n)
def lattice(rs):
    tilt = []
    for r in rs:
        a = math.degrees(float(r['angle'])) % 90.0
        if min(a, 90 - a) > 1e-6: tilt.append(a)
    return bool(tilt) and all(abs(a - 45.0) < 1e-6 for a in tilt)
def changed_round(n):
    for k in (34, 33, 32, 31, 30):
        if bars[k + 1][n] < bars[k][n] - 1e-15: return k
    return None
certt = {}
for k in (30, 31, 32, 33, 34):
    for line in open(B / f'handoff-r{k}.log', errors='replace'):
        m = re.match(r'(\S{19})\S* (\S+) -> .*certified n=(\d+)', line, re.I)
        if m: certt[(k, int(m[3]))] = m[1]
def probe_vals(line):
    return [int(x) for t in re.findall(r'probe\s*=?\s*(\d+)|(\d+)\s*s probe', line) for x in t if x]
def seeds_of(line):
    m = re.search(r'seeds\s*\[([\d,\s]+)\]', line)
    if m: return [x.strip() for x in m[1].split(',') if x.strip()]
    m = re.search(r'seeds\s+(\d+)((?:\s*(?:,|and)\s*\d+)*)', line)
    if m: return [m[1]] + re.findall(r'\d+', m[2])
    m = re.search(r'seed\s*=?\s*(\d+)', line)
    return [m[1]] if m else []
def key(rs):
    out = []
    for r in rs:
        a = float(r['angle']); a = math.degrees(a) % 90.0 if abs(a) <= 7 else a % 90.0
        out.append((round(float(r['x']), 7), round(float(r['y']), 7), round(a, 6)))
    return sorted(out)
HK = {}
def same(n, p):
    try: rs = [r for r in csv.DictReader(open(p)) if r.get('n', str(n)) == str(n)]
    except Exception: return None
    if len(rs) != n: return None
    if n not in HK: HK[n] = key(rows[n])
    a, b = key(rs), HK[n]
    return all(abs(x[0] - y[0]) < 1e-6 and abs(x[1] - y[1]) < 1e-6 and abs(x[2] - y[2]) < 1e-4 for x, y in zip(a, b))
kicks = {}   # n -> list of dict(k, t, lane, seed, probed, paths)
for k in (28, 29, 30, 31, 32, 33, 34, 35):
    p = B / f'handoff-r{k}.log'
    if not p.exists(): continue
    for line in open(p, errors='replace'):
        if not re.search(r'\b900\s*-?s\b|900s|seconds=900', line): continue
        if not re.search(r'claim|start', line, re.I) or re.search(r'certified', line, re.I): continue
        m = re.match(r'(\S{19})\S* (\S+) ->', line)
        if not m: continue
        if k == 34 and m[2] == 'twoshort': continue
        prb = any(v > 0 for v in probe_vals(line))
        sd = seeds_of(line) or [line[:120]]
        paths = re.findall(r'($SCRATCH/bounties-squares/\S+?\.csv)', line)
        for n in set(int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)):
            for s in sd:
                kicks.setdefault(n, []).append(dict(k=k, t=m[1], lane=m[2], seed=s, probed=prb, paths=paths[:3]))
# twoshort round 34 own kicks: DONE lines that ran to the end (QUEUE line gives the start; held round 33 a)
q34 = {}
for line in open(B / 'take-twoshort-r34/STATE.txt', errors='replace'):
    m = re.search(r'DONE (deep34-(\d+)-\w+) seed (\d+) n=\d+ moved \S+ of side in \d+ tries \((\w[\w-]*),', line)
    if m and m[4] == 'end':
        n = int(m[2]); st = B / f'take-twoshort-r34/work/starts/{n}-held33a.csv'
        kicks.setdefault(n, []).append(dict(k=34, t=line[:19], lane='twoshort', seed=m[3], probed=False, paths=[str(st)]))
out = []
for n in sorted(rows):
    if n % 4 != 1: continue
    why = None; s = (bar[n] + 1) * math.sqrt(n)
    tab = last.get(n); text = (tab[1] + ' ' + tab[2]) if tab else ''
    if n in OUT or re.search(r'prvsiyan/squares-verified-best-of-1105|CC BY-SA', text): why = 'source out'
    elif n in LATTICE or lattice(rows[n]): why = 'lattice'
    elif len(fr[round(s - math.floor(s), 8)]) >= 3: why = 'rigid closed form'
    cr = changed_round(n)
    t0 = (cr, certt.get((cr, n), '0000')) if cr else (0, '0000')
    if cr and (cr, n) not in certt: t0 = (cr + 1, '0000')
    after = [x for x in kicks.get(n, []) if (x['k'] > t0[0]) or (x['k'] == t0[0] and x['t'] >= t0[1])]
    unp, prb, rej = {}, set(), []
    for x in after:
        if x['probed']: prb.add((x['lane'], x['seed'])); continue
        if not why and gap.get(n, 0) >= 1e-7:
            v = [same(n, p) for p in x['paths']]
            if v and not any(v) and not all(y is None for y in v): rej.append((x['lane'], x['seed'], x['t'])); continue
        unp[(x['lane'], x['seed'])] = x['t']
    out.append(dict(n=n, gap=gap[n], side=s, changed=cr, since='r%s %s' % t0, unprobed=len(unp), probed=len(prb),
                    kicks=sorted('%s:%s:%s' % (a, b, t) for (a, b), t in unp.items()), other_bytes=len(rej),
                    seeds_left=max(0, 2 - len(unp)), skip=why))
A = [o for o in out if not o['skip'] and o['seeds_left'] == 1]
Bl = [o for o in out if not o['skip'] and o['seeds_left'] == 2]
A.sort(key=lambda o: -o['gap']); Bl.sort(key=lambda o: -o['gap'])
json.dump(dict(A=A, B=Bl, all=out), open(sys.argv[1], 'w'), indent=1)
print('class rows', len(out), 'skip', {w: sum(o['skip'] == w for o in out) for w in ('source out', 'lattice', 'rigid closed form')})
print('A (one unprobed kick since geometry, needs its second seed):', len(A), 'gap>=1e-6:', sum(o['gap'] >= 1e-6 for o in A), ' '.join('%d:%.1e' % (o['n'], o['gap']) for o in A[:40]))
print('B (no unprobed kick since geometry):', len(Bl), 'gap>=1e-6:', sum(o['gap'] >= 1e-6 for o in Bl), ' '.join('%d:%.1e' % (o['n'], o['gap']) for o in Bl[:40]))
print('done (two or more):', sum(1 for o in out if not o['skip'] and o['seeds_left'] == 0))
