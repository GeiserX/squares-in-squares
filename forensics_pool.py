#!/usr/bin/env python3
"""Corner compositions with every known version of the parts, not only the held one.

forensics_compose.py puts two held layouts into opposite corners of one square. It fails where both parts
have a square in the small square that the two boxes share. Another layout of the same part, at a side
still below the target, may keep that corner free. This tool reads every version of each part from a pool
of packing files and tries each pair of versions in the 64 pairs of symmetries. A part may also hold more
squares than the split needs: the extra squares are left out, the colliding ones first.

  versions  POOL.txt NAMES.txt OUT.pkl [CSV_GLOB ...]
            Distinct layouts per n. POOL.txt holds rows "file,id,n,square,x,y,angle" (file is the line
            number in NAMES.txt). Each CSV_GLOB adds per-n files "n,square_id,x,y,angle".
  build     VERSIONS.pkl MERGED.csv MERGED_DETAILS.csv OUT_DIR [--only N,..] [--extra 2] [--min-gain 2e-10]
            MERGED.csv gives one more version of every n and MERGED_DETAILS.csv the side to beat.
  near      VERSIONS.pkl MERGED.csv MERGED_DETAILS.csv OUT_DIR [--over 0.03] [--top 60] [--keep 3] [--extra 2]
            Starts for a quench: the parts hold one or two squares too many and lose the colliding ones,
            so the layout is valid at a side above the side to beat. The n come in the order of that excess.
  follow    MERGED.csv MERGED_DETAILS.csv OUT.tsv [--within 2e-3]
            The 10 in the corner of (m - 3, k - 1) and the 26 in the corner of (m - 5, k - 1) for every n.
  voids     MERGED.csv MERGED_DETAILS.csv
            The layouts that keep a corner free for the corner square of a host.
  worth     MERGED_DETAILS.csv [--parts 8:1,12:4,7:3,4:1,6:1]
            What a part with a free corner would open, by the sides alone.
  ctl       VERSIONS.pkl HELD.csv HELD_DETAILS.csv OUT_DIR
            Positive: 639 must come back from a 10 and a 497, below the side of the round 16 file.
            Negative: n = 18 from two packings of 5 must give no layout below the held side of 18, with
            every version of the 5 in the pool (a loose 5 in a box of side 3 gives a valid layout at side 5).
"""
import sys, os, csv, glob, math, pickle, time, argparse, collections
import numpy as np
import forensics_compose as fc

TOL = 1e-9          # pool layouts carry float noise; the quench and the certificate judge the result


def fnum(s):
    return float(s.lstrip('s'))


def add_version(vers, n, sq, name):
    if len(sq) != n:
        return False
    s, Q = fc.frame(sq)
    if not np.isfinite(s) or s < math.isqrt(n) or s > math.isqrt(n) + 1.0 + 1e-6:
        return False
    key = (round(s, 7), round(float(np.sort(Q[:, 0] + 3 * Q[:, 1])[:5].sum()), 4))
    if key in vers[n]:
        return False
    vers[n][key] = (s, Q, name)
    return True


def cmd_versions(pool, names, out, globs):
    N = [l.strip() for l in open(names)]
    vers = collections.defaultdict(dict); cur = None; buf = []; t0 = time.time(); nl = 0
    def flush():
        if cur is not None:
            add_version(vers, cur[1], buf, N[cur[0] - 1] if 0 < cur[0] <= len(N) else 'pool file %d' % cur[0])
    with open(pool) as h:
        for line in h:
            q = line.rstrip('\n').split(','); nl += 1
            if len(q) != 7:
                continue
            try:
                key = (int(q[0]), int(q[2].lstrip('s'))); row = (fnum(q[4]), fnum(q[5]), fnum(q[6]))
            except ValueError:
                continue
            if key != cur:
                flush(); cur = key; buf = []
            buf.append(row)
    flush()
    print('%d pool rows in %.0f s' % (nl, time.time() - t0), flush=True)
    for g in globs:
        for p in sorted(glob.glob(g)):
            try:
                n = int(os.path.basename(p).split('.')[0])
                sq = [(fnum(r['x']), fnum(r['y']), fnum(r['angle'])) for r in csv.DictReader(open(p))]
            except Exception:
                continue
            add_version(vers, n, sq, p)
    V = {n: sorted(v.values(), key=lambda x: x[0]) for n, v in vers.items()}
    print('versions per n:', sorted((n, len(v)) for n, v in V.items()))
    pickle.dump(V, open(out, 'wb'))


def cover(pairs, e):
    """A smallest set of squares ('A' or 'B', index) that hits every colliding pair; None if it needs more than e."""
    if not pairs:
        return []
    if e == 0:
        return None
    i, j = pairs[0]
    for side, idx in (('A', i), ('B', j)):
        rest = [p for p in pairs if (p[0] != idx if side == 'A' else p[1] != idx)]
        r = cover(rest, e - 1)
        if r is not None:
            return [(side, idx)] + r
    return None


class Part:
    """One version of a layout with its 8 symmetries cached."""
    def __init__(self, s, Q, name):
        self.s = s; self.name = name
        self.S = [fc.sym(Q, s, g) for g in range(8)]


def collide(A2, B2, s, sA, sB):
    """Colliding pairs (index in A2, index in B2) round the small square that the two boxes share."""
    ia = np.nonzero((A2[:, 0] > s - sB - 1.5) & (A2[:, 1] < sB + 1.5))[0]
    ib = np.nonzero((B2[:, 0] < sA + 1.5) & (B2[:, 1] > s - sA - 1.5))[0]
    if not len(ia) or not len(ib):
        return []
    d = np.hypot(A2[ia, None, 0] - B2[None, ib, 0], A2[ia, None, 1] - B2[None, ib, 1])
    I, J = np.nonzero(d < 1.4143)
    if not len(I):
        return []
    KA = fc.corners(A2[ia]); KB = fc.corners(B2[ib]); out = []
    for i, j in zip(I, J):
        if fc.gap(KA[i], KB[j]) < -TOL:
            out.append((int(ia[i]), int(ib[j])))
    return out


def try_pair(PA, a, PB, b, n, e):
    """The first valid layout of n squares from two parts with e squares to leave out, or the least collision."""
    sA, sB = PA.s, PB.s; f = max(sA - a, sB - b); s = a + b + f; least = None
    G = np.array([(i + 0.5, j + 0.5, 0.0) for i in range(a) for j in range(b)] + [(s - 0.5 - i, s - 0.5 - j, 0.0) for i in range(b) for j in range(a)], float).reshape(-1, 3)
    for gA in range(8):
        A2 = PA.S[gA].copy(); A2[:, 1] += s - sA
        for gB in range(8):
            B2 = PB.S[gB].copy(); B2[:, 0] += s - sB
            pairs = collide(A2, B2, s, sA, sB)
            if least is None or len(pairs) < least:
                least = len(pairs)
            c = cover(pairs, e)
            if c is None:
                continue
            da = {i for side, i in c if side == 'A'}; db = {i for side, i in c if side == 'B'}
            A3 = np.delete(A2, sorted(da), 0); B3 = np.delete(B2, sorted(db), 0)
            X = np.r_[A3, B3, G]
            if len(X) < n:
                continue
            X = X[:n]                                              # what is still extra comes off the grid blocks
            K = fc.corners(X)
            if K.min() < -TOL or K.max() > s + TOL:
                continue
            w = fc.worst_overlap(X)
            if w < -TOL:
                continue
            return (s, X, gA, gB, w, len(c)), least
    return None, least


def near_pair(PA, a, PB, b, n, e, keep):
    """Valid layouts of n squares from two parts that hold e squares too many. Each colliding pair loses one
    of its two squares, and each choice is its own layout: [(side, squares, what was left out)]."""
    sA, sB = PA.s, PB.s; f = max(sA - a, sB - b); s = a + b + f; out = []; seen = set()
    G = np.array([(i + 0.5, j + 0.5, 0.0) for i in range(a) for j in range(b)] + [(s - 0.5 - i, s - 0.5 - j, 0.0) for i in range(b) for j in range(a)], float).reshape(-1, 3)
    for gA in range(8):
        A2 = PA.S[gA].copy(); A2[:, 1] += s - sA
        for gB in range(8):
            B2 = PB.S[gB].copy(); B2[:, 0] += s - sB
            pairs = collide(A2, B2, s, sA, sB)
            if not pairs or len(pairs) > e or len({p[0] for p in pairs}) != len(pairs) or len({p[1] for p in pairs}) != len(pairs):
                continue
            for mask in range(1 << len(pairs)):
                da = sorted(p[0] for i, p in enumerate(pairs) if not mask >> i & 1); db = sorted(p[1] for i, p in enumerate(pairs) if mask >> i & 1)
                key = (tuple(np.round(A2[da, :2].ravel(), 3)), tuple(np.round(B2[db, :2].ravel(), 3)), len(da))
                if key in seen:
                    continue
                seen.add(key)
                X = np.r_[np.delete(A2, da, 0), np.delete(B2, db, 0), G]
                if len(X) < n:
                    continue
                X = X[:n]; K = fc.corners(X)
                if K.min() < -TOL or K.max() > s + TOL or fc.worst_overlap(X) < -TOL:
                    continue
                out.append((s, X, 'A' * len(da) + 'B' * len(db)))
                if len(out) >= keep:
                    return out
    return out


def cmd_near(vpkl, merged_csv, details, out, only, extra, over, top, keep, maxver):
    """Layouts that hold one or two squares too many in the parts and lose the colliding ones. They are valid
    and their side is above the side to beat by less than OVER: starts for a quench, not results."""
    V = pickle.load(open(vpkl, 'rb')); D, fh = fc.held_f(details)
    T = parts_table(V, load_merged(merged_csv)); cache = {}
    def part(key, i):
        if (key, i) not in cache:
            cache[(key, i)] = Part(*T[key][i])
        return cache[(key, i)]
    plan = []
    for n in (sorted(only) if only else range(2, 1001)):
        m, k = fc.mk(n)
        if k < 1 or (m, k) not in fh or fh[(m, k)] > 0.999:        # a grid with holes: nothing to quench
            continue
        ft = fh[(m, k)]; jobs = []
        for a in range(1, m):
            b = m - a
            for ka in range(1, 2 * a + 1):
                if (a, ka) not in T or T[(a, ka)][0][0] - a >= ft + over:
                    continue
                for kb in range(max(1, k - ka + 1), min(2 * b, k - ka + extra) + 1):
                    for i, va in enumerate(T[(a, ka)][:maxver]):
                        for j, vb in enumerate(T.get((b, kb), [])[:maxver]):
                            f = max(va[0] - a, vb[0] - b)
                            if f < ft + over:
                                jobs.append((f, ka + kb - k, a, ka, i, b, kb, j))
        if jobs:
            jobs.sort(); plan.append((jobs[0][0] - ft, n, jobs))
    plan.sort(key=lambda x: x[0]); os.makedirs(out, exist_ok=True); t0 = time.time(); wrote = 0
    print('%d n have a pair of parts with squares to lose within %.3f of the side to beat; the first %d follow' % (len(plan), over, min(top, len(plan))), flush=True)
    for ex, n, jobs in plan[:top]:
        m, k = fc.mk(n); got = []; tn = time.time()
        for f, e, a, ka, i, b, kb, j in jobs:
            if len(got) >= keep or time.time() - tn > 60:
                break
            for s, X, tag in near_pair(part((a, ka), i), a, part((b, kb), j), b, n, e, keep - len(got)):
                fc.write_csv('%s/%d-%d.csv' % (out, n, len(got)), n, X)
                got.append((s, a * a + ka, b * b + kb, tag))
        wrote += len(got)
        print('n %4d (%2d,%2d) to beat %.6f: %s' % (n, m, k, D[n], '; '.join('side +%.5f from n = %d and n = %d without %s' % (s - D[n], x, y, t) for s, x, y, t in got) or 'no valid layout (best by the sides +%.5f)' % ex), flush=True)
    print('%d starts written, %.0f s' % (wrote, time.time() - t0), flush=True)


def cmd_follow(merged_csv, details, out, within):
    """The 10 in the corner of the layout of (m - 3, k - 1) and the 26 in the corner of (m - 5, k - 1), for every n
    where that side is within WITHIN of the side to beat: is the layout valid, and which part sets its side."""
    D, fh = fc.held_f(details); M = load_merged(merged_csv); cache = {}; rows = []
    def part(n):
        if n not in cache:
            cache[n] = Part(*fc.frame(M[n]), 'merged')
        return cache[n]
    for n in range(12, 1001):
        m, k = fc.mk(n); ft = fh.get((m, k))
        if ft is None or ft > 0.999 or k < 2:
            continue
        for b, kb in ((3, 1), (5, 1)):
            a, ka = m - b, k - kb
            if a < 2 or ka < 1 or ka > 2 * a or (a, ka) not in fh:
                continue
            f = max(fh[(a, ka)], fh[(b, kb)])
            if f - ft > within:
                continue
            r, least = try_pair(part(a * a + ka), a, part(b * b + kb), b, n, 0)
            rows.append((f - ft, n, m, k, a * a + ka, b * b + kb, fh[(a, ka)], fh[(b, kb)], ft, r is not None))
    rows.sort()
    with open(out, 'w') as h:
        h.write('n\tm\tk\thost_n\tpart_n\thost_f\tpart_f\tf_to_beat\tside_above\thost_score_gain_needed\tvalid\tlimited_by\n')
        for d, n, m, k, hn, pn, hf, pf, ft, ok in rows:
            h.write('%d\t%d\t%d\t%d\t%d\t%.9f\t%.9f\t%.9f\t%.3e\t%.3e\t%s\t%s\n' % (n, m, k, hn, pn, hf, pf, ft, d, max(0.0, d) / math.sqrt(hn), 'yes' if ok else 'no', 'host' if hf > pf else 'part'))
    v = [r for r in rows if r[-1]]
    print('%d pairs within %g by the sides, %d valid, %d of them ties (within 2e-9)' % (len(rows), within, len(v), sum(1 for r in v if abs(r[0]) < 2e-9)))


def cmd_voids(merged_csv, details):
    """Which layouts keep a corner free for the corner square of a host: each layout against a 3 by 3 grid block."""
    D, fh = fc.held_f(details); M = load_merged(merged_csv); out = []
    G = np.array([(i + 0.5, j + 0.5, 0.0) for i in range(3) for j in range(3)], float)
    for n in range(2, 1001):
        b, kb = fc.mk(n)
        if kb < 1 or (b, kb) not in fh or fh[(b, kb)] > 0.999:
            continue
        PB = Part(*fc.frame(M[n]), 'merged'); S = b + 3.0; free = 0               # the host is the block: a = 2 and f = 1
        for gB in range(8):
            B2 = PB.S[gB].copy(); B2[:, 0] += S - PB.s; A2 = G.copy(); A2[:, 1] += S - 3.0
            free += not collide(A2, B2, S, 3.0, PB.s)
        if free:
            out.append('%d (%d,%d) %.4f' % (n, b, kb, fh[(b, kb)]))
    print('%d layouts keep a corner free for a unit corner square: %s' % (len(out), '; '.join(out)))


def cmd_worth(details, parts):
    """What a part with a free corner would open, by the sides alone: f(m + b, k + kb) <= max(f(m, k), f(b, kb))."""
    D, fh = fc.held_f(details)
    for b, kb in parts:
        f0 = fh[(b, kb)]; L = []
        for m in range(1, 32 - b):
            for k in range(1, 2 * m + 1):
                Mm, K = m + b, k + kb
                if (m, k) not in fh or (Mm, K) not in fh or K > 2 * Mm:
                    continue
                g = (fh[(Mm, K)] - max(fh[(m, k)], f0)) / math.sqrt(Mm * Mm + K)
                if g > 2e-10:
                    L.append((g, Mm * Mm + K, m * m + k, fh[(Mm, K)] - f0))
        print('part %d (%d,%d) f %.4f: %s' % (b * b + kb, b, kb, f0, '; '.join('n %d with host %d: gain %.2e, the part may lose %.4f' % (n, h, g, c) for g, n, h, c in sorted(L, reverse=True)) or 'opens nothing'))


def load_merged(path):
    rows = collections.defaultdict(list)
    with open(path) as h:
        head = h.readline().strip().split(','); o = 1 if head[0] == 'id' else 0
        for line in h:
            q = line.rstrip('\n').split(',')
            rows[int(q[o].lstrip('s'))].append((fnum(q[o + 2]), fnum(q[o + 3]), fnum(q[o + 4])))
    return rows


def parts_table(V, merged):
    """(a, k) -> list of Part, the lowest side first."""
    vers = collections.defaultdict(dict)
    for n, sq in merged.items():
        add_version(vers, n, sq, 'the merged file')
    for n, L in V.items():
        for s, Q, name in L:
            key = (round(s, 7), round(float(np.sort(Q[:, 0] + 3 * Q[:, 1])[:5].sum()), 4))
            vers[n].setdefault(key, (s, Q, name))
    T = {}
    for n, d in vers.items():
        a, k = fc.mk(n)
        if k >= 1:
            T[(a, k)] = sorted(d.values(), key=lambda x: x[0])
    return T


def cmd_build(vpkl, merged_csv, details, out, only, extra, min_gain, maxver, budget):
    V = pickle.load(open(vpkl, 'rb')); D, fh = fc.held_f(details)
    T = parts_table(V, load_merged(merged_csv)); cache = {}
    def part(key, i):
        if (key, i) not in cache:
            cache[(key, i)] = Part(*T[key][i])
        return cache[(key, i)]
    os.makedirs(out, exist_ok=True); got = 0; tot = 0.0; t0 = time.time()
    for n in (sorted(only) if only else range(2, 1001)):
        m, k = fc.mk(n)
        if k < 2 or (m, k) not in fh:
            continue
        ft = fh[(m, k)] - min_gain * math.sqrt(n); jobs = []
        for a in range(1, m):
            b = m - a
            for ka in range(1, 2 * a + 1):
                LA = [i for i, v in enumerate(T.get((a, ka), [])[:maxver]) if v[0] - a < ft]
                if not LA:
                    continue
                for kb in range(max(1, k - ka), min(2 * b, k - ka + extra) + 1):
                    LB = [i for i, v in enumerate(T.get((b, kb), [])[:maxver]) if v[0] - b < ft]
                    for i in LA:
                        for j in LB:
                            f = max(T[(a, ka)][i][0] - a, T[(b, kb)][j][0] - b)
                            jobs.append((f, ka + kb - k, a, ka, i, b, kb, j))
        if not jobs:
            continue
        jobs.sort(); done = None; least = None; tried = 0; tn = time.time()
        for f, e, a, ka, i, b, kb, j in jobs:
            if time.time() - tn > budget:
                break
            r, l = try_pair(part((a, ka), i), a, part((b, kb), j), b, n, e); tried += 1
            if l is not None and (least is None or l - e < least):
                least = l - e
            if r is not None:
                done = (r, a, ka, i, b, kb, j, e); break
        if done:
            (s, X, gA, gB, w, drop), a, ka, i, b, kb, j, e = done
            fc.write_csv('%s/%d.csv' % (out, n), n, X); g = (D[n] - s) / math.sqrt(n); got += 1; tot += g
            print('n %4d (%2d,%2d): VALID side %.10f, to beat %.10f, gain %.3e, smallest gap %.1e, %d left out | n = %d sym %d [%s] | n = %d sym %d [%s]' % (
                n, m, k, s, D[n], g, w, e, a * a + ka, gA, T[(a, ka)][i][2], b * b + kb, gB, T[(b, kb)][j][2]), flush=True)
        else:
            f = jobs[0][0]
            print('n %4d (%2d,%2d): no valid layout in %d of %d pairs of versions, least collision %s squares too many (gain if valid %.3e)' % (
                n, m, k, tried, len(jobs), least, (fh[(m, k)] - f) / math.sqrt(n)), flush=True)
    print('%d n built, gain %.6f before the certificate, %.0f s' % (got, tot, time.time() - t0), flush=True)
    return got


def cmd_ctl(vpkl, held, details, out):
    V = pickle.load(open(vpkl, 'rb'))
    print('versions of n = 5 in the pool: %d, of n = 497: %d' % (len(V.get(5, [])), len(V.get(497, []))))
    pos = cmd_build(vpkl, held, details, out + '/pos', {639}, 0, 2e-10, 40, 600)
    D, fh = fc.held_f(details); T = parts_table(V, load_merged(held)); bad = 0; sides = []
    for i in range(len(T[(2, 1)])):
        for j in range(i, len(T[(2, 1)])):
            r, l = try_pair(Part(*T[(2, 1)][i]), 2, Part(*T[(2, 1)][j]), 2, 18, 0)
            sides.append(None if r is None else r[0])
            bad += r is not None and r[0] < D[18] - 1e-9
    print('negative: n = 18 from two packings of 5, %d versions of the 5, %d pairs: %d layouts below the held side %.4f (want 0), %d layouts at or above it' % (
        len(T[(2, 1)]), len(sides), bad, D[18], sum(x is not None for x in sides) - bad))
    ok = pos == 1 and bad == 0
    print('CONTROL GREEN' if ok else 'CONTROL RED'); return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=['versions', 'build', 'near', 'follow', 'voids', 'worth', 'ctl']); ap.add_argument('args', nargs='*')
    ap.add_argument('--within', type=float, default=2e-3); ap.add_argument('--parts', default='8:1,12:4,7:3,4:1,6:1')
    ap.add_argument('--over', type=float, default=0.03); ap.add_argument('--top', type=int, default=60); ap.add_argument('--keep', type=int, default=3)
    ap.add_argument('--only', default=''); ap.add_argument('--extra', type=int, default=2); ap.add_argument('--min-gain', type=float, default=2e-10)
    ap.add_argument('--max-versions', type=int, default=40); ap.add_argument('--budget', type=float, default=120.0)
    a = ap.parse_args()
    if a.cmd == 'versions':
        cmd_versions(a.args[0], a.args[1], a.args[2], a.args[3:])
    elif a.cmd == 'build':
        only = {int(x) for x in a.only.split(',') if x}
        cmd_build(a.args[0], a.args[1], a.args[2], a.args[3], only, a.extra, a.min_gain, a.max_versions, a.budget)
    elif a.cmd == 'follow':
        cmd_follow(a.args[0], a.args[1], a.args[2], a.within)
    elif a.cmd == 'voids':
        cmd_voids(a.args[0], a.args[1])
    elif a.cmd == 'worth':
        cmd_worth(a.args[0], [tuple(int(v) for v in x.split(':')) for x in a.parts.split(',')])
    elif a.cmd == 'near':
        only = {int(x) for x in a.only.split(',') if x}
        cmd_near(a.args[0], a.args[1], a.args[2], a.args[3], only, a.extra, a.over, a.top, a.keep, min(a.max_versions, 3))
    else:
        sys.exit(cmd_ctl(*a.args[:4]))
