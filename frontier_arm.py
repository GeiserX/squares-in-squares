#!/usr/bin/env python3
"""frontier: the arm stretch at a fixed fractional side.

A held layout at side m + f is, in the shells that hold the gap, upright blocks plus one or two arms. An arm
is a row of rigid stacks (frontier_stacks.py) that repeat with one period vector v. A stack that is flush at
f in one shell is flush at f in every shell, so an arm can be made longer or shorter by whole periods and
carried to the side m' + f of another shell. That gives a family in m and k from one donor:

  for each arm: cut it between two stacks (along the stack direction), insert j copies of the period before
  the cut (or delete one period), and anchor either part to a corner of the new box;
  then refill the uprights exactly (Evan Daniel's fillfast, MIT, imported from his clone) and count.

A layout is scored by its own count c: it is a hit when its side m' + f is below the side we hold for c
squares. A hit is quenched with fq and certified by floatsafe.

  frontier_arm.py ctl                                   rebuild held members of a family from the member below
  frontier_arm.py scan OUT [--donors a-b] [--delta 1,2,-1] [--jobs 2] [--tilt 0.5]
  frontier_arm.py one DONOR DELTA                       print every variant's count for one donor

SQ_BEST is the held submission. Our own code; run with python (it imports the lane's helpers).
"""
import argparse, bisect, csv, itertools, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *
from engine_patch import corners, cluster, pen_matrix
import fillfast
from frontier_stacks import stacks

P = None; LS = {}; NS = []; SIDES = []
CTL = [(872, 932), (932, 994), (641, 693), (498, 544), (797, 855), (812, 870), (913, 975), (644, 696)]


def init():
    global P, NS, SIDES
    P = load()
    for n in P: LS[n] = normalize(P[n])[0]
    NS = sorted(LS); SIDES = [LS[n] for n in NS]


def need(s):
    """the smallest count that beats the held file at side s (held sides never fall with n)"""
    i = bisect.bisect_right(SIDES, s + 1e-7)
    return NS[i] if i < len(NS) else 10 ** 9


def box_ok(T, s, tol=1e-9):
    C = corners(T)
    return C.min() >= -tol and C.max() <= s + tol


def clash(A, B, tol=1e-9):
    """True when a square of A overlaps a square of B"""
    if not len(A) or not len(B): return False
    d = ((A[:, None, :2] - B[None, :, :2]) ** 2).sum(-1) < 2.0
    I, J = np.nonzero(d)
    for i, j in zip(I, J):
        if pen_matrix(A[i:i + 1], B[j:j + 1])[0, 0] > tol: return True
    return False


def self_clash(A, tol=1e-9):
    d = ((A[:, None, :2] - A[None, :, :2]) ** 2).sum(-1) < 2.0
    I, J = np.nonzero(np.triu(d, 1))
    for i, j in zip(I, J):
        if pen_matrix(A[i:i + 1], A[j:j + 1])[0, 0] > tol: return True
    return False


def arm_of(G):
    """G: the tilted squares of one patch. -> (t, tc, v) or None. t is each square's place along the arm,
    measured along v parallel to the stacks; tc is the cut; v the period vector."""
    if len(G) < 12: return None
    chains, best = stacks(G)
    by = collections.defaultdict(list)
    for ch in chains:
        if len(ch) >= 3: by[len(ch)].append(ch)
    if not by: return None
    c = max(by, key=lambda q: q * len(by[q]))
    ch = by[c]
    if len(ch) < 4: return None
    tilt = np.array([np.median(G[q, 2]) for q in ch]); med = np.median(tilt)
    ch = [q for q, t in zip(ch, tilt) if abs(t - med) < 0.15]
    if len(ch) < 4: return None
    cen = np.array([G[q, :2].mean(0) for q in ch])
    ax = np.array([G[q[-1], :2] - G[q[0], :2] for q in ch]); ax /= np.linalg.norm(ax, axis=1)[:, None]
    ax[ax @ ax[0] < 0] *= -1
    u = ax.mean(0); u /= np.linalg.norm(u)
    w = np.array([-u[1], u[0]])
    o = np.argsort(cen @ w); cen = cen[o]
    d = np.diff(cen, axis=0)
    v = np.median(d, axis=0)
    good = np.linalg.norm(d - v, axis=1) < 0.03
    if good.sum() < 3 or np.linalg.norm(v) < 0.9: return None
    v = d[good].mean(0)
    vh = v / np.linalg.norm(v); den = vh[0] * u[1] - vh[1] * u[0]
    if abs(den) < 0.2: return None
    p0 = cen[0]
    def place(X):
        q = X - p0
        return (q[:, 0] * u[1] - q[:, 1] * u[0]) / den
    t = place(G[:, :2]); ts = place(cen); per = float(np.linalg.norm(v))
    mid = len(ts) / 2 - 0.5
    for i in sorted(range(len(ts) - 1), key=lambda i: abs(i - mid)):
        if not good[i]: continue
        tc = (ts[i] + ts[i + 1]) / 2
        a = G[(t > tc - per) & (t <= tc)]; b = G[(t > tc) & (t <= tc + per)]
        if len(a) and len(a) == len(b):
            dd = np.abs((a[:, None, :2] + v) - b[None, :, :2]).sum(-1).min(1)
            if dd.max() < 0.03: return t, tc, v
    return None


def variants(G, arm, delta, s):
    """every way to carry one patch to the new box: (label, squares). Without an arm: the four corner anchors."""
    offs = [(0, 0), (delta, 0), (0, delta), (delta, delta)]
    out = []
    if arm is None:
        for o in offs:
            T = G.copy(); T[:, 0] += o[0]; T[:, 1] += o[1]
            if box_ok(T, s): out.append(('j0o%d%d' % (o[0] != 0, o[1] != 0), T))
        return out
    t, tc, v = arm
    per = float(np.linalg.norm(v))
    near = G[t <= tc]; far = G[t > tc]; slab = G[(t > tc - per) & (t <= tc)]
    js = sorted(set([0, -1] + list(range(1, abs(delta) + 2))))
    for j in js:
        if j >= 0:
            parts = [near] + [slab + np.array([i * v[0], i * v[1], 0.0]) for i in range(1, j + 1)] + [far + np.array([j * v[0], j * v[1], 0.0])]
        else:
            parts = [near, far[t[t > tc] > tc + per] - np.array([v[0], v[1], 0.0])]
        B = np.vstack(parts)
        if j and self_clash(B): continue
        for o in offs:
            for hold in ((0, 1) if j else (0,)):
                T = B.copy(); T[:, 0] += o[0] - hold * j * v[0]; T[:, 1] += o[1] - hold * j * v[1]
                if box_ok(T, s): out.append(('j%do%d%d%s' % (j, o[0] != 0, o[1] != 0, 'f' if hold else ''), T))
    return out


def build(d, delta, tilt=0.5, top=4):
    """-> list of (count, label, squares) for donor d carried delta shells, best first"""
    sd, A = normalize(P[d]); s = sd + delta
    T = A[np.abs(A[:, 2]) > tilt]
    if not len(T): return s, []
    groups = sorted(cluster(T), key=len, reverse=True)
    big = groups[:2]; rest = groups[2:]
    R = []
    for g in rest:
        G = T[g].copy(); c = G[:, :2].mean(0)
        for k in (0, 1):
            if c[k] > sd / 2: G[:, k] += delta
        R.append(G)
    R = np.vstack(R) if R else np.zeros((0, 3))
    if len(R) and not box_ok(R, s): return s, []
    V = []
    for g in big:
        G = T[g]
        vs = [(l, X) for l, X in variants(G, arm_of(G), delta, s) if not clash(X, R)]
        if not vs: return s, []
        V.append(vs)
    memo = {}
    def count(pick):
        if pick in memo: return memo[pick]
        Xs = [V[i][p][1] for i, p in enumerate(pick)]
        if len(Xs) == 2 and clash(Xs[0], Xs[1]): memo[pick] = (0, None); return memo[pick]
        T2 = np.vstack(Xs + [R])
        F = fillfast.fill(s, T2, 'greedy')
        memo[pick] = (len(F), T2); return memo[pick]
    plain = [[i for i, (l, _) in enumerate(vs) if l.startswith('j0')] or [0] for vs in V]
    base = max(itertools.product(*plain), key=lambda p: count(p)[0])
    keep = []
    for a in range(len(V)):
        sc = []
        for i in range(len(V[a])):
            p = list(base); p[a] = i; sc.append((count(tuple(p))[0], i))
        keep.append([i for _, i in sorted(sorted(sc, key=lambda x: x[1]), key=lambda x: -x[0])[:top]])
    for p in itertools.product(*keep): count(p)
    res = []
    for p, (c, T2) in sorted(memo.items(), key=lambda kv: -kv[1][0])[:3]:
        if T2 is None: continue
        F = fillfast.fill(s, T2, 'exact')
        res.append((len(F), '+'.join(V[i][q][0] for i, q in enumerate(p)), F))
    res.sort(key=lambda r: -r[0])
    return s, res


def finish(n, F, s, out, src):
    """drop uprights down to n, quench, certify; write the per-n rows when it certifies below the held side"""
    from engine_polish import certify
    from engine_fq import quench, POLISH
    up = np.nonzero(np.abs(F[:, 2]) <= 0.5)[0]
    X = np.delete(F, up[:len(F) - n], axis=0); cur = s; X0 = X
    for fl in ((), POLISH):
        s2, X2, dt = quench(cur, X, fl)
        if s2 is not None and s2 < cur: cur, X = s2, X2
    L, fr = certify(n, X)
    if L is None: L, fr = certify(n, X0)
    if L is not None and L < LS[n] - 1e-9:
        with open(os.path.join(out, '%d.csv' % n), 'w', newline='') as h:
            w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        return L
    return None


def job(a):
    d, delta, out, tilt = a
    try:
        s, res = build(d, delta, tilt)
    except Exception as e:
        return d, delta, None, 'error %s' % e, []
    if not res: return d, delta, s, 'no variant fits', []
    c, lab, F = res[0]
    nd = need(s); wins = []
    if c >= nd:
        for n in range(nd, c + 1):
            L = finish(n, F, s, out, d)
            if L is not None: wins.append((n, LS[n], L))
    return d, delta, s, '%d\t%d\t%s' % (c, nd, lab), wins


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('mode'); ap.add_argument('args', nargs='*')
    ap.add_argument('--donors', default='400-1000'); ap.add_argument('--delta', default='1')
    ap.add_argument('--jobs', type=int, default=2); ap.add_argument('--tilt', type=float, default=0.5)
    a = ap.parse_args(); init()
    if a.mode == 'ctl':
        ok = 0
        for d, n in CTL:
            delta = int(LS[n]) - int(LS[d]); t0 = time.time()
            s, res = build(d, delta, a.tilt)
            c = res[0][0] if res else 0
            _, plain = build_plain(d, delta, a.tilt)
            ok += c >= n
            print('ctl donor %d -> %d at %.6f (held side %.6f): count %d (%s), rigid patches only %d, %s, %.0fs' % (
                d, n, s, LS[n], c, res[0][1] if res else '-', plain, 'GREEN' if c >= n else 'RED', time.time() - t0), flush=True)
        print('controls green: %d of %d' % (ok, len(CTL)))
        return
    if a.mode == 'one':
        d, delta = int(a.args[0]), int(a.args[1])
        s, res = build(d, delta, a.tilt)
        print('donor', d, 'side', s, 'needs', need(s))
        for c, lab, F in res: print(c, lab)
        return
    out = a.args[0]; os.makedirs(out, exist_ok=True)
    lo, hi = map(int, a.donors.split('-'))
    jobs = []
    for d in NS:
        if not (lo <= d <= hi): continue
        m = int(LS[d]); k = d - m * m
        if LS[d] - m < 1e-6 or k > m + 8: continue
        for delta in map(int, a.delta.split(',')):
            if d + delta * 2 * m > 1010 or m + delta < 8: continue
            jobs.append((d, delta, out, a.tilt))
    print('jobs', len(jobs), flush=True)
    from multiprocessing import Pool
    tot = 0.0; t0 = time.time()
    with Pool(a.jobs, initializer=init) as pool, open(os.path.join(out, 'arm.tsv'), 'a') as h:
        h.write('donor\tdelta\tside\tcount\tneeded\tvariant\twins\n')
        for d, delta, s, txt, wins in pool.imap_unordered(job, jobs):
            h.write('%d\t%d\t%r\t%s\t%s\n' % (d, delta, s, txt, ' '.join('%d:%.9f' % (n, L) for n, _, L in wins))); h.flush()
            for n, L0, L in wins:
                g = (L0 - L) / math.sqrt(n); tot += g
                print('WIN n=%d %.9f -> %.9f donor %d delta %d gain %.3e total %.3e' % (n, L0, L, d, delta, g, tot), flush=True)
    print('done %.0fs' % (time.time() - t0), flush=True)


def build_plain(d, delta, tilt):
    """the count with rigid patches only (no period inserted): what the shell step of 2026-11-10 could reach"""
    global variants
    keep = variants
    def only_plain(G, arm, delta_, s):
        return keep(G, None, delta_, s)
    variants = only_plain
    try:
        s, res = build(d, delta, tilt)
    finally:
        variants = keep
    return s, (res[0][0] if res else 0)


if __name__ == '__main__':
    main()
