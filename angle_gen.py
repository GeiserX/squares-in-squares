#!/usr/bin/env python3
"""angle: slot-patch generator. The tilt is not a free variable: a row of c tilted squares that spans a slot of
width c - 1 + f (f = fractional part of the side) has the flush tilt th(c, f), the root of
c cos(th) + sin(th) = c - 1 + f. A patch is a stack of such rows along a wall, with whole-column jogs. The search is
over the discrete shape only: c, the wall offset, the number of rows, where the stack starts and the jog pattern.
The uprights come from Evan Daniel's exact refill (fillfast, MIT, imported from his clone, never copied).

  angle_gen.py theta C F                      flush tilt of rows of C at fractional side F
  angle_gen.py count M F  SPEC [SPEC]         count of one layout (SPEC = c,x0,ytop,R,run,s0,taper[,dth])
  angle_gen.py opt   M F  OUT.tsv [--starts 12] [--evals 400] [--cs 4-10] [--jobs 1]   hill climbs at side M + F
  angle_gen.py prune M F  SPECV SPECH         drop single tilted squares while the refill count rises
  angle_gen.py build M F N SPECV SPECH [OUT.txt]   refill, keep N squares, fq quench, print the side
  angle_gen.py held  SUB.csv                  K(m, f): the squares over m*m that SUB holds at each fractional side

A layout is one vertical slot patch near the top-left corner and one horizontal slot patch near the bottom-right
corner (the mirror image of a vertical one), each with its own shape.
"""
import argparse, itertools, math, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine_lib import *          # BOX, BEST, load, normalize, np; puts Evan Daniel's packer on sys.path
import fillfast


def theta_flush(c, w):
    """larger-tilt root of c cos t + sin t = w (t > atan(1/c)); None when the row cannot span w"""
    lo = math.atan(1.0 / c); hi = math.pi / 4
    if c * math.cos(lo) + math.sin(lo) < w or c * math.cos(hi) + math.sin(hi) > w:
        return None
    for _ in range(80):
        mid = (lo + hi) / 2
        if c * math.cos(mid) + math.sin(mid) > w:
            lo = mid
        else:
            hi = mid
    return hi


def corners_of(x, y, th):
    co, si = math.cos(th), math.sin(th)
    return [(x + (a * co - b * si) / 2, y + (a * si + b * co) / 2) for a, b in ((1, 1), (-1, 1), (-1, -1), (1, -1))]


def vpatch(L, f, c, x0, ytop, R, run, s0, taper, dth=0.0):
    """vertical slot patch in the window x0 <= x <= x0 + c + f, one column wider than a flush row of c. Rows are
    1 apart across their own direction, so any slide along a row is free. Row j sits 1/cos(th) below row j - 1 (a
    vertical stack); a jog slides a row along itself by 1/cos(th), which moves it one whole column sideways and
    tan(th) up. The jog state is s0 for the first `run` rows, then flips every `run` rows (run 0: never). With s0 = 2
    the jog does not flip but adds up: the patch drifts one column away from the wall every `run` rows. The top
    `taper` rows lose squares at their high end and the bottom `taper` rows at their low end, one more per row.
    The tilt is the flush tilt of c squares in c - 1 + f, minus dth degrees. -> list (cx, cy, deg) or None"""
    th = theta_flush(c, c - 1 + f)
    if th is None:
        return None
    th -= math.radians(dth)
    co, si = math.cos(th), math.sin(th); pitch = 1.0 / co; h = (co + si) / 2
    ox = x0 + h; oy = L - ytop - h - (c - 1) * si
    out = []
    for j in range(R):
        step = j // run if run > 0 else 0
        jog = step if s0 == 2 else (s0 + step) % 2      # s0 = 2: the patch drifts one column every `run` rows
        hi = c - max(0, taper - j); lo = max(0, taper - (R - 1 - j))
        for i in range(lo, hi):
            cx = ox + i * co + jog; cy = oy + i * si - j * pitch + jog * si / co
            if cx - h < x0 - 1e-9 or (s0 != 2 and cx + h > x0 + c + f + 1e-9) or cy - h < -1e-9 or cy + h > L + 1e-9 or cx + h > L + 1e-9:
                continue
            out.append((cx, cy, math.degrees(th)))
    return out


def mirror(T):
    """reflection across the main diagonal: a vertical slot at the top-left becomes a horizontal one at the bottom-right"""
    return [(y, x, -a) for x, y, a in T]


def clash(A, B):
    if not A or not B:
        return False
    a = np.array(A)[:, :2]; b = np.array(B)[:, :2]
    return bool((((a[:, None, :] - b[None, :, :]) ** 2).sum(-1) < 2.0).any())   # centres under sqrt(2): may overlap


def layout(L, f, sv, sh=None):
    V = vpatch(L, f, *sv)
    H = vpatch(L, f, *(sh or sv))
    if V is None or H is None or len(V) < 4 or len(H) < 4:
        return None
    H = mirror(H)
    if clash(V, H):
        return None
    return np.array(V + H, float)


def count(L, T, mode='exact'):
    return len(fillfast.fill(L, T, mode, time_limit=5))


def prune(L, T, mode='greedy', log=None):
    """drop single tilted squares while the refill count rises: the held patches have rows one square short where
    the patch drifts a column, and the row model does not make those. -> (count, T)"""
    T = np.array(T, float); best = count(L, T, mode); go = True
    while go:
        go = False
        for i in range(len(T)):
            T2 = np.delete(T, i, axis=0); v = count(L, T2, mode)
            if v > best:
                T, best, go = T2, v, True
                if log:
                    log('  prune: %d tilted, count %d' % (len(T), best))
                break
    return best, T


def spec(s):
    p = s.split(',')
    return (int(p[0]), int(p[1]), float(p[2]), int(p[3]), int(p[4]), int(p[5]), int(p[6])) + ((float(p[7]),) if len(p) > 7 else ())


RANGES = dict(c=(4, 10), x0=(0, 3), ytop=(0.0, 9.0), R=(3, 18), run=(0, 9), s0=(0, 2), taper=(0, 3), dth=(0.0, 1.2))
KEYS = ('c', 'x0', 'ytop', 'R', 'run', 's0', 'taper', 'dth')
STEPS = dict(c=(1,), x0=(1,), ytop=(0.05, 0.25, 1.0), R=(1, 2), run=(1,), s0=(1,), taper=(1,), dth=(0.02, 0.1, 0.3))


def rand_spec(rng, cs):
    return (int(rng.integers(cs[0], cs[1] + 1)), int(rng.integers(0, 4)), float(round(rng.uniform(0, 6), 2)),
            int(rng.integers(6, 15)), int(rng.integers(0, 8)), int(rng.integers(0, 3)), int(rng.integers(0, 3)),
            float(round(rng.uniform(0, 0.5), 2)))


def move(rng, sp, cs):
    k = int(rng.integers(0, len(KEYS))); key = KEYS[k]; st = STEPS[key][int(rng.integers(0, len(STEPS[key])))]
    lo, hi = cs if key == 'c' else RANGES[key]
    v = sp[k] + (st if rng.random() < 0.5 else -st)
    if key == 's0':
        v = (sp[k] + 1) % 3
    v = min(hi, max(lo, v))
    return sp[:k] + ((round(v, 3) if isinstance(lo, float) else int(v)),) + sp[k + 1:]


def opt_job(a):
    """hill climb with plateau moves from one random start; the objective is the greedy refill count"""
    m, f, seed, evals, cs, start = a
    rng = np.random.default_rng(seed); L = m + f
    def val(sv, sh):
        T = layout(L, f, sv, sh)
        return 0 if T is None else count(L, T, 'greedy')
    cur = start or (rand_spec(rng, cs), rand_spec(rng, cs)); cv = val(*cur); best = (cv, cur)
    for _ in range(evals):
        w = int(rng.integers(0, 2)); new = list(cur); new[w] = move(rng, cur[w], cs); new = tuple(new)
        if new == cur:
            continue
        v = val(*new)
        if v >= cv:
            cur, cv = new, v
            if v > best[0]:
                best = (v, new)
    T = layout(L, f, *best[1])
    return (count(L, T, 'exact') if T is not None else 0), best[1], seed


def sstr(sp):
    return ','.join(str(x) for x in sp)


def held_table(sub):
    P = load(sub); K = {}
    for n in sorted(P):
        s, _ = normalize(P[n]); m = int(s + 1e-9)
        if n > m * m:
            K.setdefault(m, []).append((s - m, n - m * m, n))
    return K


def k_held(K, m, f):
    """largest k = n - m*m that the file holds at a side <= m + f"""
    return max([k for ff, k, n in K.get(m, []) if ff <= f + 1e-12], default=0)


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'theta':
        print(math.degrees(theta_flush(int(sys.argv[2]), int(sys.argv[2]) - 1 + float(sys.argv[3]))))
    elif cmd == 'count':
        m = int(sys.argv[2]); f = float(sys.argv[3]); L = m + f
        sv = spec(sys.argv[4]); sh = spec(sys.argv[5]) if len(sys.argv) > 5 else None
        T = layout(L, f, sv, sh)
        print('tilted', None if T is None else len(T), 'count', None if T is None else count(L, T) , 'grid', m * m)
    elif cmd == 'prune':
        m = int(sys.argv[2]); f = float(sys.argv[3]); L = m + f
        T = layout(L, f, spec(sys.argv[4]), spec(sys.argv[5]))
        print('start: tilted', len(T), 'count', count(L, T))
        v, T = prune(L, T, 'greedy', print)
        print('end: tilted', len(T), 'greedy count', v, 'exact count', count(L, T), 'grid', m * m)
    elif cmd == 'held':
        K = held_table(sys.argv[2])
        for m in sorted(K):
            print(m, ' '.join('%d@%.4f' % (k, ff) for ff, k, n in sorted(K[m])))
    elif cmd == 'build':
        # angle_gen.py build M F N SPECV SPECH: refill, keep N squares, quench with fq, print the side reached
        from engine_fq import quench, POLISH
        m = int(sys.argv[2]); f = float(sys.argv[3]); n = int(sys.argv[4]); L = m + f
        T = layout(L, f, spec(sys.argv[5]), spec(sys.argv[6])); F = fillfast.fill(L, T, 'exact')
        if len(F) < n:
            print('count %d < %d' % (len(F), n)); sys.exit(1)
        up = np.nonzero(np.abs(F[:, 2]) <= 0.5)[0]; F = np.delete(F, up[:len(F) - n], axis=0); cur = L; X = F
        for fl in ((), POLISH):
            s2, X2, dt = quench(cur, X, fl)
            if s2 is not None and s2 < cur:
                cur, X = s2, X2
        print('n=%d start %.6f quenched %.9f' % (n, L, cur))
        if len(sys.argv) > 7:
            from engine_fq import write_txt
            write_txt(sys.argv[7], cur, X)
    elif cmd == 'opt':
        ap = argparse.ArgumentParser(); ap.add_argument('cmd'); ap.add_argument('m', type=int); ap.add_argument('f', type=float)
        ap.add_argument('out'); ap.add_argument('--starts', type=int, default=12); ap.add_argument('--evals', type=int, default=400)
        ap.add_argument('--cs', default='4-10'); ap.add_argument('--jobs', type=int, default=1); ap.add_argument('--seed', type=int, default=0)
        a = ap.parse_args(); cs = tuple(int(x) for x in a.cs.split('-')); t0 = time.time()
        from multiprocessing import Pool
        with Pool(a.jobs) as pool:
            res = pool.map(opt_job, [(a.m, a.f, a.seed + i, a.evals, cs, None) for i in range(a.starts)], chunksize=1)
        res.sort(key=lambda r: -r[0])
        with open(a.out, 'a') as h:
            for k, (sv, sh), seed in res:
                h.write('%d\t%.6f\t%d\t%d\t%s\t%s\n' % (a.m, a.f, k, k - a.m * a.m, sstr(sv), sstr(sh)))
        print('m=%d f=%.6f starts=%d best k=%d  %s  %s  %.0fs' % (a.m, a.f, a.starts, res[0][0] - a.m * a.m,
              sstr(res[0][1][0]), sstr(res[0][1][1]), time.time() - t0), flush=True)
