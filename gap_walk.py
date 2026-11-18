#!/usr/bin/env python3
"""gap lane: a count walk on the tilted blocks of a layout at a fixed side (avenues/gap.md).

The state is the set T of tilted squares. Its score is a count: the squares of the exact upright refill around T
(fillfast, mode exact) at the fixed side Lt, with T itself. The walk edits T and keeps the edit when the count does
not fall, and it stops when the count reaches the target n. Then fq shrinks the layout once.

Moves, on the tilted patches (each patch has its own angle and lattice vectors u, v):
  add     one square at p + u, p - u, p + v or p - v of a patch square p, where no square is
  del     one edge square of a patch leaves
  slide   one patch moves by 0.02 to 0.3 along x or y
  line    a whole lattice line beside a patch: every free site of p + u (or v) over the squares p of one row
  turn    one patch turns by 0.05 to 0.5 degrees about its centre
With --scan, each start first gets a grid scan of patch moves (scan(): 0.1 steps up to 0.5 per axis, one patch at a
time, two rounds), and the walk takes the rest of the time.
The start is a held layout of a smaller count (n - j), placed in the larger box as gap_grow.py does.
This is not a kick: no square moves by a small random step and nothing is relaxed during the walk.

  gap_walk.py run HELD.csv DETAILS.csv OUTDIR DEADLINE_EPOCH SPEC [SPEC ...] [--secs S] [--seed K]
     SPEC = n:j[:Lt]   target n from the held n - j; Lt defaults to the base side of n less 1e-5
     SPEC = n@d[:Lt]   target n from the tilted patches of the held d of a larger m: each patch moves by whole
                       cells (0 or -1 per axis for each unit of m), squares outside the box or on another square
                       leave, and the best --starts placements by refill count start a walk each
Our own code. Imports gap_grow.py, engine_lib, engine_fq and outline_lib of this lane; fillfast is Evan Daniel's
MIT packer, imported from its clone under SQ_BOX/ext/evand.
"""
import os, sys, json, math, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gap_grow as gg
from engine_lib import load, normalize, hw
from engine_fq import quench
from outline_lib import patches
import numpy as np, fillfast


def lattice(P):
    a = np.radians(P[:, 2]); a = np.where(a < 0, a + np.pi / 2, a)
    th = float(np.median(a))
    return th, np.array([math.cos(th), math.sin(th)]), np.array([-math.sin(th), math.cos(th)])


def fits(T, q, L):
    h = hw(math.radians(q[2]))
    if q[0] - h < -1e-9 or q[0] + h > L + 1e-9 or q[1] - h < -1e-9 or q[1] + h > L + 1e-9: return False
    d = np.hypot(T[:, 0] - q[0], T[:, 1] - q[1])
    near = d < 1.42
    if not near.any(): return True
    for x, y, a in T[near]:
        if not sat(x, y, a, q[0], q[1], q[2]): return False
    return True


def mtv(x1, y1, a1, x2, y2, a2):
    """the smallest move of square 2 that ends the overlap with square 1 (zero vector when apart)."""
    A, B = corners(x1, y1, a1), corners(x2, y2, a2)
    best = None
    for t in (a1, a2):
        r = math.radians(t)
        for ax in ((math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))):
            ax = np.array(ax); pa = A @ ax; pb = B @ ax
            o1 = pa.max() - pb.min(); o2 = pb.max() - pa.min()
            if o1 <= 0 or o2 <= 0: return np.zeros(2)
            o, sg = (o1, 1.0) if o1 < o2 else (o2, -1.0)
            if best is None or o < best[0]: best = (o, sg * ax)
    return best[1] * (best[0] + 1e-10)


def place(T, q, L, rng, iters=40):
    """q pushed out of every overlap, one smallest move at a time, inside the walls; None when it does not settle."""
    q = q.copy(); h = hw(math.radians(q[2]))
    for _ in range(iters):
        q[0] = min(max(q[0], h), L - h); q[1] = min(max(q[1], h), L - h)
        if fits(T, q, L): return q
        d = np.hypot(T[:, 0] - q[0], T[:, 1] - q[1]); moved = False
        for k in np.where(d < 1.42)[0]:
            v = mtv(T[k, 0], T[k, 1], T[k, 2], q[0], q[1], q[2])
            if v.any(): q[:2] += v; moved = True; break
        if not moved: break
    return q if fits(T, q, L) else None


def corners(x, y, a):
    t = math.radians(a); c, s = math.cos(t) / 2, math.sin(t) / 2
    return np.array([[x + c - s, y + s + c], [x - c - s, y - s + c], [x - c + s, y - s - c], [x + c + s, y + s - c]])


def sat(x1, y1, a1, x2, y2, a2, eps=1e-9):
    """True when the two unit squares do not overlap (separating axis)."""
    A, B = corners(x1, y1, a1), corners(x2, y2, a2)
    for t in (a1, a2):
        r = math.radians(t)
        for ax in ((math.cos(r), math.sin(r)), (-math.sin(r), math.cos(r))):
            pa = A @ ax; pb = B @ ax
            if pa.max() <= pb.min() + eps or pb.max() <= pa.min() + eps: return True
    return False


def count(L, T):
    try: return len(fillfast.fill(L, T, mode='exact', time_limit=5))
    except Exception: return -1


def moves(T, L, rng):
    groups = [g for g in patches(T) if len(g) >= 3]
    if not groups: return None
    g = groups[rng.randrange(len(groups))]
    P = T[g]; th, u, v = lattice(P); deg = math.degrees(th)
    kind = rng.choices(['add', 'del', 'slide', 'line', 'turn'], [5, 2, 3, 2, 1])[0]
    if kind == 'add' or kind == 'line':
        d = [u, -u, v, -v][rng.randrange(4)]
        if kind == 'add':
            p = P[rng.randrange(len(P))]
            q = place(T, np.array([p[0] + d[0], p[1] + d[1], p[2]]), L, rng)
            return (kind, np.vstack([T, q])) if q is not None else None
        # a line: the squares of P whose neighbour along d is free, all at once
        new = []
        cur = T.copy()
        for p in P:
            q = place(cur, np.array([p[0] + d[0], p[1] + d[1], p[2]]), L, rng)
            if q is not None: cur = np.vstack([cur, q]); new.append(q)
        return (kind, cur) if new else None
    if kind == 'del':
        c = P[:, :2].mean(0); dist = np.hypot(P[:, 0] - c[0], P[:, 1] - c[1])
        i = g[int(np.argsort(-dist)[rng.randrange(min(8, len(g)))])]
        return kind, np.delete(T, i, axis=0)
    if kind == 'slide':
        dx = rng.choice([-1, 1]) * rng.uniform(0.02, 0.3)
        ax = rng.randrange(2)
        Q = T.copy(); Q[g, ax] += dx
        rest = np.delete(T, g, axis=0)
        for q in Q[g]:
            if not fits(rest, q, L): return None
        return kind, Q
    if kind == 'turn':
        da = rng.choice([-1, 1]) * rng.uniform(0.05, 0.5)
        c = P[:, :2].mean(0); r = math.radians(da); R = np.array([[math.cos(r), -math.sin(r)], [math.sin(r), math.cos(r)]])
        Q = T.copy(); Q[g, :2] = (P[:, :2] - c) @ R.T + c; Q[g, 2] = P[:, 2] + da
        rest = np.delete(T, g, axis=0)
        for q in Q[g]:
            if not fits(rest, q, L): return None
        return kind, Q
    return None


def adds(T, L, rng):
    """every free lattice site beside a patch, pushed out of overlaps; one per 0.25 cell"""
    out, keys = [], set()
    for g in patches(T):
        if len(g) < 3: continue
        P = T[g]; th, u, v = lattice(P)
        for p in P:
            for d in (u, -u, v, -v):
                q = np.array([p[0] + d[0], p[1] + d[1], p[2]])
                if np.hypot(T[:, 0] - q[0], T[:, 1] - q[1]).min() < 0.6: continue
                k = (round(q[0] * 4), round(q[1] * 4))
                if k in keys: continue
                keys.add(k)
                w = place(T, q, L, rng)
                if w is not None: out.append(w)
    return out


def scan(n, T, L, secs, log, tag, step=0.1, reach=0.5, rounds=2):
    """each patch in turn over a grid of moves (step, up to reach per axis) with the others fixed; squares of the
    moved patch that leave the box or meet another square drop out; the best count wins, ties keep the old place"""
    t0 = time.time(); best = count(L, T); cur = T; it = 0
    grid = np.arange(-reach, reach + 1e-9, step)
    for r in range(rounds):
        moved = False
        for gi in range(min(4, len([g for g in patches(cur) if len(g) >= 3]))):
            G = [g for g in patches(cur) if len(g) >= 3]
            if gi >= len(G): break
            g = G[gi]; rest = np.delete(cur, g, axis=0); P = cur[g]
            top = (best, None, 0, 0)
            for dx in grid:
                for dy in grid:
                    if abs(dx) < 1e-12 and abs(dy) < 1e-12: continue
                    if time.time() - t0 > secs: break
                    keep = []
                    for q in P:
                        w = np.array([q[0] + dx, q[1] + dy, q[2]])
                        if fits(rest, w, L): keep.append(w)
                    if not keep: continue
                    Q = np.vstack([rest, np.array(keep)]); c = count(L, Q); it += 1
                    if c > top[0]: top = (c, Q, dx, dy)
                    if c >= n: break
                if top[0] >= n: break
            if top[1] is not None:
                best, cur, moved = top[0], top[1], True
                log.write(json.dumps(dict(tag=tag, n=n, it=it, kind='scan', count=best, dx=round(top[2], 3), dy=round(top[3], 3), t=round(time.time() - t0))) + '\n'); log.flush()
            if best >= n or time.time() - t0 > secs: return best, cur, it
        if not moved: break
    return best, cur, it


def walk(n, T0, L, secs, rng, log, tag, do_scan=False):
    t0 = time.time(); it = 0; seen = set()
    best = count(L, T0); cur = T0
    log.write(json.dumps(dict(tag=tag, n=n, start=best, L=L)) + '\n'); log.flush()
    if do_scan and best < n:
        best, cur, it = scan(n, cur, L, secs / 2, log, tag)
    while time.time() - t0 < secs and best < n:
        # a full sweep of the adds first
        top = (best, None)
        for q in adds(cur, L, rng):
            if time.time() - t0 > secs: break
            it += 1
            Q = np.vstack([cur, q]); c = count(L, Q)
            if c > top[0]: top = (c, Q)
            if c >= n: break
        if top[1] is not None:
            best, cur = top
            log.write(json.dumps(dict(tag=tag, n=n, it=it, kind='add', count=best, tilted=len(cur), t=round(time.time() - t0))) + '\n'); log.flush()
            continue
        # no add pays: plateau moves until one changes the state without losing a square
        for _ in range(40):
            m = moves(cur, L, rng)
            if m is None: continue
            kind, Q = m
            key = hash(np.round(Q, 3).tobytes())
            if key in seen: continue
            seen.add(key); it += 1
            c = count(L, Q)
            if c >= best:
                if c > best:
                    log.write(json.dumps(dict(tag=tag, n=n, it=it, kind=kind, count=c, tilted=len(Q), t=round(time.time() - t0))) + '\n'); log.flush()
                best, cur = c, Q
                break
    return best, cur, it


def shifted(T, s, dm, L, keep_best):
    """the patch placements of a donor of another box, ranked by refill count. dm > 0: the donor box is larger
    and each patch moves by 0 to -dm cells per axis; dm < 0: it is smaller and each patch moves by 0 to -dm.
    Only the four largest patches move; patches of fewer than 3 squares leave."""
    import itertools
    G = [g for g in patches(T) if len(g) >= 3][:4]
    opts = list(itertools.product(range(-dm, 1) if dm >= 0 else range(0, 1 - dm), repeat=2))
    out = []
    for combo in itertools.product(opts, repeat=len(G)):
        keep = []
        for g, (dx, dy) in zip(G, combo):
            for q in T[g]:
                w = np.array([q[0] + dx, q[1] + dy, q[2]]); h = hw(math.radians(q[2]))
                if w[0] - h < -1e-9 or w[1] - h < -1e-9 or w[0] + h > L + 1e-9 or w[1] + h > L + 1e-9: continue
                if not keep or fits(np.array(keep), w, L): keep.append(w)
        K = np.array(keep).reshape(-1, 3)
        out.append((count(L, K), 'sh' + ''.join('%d%d' % (-a, -b) for a, b in combo), K))
    out.sort(key=lambda t: -t[0])
    return out[:keep_best]


def main():
    a = sys.argv[1:]
    held, details, out, deadline = a[1], a[2], a[3], float(a[4])
    secs = float(a[a.index('--secs') + 1]) if '--secs' in a else 600
    seed = int(a[a.index('--seed') + 1]) if '--seed' in a else 1
    specs = [x for x in a[5:] if (':' in x or '@' in x) and not x.startswith('--')]
    rng = random.Random(seed)
    os.makedirs(out + '/raw', exist_ok=True)
    P = load(held); B = gg.base_of(details)
    log = open(out + '/walk.jsonl', 'a')
    nstart = int(a[a.index('--starts') + 1]) if '--starts' in a else 3
    for sp in specs:
        f = sp.replace('@', ':').split(':'); n = int(f[0])
        L = float(f[2]) if len(f) > 2 else B[n][0] - 1e-5
        if '@' in sp:
            d = int(f[1]); j = 'd%d' % d
            s, A = normalize(P[d]); T = gg.tilted(A)
            dm = int(math.floor(s)) - int(math.floor(L))
            starts = [(vt, V) for c, vt, V in shifted(T, s, dm, L, nstart)]
        else:
            j = int(f[1]); s, A = normalize(P[n - j]); T = gg.tilted(A)
            starts = list(gg.variants(T, s, L))
        for vt, V in starts:
            if time.time() > deadline: return
            tag = '%d-j%s-%s-s%d' % (n, j, vt, seed)
            best, cur, it = walk(n, V, L, min(secs, deadline - time.time()), rng, log, tag, '--scan' in a)
            rec = dict(tag=tag, n=n, end=best, its=it)
            if best >= n:
                X = gg.trim(np.array(fillfast.fill(L, cur, mode='exact')), n)
                s2, X2, _ = quench(L, X, (), timeout=900)
                rec['fq'] = s2
                if s2 is not None and s2 < B[n][0] - 1e-9:
                    p = '%s/raw/%d-w%s.csv' % (out, n, tag); gg.write_csv(p, n, X2); rec['file'] = p
                    print('HIT', tag, s2, 'base', B[n][0], flush=True)
            log.write(json.dumps(rec) + '\n'); log.flush()
            print(json.dumps(rec), flush=True)


if __name__ == '__main__':
    main()
