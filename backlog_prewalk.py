#!/usr/bin/env python3
"""backlog_prewalk: one quench_walk.check of a start in its own process, so the backlog ctl does not block on a slow
walk (round 36: a 7351-file donor walk took 258 s on the loaded boxA and another lane claimed the donor meanwhile).
A clean walk that stops at the 3000-file cap is walked again with cap 100000 (brief 6g). Writes OUT (json) by rename.

  backlog_prewalk.py START OUT
"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('BACKLOG_ROUND', '36')
import backlog_gate27  # noqa: E402,F401  the narrowed 745/858 join rule, as in the ctl
import quench_walk  # noqa: E402

start, out = sys.argv[1], sys.argv[2]
t0 = time.time()
try:
    g = quench_walk.check(start)
    if g.get('clean') and g.get('capped'):
        g = quench_walk.check(start, cap=100000)
    r = dict(clean=bool(g.get('clean')), capped=bool(g.get('capped')), files=g.get('files'), hits=(g.get('hits') or [])[:40])
except Exception as ex:
    r = dict(clean=False, capped=False, files=0, hits=['walk failed: %r' % (ex,)])
r['seconds'] = round(time.time() - t0, 1); r['start'] = start
json.dump(r, open(out + '.tmp', 'w')); os.replace(out + '.tmp', out)
