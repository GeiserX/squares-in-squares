"""r34: held rows of the round 33 a file (bar34) for border's deep-kick class n mod 4 = 0 (round 34 brief items 6c, 6d, 8).
Writes held34/<n>.csv (the submitted bytes of that n), held34/<n>.csv.json (a short record that points at the results
table row) and held34/info.json.
Screen (lesson 6d): a held row of n mod 4 = 0 is a candidate when fewer than two unprobed 900 s kicks were claimed for its
n since its current geometry, it is not one of the 14 known lattice n or another pure 45-degree row, its side fraction is
not shared by 3 or more n (a closed form), and its recorded source names none of the out sources.
Current geometry: the first round r (27 to 34) from which every roundK-briefs/barK.tsv up to bar34 holds the same score
for n (equal within 1e-15). A row equal in all of them is older than round 27: then every handoff log from r20 counts.
Kicks: the distinct claim lines (lane, n, seed) in handoff-r<since>.log to handoff-r33.log that name the n, a 900 s run,
and no probe of 1 s or more (lesson 6c: a probed kick line is not a deep kick).
Order: list 1 holds rows with a board gap of 1e-5 of score or more, largest gap first. List 2 (for idle slots, lesson 6d)
holds rows of 3e-6 to 1e-5 of gap with fewer than two kicks, then rows of list-1 gap with two or more kicks (a third seed),
largest gap first."""
import csv, json, math, re, hashlib
from pathlib import Path
csv.field_size_limit(1 << 30)
S = Path('$SCRATCH/bounties-squares'); W = S / 'take-border-r34/work'; H = W / 'held34'; H.mkdir(exist_ok=True)
R = Path('results')
SUB = S / 'gather/round33-2026-11-17a.csv'
subsha = hashlib.sha256(SUB.read_bytes()).hexdigest()
bars = {}
for k in range(27, 35):
    bars[k] = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / f'round{k}-briefs/bar{k}.tsv'), delimiter='\t')}
bar = bars[34]
rows = {}
for r in csv.DictReader(open(SUB)):
    rows.setdefault(int(r['n']), []).append(r)
tables = sorted(R.glob('round*-best-*.tsv'), key=lambda p: int(re.match(r'round(\d+)', p.name)[1]))
last = {}
for t in tables:
    for r in csv.DictReader(open(t), delimiter='\t'):
        try: last[int(r['n'])] = (t.name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError): pass
LATTICE = {626, 677, 678, 730, 731, 785, 786, 842, 843, 901, 902, 962, 963, 964}
OUT = {639, 691, 745, 858, 918, 980}
since = {}
for n in bar:
    r = 34
    while r > 27 and abs(bars[r - 1].get(n, -1) - bar[n]) <= 1e-15: r -= 1
    since[n] = r if r > 27 or abs(bars[27].get(n, -1) - bar[n]) > 1e-15 else 20
kicks = {}   # (round, lane, n, seed) -> probed
for k in range(20, 34):
    h = S / f'handoff-r{k}.log'
    if not h.exists(): continue
    for line in open(h, errors='replace'):
        if not re.search(r'claim', line, re.I) or not re.search(r'kick', line, re.I): continue
        if not re.search(r'\b900\s*-?s\b|900s|seconds=900', line): continue
        pv = [int(x) for x in re.findall(r'probe\s*=?\s*(\d+)|(?<=\()(\d+) s probe|(\d+)\s*s probe', line) for x in x if x]
        probed = any(v > 0 for v in pv)
        lane = line.split()[1] if len(line.split()) > 1 else '?'
        sm = re.search(r'seed\s*=?\s*(\d+)', line)
        seed = sm[1] if sm else line[:16]
        for m in set(int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)):
            key = (k, lane, m, seed); kicks[key] = kicks.get(key, False) or probed
unprobed, probedc = {}, {}
for (k, lane, m, seed), pr in kicks.items():
    if m not in since or k < since[m]: continue
    d = probedc if pr else unprobed; d[m] = d.get(m, 0) + 1
gap = {}
for r in csv.DictReader(open(S / 'main-r17/gap-by-n.tsv'), delimiter='\t'):
    n = int(r['n']); side = (bar[n] + 1) * math.sqrt(n); gap[n] = (side - float(r['board_L'])) / math.sqrt(n)
fr = {}
for n, b in bar.items():
    s = (b + 1) * math.sqrt(n); fr.setdefault(round(s - math.floor(s), 8), []).append(n)
def lattice(rs):
    tilt = []
    for r in rs:
        a = math.degrees(float(r['angle'])) % 90.0
        if min(a, 90 - a) > 1e-6: tilt.append(a)
    return bool(tilt) and all(abs(a - 45.0) < 1e-6 for a in tilt)
info = {}
for n in sorted(rows):
    tab = last.get(n); text = (tab[1] + ' ' + tab[2]) if tab else ''
    bad = n in OUT
    s = (bar[n] + 1) * math.sqrt(n)
    rigid = len(fr[round(s - math.floor(s), 8)]) >= 3
    lat = n in LATTICE or lattice(rows[n])
    info[n] = dict(table=tab[0] if tab else None, gap=gap.get(n), rigid=rigid, bad=bad, lattice=lat, since=since[n],
                   unprobed=unprobed.get(n, 0), probed=probedc.get(n, 0), changed33=since[n] == 34, mine=n % 4 == 0,
                   names1105=bool(re.search(r'prvsiyan/squares-verified-best-of-1105', text)))
    out = H / f'{n}.csv'
    with open(out, 'w') as f:
        w = csv.writer(f); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in rows[n]: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    src = (f'held n = {n} of round 33 a (the submitted packing gather/round33-2026-11-17a.csv, sha256 {subsha}, gate '
           f'gate/cand-round33-1117a, bar34 source "held round33-2026-11-17a"; a row of a file we submitted is our own layout, '
           f'round 34 override 2); its source and licence: the row of n = {n} in results/{tab[0]}' if tab else
           f'held n = {n} of round 33 a (gather/round33-2026-11-17a.csv, sha256 {subsha}); no results/round*-best table holds n = {n}: its row is older than round 7, see the held-file chain')
    lic = (f'own layout (held row); upstream as results/{tab[0]} records' if tab else 'own layout (held row)')
    Path(str(out) + '.json').write_text(json.dumps(dict(source=src, licence=lic, n=n, sha256=hashlib.sha256(out.read_bytes()).hexdigest(), held_file=str(SUB), held_sha256=subsha)))
(H / 'info.json').write_text(json.dumps(info))
def ok(v): return v['mine'] and v['gap'] is not None and not (v['rigid'] or v['bad'] or v['lattice'] or v['names1105'])
list1 = sorted((-v['gap'], n) for n, v in info.items() if ok(v) and v['gap'] >= 1e-5 and v['unprobed'] < 2)
list2 = (sorted((-v['gap'], n) for n, v in info.items() if ok(v) and 3e-6 <= v['gap'] < 1e-5 and v['unprobed'] < 2)
         + sorted((-v['gap'], n) for n, v in info.items() if ok(v) and v['gap'] >= 1e-5 and v['unprobed'] >= 2))
(H / 'lists.json').write_text(json.dumps(dict(list1=[n for _, n in list1], list2=[n for _, n in list2])))
mine = [v for v in info.values() if v['mine']]
print('held rows', len(rows), 'n mod 4 = 0:', len(mine), 'rigid', sum(v['rigid'] for v in mine), 'lattice', sum(v['lattice'] for v in mine),
      'names 1105', sum(v['names1105'] for v in mine), 'changed in round 33 a', sum(v['changed33'] for v in mine),
      'with gap >= 1e-5', sum(1 for v in mine if v['gap'] and v['gap'] >= 1e-5))
print('list 1 (gap >= 1e-5, < 2 unprobed 900 s kicks since current geometry):', len(list1))
print(' '.join(f"{n}:{-g:.2e}:k{info[n]['unprobed']}:s{info[n]['since']}" for g, n in list1))
print('list 2:', len(list2)); print(' '.join(f"{n}:{-g:.2e}:k{info[n]['unprobed']}" for g, n in list2[:40]))
