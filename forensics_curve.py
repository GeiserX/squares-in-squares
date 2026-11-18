#!/usr/bin/env python3
"""Read the contact chains of a held layout, and place the board's side on them.

A held layout whose tilted squares share one angle t satisfies a few chains with small whole
coefficients (see forensics_match.py). One chain with f in it is a curve f(t): the side the same
block needs at another angle. For each n where the board is ahead:

  1. the main tilted angle t of the held layout, and its f;
  2. every B chain (i + d f) C + (j + e f) S = a and L chain a C + b S = c + d f that holds at (t, f);
  3. on each chain, the angle tb where the chain gives the board's f, and tb - t;
  4. at (tb, f_board), a second chain of small height. A hit says the board holds the same block
     at the angle tb, stopped by that second chain.

Usage: forensics_curve.py HELD.csv HELD_DETAILS.csv BOARD.json OUT.tsv [n ...]
"""
import sys, csv, json, math, collections
import numpy as np

H1 = 40          # height of the chains read from the held layout
H2 = 20          # height of the second chain at the board's point
READ_TOL = 2e-8  # a chain holds in the held layout
F_TOL = 3e-10    # the second chain gives the board's f this closely


def num(s):
    return float(str(s).lstrip('s'))


def load(path):
    rows = collections.defaultdict(list)
    for r in csv.DictReader(open(path)):
        rows[int(r['n'])].append((num(r['x']), num(r['y']), num(r['angle'])))
    return rows


def main_angle(sq):
    """Most common tilted angle, in radians in (0, pi/2), and how many squares hold it or its mirror."""
    deg = any(abs(a) > 6.3 for _, _, a in sq)
    c = collections.Counter()
    for _, _, a in sq:
        t = (math.radians(a) if deg else a) % (math.pi / 2)
        if min(t, math.pi / 2 - t) > 2e-3:
            c[round(min(t, math.pi / 2 - t), 7)] += 1
    if not c:
        return None, 0, 0
    key, cnt = c.most_common(1)[0]
    # the exact value: mean of the members of that bin
    vals = []
    for _, _, a in sq:
        t = (math.radians(a) if deg else a) % (math.pi / 2)
        t = min(t, math.pi / 2 - t)
        if abs(t - key) < 1e-6:
            vals.append(t)
    return sum(vals) / len(vals), cnt, sum(c.values())


def chains_at(t, f, H, tol):
    """B and L chains that hold at (t, f): list of (kind, coefs, resid, height)."""
    C, S = math.cos(t), math.sin(t)
    out = []
    I = np.arange(-H, H + 1)
    xs = [(int(i), d) for i in I for d in (-1, 0, 1)]
    X = np.array([i + d * f for i, d in xs])
    val = (X * C)[:, None] + (X * S)[None, :]
    r = np.abs(val - np.rint(val))
    for ix, iy in zip(*np.nonzero(r < tol)):
        i, d = xs[ix]; j, e = xs[iy]
        if (i, d, j, e) <= (-i, -d, -j, -e):
            continue
        if d == 0 and e == 0:
            continue
        a = int(round(val[ix, iy]))
        if math.gcd(math.gcd(abs(i), abs(j)), math.gcd(abs(a), math.gcd(abs(d), abs(e)))) != 1:
            continue
        out.append(('B', (i, j, d, e, a), float(r[ix, iy]), max(abs(i), abs(j))))
    for a in range(0, H + 1):
        for b in range(-H, H + 1):
            if a == 0 and b <= 0:
                continue
            for d in (-1, 0, 1, 2):
                v = a * C + b * S - d * f
                if abs(v - round(v)) < tol and math.gcd(math.gcd(a, abs(b)), math.gcd(abs(d), abs(round(v)))) == 1:
                    out.append(('L', (a, b, int(round(v)), d), abs(v - round(v)), max(a, abs(b))))
    out.sort(key=lambda x: x[3])
    return out


def grad(kind, co, t, f):
    C, S = math.cos(t), math.sin(t)
    if kind == 'L':
        a, b, _, d = co
        return -a * S + b * C, -float(d)
    i, j, d, e = co[:4]
    return -(i + d * f) * S + (j + e * f) * C, d * C + e * S


def angle_on(kind, co, f, near):
    """The angle where the chain holds at this f, nearest to `near`. None when it has no solution."""
    if kind == 'L':
        a, b, c, d = co
        X, Y, Z = a, b, c + d * f
    else:
        i, j, d, e, a = co
        X, Y, Z = i + d * f, j + e * f, a
    R = math.hypot(X, Y)
    if R < 1e-12 or abs(Z) > R:
        return None
    ph = math.atan2(Y, X); w = math.acos(Z / R)
    cands = [ph + w, ph - w]
    return min(cands, key=lambda t: abs(t - near))


def fmt(kind, co):
    if kind == 'L':
        return '%d C %+d S = %d %+d f' % tuple(co)
    return '(%d%+d f) C + (%d%+d f) S = %d' % (co[0], co[2], co[1], co[3], co[4])


def main():
    held_csv, details, board, out = sys.argv[1:5]
    only = [int(v) for v in sys.argv[5:]]
    rows = load(held_csv)
    HL = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    BL = {x['n']: float(x['L']) for x in json.load(open(board))}
    res = []
    for n in sorted(rows):
        if only and n not in only:
            continue
        if not only and (n < 60 or HL[n] - BL[n] < 1e-6):
            continue
        m = int(BL[n] + 1e-9)
        f = HL[n] - m; fb = BL[n] - m
        if not (0 < fb < 1 and 0 < f < 1):
            continue
        t, cnt, ntilt = main_angle(rows[n])
        if t is None or cnt < 4:
            continue
        found = []
        for tt in (t, math.pi / 2 - t):
            for kind, co, r, h in chains_at(tt, f, H1, READ_TOL):
                gt, gf = grad(kind, co, tt, f)
                if abs(gf) < 1e-9 or abs(gt) < 1e-6:
                    continue                      # no f in it, or at its extreme angle
                tb = angle_on(kind, co, fb, tt)
                if tb is None:
                    found.append((kind, co, h, tt, None, None)); continue
                second = []
                for k2, c2, r2, h2 in chains_at(tb, fb, H2, 2e-8):
                    if (k2, c2) == (kind, co):
                        continue
                    at, af = grad(kind, co, tb, fb); bt, bf = grad(k2, c2, tb, fb)
                    det = at * bf - af * bt
                    if abs(det) < 1e-9 * (1 + abs(at) + abs(bt)):
                        continue
                    fe = abs(r2 * at / det)
                    if fe <= F_TOL:
                        second.append((h2, k2, c2, fe))
                second.sort()
                found.append((kind, co, h, tt, tb, second[:2]))
            if found:
                break
        found.sort(key=lambda x: x[2])
        k = n - m * m
        print('n=%d (m=%d, k=%d) held f %.9f board f %.9f  tilted %d of %d at %.4f deg  chains %d' % (
            n, m, k, f, fb, cnt, ntilt, math.degrees(t), len(found)))
        for kind, co, h, tt, tb, second in found[:3]:
            if tb is None:
                print('    [%s]  no angle gives the board f' % fmt(kind, co)); continue
            s2 = '; '.join('second [%s] h=%d off %.1e' % (fmt(k2, c2), h2, fe) for h2, k2, c2, fe in second) or 'no second chain'
            print('    [%s] at %.4f  board angle %.4f (%+.4f)  %s' % (fmt(kind, co), math.degrees(tt), math.degrees(tb), math.degrees(tb - tt), s2))
            res.append((n, m, k, '%.9f' % f, '%.9f' % fb, cnt, ntilt, '%.5f' % math.degrees(tt), fmt(kind, co),
                        '%.5f' % math.degrees(tb), '%+.5f' % math.degrees(tb - tt),
                        ' | '.join('%s h=%d off %.1e' % (fmt(k2, c2), h2, fe) for h2, k2, c2, fe in second)))
    with open(out, 'w') as h:
        h.write('n\tm\tk\theld_f\tboard_f\ttilted_at_angle\ttilted\theld_deg\tchain\tboard_deg\tturn_deg\tsecond_chain\n')
        for r in res:
            h.write('\t'.join(str(v) for v in r) + '\n')


if __name__ == '__main__':
    main()
