#!/usr/bin/env python3
"""Rebuild a diagonal band of turned blocks at another angle and side, with the exact upright fill.

The held layouts of 263, 332 and 409 are a band along the main diagonal between the top-left grid and
the bottom-right grid. The band is a row of blocks, each a rigid lattice of p squares along the band by
q across, turned by +delta or -delta off 45 degrees in turn. One corner of the bottom-right grid touches
the lower side of a block, and one corner of the top-left grid touches its upper side: that is the
chain (i + f) C + (j + f) S = q of forensics_curve.py.

This tool reads the blocks of a held layout, writes them again as exact lattices at a new (delta, f),
each on its own grid corner, fills the uprights exactly (Evan Daniel's fillfast, MIT, imported from his
clone, never copied into this repo) and searches the block parameters for the largest count.

Usage:
  forensics_band.py control HELD.csv N                      rebuild at the held angle and side
  forensics_band.py search HELD.csv N BOARD_F BOARD_DEG OUT [--secs S] [--seed K]
"""
import sys, os, math, csv, time, random, argparse
import numpy as np

sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import fillfast  # noqa: E402
import forensics_turn as ft  # noqa: E402


def frame(theta):
    c, s = math.cos(theta), math.sin(theta)
    return np.array([c, s]), np.array([-s, c])


def read_blocks(A, s, held_deg):
    """Blocks of the held layout: dict(sign, p, q, a, b, uoff, voff). (a + f, b) is the corner of the
    bottom-right grid nearest to the lower side; voff is the distance left to it (0 when it touches)."""
    m = int(s); f = s - m
    out = []
    used = set()
    for sign, comp in ft.blocks(A, held_deg):
        if len(comp) < 6:
            continue
        fold = held_deg if held_deg <= 45 else held_deg - 90
        theta = math.radians(sign * fold) % (math.pi / 2)
        eu, ev = frame(theta)
        U = A[comp, :2] @ eu; V = A[comp, :2] @ ev
        u0, v0 = U.min() - 0.5, V.min() - 0.5
        p = int(round(U.max() - U.min() + 1)); q = int(round(V.max() - V.min() + 1))
        best = None
        for a in range(0, m + 1):
            for b in range(0, m + 1):
                P = np.array([a + f, b])
                d = v0 - P @ ev
                u = P @ eu
                if -1e-3 <= d < 0.6 and u0 - 1.0 <= u <= u0 + p + 1.0:
                    if best is None or d < best[0]:
                        best = (d, a, b, u0 - u)
        if best is None:
            continue
        used.update(comp)
        out.append(dict(sign=sign, p=p, q=q, a=best[1], b=best[2], uoff=float(best[3]), voff=float(best[0]), size=len(comp)))
    rest = [i for i in range(len(A)) if abs(A[i, 2]) > 1e-6 and i not in used]
    return out, rest


def build(blocks, m, f, delta_deg):
    """Tilted squares (x, y, deg) of the blocks at this side and angle."""
    T = []
    for B in blocks:
        theta = math.radians(45 - B['sign'] * delta_deg)
        eu, ev = frame(theta)
        P = np.array([B['a'] + f, B['b']])
        u0 = P @ eu + B['uoff']; v0 = P @ ev + B['voff']
        deg = math.degrees(theta)
        deg = deg - 90 if deg > 45 else deg
        for i in range(B['p']):
            for j in range(B['q']):
                c = (u0 + i + 0.5) * eu + (v0 + j + 0.5) * ev
                T.append((float(c[0]), float(c[1]), deg))
    return T


def corners(T):
    P = []
    for x, y, d in T:
        t = math.radians(d); c, s = math.cos(t) / 2, math.sin(t) / 2
        P.append([(x + c - s, y + s + c), (x - c - s, y - s + c), (x - c + s, y - s - c), (x + c + s, y + s - c)])
    return np.array(P)


def valid(T, s, tol=1e-9):
    """Inside the box, and no two tilted squares of different angles overlap (separating axis test)."""
    if not T:
        return True
    P = corners(T)
    if P[:, :, 0].min() < -tol or P[:, :, 1].min() < -tol or P[:, :, 0].max() > s + tol or P[:, :, 1].max() > s + tol:
        return False
    A = np.array(T)
    n = len(T)
    for i in range(n):
        for j in range(i + 1, n):
            if abs(A[i, 2] - A[j, 2]) < 1e-9:
                # same lattice angle: squares of one block never overlap; two blocks of one angle are checked too
                pass
            if math.hypot(A[i, 0] - A[j, 0], A[i, 1] - A[j, 1]) > 1.4143:
                continue
            sep = False
            for k in (i, j):
                t = math.radians(A[k, 2])
                for ax in ((math.cos(t), math.sin(t)), (-math.sin(t), math.cos(t))):
                    pi = P[i] @ np.array(ax); pj = P[j] @ np.array(ax)
                    if pi.max() <= pj.min() + tol or pj.max() <= pi.min() + tol:
                        sep = True; break
                if sep:
                    break
            if not sep:
                return False
    return True


def count(blocks, extra, m, f, delta):
    T = build(blocks, m, f, delta) + list(extra)
    s = m + f
    if not valid(T, s):
        return -1, None
    X = fillfast.fill(s, np.array(T, float).reshape(-1, 3), mode='exact', time_limit=5)
    return len(X), X


def cmd_control(held, n):
    s, A = ft.normalize(ft.load(held, n)); m = int(s); f = s - m
    import forensics_curve as fc
    t, cnt, nt = fc.main_angle([(x, y, math.radians(d)) for x, y, d in A])
    held_deg = math.degrees(t)
    T0 = [tuple(r) for r in A if abs(r[2]) > 1e-6]
    X = fillfast.fill(s, np.array(T0, float).reshape(-1, 3), mode='exact')
    print('n', n, 'side', s, 'held tilted', len(T0), 'refill of the held tilted squares ->', len(X), '(held %d)' % n)
    blocks, rest = read_blocks(A, s, held_deg)
    for B in blocks:
        print('   block', B)
    extra = [tuple(A[i]) for i in rest]
    c, _ = count(blocks, extra, m, f, 45 - held_deg)
    print('   lattice rebuild at the held angle and side, with %d other tilted squares kept: %d' % (len(extra), c))
    c2, _ = count(blocks, [], m, f, 45 - held_deg)
    print('   lattice rebuild without them: %d' % c2)


def cmd_search(held, n, fb, board_deg, out, secs, seed):
    s, A = ft.normalize(ft.load(held, n)); m = int(s)
    import forensics_curve as fc
    t, cnt, nt = fc.main_angle([(x, y, math.radians(d)) for x, y, d in A])
    blocks, rest = read_blocks(A, s, math.degrees(t))
    delta = 45 - board_deg
    rng = random.Random(seed)
    cur = [dict(B) for B in blocks]
    best_c, best_X = count(cur, [], m, fb, delta)
    best = [dict(B) for B in cur]
    print('n', n, 'target side', m + fb, 'delta', delta, 'start blocks', len(cur), 'count', best_c, 'need', n, flush=True)
    t0 = time.time(); it = 0
    cur_c = best_c
    while time.time() - t0 < secs and best_c < n:
        it += 1
        cand = [dict(B) for B in cur]
        mv = rng.random()
        if mv < 0.08 and len(cand) < 6:
            B = dict(rng.choice(cand)); B['sign'] = -B['sign'] if rng.random() < 0.5 else B['sign']
            B['a'] = rng.randint(3, m - 1); B['b'] = B['a'] - rng.choice((2, 3, 4)); B['p'] = rng.choice((2, 3, 4, 5)); B['voff'] = 0.0
            B['uoff'] = -rng.uniform(0, B['p'])
            cand.append(B)
        elif mv < 0.14 and len(cand) > 1:
            cand.pop(rng.randrange(len(cand)))
        else:
            B = rng.choice(cand); r = rng.random()
            if r < 0.40:
                B['uoff'] += rng.choice((-1, 1)) * rng.choice((0.01, 0.03, 0.1, 0.3, 1.0)) * rng.random()
            elif r < 0.55:
                B['p'] = max(1, B['p'] + rng.choice((-1, 1)))
            elif r < 0.65:
                d = rng.choice((-1, 1)); B['p'] = max(1, B['p'] - d); B['uoff'] += d      # trim or grow at the low end
            elif r < 0.80:
                d = rng.choice((-1, 1)); B['a'] += d; B['b'] += d                           # next corner along the staircase
            elif r < 0.88:
                B['a'] += rng.choice((-1, 1))
            elif r < 0.94:
                B['sign'] = -B['sign']
            else:
                B['voff'] = 0.0 if B['voff'] else rng.uniform(0, 0.05)
        c, X = count(cand, [], m, fb, delta)
        if c >= cur_c or rng.random() < math.exp((c - cur_c) / 0.35):
            cur, cur_c = cand, c
            if c > best_c:
                best_c, best_X, best = c, X, [dict(B) for B in cand]
                print('   it %d  %.0fs  count %d  blocks %s' % (it, time.time() - t0, c, [(B['sign'], B['p'], B['q'], B['a'], B['b'], round(B['uoff'], 3), round(B['voff'], 3)) for B in cand]), flush=True)
    print('n', n, 'best count', best_c, 'of', n, 'after', it, 'tries, %.0fs' % (time.time() - t0), flush=True)
    if best_X is not None and best_c >= n:
        os.makedirs(out, exist_ok=True)
        X = best_X[:n] if best_c == n else best_X
        tilt = [r for r in best_X if abs(r[2]) > 1e-6]; upr = [r for r in best_X if abs(r[2]) <= 1e-6]
        X = np.array(tilt + upr[:n - len(tilt)])
        ft.write_rows('%s/%d-band-s%d.csv' % (out, n, seed), n, X)
        print('wrote', '%s/%d-band-s%d.csv' % (out, n, seed), 'squares', len(X), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'control':
        cmd_control(sys.argv[2], int(sys.argv[3]))
    else:
        ap = argparse.ArgumentParser()
        ap.add_argument('cmd'); ap.add_argument('held'); ap.add_argument('n', type=int); ap.add_argument('fb', type=float)
        ap.add_argument('board_deg', type=float); ap.add_argument('out')
        ap.add_argument('--secs', type=float, default=600); ap.add_argument('--seed', type=int, default=1)
        a = ap.parse_args()
        cmd_search(a.held, a.n, a.fb, a.board_deg, a.out, a.secs, a.seed)
