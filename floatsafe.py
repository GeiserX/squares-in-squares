#!/usr/bin/env python3
# Credit required: reuse of this file, its layouts or its ideas must credit Sergio Fernández Rubio (GeiserX, https://github.com/GeiserX/squares-in-squares). See NOTICE and AI_NOTICE.md.
"""Make a submission survive Kaggle's float64 round trip.

Kaggle hands the metric a pandas DataFrame, so every coordinate reaches it as a
float64, not as the decimal text we wrote. Packings with exact contacts (most
public ones above 40 digits) then overlap by rounding error and are charged the
grid. This writes every value as the shortest repr of a float64, which survives
any float parse unchanged. For each n that the metric then rejects, it scales the
centres about their mean by 1+e (e = 1e-15, 2e-15, 5e-15, ... 5e-8, angles
unchanged) until every pair of squares is at least MIN_CLEARANCE (2.2e-11) apart
on a separating axis and the metric certifies it both as written and after
pandas' default float parse (which can be one ulp off, so an exact repr alone
is not enough).
Scaling centres apart only widens every gap.

Usage: floatsafe.py <in.csv> <out.csv> [--jobs N]
"""
import argparse, csv, io, math, sys
from collections import defaultdict
from decimal import Decimal, getcontext
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kaggle_metric as km  # noqa: E402
import pandas as pd  # noqa: E402

getcontext().prec = 80
EPS = [0] + [m * 10.0 ** -k for k in range(15, 7, -1) for m in (1, 2, 5)]
# Kaggle rejected ~1e-12 gaps that the local metric accepted (Samanyu's report),
# so every pair must also clear this on its separating axis. The gate checks 2e-11
# with an independent SAT; aiming 10% higher keeps the two checkers from
# disagreeing in the last bits (both read 2.0e-11 on the first 2e-11 file).
MIN_CLEARANCE = 2.2e-11


def clearance(rows):
    """Smallest separating-axis gap over all pairs of nearby squares (float64)."""
    import numpy as np
    from scipy.spatial import cKDTree
    P = np.array([(float(r['x']), float(r['y']), float(r['angle'])) for r in rows])
    if len(P) < 2:
        return math.inf
    pairs = cKDTree(P[:, :2]).query_pairs(math.sqrt(2) + 1e-6, output_type='ndarray')
    if not len(pairs):
        return math.inf
    loc = np.array([(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)])
    c, s = np.cos(P[:, 2]), np.sin(P[:, 2])
    CX = P[:, :1] + c[:, None] * loc[:, 0] - s[:, None] * loc[:, 1]
    CY = P[:, 1:2] + s[:, None] * loc[:, 0] + c[:, None] * loc[:, 1]
    i, j = pairs[:, 0], pairs[:, 1]
    best = np.full(len(i), -np.inf)
    for k in (i, j):
        for ax, ay in ((c[k], s[k]), (-s[k], c[k])):
            pi = CX[i] * ax[:, None] + CY[i] * ay[:, None]
            pj = CX[j] * ax[:, None] + CY[j] * ay[:, None]
            gap = np.maximum(pj.min(1) - pi.max(1), pi.min(1) - pj.max(1))
            best = np.maximum(best, gap)
    return float(best.min())


def as_float_rows(rows, e):
    xs = [Decimal(r['x']) for r in rows]
    ys = [Decimal(r['y']) for r in rows]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    f = 1 + Decimal(repr(e))
    out = []
    for r, x, y in zip(rows, xs, ys):
        out.append({'n': r['n'], 'square_id': r['square_id'],
                    'x': repr(float(cx + (x - cx) * f)),
                    'y': repr(float(cy + (y - cy) * f)),
                    'angle': repr(float(r['angle']))})
    return out


def via_pandas(fr):
    """The rows as the metric sees them after pandas' default (not round-trip) float parse."""
    df = pd.read_csv(io.StringIO(pd.DataFrame(fr).to_csv(index=False)))
    return [{k: str(v) for k, v in r.items()} for r in
            km._parse_submission_csv(df.to_csv(index=False)).popitem()[1]]


def check(n, rows):
    try:
        _, s, _, why = km.evaluate_single_puzzle(n, rows)
    except Exception as ex:
        s, why = km.infeasible_score(n), f'error {ex}'
    return s, why


def work(a):
    n, rows = a
    for e in EPS:
        fr = as_float_rows(rows, e)
        if clearance(fr) < MIN_CLEARANCE:  # cheap test first; the metric is slow
            continue
        s, why = check(n, fr)
        if why == 'ok' and check(n, via_pandas(fr))[1] == 'ok':
            return n, fr, s, e
    return n, None, km.infeasible_score(n), None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('inp'); ap.add_argument('out'); ap.add_argument('--jobs', type=int, default=3)
    a = ap.parse_args()
    pz = defaultdict(list)
    with open(a.inp, newline='') as h:
        for r in csv.DictReader(h):
            pz[int(r['n'])].append(r)
    with Pool(a.jobs) as p:
        res = {r[0]: r for r in p.imap_unordered(work, sorted(pz.items()), chunksize=1)}
    dil = sorted((n, r[3]) for n, r in res.items() if r[3])
    dead = sorted(n for n, r in res.items() if r[1] is None)
    with open(a.out, 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['id', 'n', 'square_id', 'x', 'y', 'angle'])
        i = 0
        for n in range(1, 1001):
            rows = res[n][1] if n in res and res[n][1] is not None else pz.get(n, [])
            for r in sorted(rows, key=lambda r: int(r['square_id'])):
                w.writerow([i, n, r['square_id'], r['x'], r['y'], r['angle']]); i += 1
    tot = math.fsum(res[n][2] for n in res)
    print(f'float-safe total {tot:.10f}  dilated {len(dil)}  still-bad {dead}')
    for n, e in dil:
        print(f'  n={n} e={e:g}')


if __name__ == '__main__':
    main()
