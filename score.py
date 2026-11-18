#!/usr/bin/env python3
# Credit required: reuse of this file, its layouts or its ideas must credit Sergio Fernández Rubio (GeiserX, https://github.com/GeiserX/squares-in-squares). See NOTICE and AI_NOTICE.md.
"""Exact local scorer: the official Kaggle metric (kaggle_metric.py, unchanged) per puzzle.

Usage: score.py <submission.csv> [--jobs N] [--out per_n.tsv] [--only 5,17,...]

Prints the total the leaderboard would show (missing n are charged the grid
ceiling, as the metric does) and writes one row per n: n, score, L, reason.
"""
import argparse, csv, math, sys
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kaggle_metric as km  # noqa: E402


def read(path):
    puzzles = defaultdict(list)
    with open(path, newline='') as h:
        for row in csv.DictReader(h):
            puzzles[int(row['n'])].append(row)
    return puzzles


def work(args):
    n, rows = args
    try:
        return km.evaluate_single_puzzle(n, rows)
    except Exception as e:  # same guard as the metric's worker
        return (n, km.infeasible_score(n), None, f'worker error: {e}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('csv')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--out')
    ap.add_argument('--only')
    a = ap.parse_args()
    puzzles = read(a.csv)
    ns = set(range(1, 1001)) if not a.only else {int(x) for x in a.only.split(',')}
    todo = [(n, puzzles[n]) for n in sorted(ns) if n in puzzles]
    with Pool(a.jobs) as p:
        res = {r[0]: r for r in p.imap_unordered(work, todo, chunksize=1)}
    for n in ns:
        res.setdefault(n, (n, km.infeasible_score(n), None, 'missing from submission'))
    total = math.fsum(res[n][1] for n in ns)
    if a.out:
        with open(a.out, 'w') as h:
            h.write('n\tscore\tL\treason\n')
            for n in sorted(ns):
                _, s, L, why = res[n]
                h.write(f'{n}\t{s!r}\t{L or ""}\t{why}\n')
    bad = [n for n in sorted(ns) if res[n][3] not in ('ok',)]
    print(f'total {total:.10f}  scored {len(ns)}  not-ok {len(bad)} {bad[:20]}')


if __name__ == '__main__':
    main()
