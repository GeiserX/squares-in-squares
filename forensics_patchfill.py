#!/usr/bin/env python3
"""Refill joint holes using held uprights and joint-contact candidates only.

forensics_patchfill.py control HELD.csv
forensics_patchfill.py scan OUT SOURCE.csv [...]

Unlike a full fillfast refill, this model preserves the actual upright centres.
It adds the joint candidates and solves their conflict graph with one MILP thread.
A larger count is a quench start. It must pass floatsafe before publication.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
import warnings

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as fr
import forensics_upright as fu


def select(points, seconds=5):
    """Maximum independent set of axis-aligned unit squares, at fixed centres."""
    xy = np.asarray(points, float).reshape(-1, 2)
    if not len(xy):
        return np.array([], int), dict(status=0, message='empty', nodes=0)
    pairs = np.array(sorted(cKDTree(xy).query_pairs(math.sqrt(2))), int).reshape(-1, 2)
    if len(pairs):
        pairs = pairs[(np.abs(xy[pairs[:, 0]] - xy[pairs[:, 1]]) < 1 - 1e-7).all(1)]
    ij = np.repeat(np.arange(len(pairs)), 2)
    a = coo_matrix((np.ones(2 * len(pairs)), (ij, pairs.ravel())),
                   shape=(len(pairs), len(xy))).tocsc()
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', message='Unrecognized options detected')
        result = milp(-np.ones(len(xy)), integrality=np.ones(len(xy)),
                      bounds=Bounds(0, 1), constraints=LinearConstraint(a, -np.inf, 1),
                      options=dict(time_limit=seconds, mip_rel_gap=0, threads=1))
    chosen = np.flatnonzero(result.x > .5) if result.x is not None else np.array([], int)
    return chosen, dict(status=int(result.status), message=str(result.message),
                        nodes=len(xy), edges=len(pairs), count=len(chosen),
                        bound=float(-result.mip_dual_bound) if result.x is not None else None)


def refill(q, side, seconds=5, upright_deg=1e-5):
    degrees = (np.degrees(q[:, 2]) + 45) % 90 - 45
    upright = np.abs(degrees) <= upright_deg
    tilted = np.c_[q[~upright, :2], degrees[~upright]]
    extra = fu.joint_candidates(side, tilted)
    points = np.r_[q[upright, :2], extra[:, :2]]
    points = points[(points.min(1) >= .5 - 1e-7) &
                    (points.max(1) <= side - .5 + 1e-7)]
    unique = {}
    for row in points:
        unique.setdefault(tuple(np.round(row, 7)), row)
    points = np.array(list(unique.values())).reshape(-1, 2)
    chosen, stats = select(points, seconds)
    out = np.r_[q[~upright], np.c_[points[chosen], np.zeros(len(chosen))]]
    stats.update(old_uprights=int(upright.sum()), extra=len(extra), total=len(out))
    return out, stats


def control(path):
    # The exact selector must replace two diagonal squares by the four grid cells.
    points = np.array([[.5, .5], [1.5, 1.5], [.5, 1.5], [1.5, .5], [1., 1.]])
    chosen, stats = select(points)
    assert len(chosen) == 4 and 4 not in chosen, stats
    print('CONTROL conflict graph restored four grid cells and refused centre:', stats, flush=True)
    chosen, stats = select(np.array([[.5, .5], [.5, .5]]))
    assert len(chosen) == 1, stats
    print('CONTROL duplicate centres count one:', stats, flush=True)
    sq = fr.layouts(path)[854]
    side, q = fc.frame(sq)
    drop = int(np.argmin(np.hypot(q[:, 0] - 12.2202069629, q[:, 1] - 12.2196213919)))
    out, stats = refill(np.delete(q, drop, axis=0), side, 10)
    print('CONTROL removed known 854 upright:', stats, flush=True)
    assert stats['status'] == 0 and len(out) >= 854, stats
    assert fc.worst_overlap(out) > -1e-6


def main(argv):
    if argv[1] == 'control':
        return control(argv[2])
    upright_deg, overlap = 1e-5, 1e-6
    for flag in ('--upright-deg', '--overlap'):
        if flag in argv:
            index = argv.index(flag)
            value = float(argv[index + 1])
            del argv[index:index + 2]
            if flag == '--upright-deg':
                upright_deg = value
            else:
                overlap = value
    outdir = Path(argv[2]); outdir.mkdir(parents=True, exist_ok=True)
    starts = 0
    for path in argv[3:]:
        for n, sq in fr.layouts(path).items():
            if n >= 1000:
                continue
            side, q = fc.frame(sq)
            out, stats = refill(q, side, upright_deg=upright_deg)
            print('SOURCE', path, json.dumps(stats), flush=True)
            if len(out) <= n or stats['status'] != 0:
                continue
            target = min(len(out), 1000)
            out = out[:target]
            if fc.worst_overlap(out) < -overlap:
                print('DROP overlap', flush=True)
                continue
            tag = hashlib.sha256(path.encode()).hexdigest()[:8]
            dest = outdir / ('%d-cpatchfill-from%d-%s.csv' % (target, n, tag))
            fc.write_csv(dest, target, out)
            meta = dict(n=target, side=side, kind='held uprights with joint-candidate refill',
                        A=dict(source=[path, n], solver=stats, upright_deg=upright_deg, allowed_overlap=overlap))
            Path(str(dest) + '.json').write_text(json.dumps(meta))
            starts += 1
            print('START', dest, flush=True)
    print('refill starts', starts, flush=True)


if __name__ == '__main__':
    main(sys.argv)
