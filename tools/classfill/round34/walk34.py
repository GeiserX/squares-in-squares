"""Ancestry check of a start or an output with the round-generic quench_walk (fixed in 45dd8ad)."""
import os, sys, json
os.environ.setdefault('QUENCH_LIVE_ROUND', '34')
sys.path.insert(0, '.')
import quench_walk as qw
if sys.argv[1] == 'check':
    print('WALK ' + json.dumps(qw.check(sys.argv[2])), flush=True)
else:
    bad, why = qw.pol_fail(sys.argv[2], int(sys.argv[3]))
    print('POL ' + json.dumps(dict(bad=bool(bad), why=why)), flush=True)
