"""floatsafe with a bisected dilation (border r28). Same test as lanes/squares/floatsafe.py: the centres are scaled about
their mean by 1+e, every pair must clear MIN_CLEARANCE (2.2e-11) on a separating axis, and the metric must certify the
rows as written and after pandas' default float parse. floatsafe.work takes the first e of a 1-2-5 ladder that passes;
this one bisects e between the last ladder step that fails the clearance and the first that passes, then checks the
metric at that e and steps up by 2 % until it passes (never above the ladder's own e).
work((n, rows)) -> (n, rows, score, e), like floatsafe.work."""
import sys
from pathlib import Path
sys.path.insert(0, '.')
import floatsafe as fs

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
        if fs.clearance(fs.as_float_rows(rows, mid)) >= fs.MIN_CLEARANCE: hi = mid
        else: lo = mid
    e = hi
    while e < e1:
        fr = fs.as_float_rows(rows, e)
        if fs.clearance(fr) >= fs.MIN_CLEARANCE:
            s, why = fs.check(n, fr)
            if why == 'ok' and fs.check(n, fs.via_pandas(fr))[1] == 'ok':
                return (n, fr, s, e) if s < ref[2] else ref
        e *= 1.02
    return ref

if __name__ == '__main__':
    import csv, math, json
    sys.path.insert(0, str(Path(__file__).parent / 'boxC'))
    sys.path.insert(0, '.')
    import border_sweep as bs
    for txt in sys.argv[1:]:
        s0, A = bs.read_txt(txt); n = len(A)
        rows = [{'n': str(n), 'square_id': str(i), 'x': repr(x), 'y': repr(y), 'angle': repr(math.radians(t))} for i, (x, y, t) in enumerate(A)]
        ref = fs.work((n, rows)); new = work((n, rows))
        side = lambda sc: (sc + 1) * math.sqrt(n)
        print(json.dumps(dict(file=txt, n=n, raw=s0, ladder_e=ref[3], ladder_side=side(ref[2]), fine_e=new[3], fine_side=side(new[2]),
                              gain=side(ref[2]) - side(new[2]))), flush=True)
