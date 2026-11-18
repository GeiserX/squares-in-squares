#!/usr/bin/env python3
"""gap lane: grow a held layout by refilling its uprights at a larger side (avenues/gap.md).

A layout of n - j at side s holds its tilted squares T. At a side Lt between s and the base side of n, the exact
upright refill around T (fillfast, mode exact) may hold n squares: every upright is placed again, so the room the
larger side gives is used in full, not one pocket at a time. When the refill holds n, the layout is a layout of n
at Lt, and fq then shrinks it. Three ways to place T in the larger box: as it is, dilated about the box centre by
Lt / s, and each tilted patch moved to the walls it touches.

  gap_grow.py run HELD.csv DETAILS.csv OUTDIR DEADLINE_EPOCH N[,N..]|@FILE [--j 1,2] [--margin 1e-5]
  gap_grow.py ctl HELD.csv N          refill of the held N at its own side holds N, and 0.002 below it does not
  gap_grow.py finish DETAILS.csv RAW.csv OUT.csv   floatsafe, fq quench from the certified file, floatsafe again

Writes OUTDIR/log.jsonl (one line per refill) and OUTDIR/raw/<n>-<tag>.csv for each hit, quenched once by fq.
Our own code. Imports the lane's engine_lib, engine_fq, outline_lib helpers and floatsafe; fillfast is Evan
Daniel's MIT packer, imported from its clone under SQ_BOX/ext/evand.
"""
import os, sys, csv, json, math, time
os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_lib import load, normalize
from engine_fq import quench, POLISH
from outline_lib import patches
import numpy as np, fillfast

TILT = 5.0


def tilted(A):
    return A[np.abs(A[:, 2]) > TILT]


def variants(T, s, Lt):
    d = Lt - s
    yield 'asis', T
    c = s / 2.0
    D = T.copy()
    D[:, :2] = (T[:, :2] - c) * (Lt / s) + Lt / 2.0
    yield 'dilate', D
    W = T.copy()
    for g in patches(T):
        P = T[g]
        hx = P[:, 0].max() > s - 1.2
        hy = P[:, 1].max() > s - 1.2
        lx = P[:, 0].min() < 1.2
        ly = P[:, 1].min() < 1.2
        if hx and not lx: W[g, 0] += d
        elif hx and lx: W[g, 0] += d / 2
        if hy and not ly: W[g, 1] += d
        elif hy and ly: W[g, 1] += d / 2
    yield 'walls', W


def trim(X, n):
    if len(X) <= n: return X
    up = np.abs(X[:, 2]) < 1e-9
    idx = np.where(up)[0]
    return np.delete(X, idx[:len(X) - n], axis=0)


def write_csv(path, n, X):
    """X holds degrees (fq and fillfast use degrees); the csv holds radians, as the Kaggle rows do"""
    with open(path, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, (x, y, a) in enumerate(X):
            w.writerow([n, i, repr(float(x)), repr(float(y)), repr(math.radians(float(a)))])


def base_of(details):
    return {int(r['n']): (float(r['L']), float(r['score'])) for r in csv.DictReader(open(details))}


def cmd_ctl(a):
    P = load(a[0]); n = int(a[1]); s, A = normalize(P[n]); T = tilted(A)
    for L in (s + 1e-9, s - 0.002):
        X = fillfast.fill(L, T, mode='exact')
        print('ctl', n, 'L %.9f' % L, 'tilted', len(T), 'count', len(X), 'want', '>=n' if L > s else '<n', flush=True)


def cmd_run(a):
    held, details, out, deadline, targets = a[0], a[1], a[2], float(a[3]), a[4]
    J = [1]; margin = 1e-5
    if '--j' in a: J = [int(x) for x in a[a.index('--j') + 1].split(',')]
    if '--margin' in a: margin = float(a[a.index('--margin') + 1])
    if targets.startswith('@'): N = [int(x) for x in open(targets[1:]).read().split()]
    else: N = [int(x) for x in targets.split(',')]
    os.makedirs(out + '/raw', exist_ok=True)
    P = load(held); B = base_of(details)
    log = open(out + '/log.jsonl', 'a')
    for n in N:
        for j in J:
            if time.time() > deadline: print('deadline', flush=True); return
            d = n - j
            if d < 2: continue
            s, A = normalize(P[d]); T = tilted(A)
            Lt = B[n][0] - margin
            if Lt <= s + 1e-7 or len(T) == 0: continue
            for tag, V in variants(T, s, Lt):
                t = time.time()
                try: X = np.array(fillfast.fill(Lt, V, mode='exact'), float)
                except Exception as e:
                    log.write(json.dumps(dict(n=n, d=d, v=tag, err=str(e)[:200])) + '\n'); log.flush(); continue
                rec = dict(n=n, d=d, v=tag, Lt=Lt, s=s, count=len(X), dt=round(time.time() - t, 2))
                if len(X) >= n:
                    X = trim(X, n)
                    s2, X2, _ = quench(Lt, X, (), timeout=900)
                    rec['fq'] = s2
                    if s2 is not None and s2 < B[n][0] - 1e-9:
                        p = '%s/raw/%d-g%d%s.csv' % (out, n, j, tag)
                        write_csv(p, n, X2); rec['file'] = p
                        print('HIT', n, 'from', d, tag, 'side', s2, 'base', B[n][0], flush=True)
                log.write(json.dumps(rec) + '\n'); log.flush()


def cmd_finish(a):
    """floatsafe, then one fq quench from the certified file, then floatsafe again; writes the lower certified."""
    import floatsafe
    details, raw, out = a
    B = base_of(details)
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(raw))]
    n = len(rows)
    _, fr, sc, e = floatsafe.work((n, rows))
    if fr is None: print('finish', n, 'first floatsafe failed', e); return
    X = np.array([[float(r['x']), float(r['y']), float(r['angle'])] for r in fr])
    s, A = normalize([(x, y, a) for x, y, a in X])
    s2, X2, _ = quench(s, A, (), timeout=900)
    best = (sc, fr)
    if s2 is not None:
        rows2 = [dict(n=str(n), square_id=str(i), x=repr(float(x)), y=repr(float(y)), angle=repr(math.radians(float(a))))
                 for i, (x, y, a) in enumerate(X2)]
        _, fr2, sc2, e2 = floatsafe.work((n, rows2))
        if fr2 is not None and sc2 < sc: best = (sc2, fr2)
    sc, fr = best
    with open(out, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in fr: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    print('finish', n, 'score', repr(sc), 'base', repr(B[n][1]), 'gain', B[n][1] - sc, 'quenched', s2 is not None, flush=True)


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'run': cmd_run, 'ctl': cmd_ctl, 'finish': cmd_finish}[c](a)
