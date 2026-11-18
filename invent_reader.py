#!/usr/bin/env python3
"""A corner module from a two-arm layout that modules.cut refuses: cut along the stacks, then settle against flush stacks.

  invent_reader.py corner DETAILS.csv HELD.csv SCRATCH OUT.pkl OUT.tsv N [N ...] [--stacks 2.5,3.5,4.5] [--file N=PATH]

modules.cut needs three whole flush stacks of one size on each of two walls, and refuses a layout whose stacks are
sheared, stand off the wall or have many sizes. This reader asks for none of that. It turns the layout so that the
narrower arm is on the left wall and the other on the bottom wall, and takes the arm sizes from the main tilt on each
wall, as invent_parts.py does. It then cuts each arm along a line between two stacks, a few stacks from the corner,
and keeps what lies before the two cuts. The squares of the plain rest that stand on its lattice stay the rest. A
lattice cell with no square on it is a missing cell, and a square of the rest that is off the lattice goes to the corner.
The corner is then settled against the first flush stack of each arm with zone_corner.settle_zone (soft squeeze, the
contact LP, the exact test). A layout is read when a settle ends legal. Its loss is zone_corner.loss_of at the settled
lengths, with the count lowered by the missing cells, so it is in the frame of the library: a corner read here can be
compared with the staircase and block corners, and one with no missing cell is a base corner for `zone_corner.py adopt`.

The cut may fall inside the taper of an arm. The squares beyond it are then dropped, and the result is a smaller
corner than the layout's own. It is still a legal corner with a true loss, so the reader keeps the lowest loss over
the cut places of --stacks (in stacks from the corner, the same for both arms).

Our own code. Reads x, y, angle rows. Imports zone_corner and modules of this lane.
"""
import csv, glob, math, os, pickle, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M
import zone_corner as ZC

num = lambda v: float(str(v).lstrip('s'))
CACHE = {}


def rows_of(path, n):
    if path not in CACHE:
        d = {}
        for r in csv.DictReader(open(path)): d.setdefault(r.get('n', ''), []).append(r)
        CACHE[path] = d
    d = CACHE[path]
    return d.get(str(n)) or d.get('') or []


def lowest(S, held, n):
    """the lowest file of n over the held file and the take dirs of rounds 17 and 19 -> (side, lane, path or None)"""
    best = (held[n], 'held', None)
    for d in sorted(glob.glob(S + '/take-*-r17') + glob.glob(S + '/take-*-r19')):
        p = d + '/take.tsv'
        if not os.path.exists(p): continue
        try: R = list(csv.DictReader(open(p), delimiter='\t'))
        except Exception: continue
        for r in R:
            try: nn = int(r['n']); new = float(r['new'])
            except Exception: continue
            f = '%s/%d.csv' % (d, n)
            if nn == n and os.path.exists(f) and (new + 1) * math.sqrt(n) < best[0]: best = ((new + 1) * math.sqrt(n), os.path.basename(d)[5:], f)
    return best


def load(path, n):
    R = rows_of(path, n)
    P = np.array([[num(r['x']), num(r['y']), num(r['angle'])] for r in R])
    c, s = np.abs(np.cos(P[:, 2])), np.abs(np.sin(P[:, 2])); h = (c + s) / 2
    lo = min((P[:, 0] - h).min(), (P[:, 1] - h).min()); L = max((P[:, 0] + h).max(), (P[:, 1] + h).max()) - lo
    P[:, 0] -= lo; P[:, 1] -= lo
    return P, L


def turn(P, L, k):
    """the k-th of the 8 symmetries of the box"""
    x, y, a = P[:, 0].copy(), P[:, 1].copy(), P[:, 2].copy()
    if k & 1: x = L - x; a = -a
    if k & 2: y = L - y; a = -a
    if k & 4: x, y = y, x; a = math.pi / 2 - a
    return np.stack([x, y, a], 1)


def signed(a): return ((np.degrees(a) + 45) % 90) - 45


def frame(P, L):
    """-> dict(Q, m, f, c1, c2, lean1, lean2) with the narrower arm on the left wall, or a str that says why not"""
    m = int(L + 1e-9); f = L - m; best = None
    for k in range(8):
        Q = turn(P, L, k); t = np.abs(signed(Q[:, 2])); T = Q[t > 1.0]
        if len(T) < 20: return 'fewer than 20 tilted squares'
        near = ((T[:, 0] < 12.5) | (T[:, 1] < 12.5)).sum()
        left = T[(T[:, 0] < 9) & (T[:, 1] > 13)]; bot = T[(T[:, 1] < 9) & (T[:, 0] > 13)]
        if len(left) < 10 or len(bot) < 10: continue
        tl = math.radians(float(np.median(np.abs(signed(left[:, 2]))))); tb = math.radians(float(np.median(np.abs(signed(bot[:, 2])))))
        cl = (1 - f + math.sin(tl)) / (1 - math.cos(tl)); cb = (1 - f + math.sin(tb)) / (1 - math.cos(tb))
        key = (int(near), -int(cl > cb + 0.25), -abs(len(left) - len(bot)), len(left))      # most tilted squares near the two walls, then the narrower arm on the left
        if best is None or key > best[0]: best = (key, Q, left, bot, cl, cb)
    if best is None: return 'not two arms on two walls that meet'
    _, Q, left, bot, cl, cb = best
    c1, c2 = round(cl), round(cb)
    if abs(c1 - cl) > 0.25 or abs(c2 - cb) > 0.25: return 'arm sizes %.2f %.2f are not whole' % (cl, cb)
    if c1 < 3 or c2 < 3: return 'arm sizes %d %d' % (c1, c2)
    return dict(Q=Q, m=m, f=f, c1=c1, c2=c2, lean1=1 if np.median(signed(left[:, 2])) > 0 else -1, lean2=1 if np.median(signed(bot[:, 2])) > 0 else -1)


def cut_line(T, W, mid):
    """T: the squares of an arm on the left wall (x across the strip, y along the wall). The line along the stacks,
    between two stacks, nearest to y = mid on the middle of the strip. -> (q of every square of T, q of the cut, y where
    the cut crosses the middle of the strip) or None"""
    s = signed(T[:, 2]); tl = np.abs(s) > 1.0
    if tl.sum() < 4: return None
    sm = math.radians(float(np.median(s[tl])))
    v = (-math.sin(sm), math.cos(sm))                       # across the stacks
    q = T[:, 0] * v[0] + T[:, 1] * v[1]
    qmid = W / 2 * v[0] + mid * v[1]
    qq = np.sort(q[tl & (np.abs(q - qmid) < 1.6)])
    if len(qq) < 2: return None
    i = int(np.argmax(np.diff(qq))); qc = (qq[i] + qq[i + 1]) / 2
    return q, qc, (qc - W / 2 * v[0]) / v[1]


def corner_of(fr, stacks):
    """the corner of a framed layout cut `stacks` stacks from the corner -> (mod, squares in degrees, y0, x0, count) or a str"""
    Q, f, c1, c2 = fr['Q'], fr['f'], fr['c1'], fr['c2']
    mod = ZC.cmod(c1, c2, fr['lean1'], fr['lean2']); t1, t2, p1, p2, W1, W2 = ZC.geom(mod, f)
    x, y = Q[:, 0], Q[:, 1]; s = signed(Q[:, 2])
    in1 = (x < W1) & (y >= W2); in2 = (y < W2) & (x >= W1); box = (x < W1) & (y < W2); rest = (x >= W1) & (y >= W2)
    c1cut = cut_line(Q[in1], W1, W2 + stacks * p1)
    T2 = Q[in2][:, [1, 0, 2]] * [1, 1, -1] + [0, 0, math.pi / 2]
    c2cut = cut_line(T2, W2, W1 + stacks * p2)
    if c1cut is None or c2cut is None: return 'no line between two stacks'
    y0, x0 = c1cut[2], c2cut[2]
    keep = box.copy()
    keep[np.nonzero(in1)[0][c1cut[0] <= c1cut[1]]] = True
    keep[np.nonzero(in2)[0][c2cut[0] <= c2cut[1]]] = True
    # the rest beside the corner, up to the two cuts: the cells corner_state holds there; a cell with no square on its
    # lattice place is missing, and a square of the rest there that is off the lattice goes to the corner. Beyond a
    # cut the rest is the lattice, as it is beside the flush stacks of a built layout
    deep = max(M.DEEP, 2)
    im = max(int(math.floor(x0 - W1)), deep + 1); jm = max(int(math.floor(y0 - W2)), deep + 1)
    ri = np.nonzero(rest)[0]; used = set(); miss = []
    for i in range(im):
        for j in range(jm):
            if not (i <= deep or j <= deep): continue
            d = np.hypot(x[ri] - (W1 + .5 + i), y[ri] - (W2 + .5 + j))
            k = int(np.argmin(d)) if len(ri) else -1
            if k >= 0 and d[k] < 0.02 and abs(s[ri[k]]) < 0.5: used.add(int(ri[k]))
            else: miss.append((i, j))
    for k in ri:
        if int(k) in used: continue
        i, j = x[k] - W1, y[k] - W2
        if (i < deep + 1 and j < jm) or (j < deep + 1 and i < im): keep[k] = True
    P = Q[keep].copy(); P[:, 2] = signed(P[:, 2])
    mod['miss'] = miss
    return mod, P, float(y0), float(x0), len(P) - len(miss)


def read_corner(fr, stacks_list, log=None):
    """the lowest settled corner over the cut places -> dict or a str that says why not"""
    best = None; why = ''
    for st in stacks_list:
        r = corner_of(fr, st)
        if isinstance(r, str): why = r; continue
        mod, P, y0, x0, count = r
        if len(mod['miss']) > 12: why = '%d cells of the rest are off the lattice' % len(mod['miss']); continue
        try: z = ZC.settle_zone(P, mod, fr['f'], y0 + 0.05, x0 + 0.05)
        except Exception as ex: z = None; why = 'settle failed: %s' % ex
        if z is None: why = why or 'no legal settle'; continue
        ys, xs, Pz = z; ls = ZC.loss_of(mod, fr['f'], count, ys, xs)
        if log: log('    cut at %.1f stacks: %d squares, %d missing cells, y0 %.4f -> %.4f, x0 %.4f -> %.4f, loss %.4f' % (st, len(P), len(mod['miss']), y0, ys, x0, xs, ls))
        if best is None or ls < best['loss']: best = dict(mod=mod, P=Pz, y0=ys, x0=xs, count=count, loss=ls, stacks=st, cut=(y0, x0))
    return best if best is not None else (why or 'no cut')


def main():
    a = sys.argv[1:]
    if a[0] != 'corner': print(__doc__); return 1
    details, heldp, S, outp, outt = a[1:6]; rest = a[6:]
    stacks = [2.5, 3.5, 4.5]; files = {}; ns = []
    i = 0
    while i < len(rest):
        if rest[i] == '--stacks': stacks = [float(v) for v in rest[i + 1].split(',')]; i += 2
        elif rest[i] == '--file': n_, p_ = rest[i + 1].split('='); files[int(n_)] = p_; i += 2
        else: ns.append(int(rest[i])); i += 1
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    base = []; t0 = time.time()
    with open(outt, 'w') as h:
        h.write('n\tfile_of\tside\tf\tc1\tc2\tlean1\tlean2\tread\tsquares\tmissing_cells\tcut_stacks\ty0\tx0\tloss\tnote\n')
        for n in ns:
            L, lane, path = lowest(S, held, n)
            if n in files: lane, path = 'file', files[n]
            P, L2 = load(path or heldp, n)
            fr = frame(P, L2)
            if isinstance(fr, str):
                h.write('%d\t%s\t%.9f\t\t\t\t\t\t0\t\t\t\t\t\t\t%s\n' % (n, lane, L2, fr)); h.flush()
                print('n %d (%s): not read: %s' % (n, lane, fr), flush=True); continue
            print('n %d (%s) side %.6f: arms %d and %d, leans %+d %+d (%.0f s)' % (n, lane, L2, fr['c1'], fr['c2'], fr['lean1'], fr['lean2'], time.time() - t0), flush=True)
            r = read_corner(fr, stacks, log=lambda s_: print(s_, flush=True))
            if isinstance(r, str):
                h.write('%d\t%s\t%.9f\t%.4f\t%d\t%d\t%d\t%d\t0\t\t\t\t\t\t\t%s\n' % (n, lane, L2, fr['f'], fr['c1'], fr['c2'], fr['lean1'], fr['lean2'], r)); h.flush()
                print('n %d: not read: %s' % (n, r), flush=True); continue
            h.write('%d\t%s\t%.9f\t%.4f\t%d\t%d\t%d\t%d\t1\t%d\t%d\t%.1f\t%.6f\t%.6f\t%.4f\t\n' % (
                n, lane, L2, fr['f'], fr['c1'], fr['c2'], fr['lean1'], fr['lean2'], len(r['P']), len(r['mod']['miss']), r['stacks'], r['y0'], r['x0'], r['loss'])); h.flush()
            print('n %d: READ corner of %d and %d at f %.4f: %d squares, %d missing cells, loss %.4f' % (n, fr['c1'], fr['c2'], fr['f'], len(r['P']), len(r['mod']['miss']), r['loss']), flush=True)
            if not r['mod']['miss']:
                base.append(dict(id='rd%dx%d-%df%04dn%d' % (fr['c1'], fr['c2'], r['count'], round(fr['f'] * 1e4), n),
                                 src='invent_reader.py: the corner of the layout of n = %d (%s), cut %.1f stacks from the corner and settled' % (n, lane, r['stacks']),
                                 licence='see the source of n = %d' % n, c1=fr['c1'], c2=fr['c2'], lean1=fr['lean1'], lean2=fr['lean2'], f=fr['f'],
                                 count=r['count'], y0=r['y0'], x0=r['x0'], P=r['P']))
    pickle.dump(base, open(outp, 'wb'))
    print('%d n, %d corners with no missing cell written to %s' % (len(ns), len(base), outp))
    return 0


if __name__ == '__main__':
    sys.exit(main())
