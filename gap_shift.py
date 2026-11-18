#!/usr/bin/env python3
"""gap lane: move the tilted patches of a layout into the box one size smaller and count (avenues/gap.md).

A held layout of d at m + 1 is cut down to the box of side L < m + 1: every tilted patch of 3 squares or more moves
by whole cells (0 or -1 per axis; a patch that touches only the far wall of an axis moves by -1, one that touches only
the near wall stays, one that touches both or neither tries both), squares that leave the box or meet another
square drop out, and the exact upright refill (fillfast, mode exact) around what is left gives a count. The three
best placements at the box of the same k are then counted at the base side (less 1e-5) of every n of the window
(m*m + k - 6 to m*m + k + 4). A count of n or more at the base side of n is a layout of n below the base: fq
quenches it once and the file goes to OUT/raw.

  gap_shift.py HELD.csv DETAILS.csv OUT DEADLINE_EPOCH D[,D..]|@FILE [--up]
With --up the donor is of m - 1 and goes into the box one size larger: a patch that touches only the far wall of an
axis moves by +1, one that touches only the near wall stays, and the others try both. The new row and column of the
refill then pass between the patches, not only along two walls as a plain shell does.
With --dm 2 the donor is of m + 2 and its patches move by 0 to -2 cells per axis.
Writes OUT/shift.jsonl (one line per count of n - 1 or more, and one per donor) and OUT/raw/<n>-s<d><v>.csv.
Our own code. Imports gap_walk.py and gap_grow.py of this lane; fillfast is Evan Daniel's MIT packer.
"""
import os, sys, json, math, time, itertools
os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gap_walk as gw, gap_grow as gg
from engine_lib import load, normalize, hw
from engine_fq import quench
from outline_lib import patches
import numpy as np, fillfast


def clip(K, L):
    k = [q for q in K if all((q[0] - hw(math.radians(q[2])) >= -1e-9, q[1] - hw(math.radians(q[2])) >= -1e-9,
                              q[0] + hw(math.radians(q[2])) <= L + 1e-9, q[1] + hw(math.radians(q[2])) <= L + 1e-9))]
    return np.array(k).reshape(-1, 3)


def options(P, s, up=False, dm=1):
    out = []
    for ax in (0, 1):
        near = P[:, ax].min() < 1.5; far = P[:, ax].max() > s - 1.5
        if up: out.append([1] if far and not near else [0] if near and not far else [0, 1])
        else: out.append([-dm] if far and not near else [0] if near and not far else list(range(0, -dm - 1, -1)))
    return list(itertools.product(*out))


def placements(T, s, L, up=False, dm=1):
    G = [g for g in patches(T) if len(g) >= 3]
    opts = [options(T[g], s, up, dm) for g in G]
    res = []
    for combo in itertools.product(*opts):
        keep = []
        for g, (dx, dy) in zip(G, combo):
            for q in T[g]:
                w = np.array([q[0] + dx, q[1] + dy, q[2]]); h = hw(math.radians(q[2]))
                if w[0] - h < -1e-9 or w[1] - h < -1e-9 or w[0] + h > L + 1e-9 or w[1] + h > L + 1e-9: continue
                if not keep or gw.fits(np.array(keep), w, L): keep.append(w)
        K = np.array(keep).reshape(-1, 3)
        res.append((gw.count(L, K), 'sh' + ''.join('%d%d' % (-a, -b) for a, b in combo), K))
        if len(res) > 64: break
    res.sort(key=lambda t: -t[0])
    return res[:3]


def main():
    held, details, out, deadline, spec = sys.argv[1:6]
    up = '--up' in sys.argv
    dm = int(sys.argv[sys.argv.index('--dm') + 1]) if '--dm' in sys.argv else 1
    deadline = float(deadline)
    D = [int(x) for x in (open(spec[1:]).read().split() if spec.startswith('@') else spec.split(','))]
    os.makedirs(out + '/raw', exist_ok=True)
    P = load(held); B = gg.base_of(details)
    log = open(out + '/shift.jsonl', 'a')
    for d in D:
        if time.time() > deadline: break
        t = time.time()
        s, A = normalize(P[d]); T = gg.tilted(A)
        if up: m = int(math.floor(s)) + 1; k = d - (m - 1) ** 2
        else: m = int(math.floor(s)) - dm; k = d - (m + dm) ** 2
        if m < 4 or len(T) == 0: continue
        n0 = m * m + k
        if n0 not in B: continue
        L0 = B[n0][0] - 1e-5
        if L0 >= m + 1: continue
        best = placements(T, s, L0, up, dm)
        hits = 0
        for c, v, K in best:
            for n in range(n0 - 6, n0 + 5):
                if n not in B or B[n][0] - 1e-5 >= m + 1 or B[n][0] - 1e-5 <= m: continue
                L = B[n][0] - 1e-5
                KK = clip(K, L); cnt = gw.count(L, KK)
                if cnt >= n - 1:
                    rec = dict(d=d, v=v, n=n, count=cnt, short=cnt - n)
                    if cnt >= n:
                        X = gg.trim(np.array(fillfast.fill(L, KK, mode='exact')), n)
                        s2, X2, _ = quench(L, X, (), timeout=900)
                        rec['fq'] = s2; rec['base'] = B[n][0]
                        if s2 is not None and s2 < B[n][0] - 1e-9:
                            p = '%s/raw/%d-s%d%s.csv' % (out, n, d, v); gg.write_csv(p, n, X2); rec['file'] = p; hits += 1
                    log.write(json.dumps(rec) + '\n'); log.flush()
        log.write(json.dumps(dict(d=d, done=1, n0=n0, top=[(c, v) for c, v, _ in best], hits=hits, dt=round(time.time() - t, 1))) + '\n'); log.flush()


if __name__ == '__main__':
    main()
