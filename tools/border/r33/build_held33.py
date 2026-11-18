"""r33: held rows of the round 32 a file (bar33) for border's two unprobed 900 s seeds (round 33 brief items 6b and 8).
Writes held33/<n>.csv (the submitted bytes of that n), held33/<n>.csv.json (a short record that points at the
results table row) and held33/info.json. A row is a candidate when no lane kicked its n for 900 s without a probe in
rounds 31 and 32 (any 900 s kick or claim line of handoff-r31.log or handoff-r32.log that names the n and carries no
probe of 1 s or more), it is not one of the 15 rows border spent on two dry seeds, it is not a 45-degree lattice row
(every tilted square at 45 degrees, lesson 6c), its side fraction is not shared by 3 or more n (a closed form), and
its recorded source names none of the out sources. Order: the largest board gap first, changed and unchanged rows
together (brief item 8)."""
import csv, json, math, re, hashlib
from pathlib import Path
csv.field_size_limit(1 << 30)
S = Path('$SCRATCH/bounties-squares'); W = S / 'take-border-r33/work'; H = W / 'held33'; H.mkdir(exist_ok=True)
R = Path('results')
SUB = S / 'gather/round32-2026-11-16a.csv'
subsha = hashlib.sha256(SUB.read_bytes()).hexdigest()
bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / 'round33-briefs/bar33.tsv'), delimiter='\t')}
bar32 = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(S / 'round32-briefs/bar32.tsv'), delimiter='\t')}
rows = {}
for r in csv.DictReader(open(SUB)):
    rows.setdefault(int(r['n']), []).append(r)
tables = sorted(R.glob('round*-best-*.tsv'), key=lambda p: int(re.match(r'round(\d+)', p.name)[1]))
last = {}
for t in tables:
    for r in csv.DictReader(open(t), delimiter='\t'):
        try: last[int(r['n'])] = (t.name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError): pass
SPENT = {692, 746, 643, 341, 926, 863, 695, 686, 859, 989, 812, 416, 634, 912, 588}
LATTICE = {626, 677, 678, 730, 731, 785, 786, 842, 843, 901, 902, 962, 963, 964}
unprobed, probed = {}, {}
for h in ('handoff-r31.log', 'handoff-r32.log'):
    for line in open(S / h, errors='replace'):
        if not re.search(r'kick|claim', line, re.I) or not re.search(r'\b900\s*-?s\b|900s|seconds=900', line): continue
        pv = [int(x) for x in re.findall(r'probe\s*=?\s*(\d+)|(?<=\()(\d+) s probe|(\d+)\s*s probe', line) for x in x if x]
        has_probe = any(v > 0 for v in pv)
        for m in set(int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)):
            d = probed if has_probe else unprobed; d[m] = d.get(m, 0) + 1
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
    bad = bool(re.search(r'prvsiyan/squares-verified-best-of-1105|CC BY-SA', text)) or n in (639, 691, 745, 858, 918, 980)
    s = (bar[n] + 1) * math.sqrt(n)
    rigid = len(fr[round(s - math.floor(s), 8)]) >= 3
    lat = n in LATTICE or lattice(rows[n])
    info[n] = dict(table=tab[0] if tab else None, gap=gap.get(n), rigid=rigid, bad=bad, lattice=lat, spent=n in SPENT,
                   unprobed3132=unprobed.get(n, 0), probed3132=probed.get(n, 0), changed32=bar[n] < bar32.get(n, 0) - 1e-15)
    out = H / f'{n}.csv'
    with open(out, 'w') as f:
        w = csv.writer(f); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in rows[n]: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    src = (f'held n = {n} of round 32 a (the submitted packing gather/round32-2026-11-16a.csv, sha256 {subsha}, gate '
           f'gate/cand-round32-1116a, bar33 source "held round32-2026-11-16a"; a row of a file we submitted is our own layout, '
           f'round 33 override 2); its source and licence: the row of n = {n} in results/{tab[0]}' if tab else
           f'held n = {n} of round 32 a (gather/round32-2026-11-16a.csv, sha256 {subsha}); no results/round*-best table holds n = {n}: its row is older than round 7, see the held-file chain')
    lic = (f'own layout (held row); upstream as results/{tab[0]} records' if tab else 'own layout (held row)')
    Path(str(out) + '.json').write_text(json.dumps(dict(source=src, licence=lic, n=n, sha256=hashlib.sha256(out.read_bytes()).hexdigest(), held_file=str(SUB), held_sha256=subsha)))
(H / 'info.json').write_text(json.dumps(info))
cand = sorted((-v['gap'], n) for n, v in info.items() if v['gap'] and v['gap'] >= 1e-5 and not (v['rigid'] or v['bad'] or v['lattice'] or v['spent'] or v['unprobed3132']))
print('held rows', len(rows), 'changed in round 32 a', sum(v['changed32'] for v in info.values()), 'lattice', sum(v['lattice'] for v in info.values()),
      'rigid', sum(v['rigid'] for v in info.values()), 'n with an unprobed 900 s line r31/r32', len(unprobed), 'probed only', len(set(probed) - set(unprobed)))
print('candidates (gap >= 1e-5 of score)', len(cand), 'changed among them', sum(info[n]['changed32'] for _, n in cand))
print(' '.join(f'{n}:{-g:.2e}' for g, n in cand[:40]))
