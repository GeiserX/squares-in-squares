#!/usr/bin/env python3
"""Run Evan Daniel's free-tilted Monte Carlo (ftmc.py, MIT) over a queue of n.

For each n in this worker's slice of the queue: start from our packing in --sub,
run ftmc for --minutes, and if its best side beats ours, push the result through
floatsafe.work (official metric as written and after a pandas parse, 2e-11 minimum
clearance). Every result is a line in <out>/results.tsv; wins also keep their rows in
<out>/win-<n>.csv. FTMC's full-line rejection is switched off (--k 999): it steers
Evan's search away from grid-like layouts and says nothing about feasibility.

  ftmc_queue.py --queue q.txt --worker W --workers P --sub sub.csv --evand DIR --out DIR [--minutes 30]
Stop: touch <out>/STOP (the current n finishes).
"""
import argparse, csv, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import evconv, floatsafe  # noqa: E402


def side_of(txt):
    return float(open(txt).readline().split()[1])


def main():
    ap = argparse.ArgumentParser()
    for a in ('--queue', '--sub', '--evand', '--out'):
        ap.add_argument(a, required=True)
    ap.add_argument('--worker', type=int, required=True); ap.add_argument('--workers', type=int, required=True)
    ap.add_argument('--minutes', type=float, default=30); ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    ns = [int(l.split()[0]) for l in open(a.queue) if l.strip() and not l.startswith('#')]
    mine = ns[a.worker::a.workers]
    packer = Path(a.evand).resolve() / 'search' / 'packer'
    keep, rows_all = set(mine), {}
    for r in csv.DictReader(open(a.sub)):
        if int(r['n']) in keep:
            rows_all.setdefault(int(r['n']), []).append(r)
    for n in mine:
        if (out / 'STOP').exists():
            break
        if (out / f'done-{n}').exists():
            continue
        ours_rows = rows_all[n]
        _, ours, _, why = floatsafe.km.evaluate_single_puzzle(n, ours_rows)
        init = out / f'{n}.txt'
        sub_n = out / f'sub-{n}.csv'
        with open(sub_n, 'w', newline='') as h:
            w = csv.DictWriter(h, fieldnames=list(ours_rows[0].keys())); w.writeheader(); w.writerows(ours_rows)
        s0 = evconv.to_txt(str(sub_n), n, str(init))
        t0 = time.time()
        log = open(out / f'ftmc-{n}.log', 'w')
        subprocess.run([sys.executable, 'ftmc.py', '--n', str(n), '--k', '999', '--init', str(init),
                        '--seed', str(a.seed), '--time', str(a.minutes * 60), '--out', str(out / f'r{n}')],
                       cwd=packer, stdout=log, stderr=subprocess.STDOUT)
        best = out / f'r{n}.best.txt'
        s1 = side_of(best) if best.exists() else float('inf')
        verdict, new = 'no-gain', ''
        if s1 < s0 - 1e-9:
            evconv.from_txt(str(best), str(out / f'cand-{n}.csv'))
            cand = list(csv.DictReader(open(out / f'cand-{n}.csv')))
            _, fr, sc, e = floatsafe.work((n, cand))
            if fr is None:
                verdict = 'infeasible'
            elif sc < ours - 1e-12:
                verdict, new = 'WIN', repr(sc)
                with open(out / f'win-{n}.csv', 'w', newline='') as h:
                    w = csv.DictWriter(h, fieldnames=['n', 'square_id', 'x', 'y', 'angle'])
                    w.writeheader(); w.writerows(fr)
            else:
                verdict, new = 'not-better-after-safe', repr(sc)
        with open(out / 'results.tsv', 'a') as h:
            h.write(f'{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}\t{n}\t{s0!r}\t{s1!r}\t{ours!r}\t{new}\t{verdict}\t{time.time() - t0:.0f}\n')
        (out / f'done-{n}').touch()


if __name__ == '__main__':
    main()
