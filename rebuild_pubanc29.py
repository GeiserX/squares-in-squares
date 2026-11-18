"""pubanc29.py START N: the fetched public-first files a start's tree reaches (files under take-harvest-r*/ that
quench_walk.harvest_type calls public-first), with their best-of-1105 share at 1e-3 (rule 3: 0.4 or more is out, and so is
everything built from it). One JSON line."""
import csv, json, os, re, sys
sys.path.insert(0, '.')
import quench_walk as qw  # noqa: E402
import rebuild_walk27 as w27  # noqa: E402
csv.field_size_limit(1 << 28)
S = qw.S
st = sys.argv[1] if sys.argv[1].startswith('/') else S + sys.argv[1]
texts, missing, seen, helds, refused = qw.walk(st, int(sys.argv[2]))
out = []
for label, t in texts:
    lb = str(label)
    p = lb if lb.startswith('/') else S + lb
    if not re.search(r'take-harvest-r\d+/.*\.csv$', p) or not os.path.isfile(p):
        continue
    try:
        nn = int(next(csv.DictReader(open(p)))['n'])
        pf = qw.harvest_type(p, nn)
        sh = w27.prv_share(p, nn) if pf else None
    except Exception as e:
        out.append(dict(path=p.replace(S, ''), error=str(e)[:80])); continue
    if pf:
        out.append(dict(path=p.replace(S, ''), n=nn, share1e3=sh and sh['share1e3'], share1e2=sh and sh['share1e2'], out=bool(sh and sh['share1e3'] >= 0.4)))
print(json.dumps(dict(start=st.replace(S, ''), public_first=out, bad=sum(1 for x in out if x.get('out')))))
