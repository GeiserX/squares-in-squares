#!/usr/bin/env python3
# Credit required: reuse of this file, its layouts or its ideas must credit Sergio Fernández Rubio (GeiserX, https://github.com/GeiserX/squares-in-squares). See NOTICE and AI_NOTICE.md.
"""T2 gate: the last check before any file goes to Kaggle. It never submits.

  gate.py CAND.csv --out DIR [--last LASTDIR] [--prov prov.tsv] [--jobs 4] [--min-gap 2e-11]

Checks CAND exactly as given (run floatsafe.py first; the gate never repairs):
  1. all of n = 1..1000 present;
  2. Kaggle's path: pandas default read_csv of CAND, then the unchanged
     kaggle_metric.score; every n must get an L (L = 0 means rejected);
  3. an independent float64 separating-axis check on the pandas-parsed values
     (Evan Daniel's satcheck_f64 logic, MIT): every pair >= --min-gap;
  4. against LASTDIR (a previous gate dir, i.e. the last submitted file): no n
     scores worse by more than --regress-tol (1e-9; floatsafe dilation alone moves
     a score by ~1e-11) and the total is not higher.
Writes DIR/details.csv (n, L, score), DIR/gate.json and DIR/GREEN or DIR/RED.
Exit 0 only when GREEN. Prints the submit command on GREEN.
"""
import argparse, csv, hashlib, json, math, os, sys
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import kaggle_metric as km  # noqa: E402


def sat_min_gap(P):
    """Smallest separating-axis gap over pairs with centres < 1.5 apart. P: (n, 3), angle in radians."""
    n = len(P)
    if n < 2:
        return math.inf
    C = P[:, :2]
    u = np.stack([np.cos(P[:, 2]), np.sin(P[:, 2])], 1)
    v = np.stack([-u[:, 1], u[:, 0]], 1)
    corners = C[:, None, :] + 0.5 * (np.array([1, 1, -1, -1])[None, :, None] * u[:, None, :]
                                     + np.array([1, -1, -1, 1])[None, :, None] * v[:, None, :])
    worst = math.inf
    for i in range(n - 1):
        j = np.arange(i + 1, n)
        j = j[np.linalg.norm(C[j] - C[i], axis=1) < 1.5]
        if not len(j):
            continue
        gaps = []
        for ax in (u[i], v[i]):
            pi = C[i] @ ax
            pj = np.einsum('jkd,d->jk', corners[j], ax)
            gaps.append(np.maximum(pj.min(1) - (pi + 0.5), (pi - 0.5) - pj.max(1)))
        for A in (u[j], v[j]):
            pj = np.einsum('jd,jd->j', C[j], A)
            pi = np.einsum('kd,jd->jk', corners[i], A)
            gaps.append(np.maximum(pi.min(1) - (pj + 0.5), (pj - 0.5) - pi.max(1)))
        worst = min(worst, float(np.max(np.stack(gaps), 0).min()))
    return worst


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cand'); ap.add_argument('--out', required=True); ap.add_argument('--last')
    ap.add_argument('--prov'); ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--min-gap', type=float, default=2e-11)
    ap.add_argument('--regress-tol', type=float, default=1e-9,
                    help='per-n worsening allowed; floatsafe dilation moves scores by ~1e-11')
    a = ap.parse_args()
    cand = Path(a.cand).resolve()
    out = Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
    for f in ('GREEN', 'RED'):
        (out / f).unlink(missing_ok=True)
    red = []

    sub = pd.read_csv(cand)  # Kaggle's view: default dtypes, default float parser
    ns = set(sub['n'].astype(int))
    missing = sorted(set(range(1, 1001)) - ns)
    if missing:
        red.append(f'missing n: {missing[:20]}{" ..." if len(missing) > 20 else ""}')

    km.KAGGLE_CORES = a.jobs
    sol = pd.DataFrame({'id': range(1000), 'n': range(1, 1001)})
    cwd = os.getcwd(); os.chdir(out)
    try:
        total = km.score(sol, sub.copy(), 'id')
    finally:
        os.chdir(cwd)
    L = {int(r['n']): float(r['L']) for r in csv.DictReader(open(out / 'submission_details.csv'))}
    score = {n: (L[n] / math.sqrt(n) - 1 if L[n] > 0 else km.infeasible_score(n)) for n in range(1, 1001)}
    rejected = sorted(n for n in range(1, 1001) if L[n] <= 0)
    if rejected:
        red.append(f'metric rejected {len(rejected)} n: {rejected[:40]}{" ..." if len(rejected) > 40 else ""}')

    gaps = {}
    for n, g in sub.groupby('n'):
        gaps[int(n)] = sat_min_gap(g[['x', 'y', 'angle']].to_numpy(dtype=float))
    tight = sorted((g, n) for n, g in gaps.items() if g < a.min_gap)
    if tight:
        red.append(f'clearance below {a.min_gap:g} at {len(tight)} n: '
                   + ', '.join(f'{n} ({g:.2e})' for g, n in tight[:20]))

    moved, worse, last_total = [], [], None
    if a.last:
        lj = json.load(open(Path(a.last) / 'gate.json'))
        last_total = lj['total']
        last = {int(r['n']): float(r['score']) for r in csv.DictReader(open(Path(a.last) / 'details.csv'))}
        for n in range(1, 1001):
            d = score[n] - last[n]
            if d > a.regress_tol:
                worse.append((n, last[n], score[n]))
            elif d < -1e-12:
                moved.append((n, last[n], score[n]))
        if worse:
            red.append(f'{len(worse)} n worse than last: ' + ', '.join(f'{n} {o:.10f} -> {s:.10f}' for n, o, s in worse[:20]))
        if total > last_total + 1e-12:
            red.append(f'total {total:.10f} above last {last_total:.10f}')

    prov = {}
    if a.prov:
        for r in csv.DictReader(open(a.prov), delimiter='\t'):
            prov[int(r['n'])] = {k: r[k] for k in r if k != 'n'}
    with open(out / 'details.csv', 'w', newline='') as h:
        w = csv.writer(h); w.writerow(['n', 'L', 'score', 'min_gap'])
        for n in range(1, 1001):
            w.writerow([n, repr(L[n]), repr(score[n]), repr(gaps.get(n, math.nan))])
    sha = hashlib.sha256(cand.read_bytes()).hexdigest()
    verdict = 'RED' if red else 'GREEN'
    rep = {'file': str(cand), 'sha256': sha, 'total': total, 'verdict': verdict, 'reasons': red,
           'last_total': last_total, 'min_gap': min(gaps.values()),
           'moved': [{'n': n, 'old': o, 'new': s, **prov.get(n, {})} for n, o, s in moved]}
    json.dump(rep, open(out / 'gate.json', 'w'), indent=1)
    (out / verdict).write_text('\n'.join(red) + '\n')
    print(f'{verdict} total {total:.10f} sha256 {sha[:16]} min_gap {rep["min_gap"]:.3e} moved {len(moved)}')
    for r in red:
        print('  ' + r)
    if not red:
        print(f'submit: kaggle competitions submit -c squares-in-squares -f {cand} -m "<message>"')
    sys.exit(0 if not red else 1)


if __name__ == '__main__':
    main()
