"""Round 34 twoshort screen b: recount the unprobed 900 s kick lines of sel34.py by bytes. For each class row with
board gap 1e-6 or more, read each csv path a counted line names; the line counts only when that file holds the
held round 33 a geometry of n (same squares to 1e-9 after sorting, angles mod 90 degrees). A line with no readable
csv still counts. Writes sel34b.json: rows whose byte count leaves seeds, with the matched lines."""
import csv, json, math, re, sys
from pathlib import Path
csv.field_size_limit(1 << 30)
B = Path('$SCRATCH/bounties-squares')
sys.argv = [sys.argv[0], '/dev/null']
d = json.load(open(Path(__file__).parent / 'sel34.json'))
held = {}
for r in csv.DictReader(open(B / 'gather/round33-2026-11-17a.csv')):
    held.setdefault(int(r['n']), []).append(r)
def key(rows):
    out = []
    for r in rows:
        a = float(r['angle']); a = math.degrees(a) % 90.0 if abs(a) <= 7 else a % 90.0
        out.append((round(float(r['x']), 7), round(float(r['y']), 7), round(a, 6)))
    return sorted(out)
def same(n, p):
    try: rows = [r for r in csv.DictReader(open(p)) if r.get('n', str(n)) == str(n)]
    except Exception: return None
    if len(rows) != n: return None
    a, b = key(rows), key(held[n])
    return all(abs(x[0] - y[0]) < 1e-6 and abs(x[1] - y[1]) < 1e-6 and abs(x[2] - y[2]) < 1e-4 for x, y in zip(a, b))
logs = {k: [l for l in open(B / f'handoff-r{k}.log', errors='replace')] for k in (28, 29, 30, 31, 32, 33, 34) if (B / f'handoff-r{k}.log').exists()}
def probe_vals(line):
    return [int(x) for t in re.findall(r'probe\s*=?\s*(\d+)|(\d+)\s*s probe', line) for x in t if x]
res = []
for o in d['all']:
    if o['skip'] or o['gap'] < 1e-6 or o['n'] % 4 != 1: continue
    n = o['n']; k0, t0 = o['since'].split(' ', 1); k0 = int(k0[1:])
    hits = []
    for k, lines in logs.items():
        if k < k0: continue
        for line in lines:
            if k == 34 and re.match(r'\S+ twoshort ->', line): continue
            if not re.search(r'\b900\s*-?s\b|900s|seconds=900', line) or not re.search(r'claim|start', line, re.I) or re.search(r'certified', line, re.I): continue
            if k == k0 and line[:19] < t0[:19]: continue
            if n not in set(int(x) for x in re.findall(r'\bn\s*=\s*(\d+)', line)) or any(v > 0 for v in probe_vals(line)): continue
            paths = re.findall(r'($SCRATCH/bounties-squares/\S+?\.csv)', line)
            v = [same(n, p) for p in paths]
            m = re.match(r'(\S+) (\S+) ->', line); sd = re.search(r'seed\s*=?\s*(\d+)', line)
            hits.append(dict(lane=m[2] if m else '?', seed=sd[1] if sd else None, t=line[:19], match=(True if any(x for x in v) else (None if all(x is None for x in v) else False)), paths=paths[:2]))
    kk = {}
    for h in hits:
        if h['match'] is False: continue
        kk[(h['lane'], h['seed'] or h['t'])] = h
    res.append(dict(n=n, gap=o['gap'], old_unprobed=o['unprobed'], byte_unprobed=len(kk), seeds_left=max(0, 2 - len(kk)), hits=hits))
json.dump(res, open(Path(__file__).parent / 'sel34b.json', 'w'), indent=1)
for r in sorted(res, key=lambda r: -r['gap']):
    if r['old_unprobed'] != r['byte_unprobed']: print('CHANGED', r['n'], '%.1e' % r['gap'], r['old_unprobed'], '->', r['byte_unprobed'], [(h['lane'], h['match']) for h in r['hits']])
print('rows', len(res), 'with seeds left', sum(r['seeds_left'] > 0 for r in res))
