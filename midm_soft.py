#!/usr/bin/env python3
"""midm: a soft-box island for one n that starts in a box just under the held side, from many seeds at once.

methods_soft.py hangs its box under one legal layout and walks down in steps of DELTA. Here the box is set
DELTA below the held side of n from the first child, and the seeds are layouts of other n pressed into it:
  best   the held layout of n
  drop1  the layout of n+1 with one square removed (every square in turn)
  drop2  the layout of n+2 with a square and one of its neighbours removed
  grow1  the layout of n-1 with one square put into a wide hole
  peel   the layout of the same k one shell up (n + 2m + 1 squares, m = whole part of the held side) with one
         strip of width 1 cut out along x and one along y, at every pair of cut positions, and the parts
         pushed together into the box. A cut that removes a few squares too many or too few is mended with
         the squares nearest the cut. peel2 does the same from two shells up with strips of width 2
  jog    the same donor as peel with a clean cut: one straight strip across the box and one strip at right
         angles to it that may stand at one place on one side of the first strip and at another place on the
         other side (a jog), so that it passes beside two tilted patches. Only cuts that remove at most
         --max-tilt tilted squares and the right count of squares (to 1) are kept
  splice the left part of one layout and the right part of another, for every ordered pair of the layouts of
         n-3 to n+3, every one of the 8 turns and mirror images of the second, and every cut position (step
         0.5) where the two parts hold n squares between them
Every seed is relaxed once in that box (the overlap energy of methods_soft, its C kernel). The POP lowest
energies make the population, and the island then runs the moves of methods_soft at the fixed box. A member
that becomes soft-free is made legal with the ladder and the exact LP of methods_soft; a legal side below the
held one is a find, written to OUT/raw/<n>-seed-<seed>.csv (raw rows; methods_take.py certifies).

Usage: midm_soft.py --n N --sub HELD.csv [--donors FILE.csv] --out DIR [--seconds 150] [--seed 1] [--delta 2e-4]
                    [--kinds best,drop1,drop2,grow1,peel,peel2,jog,splice] [--pop 12] [--cap 400] [--deadline FILE]
Log: OUT/seed-<n>-<seed>.log (the seed energies per kind, the island every 500 children, FIND or END).
"""
import argparse, math, os, sys, time

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402
import methods_soft as ms  # noqa: E402


def tilted(P):
    d = np.degrees(P[:, 2]) % 90.0
    return np.minimum(d, 90 - d) > 1e-4


def order(P, rng):
    """Every square once: tilted ones, then the squares within 1.6 of a tilted one, then the rest."""
    t = tilted(P); near = np.zeros(len(P), bool)
    if t.any():
        dist, _ = cKDTree(P[t, :2]).query(P[:, :2]); near = (dist < 1.6) & ~t
    gs = [np.flatnonzero(t), np.flatnonzero(near), np.flatnonzero(~t & ~near)]
    for g in gs:
        rng.shuffle(g)
    return np.concatenate(gs)


def press(P, box):
    """Scale the centres of a layout into the box (the squares keep their size, so they overlap or get room)."""
    Q = mlp.normal(P); L = mlp.side(Q); h = mlp.half(Q[:, 2])
    f = (box - 1.0) / (L - 1.0)          # maps the centre range of an upright frame [0.5, L - 0.5] onto the box
    R = Q.copy()
    R[:, 0] = 0.5 + (Q[:, 0] - 0.5) * f; R[:, 1] = 0.5 + (Q[:, 1] - 0.5) * f
    R[:, 0] = np.clip(R[:, 0], h, box - h); R[:, 1] = np.clip(R[:, 1], h, box - h)
    return R


def peel_seeds(D, n, box, step=0.25, tol=4, width=1.0):
    """Strip cuts of the donor layout D that leave n squares, pressed into the box. Yields (P, x0, y0)."""
    Q = mlp.normal(D); L1 = mlp.side(Q); need = len(Q) - n; seen = set()
    x, y = Q[:, 0], Q[:, 1]; sh = L1 - box
    cuts = np.arange(0.0, L1 - width + 1e-9, step)
    for x0 in cuts:
        dx = np.where(x < x0, x0 - x, np.where(x >= x0 + width, x - x0 - width, -np.minimum(x - x0, x0 + width - x)))
        for y0 in cuts:
            dy = np.where(y < y0, y0 - y, np.where(y >= y0 + width, y - y0 - width, -np.minimum(y - y0, y0 + width - y)))
            d = np.minimum(dx, dy)                 # < 0 inside a strip (depth), > 0 outside (distance to the nearest strip)
            cnt = int((d < 0).sum())
            if abs(cnt - need) > tol:
                continue
            rm = np.argsort(d)[:need]              # the deepest squares go; a mend takes the squares nearest the cut
            key = rm.tobytes() if False else tuple(sorted(rm.tolist()))
            if key in seen:
                continue
            seen.add(key)
            keep = np.ones(len(Q), bool); keep[rm] = False
            P = Q[keep].copy()
            P[:, 0] -= np.where(P[:, 0] >= x0 + width / 2, sh, 0.0); P[:, 1] -= np.where(P[:, 1] >= y0 + width / 2, sh, 0.0)
            h = mlp.half(P[:, 2])
            P[:, 0] = np.clip(P[:, 0], h, box - h); P[:, 1] = np.clip(P[:, 1], h, box - h)
            yield P, x0, y0


def jog_seeds(D, n, box, step=0.25, tol=1, max_tilt=2, width=1.0, cap=5000, rng=None):
    """Jogged strip cuts of the donor D that leave n squares, pressed into the box. Yields (P, tag)."""
    Q0 = mlp.normal(D); L1 = mlp.side(Q0); need = len(Q0) - n; sh = L1 - box; tl = tilted(Q0)
    cuts = np.arange(0.0, L1 - width + 1e-9, step); out = []; seen = set()
    for tr in (0, 1):
        x, y = (Q0[:, 0], Q0[:, 1]) if tr == 0 else (Q0[:, 1], Q0[:, 0])
        SX = (x[None, :] >= cuts[:, None]) & (x[None, :] < cuts[:, None] + width)        # cut i holds square j
        for y0 in cuts:
            iny = (y >= y0) & (y < y0 + width); ty = int(tl[iny].sum())
            if ty > max_tilt:
                continue
            up = y >= y0 + width; lo = y < y0
            A = SX & up[None, :]; B = SX & lo[None, :]
            ca = A.sum(1); cb = B.sum(1); ta = (A & tl[None, :]).sum(1); tb = (B & tl[None, :]).sum(1)
            cnt = int(iny.sum()) + ca[:, None] + cb[None, :]; tt = ty + ta[:, None] + tb[None, :]
            for i, j in zip(*np.nonzero((np.abs(cnt - need) <= tol) & (tt <= max_tilt))):
                rm = iny | A[i] | B[j]
                key = (tr, rm.tobytes())
                if key in seen:
                    continue
                seen.add(key); out.append((tr, float(y0), float(cuts[i]), float(cuts[j]), rm, int(cnt[i, j]) - need))
    if rng is not None and len(out) > cap:
        out = [out[k] for k in rng.choice(len(out), cap, replace=False)]
    for tr, y0, xa, xb, rm, extra in out:
        x, y = (Q0[:, 0], Q0[:, 1]) if tr == 0 else (Q0[:, 1], Q0[:, 0])
        rm = rm.copy()
        if extra > 0:
            # too many: put back the removed upright squares nearest an edge of their strip
            idx = np.flatnonzero(rm & ~tl)
            edge = np.minimum(np.abs((y[idx] - y0) % 1.0 - 0.5), 0.5)      # a rough depth; any upright one will do
            rm[idx[np.argsort(-edge)[:extra]]] = False
        P = Q0[~rm].copy(); xs, ys = x[~rm].copy(), y[~rm].copy()
        upper = ys >= y0 + width / 2
        xs -= np.where(xs >= np.where(upper, xa, xb) + width / 2, sh, 0.0); ys -= np.where(upper, sh, 0.0)
        if tr == 0:
            P[:, 0], P[:, 1] = xs, ys
        else:
            P[:, 1], P[:, 0] = xs, ys
        if extra < 0:
            # too few: the squares that overlap most after the press go
            for _ in range(-extra):
                P = np.delete(P, int(np.argmax(ms.overlap_weight(P, box))), 0)
        h = mlp.half(P[:, 2])
        P[:, 0] = np.clip(P[:, 0], h, box - h); P[:, 1] = np.clip(P[:, 1], h, box - h)
        if len(P) == n:
            yield P, '%s y%.2f xa%.2f xb%.2f %+d' % ('xy'[tr], y0, xa, xb, extra)


def turns(P):
    """The 8 turns and mirror images of a layout in its own box."""
    Q = mlp.normal(P); L = mlp.side(Q); out = []
    for tr in (0, 1):
        A = Q.copy()
        if tr:
            A[:, 0], A[:, 1], A[:, 2] = Q[:, 1].copy(), Q[:, 0].copy(), math.pi / 2 - Q[:, 2]
        for mx in (0, 1):
            for my in (0, 1):
                B = A.copy()
                if mx:
                    B[:, 0] = L - B[:, 0]; B[:, 2] = -B[:, 2]
                if my:
                    B[:, 1] = L - B[:, 1]; B[:, 2] = -B[:, 2]
                out.append(B)
    return out


def splice_seeds(don, n, box, cap, rng, step=0.5):
    """Left part of layout a, right part of a turn of layout b, where the two parts hold n squares. Yields (P, tag)."""
    ks = sorted(k for k in don if abs(k - n) <= 3)
    pressed = {k: [press(T, box) for T in turns(don[k])] for k in ks}
    cuts = np.arange(2.0, box - 2.0 + 1e-9, step); combos = []
    for a in ks:
        A = pressed[a][0]; ca = (A[:, 0][None, :] < cuts[:, None]).sum(1)
        for b in ks:
            for t, B in enumerate(pressed[b]):
                if a == b and t == 0:
                    continue
                cb = (B[:, 0][None, :] >= cuts[:, None]).sum(1)
                for i in np.flatnonzero(ca + cb == n):
                    combos.append((a, b, t, float(cuts[i])))
    if len(combos) > cap:
        combos = [combos[k] for k in rng.choice(len(combos), cap, replace=False)]
    for a, b, t, c in combos:
        A = pressed[a][0]; B = pressed[b][t]
        yield np.vstack([A[A[:, 0] < c], B[B[:, 0] >= c]]), 'a%d b%d t%d c%.1f' % (a, b, t, c)


def settle(P, box, rounds=3, maxiter=1500):
    """Relax with a fresh pair list each round; the energy returned is a fresh count."""
    for _ in range(rounds):
        P, _ = ms.relax(P, box, maxiter)
    return P, ms.total_energy(P, box)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, required=True); ap.add_argument('--sub', required=True); ap.add_argument('--donors')
    ap.add_argument('--out', required=True); ap.add_argument('--seconds', type=float, default=150)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--delta', type=float, default=2e-4)
    ap.add_argument('--kinds', default='best,drop1,drop2,grow1'); ap.add_argument('--pop', type=int, default=12)
    ap.add_argument('--cap', type=int, default=400, help='most seeds of one kind'); ap.add_argument('--deadline')
    ap.add_argument('--max-tilt', type=int, default=2)
    ap.add_argument('--moves', default='row,ang,jig,clu,twi,blk,arm'); ap.add_argument('--maxiter', type=int, default=200)
    a = ap.parse_args()
    n = a.n; os.makedirs(a.out + '/raw', exist_ok=True)
    ms.load_kernel()
    rng = np.random.default_rng(a.seed * 104729 + n)
    held = mlp.normal(mlp.load(a.sub, {n})[n]); Lheld = mlp.side(held)
    m = int(math.floor(Lheld)); n_up = n + 2 * m + 1; n_up2 = n + 4 * m + 4
    don = mlp.load(a.donors or a.sub, {n - 1, n + 1, n + 2, n_up, n_up2} | set(range(n - 3, n + 4)))
    box = Lheld - a.delta; moves = a.moves.split(','); kinds = a.kinds.split(',')
    dl = float(open(a.deadline).read()) if a.deadline else math.inf
    lg = open('%s/seed-%d-%d.log' % (a.out, n, a.seed), 'a')

    def log(s):
        lg.write(s + '\n'); lg.flush()
    log('start n=%d held %.12f box %.12f delta %g kinds %s %s' % (n, Lheld, box, a.delta, a.kinds, time.strftime('%H:%M:%S', time.gmtime())))
    t0 = time.time(); seeds = []            # (E, P, kind)
    if 'best' in kinds:
        Q, E = ms.relax(held, box, a.maxiter); seeds.append((E, Q, 'best'))
    if 'drop1' in kinds and n + 1 in don:
        D = don[n + 1]
        for i in order(D, rng)[:a.cap]:
            Q, E = ms.relax(press(np.delete(D, i, 0), box), box, a.maxiter); seeds.append((E, Q, 'drop1'))
    if 'drop2' in kinds and n + 2 in don:
        D = don[n + 2]; tree = cKDTree(D[:, :2])
        for i in order(D, rng)[:a.cap]:
            _, nb = tree.query(D[i, :2], 7); j = int(nb[1 + int(rng.integers(len(nb) - 1))])
            Q, E = ms.relax(press(np.delete(D, [i, j], 0), box), box, a.maxiter); seeds.append((E, Q, 'drop2'))
    if 'grow1' in kinds and n - 1 in don:
        B = press(don[n - 1], box); tree = cKDTree(B[:, :2])
        pts = rng.uniform(0.5, box - 0.5, (6000, 2)); d, _ = tree.query(pts)
        for k in np.argsort(-d)[:min(a.cap, 120)]:
            P = np.vstack([B, [pts[k, 0], pts[k, 1], float(rng.uniform(0, math.pi / 2))]])
            Q, E = ms.relax(P, box, a.maxiter); seeds.append((E, Q, 'grow1'))
    for kd, nd, wd in (('peel', n_up, 1.0), ('peel2', n_up2, 2.0)):
        if kd in kinds and nd in don:
            got = []
            for P, x0, y0 in peel_seeds(don[nd], n, box, width=wd):
                Q, E = ms.relax(P, box, a.maxiter); got.append((E, Q, kd, x0, y0))
            got.sort(key=lambda z: z[0])
            log('peel donor n=%d side %.9f (held side of n: %.9f): %d cuts; best: %s' % (
                nd, mlp.side(don[nd]), Lheld, len(got), ' '.join('(%.2f,%.2f):%.2e' % (g[3], g[4], g[0]) for g in got[:6])))
            for E, Q, kd_, x0, y0 in got[:max(a.pop, 30)]:
                Q, E = ms.relax(Q, box, 2000); seeds.append((E, Q, kd))
    if 'jog' in kinds and n_up in don:
        got = []
        for P, tag in jog_seeds(don[n_up], n, box, max_tilt=a.max_tilt, rng=rng):
            Q, E = ms.relax(P, box, a.maxiter); got.append((E, Q, tag))
        got.sort(key=lambda z: z[0]); fin = []
        for E, Q, tag in got[:40]:
            Q, E = settle(Q, box); fin.append((E, Q, tag)); seeds.append((E, Q, 'jog'))
        fin.sort(key=lambda z: z[0])
        log('jog donor n=%d side %.9f (held side of n: %.9f): %d clean cuts; best after settling: %s' % (
            n_up, mlp.side(don[n_up]), Lheld, len(got), ' | '.join('%s: %.2e' % (g[2], g[0]) for g in fin[:6])))
    if 'splice' in kinds:
        # the turns of the held layout itself also go in (a, b = n): a cut then joins two different corners of it
        got = []
        for P, tag in splice_seeds({k: v for k, v in don.items() if abs(k - n) <= 3}, n, box, a.cap * 8, rng):
            Q, E = ms.relax(P, box, a.maxiter); got.append((E, Q, tag))
        got.sort(key=lambda z: z[0]); fin = []
        for E, Q, tag in got[:60]:
            Q, E = settle(Q, box, 2, 600); fin.append((E, Q, tag)); seeds.append((E, Q, 'splice'))
        fin.sort(key=lambda z: z[0])
        log('splice: %d seeds; best after settling: %s' % (len(got), ' | '.join('%s: %.2e' % (g[2], g[0]) for g in fin[:8])))
    for kd in kinds:
        es = sorted(e for e, _, k in seeds if k == kd)
        if es:
            log('seeds %s %d: min %.3e q10 %.3e median %.3e max %.3e' % (kd, len(es), es[0], es[len(es) // 10], es[len(es) // 2], es[-1]))
    seeds.sort(key=lambda z: z[0])
    # the energy of a first relaxation counts only the pairs that were near at its start: a seed that moved far
    # (an inserted square, a cut) reads too low. The lowest seeds are settled and counted afresh before they compete
    top = []
    for e, q, k in seeds[:3 * a.pop]:
        q, e = settle(q, box, 2, 600); top.append((e, q, k))
    seeds = sorted(top, key=lambda z: z[0])
    pop = []
    for e, q, k in seeds:
        if not any(abs(e - p[0]) <= 1e-3 * p[0] for p in pop):
            pop.append((e, q, k))
        if len(pop) >= a.pop:
            break
    log('pop after seeding (%.0f s): %s' % (time.time() - t0, ' '.join('%s:%.2e' % (p[2], p[0]) for p in pop)))
    t1 = time.time(); kids = 0; find = None; last_try = 0; last_E = math.inf; E_seed = pop[0][0]
    stats = {m: [0, 0] for m in moves}
    while time.time() - t1 < a.seconds and time.time() < dl:
        E0, P, src = pop[int(rng.integers(len(pop)))]
        w = ms.overlap_weight(pop[0][1], box)
        Q, mv = ms.mutate(P, box, w, rng, moves)
        if Q is None:
            continue
        act = ms.active_set(P, Q)
        if act is not None and act.sum() < 0.6 * n:
            e_par = ms.local_energy(P, box, act); Q, e_loc = ms.relax_local(Q, box, act, a.maxiter); E = E0 - e_par + e_loc
        else:
            Q, E = ms.relax(Q, box, a.maxiter)
        kids += 1; stats[mv][0] += 1
        if kids % 100 == 0:
            Qg, Eg = ms.relax(pop[0][1], box, a.maxiter)
            if Eg < pop[0][0]:
                pop[0] = (Eg, Qg, pop[0][2])
        dup = any(abs(E - e) <= 1e-3 * e for e, _, _ in pop) and E >= pop[0][0]
        if not dup and (len(pop) < a.pop or E < pop[-1][0]):
            pop.append((E, Q, src)); pop.sort(key=lambda z: z[0]); pop = pop[:a.pop]; stats[mv][1] += 1
        if kids % 500 == 0:
            log('t %.0f kids %d E %s' % (time.time() - t1, kids, ' '.join('%s:%.1e' % (p[2], p[0]) for p in pop[:4])))
        soft_free = pop[0][0] < 1e-10 * n
        if soft_free or (kids - last_try >= 200 and pop[0][0] < 0.97 * last_E and pop[0][0] < 3e-8 * n):
            last_try, last_E = kids, pop[0][0]
            lad = ms.ladder(pop[0][1], box, Lheld)
            if lad is not None:
                r = ms.legal(lad[0]); R, LR = r if (r is not None and r[1] < lad[1]) else lad
                ms.write(a.out, n, R, 'seed-%d' % a.seed); find = (LR, pop[0][2])
                log('FIND t %.0f kids %d from %s L %.12f (held %.12f, gain of score %.3e)' % (time.time() - t1, kids, pop[0][2], LR, Lheld, (Lheld - LR) / math.sqrt(n)))
                break
            if soft_free:
                # soft-free and not legal within the ladder: the overlap the tolerance allows. Drop this member
                log('softfree-illegal t %.0f kids %d E %.3e min_gap %.3e' % (time.time() - t1, kids, pop[0][0], mlp.min_gap(pop[0][1])))
                pop = pop[1:] if len(pop) > 1 else [(pop[0][0] + 1e-9 * n, pop[0][1], pop[0][2])]
    msg = 'n=%d kids %d seedE %.3e endE %.3e (%s) %s seconds %.0f+%.0f stats %s' % (
        n, kids, E_seed, pop[0][0], pop[0][2], 'FIND %.12f from %s gain %.3e' % (find[0], find[1], (Lheld - find[0]) / math.sqrt(n)) if find else 'no find',
        t1 - t0, time.time() - t1, stats)
    log('END ' + msg); print(msg, flush=True)


if __name__ == '__main__':
    main()
