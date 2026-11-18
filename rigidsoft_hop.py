#!/usr/bin/env python3
"""rigidsoft_hop: move one upright from one staircase row to another around a tilted block, then quench.

The fq quench never moves an upright to another row (rigidsoft.md section 7), so the staircases around a block
fix the soft form the quench can reach. This tool changes the staircases of a held layout by one square: it
takes the last square of one row (the tooth next to the block) and adds a square to the end of another row.
Every such start is quenched with every square free.

  rigidsoft_hop.py run JOBDIR WORKER NWORKERS FQ HELD_DETAILS.csv SUB.csv N [--tip 3] [--eps 0] [--sets alm0,def]
                   [--skip 0] [--moves hop] [--kmax 6] [--df 0] [--ang A]
                   [--only lf] [--done A.tsv,B.tsv] [--turn F] [--from TL4,BR8] [--depth 0.293] [--pairs TL4+BR8]
        --tip T: only the T rows at each end of every staircase (the corners of the hole); 0 takes every row
        --eps E: turn every tilted square by E degrees about its own centre first
        --skip K: leave out the first K moves of the list (to go on after a run that stopped)
        --moves kink: the compound move below instead of the single hop; --kmax is its largest K
        --moves grow: one upright becomes a tilted square next to the block (rigidsoft.md section 10); it changes
        the count of tilted squares, which a hop or a kink never does
        --moves ungrow: the reverse, one tilted square next to a wall becomes an upright in the row of that wall;
        --moves ungrow2 does it to two squares at once
        --moves home: the last square of a staircase row goes to a wall row with room for one more upright
        --moves flip: up to --kmax neighbouring rows of the block are set to one sense of turn, at the turn the
        block has (a soft block is bands of rows turned both ways)
        --df D1,D2: start each quench at the held side plus each D
        --ang A: set every tilted square to the angle A in degrees first (its centre stays)
        --turn F: multiply the turn of every tilted square away from 45 degrees by F first (its centre stays).
        A block of two domains turned in opposite senses keeps both senses, which --ang does not
        --only lf,ff: only the kink moves of these kinds. lf takes from the last rows and adds to the first rows
        of the opposite staircase, and fl is the reverse. ff and ll move squares between the two staircases on
        one wall, in the rows next to the tip of the block: the first rows on the bottom and top walls (ff), the
        last rows on the left and right walls (ll). Those two kinds have no control yet.
        --done A.tsv,B.tsv: leave out the moves that these result files of earlier runs already hold
        --from TL4,BR8: only the hops that take the last square of these staircase rows
        --moves notch: the last square of a staircase row becomes a tilted square in the notch it leaves, next
        to the block; --depth D1,D2 sets how far it stands toward the block, --pairs TL4+BR8,.. takes two rows
        appends JOBDIR/hop-N-WORKER.tsv (kink-N-WORKER.tsv); a side below the held one is written to
        JOBDIR/raw/N-<tag>.csv
  The run stops at the unix time in JOBDIR/deadline.

The kink move shifts one flank of the block by one lattice step along its chains. It takes the last square of K
neighbouring rows of one staircase and adds a square to K neighbouring rows of the staircase in the opposite
corner. The rows are the first K or the last K of a run of rows whose counts go down by one per row, and the two
runs face the same chains: the last rows of one staircase and the first rows of the other, or the reverse. From
the staircases 6,5,4,3,2,1 and 5,4,3,2,1 the move with K = 3 gives 6,5,4,2,1 twice, the ends of the held 230.
"""
import csv, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rigidsoft as RS  # noqa: E402


# a target cell is free when no other upright is nearer than this (largest coordinate difference). A quenched
# layout holds its uprights 1e-9 to 1e-7 off their cells, so a test at 1 - 1e-9 refuses the cell next to a square.
FREE = 0.97


def classify(s, X):
    """staircase and row of every upright: (region, row, index from the wall) or None"""
    out = []
    for x, y, d in X:
        if abs(d) >= 3:
            out.append(None); continue
        fx = (x - 0.5) % 1; fy = (y - 0.5) % 1
        gx = (s - x - 0.5) % 1; gy = (s - y - 0.5) % 1
        L = min(fx, 1 - fx) < 0.03; R = min(gx, 1 - gx) < 0.03
        B = min(fy, 1 - fy) < 0.03; T = min(gy, 1 - gy) < 0.03
        if not ((L or R) and (B or T)):
            out.append(None); continue
        reg = ('B' if B else 'T') + ('L' if L else 'R')
        j = int(round(y - 0.5)) if B else int(round(s - y - 0.5))
        i = int(round(x - 0.5)) if L else int(round(s - x - 0.5))
        out.append((reg, j, i))
    return out


def centre(s, reg, j, i):
    x = i + 0.5 if reg[1] == 'L' else s - i - 0.5
    y = j + 0.5 if reg[0] == 'B' else s - j - 0.5
    return x, y


def hops(s, X, tip):
    C = classify(s, X)
    rows = {}
    for q, c in enumerate(C):
        if c is not None:
            rows.setdefault((c[0], c[1]), []).append((c[2], q))
    count = {}
    for (reg, j), v in rows.items():
        v.sort()
        if [i for i, _ in v] == list(range(len(v))):      # a row that starts at its wall with no hole
            count[(reg, j)] = len(v)
    nrow = {reg: 1 + max([j for (r, j) in count if r == reg], default=-1) for reg in ('BL', 'BR', 'TL', 'TR')}

    def near_tip(reg, j):
        return tip <= 0 or j < tip or j >= nrow[reg] - tip

    takes = [(reg, j) for (reg, j) in sorted(count) if near_tip(reg, j)]
    adds = [(reg, j) for (reg, j) in sorted(count) if near_tip(reg, j)] + [(reg, nrow[reg]) for reg in ('BL', 'BR', 'TL', 'TR')]
    up = np.array([[x, y] for x, y, d in X if abs(d) < 3])
    for t in takes:
        qt = rows[t][-1][1]
        for a in adds:
            if a == t:
                continue
            x, y = centre(s, a[0], a[1], count.get(a, 0))
            if not (0.5 - 1e-9 <= x <= s - 0.5 + 1e-9 and 0.5 - 1e-9 <= y <= s - 0.5 + 1e-9):
                continue
            d = np.abs(up - np.array([x, y])).max(axis=1)
            d[np.abs(up - X[qt, :2]).max(axis=1) < 1e-9] = 9.0
            if (d < FREE).any():
                continue
            Y = X.copy(); Y[qt] = (x, y, 0.0)
            yield '%s%d-%s%d' % (t[0], t[1], a[0], a[1]), Y


OPP = {'BL': 'TR', 'TR': 'BL', 'BR': 'TL', 'TL': 'BR'}
# two staircases on one wall: the rows next to the tip of the block between them are the first rows on the bottom
# and top walls (ff) and the last rows on the left and right walls (ll)
ADJ = (('BL', 'BR', 'ff'), ('BR', 'BL', 'ff'), ('TL', 'TR', 'ff'), ('TR', 'TL', 'ff'),
       ('BL', 'TL', 'll'), ('TL', 'BL', 'll'), ('BR', 'TR', 'll'), ('TR', 'BR', 'll'))


def segments(cnt):
    """runs of rows whose counts go down by one per row: [(first row, last row)]"""
    segs = []; js = sorted(j for j in cnt if cnt[j] >= 1); i = 0
    while i < len(js):
        k = i
        while k + 1 < len(js) and js[k + 1] == js[k] + 1 and cnt[js[k + 1]] == cnt[js[k]] - 1:
            k += 1
        segs.append((js[i], js[k])); i = k + 1
    return segs


def kinks(s, X, kmax):
    C = classify(s, X)
    rows = {}
    for q, c in enumerate(C):
        if c is not None:
            rows.setdefault((c[0], c[1]), []).append((c[2], q))
    count = {}
    for (reg, j), v in rows.items():
        v.sort()
        if [i for i, _ in v] == list(range(len(v))):
            count[(reg, j)] = len(v)
    ups = [q for q in range(len(X)) if abs(X[q, 2]) < 3]
    seen = set()

    def move(S, D, src, dst, name, k):
        cd = {j: c for (r, j), c in count.items() if r == D}
        moved = [rows[(S, j)][-1][1] for j in src]
        keep = np.array([X[q, :2] for q in ups if q not in moved])
        Y = X.copy()
        for q, j in zip(moved, dst):
            x, y = centre(s, D, j, cd[j])
            if not (0.5 - 1e-9 <= x <= s - 0.5 + 1e-9 and 0.5 - 1e-9 <= y <= s - 0.5 + 1e-9) or \
                    (np.abs(keep - np.array([x, y])).max(axis=1) < FREE).any():
                return None
            Y[q] = (x, y, 0.0)
        sig = (S, tuple(src), D, tuple(dst))
        if sig in seen:
            return None
        seen.add(sig)
        return '%s%d-%s%d_k%d%s' % (S, src[0], D, dst[0], k, name), Y

    pairs = [(S, OPP[S], 'opp') for S in ('BL', 'BR', 'TL', 'TR')] + list(ADJ)
    for S, D, kind in pairs:
        cs = {j: c for (r, j), c in count.items() if r == S}; cd = {j: c for (r, j), c in count.items() if r == D}
        for a0, a1 in segments(cs):
            for b0, b1 in segments(cd):
                for k in range(1, kmax + 1):
                    if k > a1 - a0 + 1 or k > b1 - b0 + 1:
                        break
                    last_s, first_s = range(a1 - k + 1, a1 + 1), range(a0, a0 + k)
                    last_d, first_d = range(b1 - k + 1, b1 + 1), range(b0, b0 + k)
                    todo = {'opp': ((last_s, first_d, 'lf'), (first_s, last_d, 'fl')),
                            'ff': ((first_s, first_d, 'ff'),), 'll': ((last_s, last_d, 'll'),)}[kind]
                    for src, dst, name in todo:
                        got = move(S, D, src, dst, name, k)
                        if got is not None:
                            yield got


def grows(s, X):
    """one upright becomes a tilted square: every free place one step along or across the chains from a tilted
    square takes a new tilted square at the block's angle, and the upright nearest to that place goes"""
    til = np.abs(X[:, 2]) >= 3
    T = X[til]; deg = float(np.median(T[:, 2] % 90)); th = math.radians(deg)
    u = np.array([math.cos(th), math.sin(th)]); v = np.array([-u[1], u[0]])
    hw = (abs(u[0]) + abs(u[1])) / 2
    ups = np.where(~til)[0]
    seen = set()
    for t in T:
        for d in (u, -u, v, -v):
            p = t[:2] + d
            key = (int(round(p[0] * 20)), int(round(p[1] * 20)))
            if key in seen:
                continue
            seen.add(key)
            if min(p[0], p[1]) - hw < -0.02 or max(p[0], p[1]) + hw > s + 0.02:
                continue
            D = T[:, :2] - p
            if (np.maximum(np.abs(D @ u), np.abs(D @ v)) < 0.9).any():
                continue
            q = ups[np.argmin(((X[ups, :2] - p) ** 2).sum(axis=1))]
            Y = X.copy(); Y[q] = (p[0], p[1], deg)
            yield 'g%.2f_%.2f' % (p[0], p[1]), Y


def ungrows(s, X, pairs=False):
    """one tilted square next to a wall becomes an upright in the row of that wall: the reverse of the grow move.
    The held 297 differs from its fresh fq-soft form by this step (rigidsoft.md section 11): its top row holds one
    more upright and its block one square fewer. The upright goes to the free part of the wall row at the place
    of the square: at each end of that part and in its middle. With PAIRS, two squares go at once (middle only)."""
    til = np.abs(X[:, 2]) >= 3
    ups = X[~til]; one = []
    for q in np.where(til)[0]:
        x, y = float(X[q, 0]), float(X[q, 1])
        for wall, dist in (('L', x), ('R', s - x), ('B', y), ('T', s - y)):
            if dist > 1.3:
                continue
            w = 0.5 if wall in 'LB' else s - 0.5
            k, c = (0, y) if wall in 'LR' else (1, x)              # k: the coordinate fixed by the wall
            row = [float(v[1 - k]) for v in ups if abs(v[k] - w) < 0.5]
            lo = max([v for v in row if v < c] + [-0.5]) + 1.0
            hi = min([v for v in row if v > c] + [s + 0.5]) - 1.0
            if hi < lo - 0.05:
                continue
            seen = set()
            for name, pos in (('m', (lo + hi) / 2), ('a', lo), ('b', hi)):
                if round(pos, 3) in seen:
                    continue
                seen.add(round(pos, 3))
                new = (w, pos, 0.0) if k == 0 else (pos, w, 0.0)
                one.append(('u%s%.2f_%.2f%s' % (wall, x, y, name), q, new))
    if not pairs:
        for tag, q, new in one:
            Y = X.copy(); Y[q] = new
            yield tag, Y
        return
    mid = [o for o in one if o[0].endswith('m')]
    for i in range(len(mid)):
        for j in range(i + 1, len(mid)):
            if mid[i][1] == mid[j][1] or max(abs(mid[i][2][0] - mid[j][2][0]), abs(mid[i][2][1] - mid[j][2][1])) < 1.0:
                continue
            Y = X.copy(); Y[mid[i][1]] = mid[i][2]; Y[mid[j][1]] = mid[j][2]
            yield mid[i][0] + '+' + mid[j][0], Y


def block_rows(X):
    """the rows of the block: index of every tilted square, its row along the long axis of the block, and its
    turn away from 45 degrees (signed, in degrees)"""
    idx = np.where(np.abs(X[:, 2]) >= 3)[0]; T = X[idx]
    P = T[:, :2] - T[:, :2].mean(axis=0)
    w, V = np.linalg.eigh(P.T @ P)
    u = np.array([1.0, 1.0 if V[0, -1] * V[1, -1] > 0 else -1.0]) / math.sqrt(2.0)   # the diagonal nearest to the long axis
    al = P @ u
    row = np.round(al - al.min()).astype(int)
    dev = np.where(T[:, 2] > 0, T[:, 2] - 45.0, T[:, 2] + 45.0)
    return idx, row, dev


def facing(s, X):
    """for every row of the block: its turn and the staircase rows whose tooth (the inner corner of the last
    square) faces it. [(row, turn, squares, [(region, staircase row, place along the face 0..1)])]"""
    idx, row, dev = block_rows(X); T = X[idx]
    P = T[:, :2] - T[:, :2].mean(axis=0)
    w, V = np.linalg.eigh(P.T @ P)
    u = np.array([1.0, 1.0 if V[0, -1] * V[1, -1] > 0 else -1.0]) / math.sqrt(2.0)
    C = classify(s, X); last = {}
    for q, c in enumerate(C):
        if c is not None and (c[:2] not in last or c[2] > last[c[:2]][0]):
            last[c[:2]] = (c[2], q)
    out = []
    for r in range(row.max() + 1):
        m = row == r; a0 = float((T[m, :2] @ u).mean()); teeth = []
        for (reg, j), (i, q) in sorted(last.items()):
            cx = X[q, 0] + (0.5 if reg[1] == 'L' else -0.5); cy = X[q, 1] + (0.5 if reg[0] == 'B' else -0.5)
            a = float(np.array([cx, cy]) @ u)
            if abs(a - a0) <= 0.5:
                teeth.append((reg, j, round(a - a0 + 0.5, 2)))
        out.append((r, round(float(np.median(dev[m])), 3), int(m.sum()), teeth))
    return out


def flips(s, X, span=4):
    """a soft block is a stack of rows, and each band of rows is turned one way or the other (rigidsoft.md
    section 11). This move sets up to SPAN neighbouring rows to one sense, at the turn the block already has."""
    idx, row, dev = block_rows(X)
    t = float(np.median(np.abs(dev)))
    if t < 1e-3:
        return
    for r0 in range(row.max() + 1):
        for r1 in range(r0, min(r0 + span, row.max() + 1)):
            m = (row >= r0) & (row <= r1)
            for sense in (1.0, -1.0):
                if (np.abs(dev[m] - sense * t) < 0.03).all():
                    continue
                Y = X.copy(); d = sense * t
                Y[idx[m], 2] = 45.0 + d if d <= 0 else d - 45.0
                yield 'r%d-%d%s' % (r0, r1, 'p' if sense > 0 else 'm'), Y


def homes(s, X):
    """the last square of one staircase row goes to a wall row that has room for one more upright, and the
    uprights of that wall row are set at even steps. This is the hop for a square that has no free cell: the room
    of a wall row is often split in two parts, each under one square wide (rigidsoft.md section 11)."""
    C = classify(s, X); rows = {}
    for q, c in enumerate(C):
        if c is not None:
            rows.setdefault((c[0], c[1]), []).append((c[2], q))
    takes = []
    for key, v in sorted(rows.items()):
        v.sort()
        if [i for i, _ in v] == list(range(len(v))):
            takes.append((key, v[-1][1]))
    up = np.abs(X[:, 2]) < 3
    for (reg, j), q in takes:
        for name, k, w in (('B', 1, 0.5), ('T', 1, s - 0.5), ('L', 0, 0.5), ('R', 0, s - 0.5)):
            m = [int(i) for i in np.where(up & (np.abs(X[:, k] - w) < 0.5))[0] if i != q]
            if abs(X[q, k] - w) < 0.5 or s - len(m) < 1.0:
                continue
            m.sort(key=lambda i: X[i, 1 - k])
            edge = [0.0] + [float(X[i, 1 - k]) for i in m] + [s]
            g = int(np.argmax(np.diff(edge)))                      # the new square goes into the widest gap
            order = m[:g] + [q] + m[g:]
            Y = X.copy()
            for i, o in enumerate(order):
                pos = (i + 0.5) * s / len(order)
                Y[o] = (w, pos, 0.0) if k == 0 else (pos, w, 0.0)
            yield '%s%d-w%s' % (reg, j, name), Y


INWARD = {'BL': (1.0, 1.0), 'BR': (-1.0, 1.0), 'TL': (1.0, -1.0), 'TR': (-1.0, -1.0)}


def notches(s, X, depth=(0.293,), pairs=''):
    """the last square of one staircase row becomes a tilted square in the notch that it leaves. The notch is a
    right triangle with legs of 2, open to the block. A unit square at 45 degrees goes 0.914 deep into it, so it
    stands 0.086 over the line of the teeth, and the quench has to find that room. DEPTH is how far the centre
    moves from the cell centre toward the block. PAIRS 'TL4+BR8,..' does it to two rows at once."""
    C = classify(s, X); rows = {}
    for q, c in enumerate(C):
        if c is not None:
            rows.setdefault((c[0], c[1]), []).append((c[2], q))
    last = {}
    for key, v in sorted(rows.items()):
        v.sort()
        if [i for i, _ in v] == list(range(len(v))):
            last[key] = v[-1][1]

    def put(Y, key, dp):
        q = last[key]; nx, ny = INWARD[key[0]]
        Y[q] = (X[q, 0] + dp * nx / math.sqrt(2.0), X[q, 1] + dp * ny / math.sqrt(2.0), 45.0)

    if pairs:
        for pr in pairs.split(','):
            keys = [(t[:2], int(t[2:])) for t in pr.split('+')]
            if all(k in last for k in keys):
                for dp in depth:
                    Y = X.copy()
                    for k in keys:
                        put(Y, k, dp)
                    yield '%s-n%g' % ('+'.join('%s%d' % k for k in keys), dp), Y
        return
    for key in sorted(last):
        for dp in depth:
            Y = X.copy(); put(Y, key, dp)
            yield '%s%d-n%g' % (key[0], key[1], dp), Y


def cmd_run(a):
    jd, w, nw, fqbin, held_csv, sub, n = a[0], int(a[1]), int(a[2]), a[3], a[4], a[5], int(a[6])
    opt = {'--tip': '3', '--eps': '0', '--sets': 'alm0,def', '--skip': '0', '--moves': 'hop', '--kmax': '6', '--df': '0',
           '--ang': '', '--only': '', '--done': '', '--turn': '', '--from': '', '--depth': '0.293', '--pairs': ''}
    i = 7
    while i < len(a):
        opt[a[i]] = a[i + 1]; i += 2
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held_csv))}
    os.makedirs(jd + '/raw', exist_ok=True); os.makedirs(jd + '/tmp', exist_ok=True)
    s, X = RS.normalize(RS.load(sub, {n})[n])
    eps = float(opt['--eps'])
    if eps:
        X = X.copy(); t = np.abs(X[:, 2]) >= 3; X[t, 2] = X[t, 2] - eps
    if opt['--ang']:
        X = X.copy(); t = np.abs(X[:, 2]) >= 3; X[t, 2] = float(opt['--ang'])
    if opt['--turn']:
        X = X.copy(); t = np.abs(X[:, 2]) >= 3
        dev = np.where(X[:, 2] > 0, X[:, 2] - 45.0, X[:, 2] + 45.0)
        X[t, 2] = X[t, 2] + (float(opt['--turn']) - 1.0) * dev[t]
    res = '%s/%s-%d-%d.tsv' % (jd, opt['--moves'], n, w)
    done = set()
    for f in [f for f in opt['--done'].split(',') if f]:
        done.update(line.split('\t')[1] for line in open(f) if line.count('\t') >= 3)
    nq = 0; best = None
    moves = {'kink': lambda: kinks(s, X, int(opt['--kmax'])), 'grow': lambda: grows(s, X),
             'ungrow': lambda: ungrows(s, X), 'ungrow2': lambda: ungrows(s, X, True),
             'flip': lambda: flips(s, X, int(opt['--kmax'])), 'home': lambda: homes(s, X),
             'notch': lambda: notches(s, X, [float(v) for v in opt['--depth'].split(',')], opt['--pairs'])}.get(
        opt['--moves'], lambda: hops(s, X, int(opt['--tip'])))()
    for q, (tag, Y) in enumerate(moves):
        if q % nw != w or q < int(opt['--skip']) or not tag.endswith(tuple(opt['--only'].split(','))) or \
                '%s_e%g' % (tag, eps) in done or not tag.startswith(tuple(f + '-' if f else '' for f in opt['--from'].split(','))):
            continue
        if time.time() > float(open(jd + '/deadline').read()):
            break
        got = None; log = []
        for fs in opt['--sets'].split(','):
            for df in [float(v) for v in opt['--df'].split(',')]:
                s1, X1, dt = RS.fq(fqbin, jd + '/tmp', s + df, Y, RS.FLAGSETS[fs], timeout=120)
                log.append('%s:%s:%.0fs' % (fs, 'None' if s1 is None else '%.9f' % s1, dt))
                if s1 is not None and (got is None or s1 < got[0]):
                    got = (s1, X1)
        if got is not None and got[0] < held[n] + 3e-3:
            s2, X2, dt = RS.fq(fqbin, jd + '/tmp', got[0], got[1], RS.FLAGSETS['pol'])
            if s2 is not None and s2 < got[0]:
                got = (s2, X2)
        nq += 1
        sb = got[0] if got else float('nan')
        with open(res, 'a') as h:
            h.write('%d\t%s_e%g\t%.9f\t%.9f\t%.3e\t%s\n' % (n, tag, eps, held[n], sb, held[n] - sb, ' '.join(log)))
        if got is not None and (best is None or sb < best):
            best = sb
            print('BEST n=%d %s side %.9f held %.9f below %.3e' % (n, tag, sb, held[n], held[n] - sb), flush=True)
        if got is not None and sb < held[n] + float(os.environ.get('RIGIDSOFT_KEEP', '-1e-9')):
            tmpf = '%s/raw/.%d-%s.tmp' % (jd, n, tag)
            with open(tmpf, 'w', newline='') as h:
                wr = csv.writer(h); wr.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for qq, (xx, yy, d) in enumerate(got[1]):
                    wr.writerow([n, qq, repr(float(xx)), repr(float(yy)), repr(math.radians(float(d)))])
            os.rename(tmpf, '%s/raw/%d-%s_e%g.csv' % (jd, n, tag, eps))
    print('HOPEND n=%d quenches %d best %s held %.9f' % (n, nq, 'None' if best is None else '%.9f' % best, held[n]), flush=True)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] != 'run':
        sys.exit(__doc__)
    cmd_run(sys.argv[2:])
