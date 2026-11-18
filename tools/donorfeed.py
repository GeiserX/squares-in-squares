#!/usr/bin/env python3
"""donorfeed (T6): put the tilted island of a held packing into another n's box, refill the uprights exactly, and
write the result as an init file for Evan's ftmc.py / gen.seed. Also holds the win-propagation rule.

Donors for target n: our packings at n-3..n+3 and every exact family member (fractional part of the side within
--fam-tol, 1e-9 by default), smallest member first. The island T is the donor's squares tilted more than 0.5 degrees.
Each T goes through
  - the 8 symmetries of the square (in the donor's own box),
  - integer shifts (i, j), and near-integer ones (i + f, j + f) where f = D - round(D) when |f| <= 0.05
    (D = target side - donor side),
  - two diagonal placements (island centroid put on the target box's main or anti diagonal),
keeping the transforms that sit inside the target box. A greedy upright fill (Evan's fillfast) screens them; the best
--exact go through fillfast's exact fill. Every attempt goes to attempts.jsonl.

Output, in the lane's common format: cand/donorfeed/<n>/<utc>-<tag>.txt (Evan's `n s / x y deg`) and a .json beside
it. When the fill reaches n, the file holds n squares at the target side (a gen.seed / fq start). When it does not,
it holds the island plus every upright it got, with the count in the header: ftmc.py only reads the tilted squares
and the side, and rescans the side upwards itself, so a short start is still an ftmc start.

--certify polishes every layout that reached n with fq (all squares free) and certifies it with the lane's
floatsafe.work (official metric as written and after a pandas read, 2e-11 clearance). Rows go to
results/donorfeed-runs.tsv. Nothing counts until T2 (gate.py) passes it.

  donorfeed.py feed --sub SUB.csv --n N [--side S] [--donors auto|m1,m2] [--top 8] [--certify] [--out cand]
  donorfeed.py propagate --win N --sub SUB.csv [--queue results/donorfeed-queue.tsv]
  donorfeed.py selftest --sub SUB.csv          # red controls first, then the 908 reconstruction, then propagate

Evan's packer (MIT, https://github.com/evand/square-packing) is found at $EVAND_PACKER; we only import from a copy.
"""
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, math, os, socket, subprocess, sys, tempfile, time
from multiprocessing import Pool

for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ.setdefault(_v, '1')
import numpy as np

TOOLS = os.path.dirname(os.path.abspath(__file__))
LANE = os.path.dirname(TOOLS)
PACKER = os.environ.get('EVAND_PACKER', '$SCRATCH/sq-winlns/evand/packer')
FQ = os.path.join(PACKER, 'target', 'release', 'fq')
sys.path.insert(0, PACKER)
sys.path.insert(0, LANE)

TILT_MIN = 0.5
NEAR_INT = 0.05
# fq flags of Evan's POLISH_DEEP (pk/engine.py: no ALM, loosen 1.0, flip_top 64, pit 600): a seam polish, all free
FQ_POLISH = ['--no-alm', '--loosen', '1.0', '--flip-top', '64', '--pit', '600']
RUNS_COLS = ['tool', 'n', 'target_side', 'start', 'seed', 'wall_s', 'cpu_s', 'count_reached', 'side_out',
             'metric_reason', 'kaggle_safe']


# ------------------------------------------------------------------ packings

def half(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def load_sub(path, ns=None):
    """Kaggle CSV -> {n: (s, array (n, 3) of x, y, deg in [0, s]^2)}, the way evconv.to_txt normalises."""
    import pandas as pd
    d = pd.read_csv(path)
    if ns is not None:
        d = d[d.n.isin(list(ns))]
    out = {}
    for n, r in d.groupby('n'):
        r = r.sort_values('square_id')
        t = r.angle.to_numpy(float); x = r.x.to_numpy(float); y = r.y.to_numpy(float)
        h = (np.abs(np.cos(t)) + np.abs(np.sin(t))) / 2
        x0, y0 = (x - h).min(), (y - h).min()
        s = max((x + h).max() - x0, (y + h).max() - y0)
        out[int(n)] = (float(s), np.c_[x - x0, y - y0, np.degrees(t)])
    return out


def sides(path):
    """{n: side} for every n of the file (one pass)."""
    return {n: s for n, (s, _) in load_sub(path).items()}


def tilt(a):
    a = np.abs(np.asarray(a, float)) % 90.0
    return np.minimum(a, 90.0 - a)


def island(P):
    return P[tilt(P[:, 2]) > TILT_MIN]


def write_txt(path, s, sq):
    with open(path, 'w') as f:
        f.write(f'{len(sq)} {float(s)!r}\n' + ''.join(f'{float(x)!r} {float(y)!r} {float(a)!r}\n' for x, y, a in sq))


def read_txt(path):
    L = [l.split() for l in open(path) if l.strip() and not l.startswith('#')]
    n, s = int(L[0][0]), float(L[0][1])
    return s, np.array([[float(q[0]), float(q[1]), float(q[2])] for q in L[1:n + 1]])


# ------------------------------------------------------------------ donors and transforms

def frac_dist(a, b):
    d = abs((a % 1.0) - (b % 1.0))
    return min(d, 1.0 - d)


def family(n, S_of, tol):
    """exact family of n: every m != n whose side's fractional part is within tol of n's, smallest first"""
    f = S_of[n]
    return sorted(m for m, s in S_of.items() if m != n and m >= 100 and frac_dist(s, f) <= tol)


def donors_auto(n, S_of, tol):
    near = [m for m in range(n - 3, n + 4) if m != n and m in S_of]
    fam = family(n, S_of, tol)
    return sorted(set(near) | set(fam))


def symmetry(T, s, k):
    """k in 0..7: bit 0 transpose, bit 1 mirror x, bit 2 mirror y, applied inside the donor box [0, s]^2.
    A unit square's angle a maps to -a under any single reflection (mod 90 it is the same square)."""
    x, y, a = T[:, 0].copy(), T[:, 1].copy(), T[:, 2].copy()
    flips = 0
    if k & 1:
        x, y = y, x; flips += 1
    if k & 2:
        x = s - x; flips += 1
    if k & 4:
        y = s - y; flips += 1
    if flips % 2:
        a = -a
    return np.c_[x, y, a % 90.0]


def shifts(T, s_m, S):
    D = S - s_m
    lo, hi = math.floor(min(0.0, D)) - 1, math.ceil(max(0.0, D)) + 1
    out = [('int', float(i), float(j)) for i in range(lo, hi + 1) for j in range(lo, hi + 1)]
    f = D - round(D)
    if 1e-9 < abs(f) <= NEAR_INT:
        out += [('near', i + f, j + f) for _, i, j in list(out)]
    cx, cy = T[:, 0].mean(), T[:, 1].mean()
    d = cx - cy                                        # main diagonal: centroid onto x = y, moved with the box
    out.append(('diag', -d / 2 + D / 2, d / 2 + D / 2))
    e = (S - (cx + cy)) / 2                            # anti diagonal: centroid onto x + y = S
    out.append(('anti', e, e))
    return out


def inside(T, S, tol=1e-9):
    h = 0.5 * (np.abs(np.cos(np.radians(T[:, 2]))) + np.abs(np.sin(np.radians(T[:, 2]))))
    return bool(((T[:, 0] - h) >= -tol).all() and ((T[:, 0] + h) <= S + tol).all()
                and ((T[:, 1] - h) >= -tol).all() and ((T[:, 1] + h) <= S + tol).all())


def transforms(m, s_m, T, S):
    """every (label, T') of donor m's island that fits the target box"""
    seen, out = set(), []
    for k in range(8):
        Tk = symmetry(T, s_m, k)
        for kind, dx, dy in shifts(Tk, s_m, S):
            Tt = Tk + [dx, dy, 0.0]
            if not inside(Tt, S):
                continue
            key = hashlib.sha1(np.round(Tt[np.lexsort(Tt.T[::-1])], 6).tobytes()).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            out.append((f'd{m}-s{k}-{kind}{dx:+.6f},{dy:+.6f}', Tt))
    return out


# ------------------------------------------------------------------ fill, polish, certify

def fill(S, T, mode):
    import fillfast
    t0 = time.process_time()
    X = fillfast.fill(S, T, mode=mode)
    return X, time.process_time() - t0


def _screen(job):
    label, S, T = job
    X, cpu = fill(S, T, 'greedy')
    return label, len(X), cpu


def _exact(job):
    label, S, T = job
    X, cpu = fill(S, T, 'exact')
    return label, X, cpu


def fq_polish(n, S, sq, tmp):
    a, b = os.path.join(tmp, 'a.txt'), os.path.join(tmp, 'b.txt')
    write_txt(a, S, sq[:n])
    t0 = time.time()
    r = subprocess.run([FQ, 'quench', '--in', a, '--out', b] + FQ_POLISH, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(b):
        return None, None, time.time() - t0
    s2, X = read_txt(b)
    return s2, X, time.time() - t0


def to_rows(n, X):
    return [{'n': str(n), 'square_id': str(i), 'x': repr(float(x)), 'y': repr(float(y)),
             'angle': repr(math.radians(float(a)))} for i, (x, y, a) in enumerate(X)]


def certify(n, X):
    """lane floatsafe.work on these n squares: (ok, side from the metric, reason, certified rows or None)"""
    import floatsafe
    if len(X) != n:
        return False, None, f'count {len(X)} != {n}', None
    rows = to_rows(n, X)
    _, fr, score, e = floatsafe.work((n, rows))
    if fr is None:
        _, why = floatsafe.check(n, rows)
        return False, None, f'floatsafe failed: {why}', None
    return True, (score + 1.0) * math.sqrt(n), 'ok' if e == 0 else f'ok dilated {e:g}', fr


# ------------------------------------------------------------------ feed

def licence_of(m):
    p = os.path.join(LANE, 'results', 'harvest-best-2026-11-07.tsv')
    if not os.path.exists(p):
        return 'unknown'
    for line in open(p):
        f = line.rstrip('\n').split('\t')
        if f and f[0] == str(m):
            return f'{f[3]} ({f[4]})'
    return 'unknown'


def feed(sub, n, S=None, donors='auto', fam_tol=1e-9, top=8, exact=24, certify_on=False, out='cand', procs=4,
         runs_tsv=None, quiet=False):
    """Returns a list of attempt dicts (best first)."""
    t_wall = time.time()
    S_of = sides(sub)
    if n not in S_of:
        raise SystemExit(f'n={n} not in {sub}')
    S = S_of[n] if S is None else S
    D = donors_auto(n, S_of, fam_tol) if donors == 'auto' else [int(x) for x in str(donors).split(',') if x]
    P = load_sub(sub, D)
    jobs = []
    for m in D:
        s_m, Pm = P[m]
        T = island(Pm)
        if len(T) == 0:
            continue
        jobs += [(lab, S, Tt) for lab, Tt in transforms(m, s_m, T, S)]
    if not quiet:
        print(f'n={n} S={S!r} donors={D} transforms={len(jobs)}', flush=True)
    byl = {j[0]: j for j in jobs}
    with Pool(procs) as pool:
        scr = sorted(pool.map(_screen, jobs, chunksize=1), key=lambda r: -r[1])
        ex = pool.map(_exact, [byl[lab] for lab, _, _ in scr[:exact]], chunksize=1)
    cpu_screen = {lab: c for lab, _, c in scr}
    res = []
    for lab, X, cpu in ex:
        res.append(dict(label=lab, donor=int(lab.split('-')[0][1:]), count=len(X), tilted=int((tilt(X[:, 2]) > TILT_MIN).sum()),
                        cpu_s=cpu + cpu_screen.get(lab, 0.0), X=X))
    res.sort(key=lambda r: -r['count'])
    os.makedirs(os.path.join(out, 'donorfeed', str(n)), exist_ok=True)
    odir = os.path.join(out, 'donorfeed', str(n))
    utc = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    tmpd = tempfile.TemporaryDirectory(prefix=f'donorfeed-{n}-'); tmp = tmpd.name
    with open(os.path.join(odir, f'{utc}-attempts.jsonl'), 'w') as f:
        for lab, cnt, c in scr:
            f.write(json.dumps(dict(n=n, S=S, label=lab, greedy=cnt, cpu_s=c)) + '\n')
    for i, r in enumerate(res[:top]):
        X = r['X']
        reached = r['count'] >= n
        side_out, why, safe = None, 'not run', False
        if reached and certify_on:
            s2, Xp, w = fq_polish(n, S, X, tmp)
            r['cpu_s'] += w
            if Xp is None:
                why = 'fq failed'
            else:
                ok, L, why, _ = certify(n, Xp)
                if ok:
                    side_out, safe, X = L, True, Xp
        elif reached:
            why = 'reached, not certified'
        else:
            why = f'short by {n - r["count"]}'
        r.update(side_out=side_out, reason=why, kaggle_safe=safe)
        base = os.path.join(odir, f'{utc}-{i:02d}')
        sq = X[:n] if reached else X
        write_txt(base + '.txt', side_out if safe else S, sq)
        meta = dict(n=n, side=float(side_out if safe else S), side_dec=repr(float(side_out if safe else S)),
                    tool='donorfeed', method=r['label'], parent=r['donor'], source=f'ours:{os.path.basename(sub)}',
                    licence=licence_of(r['donor']), cpu_s=round(r['cpu_s'], 3), box=socket.gethostname(),
                    count=r['count'], reason=why, kaggle_safe=safe)
        json.dump(meta, open(base + '.json', 'w'), indent=1)
        if runs_tsv:
            new = not os.path.exists(runs_tsv)
            with open(runs_tsv, 'a') as f:
                if new:
                    f.write('\t'.join(RUNS_COLS) + '\n')
                f.write('\t'.join(map(str, ['donorfeed', n, repr(S), r['label'], i, round(time.time() - t_wall, 1),
                                            round(r['cpu_s'], 1), r['count'], repr(side_out) if side_out else '',
                                            why, safe])) + '\n')
        if not quiet:
            print(f'  {i:2d} {r["label"]:44s} count {r["count"]:4d}/{n} tilted {r["tilted"]:3d} -> {why}'
                  f'{"" if side_out is None else f" side {side_out:.10f}"}', flush=True)
    tmpd.cleanup()
    return res


# ------------------------------------------------------------------ propagate

def propagate(win, sub, fam_tol=1e-9, queue=None):
    """A T2-accepted win at n: queue stretch.py and donorfeed for n +- 1 and the exact-family siblings (smallest
    first). Returns the job rows; appends them to `queue` (TSV) when given."""
    S_of = sides(sub)
    fam = family(win, S_of, fam_tol)
    targets = [('family', m) for m in fam] + [('neighbour', m) for m in (win - 1, win + 1) if m in S_of and m not in fam]
    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    rows = []
    for why, m in targets:
        rows.append([now, win, m, why, 'donorfeed', f'donorfeed.py feed --sub {sub} --n {m} --donors {win} --certify'])
        rows.append([now, win, m, why, 'stretch', f'stretch.py --best <best dirs> --cur <per-n.tsv> --out <dir> --n0 {win}'])
    if queue:
        new = not os.path.exists(queue)
        with open(queue, 'a') as f:
            if new:
                f.write('utc\twin_n\ttarget_n\twhy\tkind\tcmd\n')
            for r in rows:
                f.write('\t'.join(map(str, r)) + '\n')
    return rows


# ------------------------------------------------------------------ selftest

def selftest(sub, out, procs):
    """Red controls first: the certifier must reject an overcounted fill, and an unrelated donor must not certify.
    Then the green ones. Exit 1 on any surprise."""
    S_of = sides(sub)
    fails = []

    def expect(name, cond, detail):
        print(f'[{"PASS" if cond else "FAIL"}] {name}: {detail}', flush=True)
        if not cond:
            fails.append(name)

    # R0: the certifier can go red. A tolerant fill (tau 0.2) overcounts with overlapping uprights; skip fq so the
    # overlaps reach the metric. It must reject.
    s908, P908 = load_sub(sub, [908])[908]
    import fillfast
    X = fillfast.fill(s908 - 0.05, island(P908), mode='greedy', tau=0.2)
    ok, L, why, _ = certify(908, X[:908]) if len(X) >= 908 else (False, None, f'count {len(X)}', None)
    expect('R0 certifier rejects an overlapping tolerant fill at 908, side - 0.05', not ok,
           f'count {len(X)}, certify -> {why}')
    # R0b: the certifier passes our own 908 as stored (it must not be red on everything)
    ok, L, why, _ = certify(908, P908)
    expect('R0b certifier passes our stored 908', ok and abs(L - s908) < 1e-7, f'{why}, L {L!r} vs {s908!r}')

    # R1: unrelated donor (frac distance > 1e-3) into the 791 box at our side must not certify.
    far = [m for m in (790, 789, 793) if frac_dist(S_of[m], S_of[791]) > 1e-3]
    res = feed(sub, 791, donors=','.join(map(str, far)), top=4, exact=8, certify_on=True, out=out, procs=procs,
               quiet=True)
    best = res[0] if res else None
    expect('R1 unrelated donors into 791 do not certify', not any(r.get('kaggle_safe') for r in res),
           f'donors {far} fracs {[round(S_of[m] % 1, 6) for m in far]}, best count {best["count"] if best else 0}/791')

    # G1: the plan's case, our 791 island into the 908 box. Reported, the 791 island is not 908's (146 vs 200).
    res = feed(sub, 908, donors='791', top=4, exact=24, certify_on=True, out=out, procs=procs, quiet=True)
    r = res[0]
    print(f'[INFO] G1 791 -> 908: best {r["label"]} count {r["count"]}/908 -> {r["reason"]}'
          f' side {r["side_out"]}', flush=True)

    # G2: 792 holds 908's island (same 200 tilted squares moved by (0, 2)). It must rebuild our 908 side.
    res = feed(sub, 908, donors='792', top=4, exact=24, certify_on=True, out=out, procs=procs, quiet=True)
    good = [r for r in res if r.get('kaggle_safe') and abs(r['side_out'] - s908) < 1e-7]
    r = res[0]
    expect('G2 792 island into the 908 box rebuilds our 908 side within 1e-7', bool(good),
           f'best {r["label"]} count {r["count"]}/908 -> {r["reason"]} side {r["side_out"]!r} vs {s908!r}')

    # P1: a simulated win at 791 must queue 908 and 790 / 792.
    rows = propagate(791, sub)
    tg = {r[2] for r in rows}
    expect('P1 a win at 791 queues 908, 790 and 792', {908, 790, 792} <= tg, f'targets {sorted(tg)}')
    # P1 red: an n with no family queues only its two neighbours
    lone = next(m for m in range(400, 1000) if not family(m, S_of, 1e-9))
    tl = {r[2] for r in propagate(lone, sub)}
    expect(f'P1b a win at lone n={lone} queues only n-1, n+1', tl == {lone - 1, lone + 1}, f'targets {sorted(tl)}')
    print('selftest', 'RED: ' + ', '.join(fails) if fails else 'GREEN', flush=True)
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sp = ap.add_subparsers(dest='cmd', required=True)
    f = sp.add_parser('feed')
    f.add_argument('--sub', required=True); f.add_argument('--n', type=int, required=True)
    f.add_argument('--side', type=float); f.add_argument('--donors', default='auto')
    f.add_argument('--fam-tol', type=float, default=1e-9); f.add_argument('--top', type=int, default=8)
    f.add_argument('--exact', type=int, default=24); f.add_argument('--certify', action='store_true')
    f.add_argument('--out', default=os.path.join(LANE, 'cand')); f.add_argument('--procs', type=int, default=4)
    f.add_argument('--runs', default=os.path.join(LANE, 'results', 'donorfeed-runs.tsv'))
    p = sp.add_parser('propagate')
    p.add_argument('--win', type=int, required=True); p.add_argument('--sub', required=True)
    p.add_argument('--fam-tol', type=float, default=1e-9)
    p.add_argument('--queue', default=os.path.join(LANE, 'results', 'donorfeed-queue.tsv'))
    t = sp.add_parser('selftest')
    t.add_argument('--sub', required=True); t.add_argument('--out', default=tempfile.mkdtemp(prefix='donorfeed-st-'))
    t.add_argument('--procs', type=int, default=4)
    a = ap.parse_args()
    if a.cmd == 'feed':
        feed(a.sub, a.n, a.side, a.donors, a.fam_tol, a.top, a.exact, a.certify, a.out, a.procs, runs_tsv=a.runs)
    elif a.cmd == 'propagate':
        for r in propagate(a.win, a.sub, a.fam_tol, a.queue):
            print(*r, sep='\t')
    else:
        sys.exit(selftest(a.sub, a.out, a.procs))


if __name__ == '__main__':
    main()
