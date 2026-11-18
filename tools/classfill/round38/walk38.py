"""Round 38 walk wrapper (rule 6g): quench_walk.check with a chosen file cap, written to an output JSON.
usage: walk38.py check <path> <out.json> <cap>     |   walk38.py pol <path> <out.json> <cap> <n>
'capped' is True when the walk read cap files or more (quench_walk's own flag only knows the 3000 cap).
The output JSON lives in work/walkres/ and is never named by any sidecar (rule 6h)."""
import os, sys, json
os.environ.setdefault('QUENCH_LIVE_ROUND', '38')
sys.path.insert(0, '.')
import quench_walk as qw
mode, path, out, cap = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
if mode == 'check':
    r = qw.check(path, cap=cap)  # quench_walk 2ba6b4e takes the cap itself
    r['capped'] = r.get('files', 0) >= cap
    r['cap'] = cap
else:
    bad, why = qw.pol_fail(path, int(sys.argv[5]))
    r = dict(bad=bool(bad), why=why)
tmp = out + '.tmp'
with open(tmp, 'w') as f:
    json.dump(r, f)
os.replace(tmp, out)
print('WALK ' + json.dumps(r)[:2000], flush=True)
