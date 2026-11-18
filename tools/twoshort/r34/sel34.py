"""Round 34 twoshort deep-kick screen (override 6d and 8): held rows of the round 33 a file in class n mod 4 = 1
that have had fewer than two unprobed 900 s kicks since their current geometry.

Current geometry time: the latest round R (30..33) whose held file changed the row (bar(R+1) < bar(R)); kick lines
count from the row's last 'certified n=N' line in handoff-rR.log (all of rR+1 and later). A row unchanged since
round 30 counts the lines of handoff-r28 to r34. A kick is a claim or start line of another lane, or ours, naming
n=N with 900 s and no probe of 1 s or more; one count per (lane, seed) or per line when no seed is named.
Skips: rigid (side fraction shared by 3 or more n), the 14 lattice n and any 45-degree lattice row, rows whose last
results table names the 1105 file or CC BY-SA, the five penguin n.
Order: rows changed in round 33 a whose 900 s kicks since the change were all probed (list A), then the rest by
largest board gap (list B). Writes sel34.json with seeds_left per row."""
import csv, json, math, re, sys, glob
from pathlib import Path
csv.field_size_limit(1 << 30)
B = Path('$SCRATCH/bounties-squares')
R = Path('results')
bars = {k: {int(r['n']): float(r['bar']) for r in csv.DictReader(open(B / f'round{k}-briefs/bar{k}.tsv'), delimiter='\t')} for k in (30, 31, 32, 33, 34)}
bar = bars[34]
OUT = {639, 691, 745, 858, 918, 980}
LATTICE = {626, 677, 678, 730, 731, 785, 786, 842, 843, 901, 902, 962, 963, 964}
rows = {}
for r in csv.DictReader(open(B / 'gather/round33-2026-11-17a.csv')):
    rows.setdefault(int(r['n']), []).append(r)
def tkey(p):
    m = re.match(r'round(\d+)', p.name); return int(m[1])
last = {}
for t in sorted(R.glob('round*-best-*.tsv'), key=tkey):
    for r in csv.DictReader(open(t), delimiter='\t'):
        try: last[int(r['n'])] = (t.name, r.get('source', ''), r.get('licence', ''))
        except (ValueError, KeyError): pass
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
    for k in (33, 32, 31, 30):
        if bars[k + 1][n] < bars[k][n] - 1e-15: return k
    return None
certt = {}
for k in (30, 31, 32, 33):
    for line in open(B / f'handoff-r{k}.log', errors='replace'):
        m = re.match(r'(\S{19})\S* (\S+) -> .*certified n=(\d+)', line, re.I)
        if m: certt[(k, int(m[3]))] = m[1]
def probe_vals(line):
    return [int(x) for t in re.findall(r'probe\s*=?\s*(\d+)|(\d+)\s*s probe', line) for x in t if x]
kicks = {}   # n -> list of (logk, time, lane, key, probed)
for k in (28, 29, 30, 31, 32, 33, 34):
    p = B / f'handoff-r{k}.log'
    if not p.exists(): continue
    for line in open(p, errors='replace'):
        if not re.search(r'\b900\s*-?s\b|900s|seconds=900', line): continue
        if not re.search(r'claim|start', line, re.I) or re.search(r'certified', line, re.I): continue
        m = re.match(r'(\S{19})\S* (\S+) ->', line)
        if not m: continue
        prb = any(v > 0 for v in probe_vals(line))
        sd = re.search(r'seed\s*=?\s*(\d+)', line)
        for n in set(int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)):
            kicks.setdefault(n, []).append((k, m[1], m[2], sd[1] if sd else line[:120], prb))
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
    if cr and (cr, n) not in certt: t0 = (cr + 1, '0000')   # no cert line: count from the next round
    after = [x for x in kicks.get(n, []) if (x[0], x[1]) >= t0 and (x[0] > t0[0] or x[1] >= t0[1])]
    unp = {(x[2], x[3]) for x in after if not x[4]}; prb = {(x[2], x[3]) for x in after if x[4]}
    out.append(dict(n=n, gap=gap[n], side=s, changed=cr, since='r%s %s' % t0, unprobed=len(unp), probed=len(prb),
                    seeds_left=max(0, 2 - len(unp)), skip=why))
A = [o for o in out if not o['skip'] and o['changed'] == 33 and o['unprobed'] == 0]
Bl = [o for o in out if not o['skip'] and o not in A and o['seeds_left'] > 0]
A.sort(key=lambda o: -o['gap']); Bl.sort(key=lambda o: -o['gap'])
json.dump(dict(A=A, B=Bl, all=out), open(sys.argv[1], 'w'), indent=1)
print('class rows', len(out), 'skip', {w: sum(o['skip'] == w for o in out) for w in ('source out', 'lattice', 'rigid closed form')})
print('A (changed r33, only probed 900 s since):', len(A), ' '.join('%d:%.1e:%d' % (o['n'], o['gap'], o['seeds_left']) for o in A))
print('B:', len(Bl), 'gap>=1e-5:', sum(o['gap'] >= 1e-5 for o in Bl), ' '.join('%d:%.1e:%d' % (o['n'], o['gap'], o['seeds_left']) for o in Bl[:60]))
