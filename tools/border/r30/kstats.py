"""Round 30 kick summary for the doc and report: one line per finished kick of kfeed30.py (class, n, seconds, move, end vs bar)."""
import re, json, os
W = os.path.dirname(os.path.abspath(__file__))
ix = json.load(open(os.path.join(W, 'kq/index.json')))
cls = {}
for line in open(os.path.join(W, 'kfeed30.log'), errors='replace'):
    m = re.search(r'KICK queue (\d+) from (\S+) \(sha256 ([0-9a-f]{12})', line)
    if m:
        why = 'take' if 'fresh take row' in line else 'near' if 'near file of' in line else 'seed' if 'parked Samanyu' in line else 'held' if 'held row of bar30' in line else '?'
        cls[m[3]] = why
    m = re.search(r'KICK chain (\d+): leg (\d+) queued from the certified find \S+-leg\d+-([0-9a-f]{12})', line)
    if m: cls[m[3]] = 'leg'
rows = []
for line in open(os.path.join(W, 'kfeed30.log'), errors='replace'):
    m = re.search(r'Z KICK (\d+) ([0-9a-f]{12}): (?:raw find [0-9.]+ \(([-0-9.e+]+) vs its start\), certified side [0-9.]+, ([-0-9.e+]+) vs the live bar|no find)', line)
    if not m: continue
    v = ix.get(m[2], {})
    rows.append(dict(n=int(m[1]), id=m[2], cls=cls.get(m[2], '?'), sec=v.get('seconds', 900), move=float(m[3]) if m[3] else 0.0, end=float(m[4]) if m[4] else None, path=v.get('path', '')))
seen = set(); out = []
for r in rows:
    if r['id'] in seen: continue
    seen.add(r['id']); out.append(r)
for r in out: print(f"{r['n']}\t{r['cls']}\t{r['sec']}\t{r['move']:.3e}\t{'' if r['end'] is None else '%.3e' % r['end']}\t{os.path.basename(r['path'])}")
import collections
c = collections.Counter(r['cls'] for r in out); big = collections.Counter(r['cls'] for r in out if r['move'] < -1e-6)
print('kicks', len(out), dict(c), 'moved more than 1e-6:', dict(big))
