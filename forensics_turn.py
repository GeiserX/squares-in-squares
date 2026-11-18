#!/usr/bin/env python3
"""Turn the tilted block of a held layout to the angle the board's side asks for, then quench.

forensics_curve.py gives, for an n, the chain of the held block and the angle where that chain
gives the board's side. This tool turns every block of the held layout to that angle (each block
as one rigid piece about its own centre, a mirrored block the other way), writes the start and
lets the fq quench settle it. A start can also stop part of the way (--frac) or go past it.

Usage: forensics_turn.py HELD.csv N HELD_DEG BOARD_DEG OUTDIR [--frac 0.5,1.0,...] [--fq PATH]
                         [--shrink SIDE] [--polish] [--jit SIGMA --seeds K]
Writes OUTDIR/<n>-<tag>.csv (Kaggle rows, angles in radians) for every quench that ends below the held side.
"""
import sys, os, csv, math, subprocess, tempfile, collections, argparse
import numpy as np

POLISH = ['--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600']


def hw(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def load(path, n):
    sq = []
    for r in csv.DictReader(open(path)):
        if int(r['n']) == n:
            sq.append((float(str(r['x']).lstrip('s')), float(str(r['y']).lstrip('s')), float(str(r['angle']).lstrip('s'))))
    return sq


def normalize(sq):
    x0 = min(x - hw(a) for x, y, a in sq); y0 = min(y - hw(a) for x, y, a in sq)
    s = max(max(x - x0 + hw(a) for x, y, a in sq), max(y - y0 + hw(a) for x, y, a in sq))
    out = []
    for x, y, a in sq:
        d = math.degrees(a) % 90.0
        if d > 45:
            d -= 90
        out.append((x - x0, y - y0, d))
    return s, np.array(out)


def blocks(A, held_deg, tol=0.02):
    """Groups of touching squares at +held or -held (degrees folded to (-45, 45])."""
    fold = held_deg if held_deg <= 45 else held_deg - 90
    groups = []
    for sign in (1, -1):
        idx = [i for i in range(len(A)) if abs(A[i, 2] - sign * fold) < tol]
        seen = set()
        for i in idx:
            if i in seen:
                continue
            comp = [i]; seen.add(i); q = [i]
            while q:
                a = q.pop()
                for b in idx:
                    if b not in seen and math.hypot(A[a, 0] - A[b, 0], A[a, 1] - A[b, 1]) < 1.45:
                        seen.add(b); comp.append(b); q.append(b)
            groups.append((sign, comp))
    return groups


def turned(A, groups, delta_deg):
    B = A.copy()
    for sign, comp in groups:
        d = math.radians(sign * delta_deg)
        cx, cy = B[comp, 0].mean(), B[comp, 1].mean()
        c, s = math.cos(d), math.sin(d)
        for i in comp:
            x, y = A[i, 0] - cx, A[i, 1] - cy
            B[i, 0] = cx + c * x - s * y; B[i, 1] = cy + s * x + c * y
            B[i, 2] = A[i, 2] + sign * delta_deg
    return B


def quench(fq, s, X, flags=(), timeout=900):
    d = tempfile.mkdtemp(prefix='fqt')
    a, b = d + '/a.txt', d + '/b.txt'
    with open(a, 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, g in X:
            h.write('%r %r %r\n' % (float(x), float(y), float(g)))
    out = (None, None)
    try:
        r = subprocess.run([fq, 'quench', '--in', a, '--out', b] + list(flags), capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and os.path.exists(b):
            L = [l.split() for l in open(b) if l.strip() and not l.startswith('#')]
            k = int(L[0][0])
            out = (float(L[0][1]), np.array([[float(v) for v in q[:3]] for q in L[1:k + 1]]))
    except subprocess.TimeoutExpired:
        pass
    for f in (a, b):
        if os.path.exists(f):
            os.remove(f)
    os.rmdir(d)
    return out


def write_rows(path, n, X):
    with open(path, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, g) in enumerate(X):
            w.writerow([n, i, repr(float(x)), repr(float(y)), repr(math.radians(float(g)))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('held'); ap.add_argument('n', type=int); ap.add_argument('held_deg', type=float)
    ap.add_argument('board_deg', type=float); ap.add_argument('out')
    ap.add_argument('--frac', default='0,0.25,0.5,0.75,1.0,1.15')
    ap.add_argument('--fq', default=os.path.expanduser('$SCRATCH/squares-base/fq'))
    ap.add_argument('--shrink', type=float, default=0.0, help='start side; 0 keeps the held side')
    ap.add_argument('--polish', action='store_true')
    ap.add_argument('--jit', type=float, default=0.0); ap.add_argument('--seeds', type=int, default=1)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    s, A = normalize(load(a.held, a.n))
    groups = blocks(A, a.held_deg)
    print('n', a.n, 'held side', repr(s), 'blocks', [(sg, len(c)) for sg, c in groups], flush=True)
    flags = POLISH if a.polish else []
    for fr in (float(v) for v in a.frac.split(',')):
        for seed in range(a.seeds):
            B = turned(A, groups, fr * (a.board_deg - a.held_deg))
            s0 = a.shrink or s
            if a.shrink:
                B[:, :2] *= s0 / s
            if a.jit:
                rng = np.random.default_rng(1000 * seed + int(fr * 100))
                B[:, :2] += rng.normal(0, a.jit, (len(B), 2))
            s2, X = quench(a.fq, s0, B, flags)
            tag = 'f%03d%s-s%d' % (round(fr * 100), 'p' if a.polish else '', seed)
            if s2 is None:
                print(a.n, tag, 'quench failed', flush=True); continue
            ang = collections.Counter(round(abs(float(g)), 3) for g in X[:, 2] if abs(g) > 0.1).most_common(2)
            print(a.n, tag, 'start side %.9f -> %.9f  (held %.9f, %+.2e)  angles %s' % (s0, s2, s, s2 - s, ang), flush=True)
            if s2 < s - 1e-9:
                write_rows('%s/%d-%s.csv' % (a.out, a.n, tag), a.n, X)


if __name__ == '__main__':
    main()
