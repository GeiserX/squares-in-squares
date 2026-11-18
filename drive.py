#!/usr/bin/env python3
"""Long-running per-n search driver for Squares in Squares.

Loop forever:
  1. pick a puzzle n, weighted by our gap to the per-puzzle leaderboard best
     (plus a floor, so every n with room above the area bound gets tried);
  2. run Couzo's sqpack local search (MIT, github.com/franciscouzo/square-packing)
     from our current packing for that n, from n+1 minus a square, from n-1
     plus one, or (n >= 100) from a tilted-band layout built by bandseed.py at
     the smallest side where it holds n;
  3. if it returns a smaller side, dilate the centres by (1 + eps) so float
     contacts become certified gaps, score that one puzzle with the official
     metric (kaggle_metric.py, unchanged) and keep it only if the metric says
     ok and the score went down.

State lives in --state:
  best/<n>.csv     current best rows for n (id column omitted), metric-checked
  best/<n>.score   its metric score
  improvements.tsv one row per accepted improvement (utc, n, old, new, host)
Assemble a full submission with assemble.py.

Usage:
  drive.py --state DIR --seed merged.csv --seed-tsv merged.tsv --targets ppl.json \
           --sqpack bin/sqpack --threads 4 --seconds 120
"""
import argparse, csv, json, math, os, random, shutil, socket, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kaggle_metric as km  # noqa: E402

EPS = (1e-12, 1e-11, 1e-10, 1e-9)


def log(msg):
    print(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), msg, flush=True)


def init_state(state, seed_csv, seed_tsv):
    best = state / 'best'
    if best.exists():
        return
    tmp = state / 'best.tmp'
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    scores = {int(r['n']): r for r in csv.DictReader(open(seed_tsv), delimiter='\t')}
    rows = {}
    for r in csv.DictReader(open(seed_csv)):
        rows.setdefault(int(r['n']), []).append(r)
    for n, rs in rows.items():
        if scores[n]['reason'] != 'ok':
            continue
        write_rows(tmp / f'{n}.csv', sorted(rs, key=lambda r: int(r['square_id'])))
        (tmp / f'{n}.score').write_text(scores[n]['score'] + '\n')
    tmp.rename(best)


def write_rows(path, rows):
    t = path.with_suffix('.tmp')
    with open(t, 'w', newline='') as h:
        w = csv.writer(h, lineterminator='\n')
        w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in rows:
            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    t.replace(path)


def current(state, n):
    p = state / 'best' / f'{n}.score'
    if not p.exists():
        return km.infeasible_score(n), None
    return float(p.read_text()), list(csv.DictReader(open(state / 'best' / f'{n}.csv')))


def pick(state, targets, rng, floor, mod=None):
    weights = []
    for n in range(2, 1001):
        if mod and n % mod[0] != mod[1]:
            continue
        s, _ = current(state, n)
        if s <= 1e-15:
            continue  # perfect squares on the grid
        gap = max(0.0, s - targets.get(n, s))
        weights.append((n, gap + floor))
    tot = sum(w for _, w in weights)
    x = rng.random() * tot
    for n, w in weights:
        x -= w
        if x <= 0:
            return n
    return weights[-1][0]


def to_rows(n, z, eps):
    xs = [p[0] for p in z]
    ys = [p[1] for p in z]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    f = 1.0 + eps
    return [dict(n=str(n), square_id=str(i), x=repr(cx + (x - cx) * f), y=repr(cy + (y - cy) * f), angle=repr(t))
            for i, (x, y, t) in enumerate(z)]


def read_txt(path):
    z = []
    for line in open(path):
        if line.startswith('#') or not line.strip():
            continue
        a = line.split()
        z.append((float(a[0]), float(a[1]), float(a[2])))
    return z


def band_rows(n, L_old, rng, seconds):
    """A tilted-band layout (bandseed.py) at the smallest side where it holds n.

    The parameters are searched at our side first, then at a few slightly larger
    sides; the first side where some layout holds n is shrunk by bisection.
    """
    import bandseed
    for dL in (0.0, 0.03, 0.06, 0.1):
        c, p = bandseed.best_count(L_old + dL, seconds / 4, rng)
        if p is not None and c >= n:
            break
    else:
        log(f'n={n} band: no layout holds n within +0.1 of our side')
        return None
    L = bandseed.min_side(n, p, math.sqrt(n), L_old + dL)
    sq = bandseed.layout(L, *p)
    log(f'n={n} band seed side {L:.6f} (ours {L_old:.6f}) squares {len(sq)} '
        f'theta={math.degrees(p[0]):.3f} off={p[1]:.4f} w1={p[2]:.4f} w2={p[3]:.4f}')
    return [dict(x=repr(float(x)), y=repr(float(y)), angle=repr(float(t))) for x, y, t in sq]


def one_job(args, state, n, rng, host):
    old, rows = current(state, n)
    # init: our own packing (local polish), n+1's minus a random square (drop),
    # n-1's plus one (grow), or a tilted-band layout (band); sqpack handles
    # drop/grow by the init's size
    modes, weights = ['local', 'drop', 'grow', 'band'], [0.35, 0.35, 0.15, 0.15 if n >= 100 else 0]
    mode = rng.choices(modes, weights=weights)[0]
    src = rows
    if mode in ('drop', 'grow'):
        _, src = current(state, n + 1 if mode == 'drop' else n - 1)
        if not src:
            mode, src = 'local', rows
    elif mode == 'band':
        src = band_rows(n, (old + 1) * math.sqrt(n), rng, args.band_seconds)
        if not src:
            mode, src = 'local', rows
    work = Path(tempfile.mkdtemp(prefix=f'n{n}-', dir=args.work))
    try:
        init = work / 'init.txt'
        with open(init, 'w') as h:
            h.write(f'# n = {n}\n')
            for r in src or []:
                h.write(f"{float(r['x'])!r} {float(r['y'])!r} {float(r['angle'])!r}\n")
        L_old = (old + 1) * math.sqrt(n)
        (work / 'records.txt').write_text(f'{n} {L_old!r}\n')
        cmd = [str(Path(args.sqpack).resolve()), 'search', str(n), '--time', str(args.seconds),
               '--threads', str(args.threads), '--seed', str(rng.randrange(1 << 31))]
        if src:
            cmd += ['--init', 'init.txt'] + (['--local'] if mode == 'local' else [])
        with open(work / 'sqpack.log', 'w') as lf:
            subprocess.run(cmd, cwd=work, stdout=lf, stderr=subprocess.STDOUT,
                           timeout=args.seconds * 3 + 120)
        res = work / 'results' / f'n{n}.txt'
        if not res.exists():
            return None
        z = read_txt(res)
        if len(z) != n:
            return None
        for eps in EPS:
            cand = to_rows(n, z, eps)
            _, s, L, why = km.evaluate_single_puzzle(n, cand)
            if why == 'ok':
                break
        else:
            log(f'n={n} candidate rejected by metric: {why}')
            return None
        old = min(old, current(state, n)[0])   # an import may have landed during the job
        if s < old - 1e-13:
            write_rows(state / 'best' / f'{n}.csv', cand)
            (state / 'best' / f'{n}.score').write_text(repr(s) + '\n')
            with open(state / 'improvements.tsv', 'a') as h:
                h.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\t{n}\t{old!r}\t{s!r}\t{host}\n")
            log(f'n={n} IMPROVED [{mode}] {old:.12f} -> {s:.12f} (L {L[:20]})')
            return s
        return None
    except subprocess.TimeoutExpired:
        log(f'n={n} sqpack timed out')
        return None
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--state', type=Path, required=True)
    ap.add_argument('--seed')
    ap.add_argument('--seed-tsv')
    ap.add_argument('--targets', required=True, help='per-puzzle leaderboard json (n, L)')
    ap.add_argument('--sqpack', required=True)
    ap.add_argument('--threads', type=int, default=4)
    ap.add_argument('--seconds', type=float, default=120)
    ap.add_argument('--floor', type=float, default=2e-4)
    ap.add_argument('--band-seconds', type=float, default=20, help='bandseed parameter search per band job')
    ap.add_argument('--only', help='comma list of n to restrict to')
    ap.add_argument('--work', default=None)
    ap.add_argument('--mod', help='K,R: only n with n %% K == R (split n across boxes)')
    ap.add_argument('--max-load', type=float, help='pause while the 1-min load average is above this')
    a = ap.parse_args()
    a.state.mkdir(parents=True, exist_ok=True)
    a.work = a.work or str(a.state / 'work')
    Path(a.work).mkdir(parents=True, exist_ok=True)
    if a.seed:
        init_state(a.state, a.seed, a.seed_tsv)
    targets = {int(r['n']): float(r['L']) / math.sqrt(int(r['n'])) - 1
               for r in json.load(open(a.targets)) if float(r['L']) > 0}
    host = socket.gethostname()
    rng = random.Random(os.getpid() ^ int(time.time()))
    only = [int(x) for x in a.only.split(',')] if a.only else None
    log(f'start host={host} threads={a.threads} seconds={a.seconds}')
    while True:
        if (a.state / 'STOP').exists():
            log('STOP file found, exiting')
            return
        if a.max_load and os.getloadavg()[0] > a.max_load:
            time.sleep(60)
            continue
        mod = tuple(int(x) for x in a.mod.split(',')) if a.mod else None
        n = rng.choice(only) if only else pick(a.state, targets, rng, a.floor, mod)
        one_job(a, a.state, n, rng, host)


if __name__ == '__main__':
    main()
