#!/usr/bin/env python3
"""A diagonal band built from sticks, at the angle and side that forensics_curve.py reads off the board.

What the held layouts of 263 and 332 show: the band runs along the main diagonal between the
bottom-right grid and the top-left grid. It is a row of sticks. A stick is q squares face to face
across the band, turned by delta off 45 degrees. Sticks stand one unit apart and each slides along
its own length until it rests on the staircase. One corner of the bottom-right staircase and one
corner of the top-left staircase, (i + f, j + f) apart, hold a stick: (i + f) C + (j + f) S = q.

This tool builds such bands at a chosen (delta, f): runs of sticks of either turn, each stick resting
on the lower staircase or hanging from the upper one, then the exact upright fill (Evan Daniel's
fillfast, MIT, imported from his clone). A search over the runs looks for the count n.

Usage:
  forensics_sticks.py control HELD.csv N                      stick rebuild of the held blocks at the held angle
  forensics_sticks.py search N M F DELTA_DEG OUT [--chain 4,3,6] [--secs S] [--seed K] [--diag 3]
  forensics_sticks.py lock N M F DELTA_DEG OUT [--chain 4,3,6] [--p 13] [--diag 3] [--secs S]     one straight run on a corner
"""
import sys, os, math, time, random, argparse
import numpy as np

sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import fillfast  # noqa: E402
import forensics_turn as ft  # noqa: E402


class Channel:
    """The two staircases. Lower: corners (c + f + k, k) of the bottom-right grid. Upper: corners
    (c - i + k, j + f + k) of the top-left grid, so the pair k, k is (i + f, j + f) apart."""

    def __init__(self, m, f, c, i, j, q):
        self.m, self.f, self.c, self.i, self.j, self.q = m, f, c, i, j, q
        ks = np.arange(-3, m + 4)
        self.lo_peak = np.c_[c + f + ks, ks.astype(float)]            # top-left corners of bottom-right cells
        self.lo_val = self.lo_peak + np.array([1.0, 0.0])
        self.up_peak = np.c_[c - i + ks, j + f + ks]                  # bottom-right corners of top-left cells
        self.up_val = self.up_peak + np.array([0.0, 1.0])

    def rest(self, theta, u_lo, u_hi):
        """(v of the lower outline's highest point, v of the upper outline's lowest point) over the stick."""
        eu = np.array([math.cos(theta), math.sin(theta)]); ev = np.array([-math.sin(theta), math.cos(theta)])
        out = []
        for peak, val, sign in ((self.lo_peak, self.lo_val, 1), (self.up_peak, self.up_val, -1)):
            pts = np.r_[peak, val]
            U = pts @ eu; V = pts @ ev
            o = np.argsort(U); U, V = U[o], V[o]
            best = sign * np.interp([u_lo, u_hi], U, V).max() if sign > 0 else -np.interp([u_lo, u_hi], U, V).min()
            ins = (U > u_lo) & (U < u_hi)
            if ins.any():
                best = max(best, (sign * V[ins]).max())
            out.append(sign * best)
        return out[0], out[1]


def build(ch, runs, delta_deg):
    """runs: list of dict(turn=+1|-1, u0, p, split, du). The lower `split` rows of each stick rest on the
    lower staircase. The other rows hang from the upper staircase, moved by du along the band (the held
    layouts show such a slip between two layers). split = q is a whole stick at rest, split = 0 a whole
    stick that hangs. Returns the tilted squares and how many whole sticks do not fit."""
    T = []; misfit = 0
    for R in runs:
        theta = math.radians(45 + R['turn'] * delta_deg)
        eu = np.array([math.cos(theta), math.sin(theta)]); ev = np.array([-math.sin(theta), math.cos(theta)])
        deg = math.degrees(theta); deg = deg - 90 if deg > 45 else deg
        split = R.get('split', 0 if R.get('hang') else ch.q); du = R.get('du', 0.0)
        for s in range(R['p']):
            u_lo = R['u0'] + s
            lo, up = ch.rest(theta, u_lo, u_lo + 1)
            if lo + ch.q > up + 1e-9:
                misfit += 1
            for r in range(split):
                c = (u_lo + 0.5) * eu + (lo + r + 0.5) * ev
                T.append((float(c[0]), float(c[1]), deg))
            if split < ch.q:
                u2 = u_lo + du
                lo2, up2 = (lo, up) if du == 0.0 else ch.rest(theta, u2, u2 + 1)
                for r in range(split, ch.q):
                    c = (u2 + 0.5) * eu + (up2 - ch.q + r + 0.5) * ev
                    T.append((float(c[0]), float(c[1]), deg))
    return T, misfit


def valid(T, side, tol=1e-9):
    if not T:
        return True
    A = np.array(T)
    th = np.radians(A[:, 2]); c, s = np.cos(th) / 2, np.sin(th) / 2
    hw = np.abs(c) + np.abs(s)
    if (A[:, 0] - hw).min() < -tol or (A[:, 1] - hw).min() < -tol or (A[:, 0] + hw).max() > side + tol or (A[:, 1] + hw).max() > side + tol:
        return False
    n = len(A)
    E = np.stack([np.c_[np.cos(th), np.sin(th)], np.c_[-np.sin(th), np.cos(th)]], axis=1)
    for a in range(n):
        d = np.hypot(A[a + 1:, 0] - A[a, 0], A[a + 1:, 1] - A[a, 1])
        for b in np.nonzero(d < 1.4143)[0] + a + 1:
            sep = False
            for k in (a, b):
                for ax in E[k]:
                    dd = abs(ax @ (A[b, :2] - A[a, :2]))
                    need = (abs(ax @ E[a, 0]) + abs(ax @ E[a, 1]) + abs(ax @ E[b, 0]) + abs(ax @ E[b, 1])) / 2
                    if dd >= need - tol:
                        sep = True; break
                if sep:
                    break
            if not sep:
                return False
    return True


def count(ch, runs, delta_deg, time_limit=5):
    T, misfit = build(ch, runs, delta_deg)
    side = ch.m + ch.f
    if not T:
        return ch.m * ch.m, None, 0
    if not valid(T, side):
        return -1, None, misfit
    X = fillfast.fill(side, np.array(T, float).reshape(-1, 3), mode='exact', time_limit=time_limit)
    return len(X), X, misfit


def cmd_control(held, n, chain):
    s, A = ft.normalize(ft.load(held, n)); m = int(s); f = s - m
    import forensics_curve as fc
    t, cnt, nt = fc.main_angle([(x, y, math.radians(d)) for x, y, d in A])
    held_deg = math.degrees(t); delta = 45 - held_deg
    i, j, q = chain
    print('n', n, 'side', s, 'held angle', held_deg, 'delta', delta)
    for sign, comp in ft.blocks(A, held_deg):
        if len(comp) < 12:
            continue
        turn = -sign                                   # sign -1 in the file is 45 + delta
        theta = math.radians(45 + turn * delta)
        eu = np.array([math.cos(theta), math.sin(theta)]); ev = np.array([-math.sin(theta), math.cos(theta)])
        U = A[comp, :2] @ eu
        u0 = U.min() - 0.5; p = int(round(U.max() - U.min() + 1))
        Th = [tuple(A[k]) for k in comp]
        ch_best = None
        for c in range(0, 8):
            ch = Channel(m, f, c, i, j, q)
            for du in (0.0, -0.06, -0.03, 0.03, 0.06):
                for hang in (0, 1):
                    runs = [dict(turn=turn, u0=u0 + du, p=p, split=0 if hang else q, du=0.0)]
                    cnt2, _, mis = count(ch, runs, delta)
                    if ch_best is None or cnt2 > ch_best[0]:
                        ch_best = (cnt2, c, du, hang, mis)
        Xh = fillfast.fill(s, np.array(Th, float).reshape(-1, 3), mode='exact')
        print('   block of %d (turn %+d, %d sticks): the held squares alone fill to %d; sticks fill to %d (diagonal %d, shift %.2f, hang %d, misfits %d)' % (
            len(comp), turn, p, len(Xh), ch_best[0], ch_best[1], ch_best[2], ch_best[3], ch_best[4]))


def show(runs):
    return [(R['turn'], round(R['u0'], 3), R['p'], R.get('split', 0 if R.get('hang') else 6), round(R.get('du', 0.0), 3)) for R in runs]


def cmd_search(n, m, f, delta, out, chain, secs, seed, diag):
    i, j, q = chain
    ch = Channel(m, f, diag, i, j, q)
    rng = random.Random(seed)
    side = m + f
    umax = side * math.sqrt(2)
    cur = []; cur_c = m * m
    best_c, best_X, best = cur_c, None, []
    t0 = time.time(); it = 0
    print('n', n, 'side', side, 'delta', delta, 'chain', chain, 'diagonal', diag, 'plain grid', m * m, flush=True)
    while time.time() - t0 < secs and best_c < n:
        it += 1
        cand = [dict(R) for R in cur]
        r = rng.random()
        if (r < 0.15 or not cand) and len(cand) < 6:
            cand.append(dict(turn=rng.choice((1, -1)), u0=rng.uniform(2.0, umax - 4.0), p=rng.randint(1, 8), split=rng.choice((0, q, q, 3)), du=0.0))
        elif r < 0.22 and cand:
            cand.pop(rng.randrange(len(cand)))
        else:
            R = rng.choice(cand); z = rng.random()
            if z < 0.35:
                R['u0'] += rng.choice((-1, 1)) * rng.choice((0.005, 0.02, 0.08, 0.3)) * rng.random()
            elif z < 0.55:
                R['p'] = max(1, R['p'] + rng.choice((-1, 1)))
            elif z < 0.70:
                d = rng.choice((-1, 1)); R['p'] = max(1, R['p'] - d); R['u0'] += d
            elif z < 0.80:
                R['u0'] += rng.choice((-1, 1))
            elif z < 0.86:
                R['split'] = min(q, max(0, R.get('split', q) + rng.choice((-1, 1, -3, 3))))
            elif z < 0.94:
                R['du'] = 0.0 if rng.random() < 0.3 else R.get('du', 0.0) + rng.choice((-1, 1)) * rng.choice((0.01, 0.05, 0.2)) * rng.random()
            else:
                R['turn'] = -R['turn']
        c, X, mis = count(ch, cand, delta)
        if c < 0:
            continue
        if c >= cur_c or rng.random() < math.exp((c - cur_c) / 0.4):
            cur, cur_c = cand, c
            if c > best_c:
                best_c, best_X, best = c, X, [dict(R) for R in cand]
                print('   it %d %.0fs count %d (%+d) misfits %d runs %s' % (it, time.time() - t0, c, c - m * m, mis, show(cand)), flush=True)
    print('n', n, 'diagonal', diag, 'seed', seed, 'best count', best_c, 'need', n, 'tries', it, '%.0fs' % (time.time() - t0), 'runs', show(best), flush=True)
    if best_X is not None and best_c >= n:
        os.makedirs(out, exist_ok=True)
        tilt = [r for r in best_X if abs(r[2]) > 1e-6]; upr = [r for r in best_X if abs(r[2]) <= 1e-6]
        X = np.array(tilt + upr[:n - len(tilt)])
        p = '%s/%d-sticks-d%d-s%d.csv' % (out, n, diag, seed)
        ft.write_rows(p, n, X)
        print('wrote', p, flush=True)


def cmd_lock(n, m, f, delta, out, chain, pvals, secs, diag=3):
    """One straight run of p sticks whose first side passes through a corner of the bottom-left grid
    (or whose last side passes through a corner of the top-right grid). The first chain plus k times
    the chain without f reads, along the band, as p = 13 (18) sticks between two such corners."""
    i, j, q = chain
    side = m + f
    theta = math.radians(45 + delta); eu = np.array([math.cos(theta), math.sin(theta)])
    res = []; t0 = time.time(); tries = 0
    print('n', n, 'side', side, 'delta', delta, 'chain', chain, 'sticks', pvals, 'plain grid', m * m, flush=True)
    for c in range(max(1, diag - 2), diag + 4):
        ch = Channel(m, f, c, i, j, q)
        for X in range(0, m + 1):
            for Y in range(0, m + 1):
                if not (c - i - j - 2 <= X - Y <= c + 1):
                    continue
                for p in pvals:
                    for cls, u0 in (('BL', float(np.array([X, Y]) @ eu)), ('TR', float(np.array([X + f, Y + f]) @ eu) - p)):
                        for split in (q, 0, 3):
                            if time.time() - t0 > secs:
                                break
                            runs = [dict(turn=1, u0=u0, p=p, split=split, du=0.0)]
                            cnt, Xs, mis = count(ch, runs, delta)
                            tries += 1
                            if cnt > 0:
                                res.append((cnt, c, cls, X, Y, p, split, mis, Xs))
    res.sort(key=lambda r: -r[0])
    print('%d placements, %.0fs' % (tries, time.time() - t0), flush=True)
    for cnt, c, cls, X, Y, p, split, mis, Xs in res[:12]:
        print('   count %d (%+d)  diagonal %d, %s corner (%d, %d), %d sticks, %d rows at rest, misfits %d' % (cnt, cnt - m * m, c, cls, X, Y, p, split, mis), flush=True)
    k = 0
    for cnt, c, cls, X, Y, p, split, mis, Xs in res:
        if cnt < n or k >= 3:
            break
        os.makedirs(out, exist_ok=True)
        tilt = [r for r in Xs if abs(r[2]) > 1e-6]; upr = [r for r in Xs if abs(r[2]) <= 1e-6]
        path = '%s/%d-lock-%d.csv' % (out, n, k)
        ft.write_rows(path, n, np.array(tilt + upr[:n - len(tilt)]))
        print('wrote', path, flush=True); k += 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd'); ap.add_argument('args', nargs='*')
    ap.add_argument('--chain', default='4,3,6'); ap.add_argument('--secs', type=float, default=600)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--diag', type=int, default=3)
    ap.add_argument('--p', default='13')
    a = ap.parse_args()
    chain = tuple(int(v) for v in a.chain.split(','))
    if a.cmd == 'control':
        cmd_control(a.args[0], int(a.args[1]), chain)
    elif a.cmd == 'lock':
        n, m = int(a.args[0]), int(a.args[1]); f, delta = float(a.args[2]), float(a.args[3])
        cmd_lock(n, m, f, delta, a.args[4], chain, [int(v) for v in a.p.split(',')], a.secs, a.diag)
    else:
        n, m = int(a.args[0]), int(a.args[1]); f, delta = float(a.args[2]), float(a.args[3])
        cmd_search(n, m, f, delta, a.args[4], chain, a.secs, a.seed, a.diag)
