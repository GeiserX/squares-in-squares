#!/usr/bin/env python3
"""Try one upright at exact joint-contact centres in a packing.

forensics_jointgrow.py control HELD.csv
forensics_jointgrow.py scan OUT SOURCE.csv [...]

Inputs and output angles are radians. The joint generator uses degrees.
Only starts with overlap depth at most 1e-6 are written. They require a
quench and floatsafe before they count as packing results.
"""
import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as fr
import forensics_upright as fu


def candidates(q, side, tol=1e-6):
    deg = np.degrees(q[:, 2]) % 90
    deg = np.where(deg > 45, deg - 90, deg)
    tilted = np.abs(deg) > 1e-5
    t = np.c_[q[tilted, :2], deg[tilted]]
    points = fu.joint_candidates(side, t)
    corners = fc.corners(q)
    tree = cKDTree(q[:, :2])
    accepted = []
    for x, y, _ in points:
        r = np.array([[x, y, 0.]])
        kr = fc.corners(r)[0]
        gap = math.inf
        neighbors = tree.query_ball_point([x, y], 1.5)
        neighbors.sort(key=lambda j: bool(tilted[j]))
        for j in neighbors:
            gap = min(gap, fc.gap(corners[j], kr))
            if gap < -tol:
                break
        if gap >= -tol:
            accepted.append((float(gap), r[0]))
    return sorted(accepted, key=lambda row: -row[0])


def control(path):
    sq = fr.layouts(path)[854]
    side, q = fc.frame(sq)
    near = np.hypot(q[:, 0] - 12.2202069629, q[:, 1] - 12.2196213919)
    drop = int(np.argmin(near))
    host = np.delete(q, drop, axis=0)
    found = candidates(host, side)
    restored = [(g, r) for g, r in found if np.hypot(*(r[:2] - q[drop, :2])) < .01]
    print('CONTROL removed upright %d: %d insertion candidates, %d restore its cavity' %
          (drop, len(found), len(restored)), flush=True)
    assert restored
    gap = fc.worst_overlap(q, np.array([restored[0][1]]))
    print('CONTROL occupied cavity overlap %.9g' % gap, flush=True)
    assert gap < -.5


def main(argv):
    if argv[1] == 'control':
        return control(argv[2])
    out = Path(argv[2]); out.mkdir(parents=True, exist_ok=True)
    total = 0
    for path in argv[3:]:
        for n, sq in fr.layouts(path).items():
            if n >= 1000:
                continue
            side, q = fc.frame(sq)
            found = candidates(q, side)
            print('source n=%d side=%.12f insertion candidates=%d %s' %
                  (n, side, len(found), path), flush=True)
            if not found:
                continue
            gap, point = found[0]
            name = '%d-cjointgrow-from%d-%s.csv' % (n + 1, n, hashlib.sha256(path.encode()).hexdigest()[:8])
            dest = out / name
            fc.write_csv(dest, n + 1, np.r_[q, point[None, :]])
            meta = dict(kind='joint-contact upright insertion', n=n+1, side=side,
                        A=dict(source=[path,n], method='one upright at a joint of two expanded tilted-square boundaries', gap=gap))
            Path(str(dest)+'.json').write_text(json.dumps(meta))
            print('START target=%d side=%.12f overlap=%+.3e %s' % (n+1,side,gap,dest), flush=True)
            total += 1
    print('insertion starts', total, flush=True)


if __name__ == '__main__':
    main(sys.argv)
