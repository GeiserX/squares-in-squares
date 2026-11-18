#!/usr/bin/env python3
"""Drop scan: the held n+1 with one chosen square removed, then the fq quench, for every candidate square.

A plateau pair is an n whose held side is within half a square's worth of the held n+1. There the layout of
n+1 is the better design, and n needs it with one square less. The scan removes one tilted square at a time
(the CANDS tilted squares nearest each corner of the box: the two far ends of the arms and the corner between
them), quenches each start with fq (default flags) and ranks the ends. The best end is written as raw rows,
as the start of the soft chain.

Usage: invent_drop.py PAIR.csv N OUTDIR --fq FQ [--cands 12] [--timeout 90] [--control]
  PAIR.csv   raw rows (n, square_id, x, y, angle) of the held N and the held N+1
  --control  no square is removed: the held N must come back to its own side (the tool control)
Output: OUTDIR/dropscan-N.tsv (one row per candidate) and OUTDIR/N-dq.csv (the best end, raw rows).
Our own code. Reads packings as data only. Nothing is certified here.
"""
import argparse, csv, math, os, subprocess, sys, tempfile, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402


def hw(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def to_fq(P):
    """raw rows (x, y, radians) -> side, rows (x, y, degrees in (-45, 45]) with the box at the origin"""
    x0 = min(x - hw(a) for x, y, a in P); y0 = min(y - hw(a) for x, y, a in P)
    s = max(max(x - x0 + hw(a) for x, y, a in P), max(y - y0 + hw(a) for x, y, a in P))
    out = []
    for x, y, a in P:
        d = math.degrees(a) % 90.0
        if d > 45: d -= 90
        out.append((x - x0, y - y0, d))
    return s, np.array(out)


def quench(fq, tmp, s, X, timeout):
    d = tempfile.mkdtemp(prefix='dq', dir=tmp); a, b = d + '/a.txt', d + '/b.txt'
    with open(a, 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, g in X: h.write('%r %r %r\n' % (float(x), float(y), float(g)))
    out = (None, None)
    try:
        r = subprocess.run([fq, 'quench', '--in', a, '--out', b], capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(b):
            L = [l.split() for l in open(b) if l.strip() and not l.startswith('#')]
            n = int(L[0][0]); out = (float(L[0][1]), np.array([[float(v) for v in q[:3]] for q in L[1:n + 1]]))
    except subprocess.TimeoutExpired:
        pass
    for f in (a, b):
        if os.path.exists(f): os.remove(f)
    os.rmdir(d)
    return out


def write_raw(path, n, X):
    tmp = path + '.tmp'
    with open(tmp, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, a) in enumerate(X):
            w.writerow([n, i, repr(float(x)), repr(float(y)), repr(math.radians(float(a)))])
    os.rename(tmp, path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pair'); ap.add_argument('n', type=int); ap.add_argument('out')
    ap.add_argument('--fq', required=True); ap.add_argument('--cands', type=int, default=12)
    ap.add_argument('--timeout', type=float, default=90); ap.add_argument('--control', action='store_true')
    a = ap.parse_args()
    n = a.n; os.makedirs(a.out, exist_ok=True); tmp = a.out + '/tmp'; os.makedirs(tmp, exist_ok=True)
    H = mlp.load(a.pair, {n, n + 1})
    Ln = mlp.side(H[n])
    if a.control:
        s, X = to_fq([tuple(r) for r in H[n]])
        s2, X2 = quench(a.fq, tmp, s, X, a.timeout)
        ok = s2 is not None and abs(s2 - Ln) < 1e-7
        print('CONTROL n=%d held %.12f quench %r %s' % (n, Ln, s2, 'green' if ok else 'RED'), flush=True)
        return 0 if ok else 1
    s1, X1 = to_fq([tuple(r) for r in H[n + 1]])
    tilted = np.where(np.abs(X1[:, 2]) > 0.5)[0]
    cand = []
    for cx, cy in ((0, 0), (0, s1), (s1, 0), (s1, s1)):
        d = np.hypot(X1[tilted, 0] - cx, X1[tilted, 1] - cy)
        for j in np.argsort(d)[:a.cands]:
            if int(tilted[j]) not in cand: cand.append(int(tilted[j]))
    print('DROP n=%d held %.12f, n+1 side %.12f (step %.6f), %d tilted, %d candidates' % (n, Ln, s1, s1 - Ln, len(tilted), len(cand)), flush=True)
    rows = []; best = None; t0 = time.time()
    for i in cand:
        X = np.delete(X1, i, axis=0)
        s2, X2 = quench(a.fq, tmp, s1, X, a.timeout)
        if s2 is None:
            rows.append((i, X1[i, 0], X1[i, 1], X1[i, 2], float('nan'))); continue
        rows.append((i, X1[i, 0], X1[i, 1], X1[i, 2], s2))
        if best is None or s2 < best[0]:
            best = (s2, X2, i); write_raw('%s/%d-dq.csv' % (a.out, n), n, X2)
        print('  drop %4d at (%.2f, %.2f) %+.1f deg -> %.9f (%+.6f on held)%s' % (i, X1[i, 0], X1[i, 1], X1[i, 2], s2, s2 - Ln, '  BELOW HELD' if s2 < Ln else ''), flush=True)
    with open('%s/dropscan-%d.tsv' % (a.out, n), 'w') as h:
        h.write('n\tsquare\tx\ty\tdeg\tside_after_quench\tminus_held\tgiven_back\n')
        for i, x, y, g, s2 in sorted(rows, key=lambda r: (math.isnan(r[4]), r[4])):
            h.write('%d\t%d\t%.4f\t%.4f\t%.2f\t%.12f\t%.3e\t%.3e\n' % (n, i, x, y, g, s2, s2 - Ln, s1 - s2))
    if best:
        print('DROPEND n=%d best %.12f (%+.6f on held, %.6f given back of %.6f) square %d, %.0f s' % (
            n, best[0], best[0] - Ln, s1 - best[0], s1 - Ln, best[2], time.time() - t0), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
