#!/usr/bin/env python3
"""winlns (T5): window ruin-and-recreate at a fixed side. Fit one more square into a packing without growing the box.

Input: m squares feasible at side L. Goal: m + extra squares feasible at L (extra = 1 by default).
One attempt:
  1. pick a window centre (a tilted island square 80% of the time, else any square within 2 of the island) and a
     radius r in [2, 4]; the k squares whose centres lie within r are removed (8-40 at r 2-4), the rest is frozen
  2. sample an upright count u from k_up - 2 .. k_up + 1 (the staircase may lose or gain a step)
  3. keep up to k + extra - u of the removed tilted poses
  4. uprights: keep u of the window's own (random subset when u < k_up); when u > k_up the extra ones come from
     fillfast's exact fill around everything else, nearest the centre first
  5. any shortfall: fill_resolve.greedy_place (clean max-contact poses first, then least penetration) at the
     island's angles
  6. `packer relax` at side L with every square farther than r + 1.5 frozen; if it does not reach E <= 1e-20, a
     second relax with the ring widened to r + 3 (the one-ring release), then a kick (sigma 0.03, 0.6 deg) and relax
  7. a jammed fit is a single point, so a fixed-side relax converges slowly: when the best relax energy is below
     1e-4, fq polishes it (all free, side minimised) and the attempt succeeds when that side is <= L + 1e-9
A success is polished with fq (all free) and certified by floatsafe.work (official metric, as written and after a
pandas read, 2e-11 clearance). Nothing counts until T2 (gate.py) passes it.

  winlns.py prep --sub SUB.csv --n N --side L --out start.txt [--tries 20]   # drop one, fq-squeeze n-1 to <= L (class b)
  winlns.py run --in start.txt [--n N] --side L [--extra 1] [--restarts R] [--cpu-budget S] [--procs P]
                [--centre x,y] [--out cand/winlns/N/ | file.txt] [--seed s]
  winlns.py engine IN SIDE OUT N CPU                                         # T3 insbench template
  winlns.py selftest --sub SUB.csv                                           # red first

Evan's packer (MIT, https://github.com/evand/square-packing) is found at $EVAND_PACKER; we only import from a copy.
"""
from __future__ import annotations
import argparse, datetime as dt, json, math, os, random, socket, subprocess, sys, tempfile, time
from multiprocessing import Pool

for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_v, '1')
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
LANE = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import donorfeed as DF  # noqa: E402  (packings, fq polish, certify; also puts Evan's packer and the lane on sys.path)

PACKER_BIN = os.path.join(DF.PACKER, 'target', 'release', 'packer')
sys.path.insert(0, os.path.join(DF.PACKER, 'shove'))
E_OK = 1e-20
E_NEAR = 1e-4     # relax energy below which fq polish decides
SIDE_TOL = 1e-9   # success: fq side <= L + SIDE_TOL
RING = 1.5
RUNS_COLS = DF.RUNS_COLS


# ------------------------------------------------------------------ packer relax with frozen squares

def write_cfg(path, s, sq, frozen=None):
    with open(path, 'w') as f:
        f.write(f'{len(sq)} {float(s)!r}\n')
        for i, (x, y, a) in enumerate(sq):
            f.write(f'{float(x)!r} {float(y)!r} {float(a)!r}{" F" if frozen is not None and frozen[i] else ""}\n')


def relax(s, sq, tmp, frozen=None, maxit=5000):
    a, b = os.path.join(tmp, 'r_in.txt'), os.path.join(tmp, 'r_out.txt')
    write_cfg(a, s, sq, frozen)
    r = subprocess.run([PACKER_BIN, 'relax', '--in', a, '--s', repr(float(s)), '--out', b, '--maxit', str(maxit)],
                       capture_output=True, text=True)
    out = r.stdout
    E = float(out.split('E=')[1].split()[0]) if 'E=' in out else math.inf
    if not os.path.exists(b):
        return E, None
    _, X = DF.read_txt(b)
    return E, X


# ------------------------------------------------------------------ one attempt

def centres(X):
    """candidate window centres: tilted squares (80%) and squares within 2 of one (20%)"""
    t = DF.tilt(X[:, 2]) > DF.TILT_MIN
    T = X[t]
    if not len(T):
        return X[:, :2], X[:, :2]
    d = np.sqrt(((X[:, None, :2] - T[None, :, :2]) ** 2).sum(-1)).min(1)
    return T[:, :2], X[(d < 2.0) & ~t][:, :2] if ((d < 2.0) & ~t).any() else T[:, :2]


def attempt(X, L, extra, rng, centre=None, tmp=None, goal=None):
    """-> (ok, Y, info): Y has len(X) + extra squares. L is the work side (the input's box). goal (default L): with
    goal < L every near fit is fq-squeezed and ok means its side is <= goal + SIDE_TOL (insert, then squeeze)."""
    goal = L if goal is None else goal
    squeeze = goal < L - 1e-12
    import fillfast, fill_resolve as FR
    if centre is None:
        A, B = centres(X)
        P = A if rng.random() < 0.8 else B
        c = P[rng.randrange(len(P))]
    else:
        c = np.asarray(centre, float)
    r = rng.uniform(2.0, 4.0)
    dist = np.hypot(X[:, 0] - c[0], X[:, 1] - c[1])
    win = dist < r
    k = int(win.sum())
    W, F = X[win], X[~win]
    up = DF.tilt(W[:, 2]) <= DF.TILT_MIN
    k_up, k_t = int(up.sum()), int((~up).sum())
    need = k + extra
    u = max(0, rng.randint(k_up - 2, k_up + 1))
    t_need = max(0, need - u)
    Tw = [tuple(q) for q in W[~up]]
    rng.shuffle(Tw)
    Tw = Tw[:t_need]                                        # kept poses; the shortfall goes to greedy_place below
    # uprights, keep semantics: the window's own upright poses (a random u of them when u < k_up: the staircase loses
    # steps); when u > k_up the extra ones come from fillfast's exact fill around everything else, nearest first
    Uo = [tuple(q) for q in W[up]]
    rng.shuffle(Uo)
    Uo = Uo[:u]
    Z = np.zeros((0, 3))
    if u > len(Uo):
        obst = np.r_[F, np.array(Tw + Uo, float).reshape(-1, 3)]
        Z = fillfast.fill(L, obst, mode='exact')[len(obst):]
        if len(Z):
            dz = np.hypot(Z[:, 0] - c[0], Z[:, 1] - c[1])
            Z = Z[dz < r + 0.5][np.argsort(dz[dz < r + 0.5])][:u - len(Uo)]
    new = list(Tw) + Uo + [tuple(q) for q in Z]
    short = need - len(new)
    if short > 0:                                           # least-penetration poses at the island's angles
        angs = sorted({round(a % 90.0, 1) for a in W[~up][:, 2]} | {0.0}) if k_t else [0.0, 25.0, 45.0]
        Bd = FR.Board(L, np.r_[F, np.array(new, float).reshape(-1, 3)])
        g = np.linspace(-r, r, 41)
        pts = np.array([(c[0] + a, c[1] + b) for a in g for b in g if a * a + b * b < r * r
                        and 0.5 <= c[0] + a <= L - 0.5 and 0.5 <= c[1] + b <= L - 0.5])
        placed, _ = FR.greedy_place(Bd, short, pts, angs, rng, samples=800, local=False)
        new += placed
    if len(new) < need:
        return False, None, dict(k=k, r=r, u=u, stage='place')
    Y = np.r_[F, np.array(new[:need], float)]
    dY = np.hypot(Y[:, 0] - c[0], Y[:, 1] - c[1])
    info = dict(k=k, k_up=k_up, k_t=k_t, u=u, r=round(r, 3), c=[round(float(c[0]), 4), round(float(c[1]), 4)])
    best = (math.inf, None)
    for ring in (RING, 3.0):
        E, R = relax(L, Y, tmp, frozen=dY > r + ring)
        if R is not None and E <= E_OK and not squeeze:
            return True, R, dict(info, stage=f'relax ring {ring}', E=E)
        if R is not None and E < best[0]:
            best = (E, R)
    if R is not None:                                       # kick (fill_resolve kick: sigma 0.03, 0.6 deg), relax again
        free = dY <= r + 3.0
        K = R.copy()
        K[free, 0] += np.array([rng.gauss(0, 0.03) for _ in range(free.sum())])
        K[free, 1] += np.array([rng.gauss(0, 0.03) for _ in range(free.sum())])
        K[free, 2] += np.array([rng.gauss(0, 0.6) for _ in range(free.sum())])
        K[:, :2] = np.clip(K[:, :2], 0.5, L - 0.5)
        E, R = relax(L, K, tmp, frozen=~free)
        if R is not None and E <= E_OK and not squeeze:
            return True, R, dict(info, stage='kick', E=E)
        if R is not None and E < best[0]:
            best = (E, R)
    E, R = best
    if R is not None and E <= E_NEAR:                       # a jammed fit is one point: fixed-side relax converges
        s2, Q, _ = DF.fq_polish(len(R), L, R, tmp)          # slowly, so polish with fq (all free, side minimised)
        if Q is not None and s2 <= goal + SIDE_TOL:
            return True, Q, dict(info, stage='fq polish', E=E, s_fq=s2)
        return False, None, dict(info, stage='fq polish', E=E, s_fq=s2)
    return False, None, dict(info, stage='relax', E=E)


# ------------------------------------------------------------------ run

def _worker(job):
    X, L, extra, seed, budget, centre, max_restarts, goal = job
    rng = random.Random(seed)
    t0 = time.process_time(); w0 = time.time()
    tries = 0
    with tempfile.TemporaryDirectory(prefix='winlns-') as tmp:
        while (time.process_time() - t0 + _child_cpu() < budget and time.time() - w0 < 1.1 * budget
               and tries < max_restarts):
            tries += 1
            ok, Y, info = attempt(X, L, extra, rng, centre, tmp, goal)
            if ok:
                return dict(ok=True, Y=Y, info=info, tries=tries, seed=seed, cpu=time.process_time() - t0 + _child_cpu(),
                            wall=time.time() - w0)
    return dict(ok=False, tries=tries, seed=seed, cpu=time.process_time() - t0 + _child_cpu(), wall=time.time() - w0)


def _child_cpu():
    r = __import__('resource').getrusage(__import__('resource').RUSAGE_CHILDREN)
    return r.ru_utime + r.ru_stime


def run(X, L, n=None, extra=1, restarts=10 ** 9, cpu_budget=600.0, procs=4, centre=None, seed=1, out=None,
        certify_on=True, label='', runs_tsv=None, quiet=False, goal=None):
    """-> result dict (ok, side_out, reason, cpu_s, tries, path). cpu_budget is total CPU over all procs (python +
    packer children), also capped at 1.1x in wall time per proc. L = work side; goal = side to reach (default L)."""
    goal = L if goal is None else goal
    n = len(X) + extra if n is None else n
    extra = n - len(X)
    w0 = time.time()
    jobs = [(X, L, extra, seed * 1000 + i, cpu_budget / procs, centre, restarts, goal) for i in range(procs)]
    with Pool(procs) as pool:
        it = pool.imap_unordered(_worker, jobs)
        res = []
        for r in it:
            res.append(r)
            if r['ok']:
                pool.terminate()
                break
    cpu = sum(r['cpu'] for r in res)
    tries = sum(r['tries'] for r in res)
    win = next((r for r in res if r['ok']), None)
    outp = dict(ok=False, n=n, L=L, side_out=None, reason='no fit', cpu_s=cpu, tries=tries, wall_s=time.time() - w0,
                kaggle_safe=False, path=None)
    if win:
        outp.update(reason='relaxed, not certified', info=win['info'], seed=win['seed'])
        Y = win['Y']
        if certify_on:
            with tempfile.TemporaryDirectory() as tmp:
                s2, Yp, wfq = DF.fq_polish(n, goal, Y, tmp)
            if Yp is None:
                outp.update(reason='fq failed')
            else:
                ok, Lc, why, _ = DF.certify(n, Yp)
                outp.update(reason=why, side_out=Lc)
                if ok and Lc <= goal + 1e-9:
                    outp.update(ok=True, kaggle_safe=True)
                    Y = Yp
                elif ok:
                    outp.update(reason=f'{why} but side {Lc!r} > {goal!r}')
        else:
            outp.update(ok=True)
        outp['Y'] = Y
        if out and outp['ok']:
            utc = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            base = out[:-4] if out.endswith('.txt') else os.path.join(out, f'{utc}-{win["seed"]}')
            os.makedirs(os.path.dirname(base) or '.', exist_ok=True)
            s_w = outp['side_out'] or L
            DF.write_txt(base + '.txt', s_w, Y)
            json.dump(dict(n=n, side=float(s_w), side_dec=repr(float(s_w)), tool='winlns', method='window lns',
                           parent=label, source=label, licence='ours; parent licence per results/harvest-best tsv',
                           cpu_s=round(cpu, 2), box=socket.gethostname(), info=win['info'], reason=outp['reason']),
                      open(base + '.json', 'w'), indent=1)
            outp['path'] = base + '.txt'
    if runs_tsv:
        new = not os.path.exists(runs_tsv)
        with open(runs_tsv, 'a') as f:
            if new:
                f.write('\t'.join(RUNS_COLS) + '\n')
            f.write('\t'.join(map(str, ['winlns', n, repr(L), label, seed, round(outp['wall_s'], 1), round(cpu, 1),
                                        n if outp['ok'] else len(X), repr(outp['side_out']) if outp['side_out'] else '',
                                        outp['reason'], outp['kaggle_safe']])) + '\n')
    if not quiet:
        print(f'winlns n={n} L={L!r} ok={outp["ok"]} tries={tries} cpu={cpu:.0f}s -> {outp["reason"]}'
              f'{"" if not outp["side_out"] else f" side {outp["side_out"]!r}"} {outp["path"] or ""}', flush=True)
    return outp


# ------------------------------------------------------------------ engine (T3 insbench template)

def bench_write(path, n, Y, goal):
    """write Y (deg) so it passes the metric the way insbench reads it (repr floats, radians(deg)) with the gate's
    2e-11 clearance: dilate centres about their mean by floatsafe's steps until it does. -> (L, e) or (None, None)"""
    import floatsafe, kaggle_metric as km
    for e in floatsafe.EPS:
        Z = Y.copy(); m = Z[:, :2].mean(0); Z[:, :2] = m + (Z[:, :2] - m) * (1 + e)
        rows = [{'n': n, 'square_id': i, 'x': repr(float(x)), 'y': repr(float(y)), 'angle': repr(math.radians(float(d)))}
                for i, (x, y, d) in enumerate(Z)]
        _, _, Lt, why = km.evaluate_single_puzzle(n, rows)
        if why == 'ok' and floatsafe.clearance(rows) >= floatsafe.MIN_CLEARANCE:
            DF.write_txt(path, float(Lt), Z)
            return float(Lt), e
    return None, None


def engine(inp, side, out, n, cpu):
    """insbench engine: {in} holds n - 1 squares at their own side; insert at that side, fq-squeeze, and write n squares
    at <= side to {out}. Single process: the bench runs cases in parallel."""
    s_in, X = DF.read_txt(inp)
    o = run(X, s_in, n=n, cpu_budget=0.85 * cpu, procs=1, certify_on=False, quiet=True, goal=side, seed=n)
    if o['ok']:
        L, e = bench_write(out, n, o['Y'], side)
        print(f'engine n={n} fit, side {L!r} (dilated {e}) goal {side!r} tries {o["tries"]} cpu {o["cpu_s"]:.0f}s')
        return 0 if L is not None and L <= side + 1e-9 else 3
    print(f'engine n={n} no fit in {o["tries"]} tries, cpu {o["cpu_s"]:.0f}s')
    return 2


# ------------------------------------------------------------------ prep (class b start on a real target)

def prep(s, P, L, tries=20, seed=1, tmp=None):
    """class (b) start, as T3 builds it: drop one square (tilted first, random), squeeze the n - 1 with fq (side
    free: the polish, then the default ALM quench), keep it when the squeezed side is <= L (a packing at s' <= L sits
    in the L box as it is). -> (X, dropped index, s') or (None, None, None)"""
    import subprocess
    rng = random.Random(seed)
    n = len(P)
    tl = [i for i in range(n) if DF.tilt(P[i, 2]) > DF.TILT_MIN] or list(range(n))
    order = rng.sample(tl, min(tries, len(tl)))
    best = (math.inf, None, None)
    for i in order:
        X = np.delete(P, i, axis=0).copy()
        s2, Q, _ = DF.fq_polish(n - 1, s, X, tmp)
        if Q is not None and s2 > L:
            a, b = os.path.join(tmp, 'p_in.txt'), os.path.join(tmp, 'p_out.txt')
            DF.write_txt(a, s, X)
            r = subprocess.run([DF.FQ, 'quench', '--in', a, '--out', b], capture_output=True, text=True)
            if r.returncode == 0 and os.path.exists(b):
                s2, Q = DF.read_txt(b)
        if Q is not None and s2 <= L:
            return Q, i, s2
        if Q is not None and s2 < best[0]:
            best = (s2, Q, i)
    if L == math.inf or best[1] is None:
        return (best[1], best[2], best[0]) if best[1] is not None else (None, None, None)
    return None, None, best[0]


# ------------------------------------------------------------------ selftest

def selftest(sub, procs, budget):
    fails = []

    def expect(name, cond, detail):
        print(f'[{"PASS" if cond else "FAIL"}] {name}: {detail}', flush=True)
        if not cond:
            fails.append(name)

    s, P = DF.load_sub(sub, [498])[498]
    T = np.nonzero(DF.tilt(P[:, 2]) > DF.TILT_MIN)[0]
    rng = random.Random(7)
    hole = int(T[rng.randrange(len(T))])
    hx, hy = P[hole, :2]
    X = np.delete(P, hole, axis=0)                          # known-improvable: the hole is still there
    print(f'control: 498 minus square {hole} at ({hx:.3f}, {hy:.3f}), side {s!r}', flush=True)

    # R0: the success check can go red: the 498 control plus a square dropped on top of another, unrelaxed
    bad = np.r_[X, X[:1] + [0.3, 0.0, 0.0]]
    ok, _, why, _ = DF.certify(498, bad)
    expect('R0 certifier rejects an unrelaxed overlapping insert', not ok, why)

    # R1: known-improvable window, but the window is forced far from the hole (> 8 away): must fail
    d = np.hypot(X[:, 0] - hx, X[:, 1] - hy)
    far = X[np.argmax(d)][:2]
    # far window, on the jammed upright grid; radius <= 4 cannot reach the hole
    r1 = run(X, s, n=498, cpu_budget=budget / 2, procs=procs, centre=far, seed=11, quiet=True)
    expect('R1 window far from the hole does not fit 498', not r1['ok'],
           f'centre ({far[0]:.2f},{far[1]:.2f}) {d.max():.1f} from hole, tries {r1["tries"]}, {r1["reason"]}')

    # N1: k + 2 at side - 0.05 must fail (start: the 497 control relaxed at s - 0.05 if it fits; else from X)
    with tempfile.TemporaryDirectory() as tmp:
        X2 = X.copy(); X2[:, :2] = (X2[:, :2] - s / 2) * ((s - 0.05) / s) + (s - 0.05) / 2
        E, R = relax(s - 0.05, X2, tmp, maxit=20000)
    start = R if (R is not None and E <= E_OK) else X2
    n1 = run(start, s - 0.05, n=499, cpu_budget=budget / 2, procs=procs, seed=13, quiet=True)
    expect('N1 499 at side - 0.05 does not fit', not n1['ok'],
           f'497 start feasible at s-0.05: {E <= E_OK} (E {E:.1e}), tries {n1["tries"]}, {n1["reason"]}')

    # G1: windows auto on the same control must refit 498, 5 of 5 seeds
    wins = 0
    for sd in range(5):
        g = run(X, s, n=498, cpu_budget=budget, procs=procs, seed=100 + sd, quiet=True)
        wins += g['ok']
        print(f'   G1 seed {sd}: ok={g["ok"]} tries={g["tries"]} cpu={g["cpu_s"]:.0f}s {g["reason"]}'
              f'{"" if not g["side_out"] else f" side {g["side_out"]:.10f}"}', flush=True)
    expect('G1 auto windows refit the deleted island square, 5 of 5', wins == 5, f'{wins}/5')
    print('selftest', 'RED: ' + ', '.join(fails) if fails else 'GREEN', flush=True)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sp = ap.add_subparsers(dest='cmd', required=True)
    p = sp.add_parser('prep')
    p.add_argument('--sub', required=True); p.add_argument('--n', type=int, required=True)
    p.add_argument('--side', type=float, default=math.inf,
                   help='squeeze target; omit to keep the best squeeze over --tries drops')
    p.add_argument('--out', required=True)
    p.add_argument('--tries', type=int, default=20); p.add_argument('--seed', type=int, default=1)
    r = sp.add_parser('run')
    r.add_argument('--in', dest='inp', required=True); r.add_argument('--n', type=int)
    r.add_argument('--side', type=float, required=True); r.add_argument('--extra', type=int, default=1)
    r.add_argument('--restarts', type=int, default=10 ** 9); r.add_argument('--cpu-budget', type=float, default=600)
    r.add_argument('--procs', type=int, default=4); r.add_argument('--centre')
    r.add_argument('--windows', default='auto'); r.add_argument('--seed', type=int, default=1)
    r.add_argument('--out'); r.add_argument('--label', default='')
    r.add_argument('--runs', default=os.path.join(LANE, 'results', 'winlns-runs.tsv'))
    e = sp.add_parser('engine', help="insbench: winlns.py engine {in} {side} {out} {n} {cpu}")
    e.add_argument('inp'); e.add_argument('side', type=float); e.add_argument('out')
    e.add_argument('n', type=int); e.add_argument('cpu', type=float)
    t = sp.add_parser('selftest')
    t.add_argument('--sub', required=True); t.add_argument('--procs', type=int, default=4)
    t.add_argument('--budget', type=float, default=240)
    a = ap.parse_args()
    if a.cmd == 'prep':
        s, P = DF.load_sub(a.sub, [a.n])[a.n]
        with tempfile.TemporaryDirectory() as tmp:
            X, i, s2 = prep(s, P, a.side, a.tries, a.seed, tmp)
        if X is None:
            print(f'prep n={a.n}: no single drop squeezes to {a.side!r} (best {s2!r}, ours {s!r})'); sys.exit(1)
        DF.write_txt(a.out, min(a.side, s2), X)
        print(f'prep n={a.n}: dropped {i}, {len(X)} squares squeezed to {s2!r} <= {a.side!r} -> {a.out}')
    elif a.cmd == 'run':
        s, X = DF.read_txt(a.inp)
        c = [float(v) for v in a.centre.split(',')] if a.centre else None
        n = a.n if a.n else len(X) + a.extra
        o = run(X, a.side, n=n, restarts=a.restarts, cpu_budget=a.cpu_budget, procs=a.procs, centre=c, seed=a.seed,
                out=a.out, label=a.label or os.path.basename(a.inp), runs_tsv=a.runs)
        sys.exit(0 if o['ok'] else 2)
    elif a.cmd == 'engine':
        sys.exit(engine(a.inp, a.side, a.out, a.n, a.cpu))
    else:
        sys.exit(selftest(a.sub, a.procs, a.budget))


if __name__ == '__main__':
    main()
