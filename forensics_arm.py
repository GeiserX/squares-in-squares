#!/usr/bin/env python3
"""A closed arm beside the 0.6841 block: flush rows with two end zones in a slot C + F wide, counted with the exact fill.

The board's layouts at f = 0.6841 are two parts that share no row and no column. Each part is a block in a
slot (c + f) wide and c + 7 long, and it holds c // 2 squares more than the grid. The held 685 is the block
of c = 10 (the pod of forensics_pod.py) and the block of c = 9 (an arm of rows of 8). A part alone in a square
of side c + 7 + f gives (c + 7)^2 + c // 2, so every builder here is tested alone: the arm at the right wall
of a square of side MP + F, the rest upright, the uprights from the exact fill (Evan Daniel's fillfast, MIT,
imported from his clone through EVAND_PACKER).

  ctl      HELD.csv            the readings the builders are measured against: the pod of the held 685 alone
                               at m = 17 must give 294 and its arm alone at m = 16 must give 260. It also
                               prints the count of the pod's lattice squares alone, without its loose squares.
  table    CS LEN [LEN ...]    the best arm of flush stacks of CS squares with a lattice taper at both ends
                               (zone_search.taper_best), by the count of the strip alone
  ends     CS MP OUT_PREFIX    every pair of taper end zones with as many flush stacks as fit, exact fill
  jog      CS C MP OUT_PREFIX [--joint] [--ph 0.05]
                               flush rows that move one column to the right once or twice (a jog saves tan t of
                               length), end rows on the lattice cut at the slot. --joint puts a row of CS + 1
                               squares, flush in the wider strip, at each jog
  endsjog  CS C MP OUT_PREFIX [--within 3]
                               taper end zones, jogs and joint rows together

FADD in the environment adds to F: the same designs at a larger side.

Control of the builders (2026-11-12, round 19): the arm of the held 685 alone holds 260 at m = 16. `ends` gives
259, `jog` 257, `jog --joint` 257 and `endsjog` 257. So the control is red and nothing built here counts.
"""
import sys, os, math, time, pickle, itertools
import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
sys.path.insert(0, os.environ.get('EVAND_PACKER', '$SCRATCH/bounties-squares/ext/evand/search/packer'))
import fillfast

FADD = float(os.environ.get('FADD', '0'))
F = 0.6841436063588683 + 2e-9 + FADD


def fill(side, T, tl=5):
    return fillfast.fill(side, T, mode='exact', time_limit=tl)


# ------------------------------------------------------------------------------------------- geometry

def tilt(cs, f=F):
    """Flush rows of cs squares in a strip cs - 1 + f wide: cs cos t + sin t = cs - 1 + f. -> (t, strip width)"""
    W = cs - 1 + f
    return math.atan2(1, cs) + math.acos(W / math.hypot(cs, 1)), W


def corners(Q):
    th = np.radians(Q[:, 2]); c, s = np.cos(th), np.sin(th)
    off = np.array([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]])
    return Q[:, None, :2] + np.stack([off[:, 0] * c[:, None] - off[:, 1] * s[:, None], off[:, 0] * s[:, None] + off[:, 1] * c[:, None]], -1)


def overlaps(A, B, tol=1e-10):
    """True when some square of A overlaps some square of B by more than tol (separating axes)."""
    PA, PB = corners(A), corners(B)
    for i in range(len(A)):
        for j in range(len(B)):
            if math.hypot(A[i, 0] - B[j, 0], A[i, 1] - B[j, 1]) > 1.4143: continue
            sep = False
            for ang in (A[i, 2], A[i, 2] + 90, B[j, 2], B[j, 2] + 90):
                u = np.array([math.cos(math.radians(ang)), math.sin(math.radians(ang))])
                a = PA[i] @ u; b = PB[j] @ u
                if a.max() <= b.min() + tol or b.max() <= a.min() + tol: sep = True; break
            if not sep: return True
    return False


def valid(T, side, tol=1e-9):
    """No two tilted squares overlap and none leaves the square. The exact fill does not test this."""
    P = corners(T)
    if P.min() < -tol or P.max() > side + tol: return False
    for i in range(len(T)):
        if overlaps(T[i:i + 1], T[i + 1:], tol): return False
    return True


def row(n, t, e, yL):
    """n squares face to face at tilt -t (the row falls to the right), left end at x = e, first centre at height yL."""
    ct, st = math.cos(t), math.sin(t); h = 0.5 * (ct + st); i = np.arange(n)
    return np.c_[e + h + i * ct, yL - i * st, np.full(n, -math.degrees(t))]


def rest(lower, n, t, e, y_lo, y_hi):
    """The lowest yL at which the row (n, t, e) clears the squares of lower, between y_lo (overlaps) and y_hi (clear)."""
    for _ in range(46):
        mid = 0.5 * (y_lo + y_hi)
        if overlaps(row(n, t, e, mid), lower): y_lo = mid
        else: y_hi = mid
    return y_hi


_JOINT = {}
def joint_steps(cs, f=F):
    """A joint row of cs + 1 squares (flush in the strip one column wider) on a main row, and the next main row,
    one column on, on the joint. -> (tilt of the joint row, its step up, the step of the next row)"""
    if cs not in _JOINT:
        t, W = tilt(cs, f); t2, W2 = tilt(cs + 1, f)
        A = row(cs, t, 0.0, 10.0)
        y1 = rest(A, cs + 1, t2, 0.0, 10.0, 12.5)
        y2 = rest(row(cs + 1, t2, 0.0, y1), cs, t, 1.0, y1, y1 + 2.5)
        _JOINT[cs] = (t2, y1 - 10.0, y2 - y1)
    return _JOINT[cs]


# ------------------------------------------------------------------------------------------- ctl

def cmd_ctl(held):
    import forensics_turn as ft
    s, A = ft.normalize(ft.load(held, 685))
    T = A[np.abs(A[:, 2]) > 0.5]
    inpod = (T[:, 1] > 16.5) & (T[:, 0] < 18)
    pod, arm = T[inpod].copy(), T[~inpod].copy()
    P = pod.copy(); P[:, 1] -= 9.0
    k1 = len(fill(s - 9.0, P)); print('the pod of the held 685 alone at m = 17 (%d tilted squares): %d (want 294)' % (len(pod), k1))
    Q = arm.copy(); Q[:, 0] -= 10.0
    k2 = len(fill(s - 10.0, Q)); print('the arm of the held 685 alone at m = 16 (%d tilted squares): %d (want 260)' % (len(arm), k2))
    main = pod[np.abs(pod[:, 2] + 23.9886) < 0.01]
    P = main.copy(); P[:, 1] -= 9.0
    k3 = len(fill(s - 9.0, P)); print('the %d pod squares at 23.9886 degrees alone at m = 17: %d (the loose squares at other angles are left out)' % (len(main), k3))
    ok = k1 == 294 and k2 == 260 and k3 < 294
    print('CONTROL GREEN' if ok else 'CONTROL RED'); return 0 if ok else 1


# ------------------------------------------------------------------------------------------- taper end zones

def taper_table(c, f=F, step=0.004, span=1.6):
    """The largest lattice taper count at every position of the flush stack, from the lowest legal one up."""
    import zone_search as Z
    t, p, W = Z.geom(c, f)
    lmin = (c * math.sin(t) + math.cos(t) - p) / 2           # below this the flush stack itself leaves through the end wall
    cache = 'armtable-c%d%s.pkl' % (c, ('-f%g' % FADD) if FADD else '')
    if os.path.exists(cache): return pickle.load(open(cache, 'rb'))
    lams = np.arange(lmin + 1e-6, lmin + span * p, step); N = np.zeros(len(lams), int)
    for i, lam in enumerate(lams): N[i] = Z.taper_best(c, f, float(lam))[0]
    N = np.maximum.accumulate(N)
    pickle.dump((lams, N), open(cache, 'wb'))
    return lams, N


def firsts(lams, N):
    out = {}
    for i in range(len(lams)):
        if int(N[i]) not in out: out[int(N[i])] = float(lams[i])
    return out


def cmd_table(c, lens):
    import zone_search as Z
    t, p, W = Z.geom(c, F); lams, N = taper_table(c); step = lams[1] - lams[0]
    print('stacks of %d: tilt %.4f pitch %.5f strip %.5f, %.4f squares per unit; %d positions, taper counts %d to %d' % (c, math.degrees(t), p, W, c * math.cos(t), len(lams), N.min(), N.max()))
    for LR in lens:
        best = None
        for s in range(0, int(LR / p) + 1):
            restl = LR - s * p
            for i, l1 in enumerate(lams):
                l2 = restl - l1
                if l2 < lams[0] or l2 < l1 - 1e-9: break
                j = int((l2 - lams[0]) / step + 1e-9)
                if j >= len(lams): continue
                tot = int(N[i] + N[j] + s * c)
                if best is None or tot > best[0]: best = (tot, s, float(l1), float(lams[j]), int(N[i]), int(N[j]))
        grid = (c - 1) * math.floor(LR + 1e-9)
        print('  length %.4f: %s' % (LR, 'no arm' if best is None else 'best %d = grid %d %+d (%d stacks, zones %.3f + %.3f holding %d + %d)' % (best[0], grid, best[0] - grid, best[1], best[2], best[3], best[4], best[5])))


def cmd_ends(c, mp, pre):
    import zone_search as Z
    side = mp + F; t, p, W = Z.geom(c, F); ct, st = math.cos(t), math.sin(t); ii = np.arange(c) - (c - 1) / 2
    lams, N = taper_table(c); fz = firsts(lams, N); cache = {}
    def zone(l):
        if l not in cache:
            r = Z.taper_best(c, F, l); cache[l] = np.array([(x, y, d) for x, y, d in r[2] if abs(d) > 1e-9]).reshape(-1, 3)
        return cache[l]
    best = 0; nf = 0; t0 = time.time()
    for n1, l1 in sorted(fz.items()):
        for n2, l2 in sorted(fz.items()):
            if n2 < n1: continue
            s = int(math.floor((side - l1 - l2) / p + 1e-9))
            if s < 0: continue
            spare = side - l1 - l2 - s * p
            for at_bottom in (True, False):                      # the spare length goes to the bottom zone or to the top zone
                la = l1 + (spare if at_bottom else 0.0); lb = l2 + (0.0 if at_bottom else spare)
                T = [zone(l1) + np.array([0, la - l1, 0])]
                for k in range(s):
                    T.append(np.c_[W / 2 + ii * ct, la + p / 2 + k * p - ii * st, np.full(c, -math.degrees(t))])
                q = zone(l2).copy(); q[:, 0] = W - q[:, 0]; q[:, 1] = side - (q[:, 1] + (lb - l2)); T.append(q)
                T = np.vstack(T); T[:, 0] += side - W
                R = fill(side, T); nf += 1
                if len(R) > best and valid(T, side):
                    best = len(R)
                    print('zones %d + %d (%.3f, %.3f), %d stacks, spare %.3f at the %s: %d tilted, fill %d = %d^2 %+d' % (n1, n2, l1, l2, s, spare, 'bottom' if at_bottom else 'top', len(T), best, mp, best - mp * mp), flush=True)
                    np.save('%s-n%d.npy' % (pre, best), np.array(R, float))
    print('done: %d fills in %.0f s, best %d = %d^2 %+d at side %d + %.6f' % (nf, time.time() - t0, best, mp, best - mp * mp, mp, F), flush=True)


# ------------------------------------------------------------------------------------------- jogs

def design(cs, c, mp, ph, o, jogs, down, up, f=F, joint=False):
    """Tilted squares of one jogged arm. ph: height of the lowest main row above its lowest legal place. o: spare
    columns left of the lowest run. jogs: main rows after which the run moves one column to the right. down, up:
    (kF, kL) rows beyond the main run at each end, kF flush steps and then kL lattice steps, cut at the slot."""
    t, W = tilt(cs, f); ct, st = math.cos(t), math.sin(t); h = 0.5 * (ct + st); p = 1 / ct
    side = mp + f; X0 = side - (c + f); X1 = side
    e = X0 + o; yL = (cs - 1) * st + h + ph
    main = []; extra = []; k = 0
    if joint: t2, dj1, dj2 = joint_steps(cs, f)
    while True:
        main.append((e, yL))
        if k in jogs and joint:
            yj = yL + dj1; h2 = 0.5 * (math.cos(t2) + math.sin(t2)); ej = e
            e += 1.0; yL = yj + dj2; k += 1
            # a joint row stays only when the main row above it is whole too: the end rows start from the last whole main row
            if yL + h <= side + 1e-9 and e + W <= X1 + 1e-9 and yj + h2 <= side + 1e-9: extra.append(row(cs + 1, t2, ej, yj))
        else:
            d = 1.0 if k in jogs else 0.0
            e += d; yL += (1 - d * st) / ct; k += 1
        if yL - (cs - 1) * st - h > side - 1e-9: break
    whole = [(e, y) for e, y in main if y + h <= side + 1e-9 and e + W <= X1 + 1e-9]
    if not whole: return None
    rows = list(whole)
    e, y = whole[0]
    for _ in range(down[0]): y -= p; rows.append((e, y))
    for _ in range(down[1]): e -= st; y -= ct; rows.append((e, y))
    e, y = whole[-1]
    for _ in range(up[0]): y += p; rows.append((e, y))
    for _ in range(up[1]): e += st; y += ct; rows.append((e, y))
    sq = []
    for e, y in rows:
        i = np.arange(cs); cx = e + h + i * ct; cy = y - i * st
        ok = (cx - h >= X0 - 1e-9) & (cx + h <= X1 + 1e-9) & (cy - h >= -1e-9) & (cy + h <= side + 1e-9)
        sq += [(cx[j], cy[j], -math.degrees(t)) for j in range(cs) if ok[j]]
    for q in extra: sq += [tuple(v) for v in q]
    return np.array(sq)


ENDS = [(a, b) for a in range(0, 3) for b in range(0, 4)]


def prune(side, T, k, rounds=8, band=4.5):
    """Leave out one tilted square of the end rows at a time while the exact fill gains by it."""
    T = T.copy()
    for _ in range(rounds):
        lo, hi = T[:, 1].min() + band, T[:, 1].max() - band
        bi, bk = None, k
        for i in [i for i in range(len(T)) if T[i, 1] < lo or T[i, 1] > hi]:
            k2 = len(fill(side, np.delete(T, i, 0)))
            if k2 > bk: bi, bk = i, k2
        if bi is None: break
        T = np.delete(T, bi, 0); k = bk
    return T, k


def cmd_jog(cs, c, mp, pre, phs, joint):
    side = mp + F; t, W = tilt(cs); p = 1 / math.cos(t)
    spare = c - (cs - 1); want = mp * mp + c // 2; nmain = int(side / p) + 2
    cfgs = []
    for o in range(0, spare + 1):
        nj = spare - o
        cfgs += [(o, jj) for jj in itertools.combinations(range(nmain), nj)]
        if nj >= 1: cfgs += [(o, jj) for jj in itertools.combinations(range(nmain), nj - 1)]
    print('rows of %d in a slot of %d columns, m = %d: tilt %.4f pitch %.5f, %d spare columns, %d jog schedules, want %d = %d^2 + %d%s' % (cs, c, mp, math.degrees(t), p, spare, len(cfgs), want, mp, c // 2, ('; joint row of %d at %.4f degrees, steps %.5f + %.5f (plain jog %.5f)' % ((cs + 1, math.degrees(joint_steps(cs)[0])) + joint_steps(cs)[1:] + ((1 - math.sin(t)) / math.cos(t),))) if joint else ''), flush=True)
    best = 0; t0 = time.time(); nf = 0; top = []
    for o, jj in cfgs:
        for ph in np.arange(0, p, phs):
            T = design(cs, c, mp, float(ph), o, set(jj), (1, 2), (1, 2), joint=joint)
            if T is None: continue
            k = len(fill(side, T)); nf += 1
            if k > best and not valid(T, side): continue
            top.append((k, float(ph), o, jj))
            if k > best: best = k; print('  pass 1: %d spare columns left, jogs %s, phase %.2f: %d tilted, fill %d (%+d)' % (o, jj, ph, len(T), k, k - mp * mp), flush=True)
    top.sort(key=lambda r: -r[0]); top = top[:40]
    print('pass 1: %d fills in %.0f s, best %d; pass 2 on the best %d' % (nf, time.time() - t0, best, len(top)), flush=True)
    for k0, ph, o, jj in top:
        bd = bu = (1, 2); bk = k0
        for which in (0, 1, 0):
            for en in ENDS:
                d2, u2 = (en, bu) if which == 0 else (bd, en)
                T = design(cs, c, mp, ph, o, set(jj), d2, u2, joint=joint); k = len(fill(side, T)); nf += 1
                if k > bk and valid(T, side): bk = k; bd, bu = d2, u2
        T = design(cs, c, mp, ph, o, set(jj), bd, bu, joint=joint)
        if not valid(T, side): continue
        k1 = len(fill(side, T)); T2, k2 = prune(side, T, k1)
        if k2 > best or (k2 == best and k2 >= want):
            best = k2
            print('  pass 2: %d spare columns left, jogs %s, phase %.2f, ends %s %s: %d tilted, fill %d, with %d left out %d (%+d)%s' % (o, jj, ph, bd, bu, len(T), k1, len(T) - len(T2), k2, k2 - mp * mp, '  REACHED' if k2 >= want else ''), flush=True)
            np.save('%s-n%d.npy' % (pre, k2), np.array(fill(side, T2), float))
    print('done: %d fills in %.0f s, best %d = %d^2 %+d, want %+d' % (nf, time.time() - t0, best, mp, best - mp * mp, c // 2), flush=True)


def cmd_endsjog(cs, c, mp, pre, within):
    import zone_search as Z
    t, p, W = Z.geom(cs, F); ct, st = math.cos(t), math.sin(t); side = mp + F; X0 = side - (c + F)
    spare_cols = c - (cs - 1); t2, dj1, dj2 = joint_steps(cs, F)
    lams, N = taper_table(cs); fz = firsts(lams, N); cache = {}
    def zone(l):
        if l not in cache:
            r = Z.taper_best(cs, F, l); cache[l] = np.array([(x, y, d) for x, y, d in r[2] if abs(d) > 1e-9]).reshape(-1, 3)
        return cache[l]
    want = mp * mp + c // 2
    cand = []
    for n1, l1 in fz.items():
        for n2, l2 in fz.items():
            for nj in range(0, spare_cols + 1):
                s = int(math.floor((side - l1 - l2 - nj * (dj1 + dj2)) / p + 1e-9)) + nj
                if s >= nj + 1: cand.append((n1 + n2 + cs * s + (cs + 1) * nj, n1, l1, n2, l2, nj, s))
    top = max(q[0] for q in cand)
    cand = sorted([q for q in cand if q[0] >= top - within], key=lambda q: -q[0])
    print('rows of %d in a slot of %d columns, m = %d: %d choices of zones and jogs within %d of the largest arm count %d, want %d = %d^2 %+d' % (cs, c, mp, len(cand), within, top, want, mp, c // 2), flush=True)
    best = 0; nf = 0; bad = 0; t0 = time.time()
    for tot, n1, l1, n2, l2, nj, s in cand:
        Lt = l1 + l2 + (s - nj) * p + nj * (dj1 + dj2)
        for o in range(0, spare_cols - nj + 1):
            for jogs in itertools.combinations(range(s - 1), nj):
                for at_top in (True, False):                     # the spare length sits above the arm or below it
                    base = 0.0 if at_top else side - Lt
                    z1 = zone(l1).copy(); z1[:, 0] += X0 + o; z1[:, 1] += base; T = [z1]
                    e = X0 + o; yL = base + l1 + p / 2 + (cs - 1) / 2 * st
                    for k in range(s):
                        T.append(row(cs, t, e, yL))
                        if k == s - 1: break
                        if k in jogs: T.append(row(cs + 1, t2, e, yL + dj1)); e += 1.0; yL += dj1 + dj2
                        else: yL += p
                    Ltop = yL + l2 + p / 2 - (cs - 1) / 2 * st
                    z2 = zone(l2).copy(); z2[:, 0] = e + W - z2[:, 0]; z2[:, 1] = Ltop - z2[:, 1]; T.append(z2)
                    T = np.vstack(T); k = len(fill(side, T)); nf += 1
                    if k > best or (k == best and k >= want):
                        if not valid(T, side): bad += 1; continue
                        best = k
                        print('zones %d + %d, %d rows, %d spare columns left, jogs %s, spare length %s: %d tilted, fill %d = %d^2 %+d%s' % (n1, n2, s, o, jogs, 'above' if at_top else 'below', len(T), k, mp, k - mp * mp, '  REACHED' if k >= want else ''), flush=True)
                        np.save('%s-n%d.npy' % (pre, k), np.array(fill(side, T), float))
    print('done: %d fills in %.0f s, %d designs dropped for overlapping tilted squares, best %d = %d^2 %+d, want %+d' % (nf, time.time() - t0, bad, best, mp, best - mp * mp, c // 2), flush=True)


if __name__ == '__main__':
    a = sys.argv
    if len(a) < 3: print(__doc__); sys.exit(2)
    if a[1] == 'ctl': sys.exit(cmd_ctl(a[2]))
    if a[1] == 'table': cmd_table(int(a[2]), [float(v) for v in a[3:]])
    elif a[1] == 'ends': cmd_ends(int(a[2]), int(a[3]), a[4])
    elif a[1] == 'jog': cmd_jog(int(a[2]), int(a[3]), int(a[4]), a[5], float(a[a.index('--ph') + 1]) if '--ph' in a else 0.05, '--joint' in a)
    elif a[1] == 'endsjog': cmd_endsjog(int(a[2]), int(a[3]), int(a[4]), a[5], int(a[a.index('--within') + 1]) if '--within' in a else 3)
    else: print(__doc__); sys.exit(2)
