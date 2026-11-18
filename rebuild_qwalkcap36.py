"""qwalkcap.py CAP START.csv [...]: quench_walk.check (imported unchanged) with its walk cap raised from 3000 to CAP files.
Round 36: check() now takes cap= and passes it to walk() itself (cb2ac67), so the round 35 trick of setting walk's default
no longer reaches the walk; pass cap= to check, and print capped (rule 6g)."""
import json, sys
sys.path.insert(0, '.')
import quench_walk as q  # noqa: E402
q.walk.__defaults__ = (int(sys.argv[1]),)
for p in sys.argv[2:]:
    print(json.dumps(q.check(p, cap=int(sys.argv[1]))), flush=True)
