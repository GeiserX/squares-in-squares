"""Round 32 kick summary for the doc and report: one line per finished kick of kfeed34.py (kind, n, seconds, move of side,
end vs the live bar at the time). Kinds: seed1 (first unprobed 900 s seed of a held row), seed2 (its second seed), leg,
control."""
import re, json, os, collections
W = os.path.dirname(os.path.abspath(__file__))
ix = json.load(open(os.path.join(W, 'kq/index.json')))
rows = []
for line in open(os.path.join(W, 'kfeed34.log'), errors='replace'):
    m = re.search(r'Z KICK (\d+) (\S+): (?:raw find [0-9.]+ \(([-0-9.e+]+) vs its start\), certified side [0-9.]+, ([-0-9.e+]+) vs the live bar|no find)', line)
    if not m: continue
    v = ix.get(m[2], {})
    kind = 'control' if v.get('control') else 'leg' if v.get('leg') else 'seed2' if v.get('reseed') else 'seed1'
    sec = re.search(r'seconds (\d+)', line)
    rows.append(dict(n=int(m[1]), id=m[2], kind=kind, sec=int(sec[1]) if sec else v.get('seconds', 900), move=float(m[3]) if m[3] else 0.0,
                     end=float(m[4]) if m[4] else None, leg=v.get('leg', 0)))
seen = set(); out = []
for r in rows:
    if r['id'] in seen: continue
    seen.add(r['id']); out.append(r)
for r in out: print(f"{r['n']}\t{r['kind']}{r['leg'] or ''}\t{r['sec']}\t{r['move']:.3e}\t{'' if r['end'] is None else '%.3e' % r['end']}\t{r['id']}")
c = collections.Counter(r['kind'] for r in out); big = collections.Counter(r['kind'] for r in out if r['move'] < -1e-6)
secs = collections.Counter(); [secs.update({r['kind']: r['sec']}) for r in out]
print('kicks', len(out), dict(c), 'seconds', dict(secs), 'moved more than 1e-6 of side:', dict(big))
