#!/usr/bin/env python3
"""invent_rest: slide segments of the plain rest beside the arms, then the family squeeze (avenues/invent.md, Round 20).

A block layout stops where the family squeeze stalls (f 0.619580678 for the arm cf9-72f6227 in 907 and in 969): the
arm cannot turn further, because a longer arm needs room that rows of the plain rest hold. In round 19 one build of
907 passed that stop by chance, with rest squares 0.019 and 0.024 off the lattice. This tool makes that move on
purpose. A try takes the start, picks K row or column segments of upright squares near the tilted squares (a segment
is a run of upright squares that touch in one row or one column), and shifts each along its own line by a random part
of DMAX, toward one end or the other. A shift that makes an overlap deeper than 1e-9 is halved up to six times,
then dropped, so the start stays legal to 1e-9 (the squeeze repairs that). Then family_step.squeeze runs from that start (without fq unless --fq is given).

Mode lkick (--modes seg,lkick rotates the two): every square within R (1.2 to RMAX) of a square near the tilted ones
(or of any square inside --cbox X0,Y0,X1,Y1) moves by a normal draw of sigma SIG (0.003 to 0.02) and turns by one of
sigma TFAC * SIG radians (--tfac, default 0.5). The start overlaps; the
squeeze repairs up to --apart (0.05) by opening the box and takes the room back with the exact LP. A kick of midm
quenches with fq, and fq does not come back to the side of a block layout (round 20, kick907): this is the same kick
with the squeeze that built the layout.

  invent_rest.py N START.csv OUT --seconds S --seed K [--deadline FILE] [--fq PATH] [--reach 2.2] [--dmax 0.12]
                  [--kmax 6] [--walk T] [--bar L] [--sweeps 0] [--modes seg|lkick|seg,lkick] [--rmax 3.0]
                  [--sigs 0.003,0.006,0.01,0.02] [--apart 0.05] [--cbox X0,Y0,X1,Y1] [--tfac 0.5]
    START.csv  a file holding the layout of N (columns n, square_id, x, y, angle in radians)
    --bar      a side to report against (the best of every take); results are written when below the start
    --walk T   a try that is not a new best still becomes the next start when its side is below the walker's side
               plus T times an exponential draw; after 40 tries with no new best the walker goes back to the best
    --sweeps 1 one try in four shifts every segment near the tilted squares at once (a sweep), not K of them
  --plateau-stop 1 stops after six completed tries when three end sides agree within 5e-9 and none moves over 1e-8.
  If unset, invent_plateau23.json beside this tool enables the policy for its named seeds.
  A result below the best side so far by 1e-9 is written to OUT/raw/<n>-sl<seed>-<try>.csv (raw rows; certification
  is modules.py take or methods_take.py on boxA). Every try is one line of OUT/slide-<n>-<seed>.tsv.
"""
import argparse, json, math, os, random, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import methods_lp as mlp  # noqa: E402


def upright_mask(P, tol=1e-6):
    t = np.mod(P[:, 2], math.pi / 2)
    return np.minimum(t, math.pi / 2 - t) < tol


def segments(P, up, axis):
    """Runs of upright squares that touch along AXIS (0: a row, the squares move in x; 1: a column, in y)."""
    idx = np.nonzero(up)[0]
    other = 1 - axis
    key = np.round(P[idx, other], 6)
    out = []
    for v in np.unique(key):
        row = idx[key == v]
        row = row[np.argsort(P[row, axis])]
        run = [row[0]]
        for a, b in zip(row[:-1], row[1:]):
            if P[b, axis] - P[a, axis] < 1 + 1e-6:
                run.append(b)
            else:
                out.append(np.array(run)); run = [b]
        out.append(np.array(run))
    return out


def local_gap(P, moved, s):
    """The smallest gap between the moved squares and everything within 2.5 of them, and the walls of the box."""
    c = P[moved, :2]
    lo, hi = c.min(0) - 2.5, c.max(0) + 2.5
    near = np.nonzero(np.all((P[:, :2] >= lo) & (P[:, :2] <= hi), axis=1))[0]
    g = mlp.min_gap(P[near]) if len(near) > 1 else math.inf
    wall = min(float((P[moved, :2] - 0.5).min()), float((s - 0.5 - P[moved, :2]).min()))
    return min(g, wall)


def move(P, segs, k, dmax, rng, s):
    Q = P.copy(); done = []
    for j in rng.sample(range(len(segs)), min(k, len(segs))):
        axis, seg = segs[j]
        d = rng.uniform(0.15, 1.0) * dmax * rng.choice((-1.0, 1.0))
        for _ in range(7):
            R = Q.copy(); R[seg, axis] += d
            if local_gap(R, seg, s) >= -1e-9:                # faces that touch stay at 0; the squeeze repairs 1e-9
                Q = R; done.append((axis, len(seg), d)); break
            d /= 2
    return Q, done


def plateau_stop(outcomes, start):
    if len(outcomes) != 6:
        return False
    floor = min(outcomes)
    return sum(abs(v - floor) < 5e-9 for v in outcomes) >= 3 and floor >= start - 1e-8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int); ap.add_argument('start'); ap.add_argument('out')
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--deadline'); ap.add_argument('--fq'); ap.add_argument('--reach', type=float, default=2.2)
    ap.add_argument('--dmax', type=float, default=0.12); ap.add_argument('--kmax', type=int, default=6)
    ap.add_argument('--walk', type=float, default=0.0); ap.add_argument('--bar', type=float, default=0.0)
    ap.add_argument('--sweeps', type=int, default=0)
    ap.add_argument('--modes', default='seg'); ap.add_argument('--rmax', type=float, default=3.0)
    ap.add_argument('--sigs', default='0.003,0.006,0.01,0.02'); ap.add_argument('--apart', type=float, default=0.05)
    ap.add_argument('--cbox', default=''); ap.add_argument('--tfac', type=float, default=0.5)
    ap.add_argument('--plateau-stop', type=int, choices=(0, 1), default=None)
    a = ap.parse_args()
    if a.plateau_stop is None:
        cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'invent_plateau23.json')
        a.plateau_stop = int(os.path.exists(cfg) and a.seed in json.load(open(cfg)).get('seeds', []))
    if a.fq: os.environ['SQ_FQ'] = a.fq
    import family_step as FS                                  # sets methods_lp.GAP and its LP solver for this process
    n = a.n; rng = random.Random(a.seed)
    P0 = FS.load(a.start, {n})[n]
    s0, P0 = FS.canon(P0)
    os.makedirs(a.out + '/raw', exist_ok=True)
    lg = open('%s/slide-%d-%d.tsv' % (a.out, n, a.seed), 'a')
    lg.write('# n=%d start=%.12f bar=%.12f seed=%d modes=%s dmax=%g kmax=%d reach=%g rmax=%g sigs=%s walk=%g %s\n' % (
        n, s0, a.bar, a.seed, a.modes, a.dmax, a.kmax, a.reach, a.rmax, a.sigs, a.walk, time.strftime('%H:%M:%S', time.gmtime()))); lg.flush()
    lg.write('# plateau_stop=%d reference=min(first-six)\n' % a.plateau_stop); lg.flush()
    outcomes = []
    best, bestP = s0, P0; cur, curP = s0, P0; since = 0
    t_end = time.time() + a.seconds
    if a.deadline and os.path.exists(a.deadline):
        t_end = min(t_end, float(open(a.deadline).read().split()[0]) - 60)
    k = 0; modes = a.modes.split(','); sigs = [float(x) for x in a.sigs.split(',')]
    while time.time() < t_end:
        k += 1
        up = upright_mask(curP)
        tl = np.nonzero(~up)[0]
        if len(tl) == 0: break
        from scipy.spatial import cKDTree
        tree = cKDTree(curP[tl, :2])
        dist, _ = tree.query(curP[:, :2])
        near = up & (dist < a.reach)
        segs = [(ax, sg) for ax in (0, 1) for sg in segments(curP, up, ax) if near[sg].any()]
        if k == 1: lg.write('# %d segments near the tilted squares (%d upright, %d tilted)\n' % (len(segs), up.sum(), len(tl))); lg.flush()
        mode = modes[(k - 1) % len(modes)]
        t0 = time.time(); apart = None
        if mode == 'lkick':
            cand = np.nonzero(near | ~up)[0]
            if a.cbox:                                        # --cbox X0,Y0,X1,Y1: kick centres in this box only
                x0, y0, x1, y1 = [float(v) for v in a.cbox.split(',')]
                cand = np.nonzero((curP[:, 0] > x0) & (curP[:, 0] < x1) & (curP[:, 1] > y0) & (curP[:, 1] < y1))[0]
            c = curP[rng.choice(list(cand)), :2]; r = rng.uniform(1.2, a.rmax); sig = rng.choice(sigs)
            sel = np.nonzero(np.hypot(curP[:, 0] - c[0], curP[:, 1] - c[1]) < r)[0]
            G = curP.copy()
            G[sel, 0] += np.array([rng.gauss(0, sig) for _ in sel]); G[sel, 1] += np.array([rng.gauss(0, sig) for _ in sel])
            G[sel, 2] += np.array([rng.gauss(0, sig * a.tfac) for _ in sel])
            done = [(2, len(sel), sig)]; sweep = False; apart = a.apart
        else:
            sweep = a.sweeps and rng.random() < 0.25
            kk = len(segs) if sweep else rng.randint(1, a.kmax)
            G, done = move(curP, segs, kk, a.dmax, rng, cur + 1e-9)
        if not done:
            lg.write('%d\tnone\t0\t%.12f\t-\t0\n' % (k, cur)); lg.flush(); continue
        try:
            Q, L, trace = FS.squeeze(G, log=None, fq=bool(a.fq), apart=apart)
            Q = mlp.normal(Q); L = float(mlp.side(Q))
            if mlp.min_gap(Q) < -1e-9: L = math.inf
        except Exception as ex:
            lg.write('%d\tfail\t%d\t%.12f\t%s\t%.1f\n' % (k, len(done), cur, str(ex)[:60], time.time() - t0)); lg.flush(); continue
        what = ('lkick%d@%.1f,%.1f,r%.1f' % (done[0][1], c[0], c[1], r)) if mode == 'lkick' else '%s%d' % ('sweep' if sweep else 'seg', len(done))
        mark = ''
        if L < best - 1e-9:
            best, bestP = L, Q; cur, curP = L, Q; since = 0; mark = 'BEST'
            FS.write_rows('%s/raw/%d-sl%d-%d.csv' % (a.out, n, a.seed, k), n, Q)
        else:
            since += 1
            if a.walk > 0 and L < cur + a.walk * rng.expovariate(1.0):
                cur, curP = L, Q; mark = 'walk'
            if since >= 40 and cur > best:
                cur, curP = best, bestP; since = 0; mark += 'back'
        lg.write('%d\t%s\t%s\t%.12f\t%.12f\t%.1f\t%s\n' % (
            k, what, ','.join('%s%+.3f' % ('xys'[ax], d) for ax, _, d in done[:8]), cur, L, time.time() - t0, mark))
        lg.flush()
        outcomes.append(L)
        if a.plateau_stop and plateau_stop(outcomes, s0):
            lg.write('# plateau stop after six completed tries, three matching end sides and no step over 1e-8\n'); lg.flush()
            break
    lg.write('# end %s best %.12f tries %d\n' % (time.strftime('%H:%M:%S', time.gmtime()), best, k)); lg.close()
    print('n=%d start %.12f best %.12f tries %d' % (n, s0, best, k))


if __name__ == '__main__':
    main()
