#!/usr/bin/env python3
"""Follow the held band down its chain curve in the stick model, from the held angle toward the board's.

forensics_sticks.py searches the runs of sticks from nothing, and its control at the held side and
angle is red: it does not find our own layout again. This tool starts from the held layout instead.

  1. Read the blocks of the held layout as runs of sticks (turn, first stick, number of sticks, how
     many rows rest on the lower staircase). Tilted squares that belong to no run stay as they are,
     at a fixed distance from the nearest corner of the square.
  2. Seed check: the runs plus the exact upright fill must give the held count at the held side.
  3. Turn the band in small steps along the chain (i + f) C + (j + f) S = q. At each step the side is
     the one the chain gives, the sticks rest again on the staircases, a short local search moves the
     runs, and the exact fill counts.

Any step that still holds n squares has a side below the held one. The count per step says how far
the band of the held layout can turn before it loses squares.

State on 2026-11-12: the seed check fails on n = 263. The runs read from the held layout overlap where
two runs of opposite turn meet, because the held layout sets 5 squares there at a third angle and the
stick model has one angle per run. No step counts until the model has that joint.

The exact fill is Evan Daniel's fillfast (MIT), imported from his clone.

Usage: forensics_follow.py HELD.csv N BOARD_DEG OUT [--chain 4,3,6] [--steps 28] [--tries 300] [--seed 1]
"""
import sys, os, math, random, time, argparse
import numpy as np

sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import fillfast  # noqa: E402
import forensics_turn as ft  # noqa: E402
import forensics_sticks as fs  # noqa: E402
import forensics_curve as fc  # noqa: E402


def chain_f(deg_t, i, j, q):
    t = math.radians(deg_t); C, S = math.cos(t), math.sin(t)
    return (q - i * C - j * S) / (C + S)


def place_extras(extras, side):
    """extras: (dx, dy, deg, cx, cy) with cx, cy in {0, 1}: the distance is kept from that corner."""
    return [((side - dx) if cx else dx, (side - dy) if cy else dy, deg) for dx, dy, deg, cx, cy in extras]


def count(ch, runs, delta, extras, time_limit=5):
    side = ch.m + ch.f
    T, mis = fs.build(ch, runs, delta)
    T = T + place_extras(extras, side)
    if not fs.valid(T, side):
        return -1, None
    X = fillfast.fill(side, np.array(T, float).reshape(-1, 3), mode='exact', time_limit=time_limit)
    return len(X), X


def read_runs(A, s, held_deg, chain):
    """Runs of the held blocks, on the diagonal c and with the rest or hang that puts the model's squares
    nearest to the held ones, and the tilted squares left over."""
    m = int(s); f = s - m; delta = 45 - held_deg; q = chain[2]
    blocks = [(sg, comp) for sg, comp in ft.blocks(A, held_deg) if len(comp) >= 6]
    H = A[np.abs(A[:, 2]) > 1e-6][:, :2]
    best = None
    for c in range(0, 9):
        ch = fs.Channel(m, f, c, *chain)
        runs = []; total = 0.0
        for sg, comp in blocks:
            turn = -sg
            th = math.radians(45 + turn * delta)
            eu = np.array([math.cos(th), math.sin(th)])
            U = A[comp, :2] @ eu
            u0 = U.min() - 0.5; p = int(round(U.max() - U.min() + 1))
            cand = None
            for split in (q, 0, 3):
                R = dict(turn=turn, u0=float(u0), p=p, split=split, du=0.0)
                P = np.array(fs.build(ch, [R], delta)[0])[:, :2]
                cost = float(np.mean([np.hypot(H[:, 0] - x, H[:, 1] - y).min() for x, y in P]))
                if cand is None or cost < cand[0]:
                    cand = (cost, R)
            runs.append(cand[1]); total += cand[0]
        if best is None or total < best[0]:
            best = (total, c, runs)
    total, c, runs = best
    print('reading: diagonal %d, mean distance of a model square to a held square %.4f' % (c, total / max(1, len(runs))), flush=True)
    ch = fs.Channel(m, f, c, *chain)
    T, _ = fs.build(ch, runs, delta)
    P = np.array(T)[:, :2]
    extras = []
    for x, y, d in A:
        if abs(d) < 1e-6:
            continue
        if np.hypot(P[:, 0] - x, P[:, 1] - y).min() > 0.6:
            cx, cy = int(x > s / 2), int(y > s / 2)
            extras.append(((s - x) if cx else x, (s - y) if cy else y, float(d), cx, cy))
    return c, runs, extras


def climb(ch, runs, delta, extras, tries, rng, target):
    q = ch.q
    cur = [dict(R) for R in runs]
    cur_c, cur_X = count(ch, cur, delta, extras)
    best = (cur_c, cur_X, [dict(R) for R in cur])
    for _ in range(tries):
        if best[0] >= target:
            break
        cand = [dict(R) for R in cur]
        R = rng.choice(cand); z = rng.random()
        if z < 0.45:
            R['u0'] += rng.choice((-1, 1)) * rng.choice((0.002, 0.01, 0.04, 0.15)) * rng.random()
        elif z < 0.60:
            R['du'] = 0.0 if rng.random() < 0.3 else R.get('du', 0.0) + rng.choice((-1, 1)) * rng.choice((0.01, 0.05)) * rng.random()
        elif z < 0.72:
            R['split'] = min(q, max(0, R['split'] + rng.choice((-1, 1, -3, 3))))
        elif z < 0.84:
            R['p'] = max(1, R['p'] + rng.choice((-1, 1)))
        elif z < 0.94:
            d = rng.choice((-1, 1)); R['p'] = max(1, R['p'] - d); R['u0'] += d
        else:
            R['u0'] += rng.choice((-1, 1))
        c, X = count(ch, cand, delta, extras)
        if c >= cur_c:
            cur, cur_c = cand, c
            if c > best[0]:
                best = (c, X, [dict(R) for R in cand])
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('held'); ap.add_argument('n', type=int); ap.add_argument('board_deg', type=float); ap.add_argument('out')
    ap.add_argument('--chain', default='4,3,6'); ap.add_argument('--steps', type=int, default=28)
    ap.add_argument('--tries', type=int, default=300); ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    chain = tuple(int(v) for v in a.chain.split(','))
    rng = random.Random(a.seed)
    s, A = ft.normalize(ft.load(a.held, a.n)); m = int(s); f0 = s - m
    t, _, _ = fc.main_angle([(x, y, math.radians(d)) for x, y, d in A])
    held_deg = math.degrees(t)
    c, runs, extras = read_runs(A, s, held_deg, chain)
    ch = fs.Channel(m, f0, c, *chain)
    cnt, X = count(ch, runs, 45 - held_deg, extras)
    print('n %d held side %.10f angle %.5f: diagonal %d, runs %s, %d other tilted squares' % (a.n, s, held_deg, c, fs.show(runs), len(extras)), flush=True)
    print('seed check: the runs and the exact fill give %d, the held layout has %d' % (cnt, a.n), flush=True)
    cnt, X, runs = climb(ch, runs, 45 - held_deg, extras, a.tries, rng, a.n)
    print('after the local search at the held point: %d' % cnt, flush=True)
    kept = None
    t0 = time.time()
    for st in range(1, a.steps + 1):
        deg = held_deg + (a.board_deg - held_deg) * st / a.steps
        f = chain_f(deg, *chain) + 2e-10
        ch = fs.Channel(m, f, c, *chain)
        cnt, X, runs2 = climb(ch, runs, 45 - deg, extras, a.tries, rng, a.n)
        print('step %2d angle %.5f side %.10f (%+.2e to held) count %d of %d  runs %s  %.0fs' % (
            st, deg, m + f, m + f - s, cnt, a.n, fs.show(runs2), time.time() - t0), flush=True)
        if cnt >= 0:
            runs = runs2
        if cnt >= a.n:
            kept = (m + f, deg, X)
    if kept:
        side, deg, X = kept
        os.makedirs(a.out, exist_ok=True)
        tilt = [r for r in X if abs(r[2]) > 1e-6]; upr = [r for r in X if abs(r[2]) <= 1e-6]
        path = '%s/%d-follow.csv' % (a.out, a.n)
        ft.write_rows(path, a.n, np.array(tilt + upr[:a.n - len(tilt)]))
        print('lowest side with %d squares: %.10f at %.5f degrees; wrote %s' % (a.n, side, deg, path), flush=True)
    else:
        print('no step holds %d squares' % a.n, flush=True)


if __name__ == '__main__':
    main()
