"""backlog_finesafe: floatsafe with a bisected dilation, copied from border's take-border-r28/work/finesafe.py (round 28)
so the box workers of the backlog lane need no file of a frozen take dir. Same test as floatsafe.py: the centres are
scaled about their mean by 1+e, every pair must clear MIN_CLEARANCE (2.2e-11) on a separating axis, and the metric
must certify the rows as written and after pandas' default float parse. floatsafe.work takes the first e of a 1-2-5
ladder that passes; this one bisects e between the last ladder step that fails the clearance and the first that
passes, then checks the metric at that e and steps up by 2 % until it passes (never above the ladder's own e).
Border measured 3.0e-10 to 8.2e-10 of side lower than the ladder on 19 fq outputs.
work((n, rows)) -> (n, rows, score, e), like floatsafe.work."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import floatsafe as fs  # noqa: E402


def work(a, iters=40):
    n, rows = a
    ref = fs.work((n, rows))
    if ref[1] is None or not ref[3]:
        return ref
    e1 = ref[3]; i = fs.EPS.index(e1); e0 = fs.EPS[i - 1] if i else 0.0
    lo, hi = e0, e1
    if fs.clearance(fs.as_float_rows(rows, lo)) >= fs.MIN_CLEARANCE:
        return ref                       # the ladder's previous step clears; the metric refused it, keep the ladder e
    for _ in range(iters):
        mid = (lo + hi) / 2
        if fs.clearance(fs.as_float_rows(rows, mid)) >= fs.MIN_CLEARANCE:
            hi = mid
        else:
            lo = mid
    e = hi
    while e < e1:
        fr = fs.as_float_rows(rows, e)
        if fs.clearance(fr) >= fs.MIN_CLEARANCE:
            s, why = fs.check(n, fr)
            if why == 'ok' and fs.check(n, fs.via_pandas(fr))[1] == 'ok':
                return (n, fr, s, e) if s < ref[2] else ref
        e *= 1.02
    return ref
