#!/usr/bin/env python3
"""T3 insbench: fit-n-again controls that kill weak engines in hours.

  insbench.py make --sub SUB.csv --board BOARD.json --ns 498,593 --seeds 3 --evand DIR --out BENCH
  insbench.py run  --bench BENCH --engine 'CMD {in} {side} {out}' --name NAME --cpu 120
                   [--classes a,b] [--jobs 4] [--ns ...]

A case is one of our packings with one square removed. The engine gets the n-1
squares (`{in}`, Evan Daniel's `n s / x y deg` text) and a side (`{side}`), and
must write n squares inside that side to `{out}`. Also available: `{n}`, `{cpu}`
(seconds), `{drop}` (the removed square's pose, for the trivial control only).
Classes:
  a0  removed only: the hole is still there (plumbing; the trivial engine passes)
  a   removed, the rest jittered (sigma 0.02, 0.5 deg) and quenched with fq;
      side = our side
  b   removed, scaled to halfway between our side and the board's best, quenched;
      side = that halfway side (feasible: the board holds n below it)
  c   negative: side = sqrt(n) - 0.01 (area-infeasible); for 498 also board - 0.05
A result passes when it has exactly n squares, the official metric (as
evaluate_single_puzzle) says ok, and its side is <= the case side + 1e-9.
Results append to results/insbench.tsv in the lane.
"""
import argparse, csv, json, math, os, random, shlex, subprocess, sys, time
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE))
import evconv  # noqa: E402
import kaggle_metric as km  # noqa: E402

TSV = LANE / 'results' / 'insbench.tsv'


def load(p):
    L = [l.split() for l in open(p) if l.strip() and not l.startswith('#')]
    n, s = int(L[0][0]), float(L[0][1])
    return s, [tuple(map(float, q[:3])) for q in L[1:n + 1]]


def write(p, s, Q):
    with open(p, 'w') as h:
        h.write(f'{len(Q)} {s!r}\n')
        for x, y, d in Q:
            h.write(f'{x!r} {y!r} {d!r}\n')


def fq(evand, inp, out, timeout=600):
    b = Path(evand).resolve() / 'search/packer/target/release/fq'
    r = subprocess.run([str(b), 'quench', '--in', str(inp), '--out', str(out)], capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode == 0 and Path(out).exists()


def make(a):
    board = {int(r['n']): float(r['L']) for r in json.load(open(a.board))}
    bench = Path(a.out).resolve(); (bench / 'cases').mkdir(parents=True, exist_ok=True)
    tmp = bench / 'tmp'; tmp.mkdir(exist_ok=True)
    cases = []
    for n in map(int, a.ns.split(',')):
        full = tmp / f'{n}.txt'
        evconv.to_txt(a.sub, n, str(full))
        s, Q = load(full)
        for seed in range(a.seeds):
            rng = random.Random(1000 * n + seed)
            k = rng.randrange(len(Q))
            drop, rest = Q[k], Q[:k] + Q[k + 1:]
            def case(cls, side, R, Rs, tag=''):
                cid = f'{n}-{cls}{tag}-{seed}'
                d = bench / 'cases' / cid; d.mkdir(exist_ok=True)
                write(d / 'in.txt', Rs, R)
                json.dump({'id': cid, 'n': n, 'class': cls, 'side': side, 'drop': drop, 'ours': s,
                           'board': board.get(n)}, open(d / 'case.json', 'w'))
                write(d / 'drop.txt', s, [drop])
                cases.append(cid)
            case('a0', s, rest, s)
            J = [(x + rng.gauss(0, .02), y + rng.gauss(0, .02), dg + rng.gauss(0, .5)) for x, y, dg in rest]
            write(tmp / 'j.txt', s, J)
            if fq(a.evand, tmp / 'j.txt', tmp / 'jq.txt'):
                sq, R = load(tmp / 'jq.txt'); case('a', s, R, sq)
            half = (s + board[n]) / 2 if n in board else s
            f = half / s
            write(tmp / 'h.txt', half, [(x * f, y * f, dg) for x, y, dg in rest])
            if fq(a.evand, tmp / 'h.txt', tmp / 'hq.txt'):
                sq, R = load(tmp / 'hq.txt'); case('b', half, R, sq)
            case('c', math.sqrt(n) - 0.01, rest, s)
            if n == 498 and n in board and seed == 0:
                case('c', board[n] - 0.05, rest, s, tag='L')
    print(f'{len(cases)} cases in {bench / "cases"}')


def certify(c, out):
    n, side = c['n'], c['side']
    if not out.exists():
        return False, None, 'no output'
    try:
        s, Q = load(out)
    except Exception as e:
        return False, None, f'unreadable: {e}'
    if len(Q) != n:
        return False, None, f'{len(Q)} squares, need {n}'
    rows = [{'n': n, 'square_id': i, 'x': repr(x), 'y': repr(y), 'angle': repr(math.radians(d))}
            for i, (x, y, d) in enumerate(Q)]
    _, sc, Ltext, why = km.evaluate_single_puzzle(n, rows)
    if why != 'ok':
        return False, None, why
    L = float(Ltext)
    return (L <= side + 1e-9), L, 'ok' if L <= side + 1e-9 else f'side {L:.9f} > {side:.9f}'


def one(args):
    c, engine, cpu, bench = args
    d = bench / 'cases' / c['id']
    out = d / f'out-{os.getpid()}.txt'
    out.unlink(missing_ok=True)
    cmd = engine.format(**{'in': shlex.quote(str(d / 'in.txt')), 'side': repr(c['side']), 'out': shlex.quote(str(out)),
                           'n': c['n'], 'cpu': cpu, 'drop': shlex.quote(str(d / 'drop.txt'))})
    t0 = time.time()
    try:
        subprocess.run(cmd, shell=True, timeout=cpu * 1.2 + 30, capture_output=True, start_new_session=True)
    except subprocess.TimeoutExpired:
        pass
    ok, L, why = certify(c, out)
    out.unlink(missing_ok=True)
    return c, ok, L, why, time.time() - t0


def run(a):
    from multiprocessing import Pool
    bench = Path(a.bench).resolve()
    classes = set(a.classes.split(','))
    want = set(map(int, a.ns.split(','))) if a.ns else None
    cs = [json.load(open(p / 'case.json')) for p in sorted((bench / 'cases').iterdir())]
    cs = [c for c in cs if c['class'] in classes and (want is None or c['n'] in want)]
    TSV.parent.mkdir(exist_ok=True)
    new = not TSV.exists()
    agg = {}
    with Pool(a.jobs) as p, open(TSV, 'a') as h:
        if new:
            h.write('utc\tengine\tcase\tn\tclass\tside\tpass\tL\treason\twall_s\tcpu_budget\n')
        for c, ok, L, why, wall in p.imap_unordered(one, [(c, a.engine, a.cpu, bench) for c in cs]):
            h.write(f'{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\t{a.name}\t{c["id"]}\t{c["n"]}\t{c["class"]}\t'
                    f'{c["side"]!r}\t{int(ok)}\t{"" if L is None else repr(L)}\t{why}\t{wall:.0f}\t{a.cpu}\n'); h.flush()
            t = agg.setdefault(c['class'], [0, 0, 0.0]); t[0] += ok; t[1] += 1; t[2] += wall
    for k, (p_, t, w) in sorted(agg.items()):
        rate = p_ / (w / 3600) if w else 0
        print(f'{a.name} class {k}: {p_}/{t} pass ({100 * p_ / t:.0f}%), {rate:.2f} passes per CPU-hour')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    m = sp.add_parser('make')
    for x in ('--sub', '--board', '--ns', '--evand', '--out'):
        m.add_argument(x, required=True)
    m.add_argument('--seeds', type=int, default=3)
    r = sp.add_parser('run')
    for x in ('--bench', '--engine', '--name'):
        r.add_argument(x, required=True)
    r.add_argument('--cpu', type=int, default=120); r.add_argument('--classes', default='a,b')
    r.add_argument('--jobs', type=int, default=4); r.add_argument('--ns')
    a = ap.parse_args()
    make(a) if a.cmd == 'make' else run(a)
