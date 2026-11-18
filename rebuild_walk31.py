"""walk28.py START.csv [...]: the rebuild round 27 walk (rebuild_walk27.check, Samanyu signals lifted, share test of the
start) plus the round 28 ancestor share test: every complete per-n csv the walk reaches gets the prvsiyan best-of-1105
share within 1e-3 of its own n; 0.4 or more in any ancestor is a hit (the rule invent and k123 applied in round 27).
One JSON line per start. Imports rebuild_walk27 and quench_walk unchanged."""
import csv, json, os, sys
sys.path.insert(0, '.')
import rebuild_walk27 as w27  # noqa: E402
csv.field_size_limit(1 << 28)
_orig = w27.qw.walk
_cache = {}
def _mw(start, n, cap=3000):
    r = _orig(start, n, cap); _cache[start] = r; return r
w27.qw.walk = _mw

def anc_shares(seen, me):
    out = []
    for f in sorted(x for x in seen if isinstance(x, str)):
        if f == me or not f.endswith('.csv') or not os.path.isfile(f) or os.path.getsize(f) > 3_000_000:
            continue
        try:
            rows = list(csv.DictReader(open(f)))
            ns = set(r['n'] for r in rows)
            if len(ns) != 1: continue
            n = int(ns.pop())
            if len(rows) != n or 'x' not in rows[0]: continue
            sh = w27.prv_share(f, n)
            if sh: out.append((sh['share1e3'], n, f.replace(w27.S, '')))
        except Exception:
            continue
    return sorted(out, reverse=True)

for p in sys.argv[1:]:
    p = os.path.abspath(p)
    r = w27.check(p)
    seen = _cache.get(p, (None, None, set()))[2]
    a = anc_shares(seen, p)
    bad = [x for x in a if x[0] >= 0.4]
    r['anc_share_max'] = a[0] if a else None
    r['anc_share_hits'] = bad[:10]
    r['anc_csvs'] = len(a)
    if bad:
        r['clean'] = False
    print(json.dumps(r), flush=True)
