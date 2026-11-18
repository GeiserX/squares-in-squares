#!/usr/bin/env python3
"""A third rectangle window replaces a plain block beside two opposite parts.

forensics_three.py CACHE.pkl DETAILS.csv OUT [--per-n 4] [--max-mesh 80]
                    [--slack 0.004] [--collide 0.65] [--fresh-start 0]
                    [--total 24] [--seconds 180]
forensics_three.py control CACHE_685.pkl

The cache is the trusted local table written by forensics_rect.py. The third
part occupies the bottom-left block and meets the first two along strips of
width F. Each part has positive excess over its plain grid block. The last
block stays plain. Every start has exactly n squares. Starts with overlaps
below --collide need the default fq quench before certification.
"""
import csv
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as fr


def build(a, b, c, m, wa, ha, f):
    side = m + f
    a, b = a.copy(), b.copy()
    a[:, 1] = side - a[:, 1]
    a[:, 2] = -a[:, 2]
    b[:, 0] = side - b[:, 0]
    b[:, 2] = -b[:, 2]
    wb, hb = m - wa, m - ha
    grid = np.array([(side - .5 - i, side - .5 - j, 0.)
                     for i in range(wb) for j in range(ha)]).reshape(-1, 3)
    gap = min(fc.worst_overlap(a, b), fc.worst_overlap(a, c), fc.worst_overlap(b, c))
    return np.r_[a, b, c, grid], gap


def part(saved, w, h, e, rank):
    f = saved['TF'][w, h, e, rank]
    g = int(saved['TI'][w, h, e, rank])
    key, side, q = saved['src'][g // 8]
    r = dict(fr.sym8(q, side))[g % 8]
    corners = fc.corners(r)
    use = np.flatnonzero(np.maximum(corners[:, :, 0].max(1) - w,
                                   corners[:, :, 1].max(1) - h) <= f + 1e-15)[:w * h + e]
    return r[use].copy(), dict(source=key, sym=g % 8, w=int(w), h=int(h), excess=int(e))


def control(cache):
    saved = pickle.load(open(cache, 'rb'))
    a, _ = part(saved, 9, 16, 4, 0)
    b, _ = part(saved, 17, 10, 5, 0)
    c = np.array([(i + .5, j + .5, 0.) for i in range(9) for j in range(10)])
    f = max(saved['TF'][9, 16, 4, 0], saved['TF'][17, 10, 5, 0])
    q, gap = build(a, b, c, 26, 9, 16, f)
    actual = fc.worst_overlap(q)
    print('control 685 count=%d side=%.12f cross=%.3g all=%.3g' % (len(q), 26 + f, gap, actual))
    assert len(q) == 685 and actual > -1e-9
    # A counted third window: the five-square construction with one border
    # has ten squares in a 3+sqrt(1/2) box, one above the 3x3 grid.
    f10 = math.sqrt(.5)
    s5 = 2 + f10
    third = [[x, y, 0.] for x in (.5, s5 - .5) for y in (.5, s5 - .5)]
    third += [[s5 / 2, s5 / 2, math.pi / 4]]
    third += [[3 + f10 - .5, j + .5, 0.] for j in range(3)]
    third += [[i + .5, 3 + f10 - .5, 0.] for i in range(2)]
    plain = np.array([(i + .5, j + .5, 0.) for i in range(3) for j in range(3)])
    q10, _ = build(plain, plain, np.array(third), 6, 3, 3, f10)
    gap10 = fc.worst_overlap(q10)
    print('counted third: n=%d side=%.12f gap=%.3g' % (len(q10), 6 + f10, gap10))
    assert len(q10) == 37 and gap10 > -1e-9
    c[-1, 1] += .6
    _, gap = build(a, b, c, 26, 9, 16, f)
    print('broken third part cross=%.3g' % gap)
    assert gap < -.1


def main(argv):
    if argv[1] == 'control':
        return control(argv[2])
    slack = float(fr.opt(argv, '--slack', '0.004'))
    collide = float(fr.opt(argv, '--collide', '0.65'))
    total = int(fr.opt(argv, '--total', '24'))
    seconds = float(fr.opt(argv, '--seconds', '180'))
    max_mesh = int(fr.opt(argv, '--max-mesh', '80'))
    per_n = int(fr.opt(argv, '--per-n', '4'))
    fresh_start = int(fr.opt(argv, '--fresh-start', '0'))
    cache, details, out = argv[1:4]
    stopped = Path(cache).parent / 'STOP_THREE'
    if stopped.exists():
        print('three disabled:', stopped.read_text().strip(), flush=True)
        return
    saved = pickle.load(open(cache, 'rb'))
    Path(out).mkdir(parents=True, exist_ok=True)
    tf, ti = saved['TF'], saved['TI']
    fb = tf[..., 0]
    targets = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    tried = kept = 0
    started = time.time()
    board_path = Path(cache).parents[2] / 'main-r17/gap-by-n.tsv'
    board = {int(r['n']): float(r['board_L']) for r in csv.DictReader(open(board_path), delimiter='\t')} if board_path.exists() else {}
    order = sorted(targets, key=lambda n: (-(targets[n] - board.get(n, targets[n])) / math.sqrt(n), n))
    nearest = -math.inf
    for n in order:
        if kept >= total or time.time() - started > seconds:
            break
        old = targets[n]
        m = math.isqrt(n)
        k = n - m * m
        if k < 3 or m < 3:
            continue
        ft = old - m + slack
        candidates = []
        for ec in range(1, min(k - 1, 9)):
            a = fb[1:m, 1:m, 1:k - ec]
            b = fb[m - 1:0:-1, m - 1:0:-1, k - ec - 1:0:-1]
            c = fb[1:m, m - 1:0:-1, ec]
            ok = (a < ft) & (b < ft) & (c[:, :, None] < ft)
            for wi, hi, ei in zip(*np.nonzero(ok)):
                wa, ha, ea = wi + 1, hi + 1, ei + 1
                wb, hb, eb = m - wa, m - ha, k - ea - ec
                for ra in range(min(2, saved['keep'])):
                    for rb in range(min(2, saved['keep'])):
                        for rc in range(min(2, saved['keep'])):
                            fa, fb1, fc1 = tf[wa, ha, ea, ra], tf[wb, hb, eb, rb], tf[wa, hb, ec, rc]
                            f = max(fa, fb1, fc1)
                            if not f < ft or abs(f - (old - m)) < 2e-8:
                                continue
                            if max(ti[wa, ha, ea, ra], ti[wb, hb, eb, rb], ti[wa, hb, ec, rc]) // 8 < fresh_start:
                                continue
                            candidates.append((f, wa, ha, ea, eb, ec, ra, rb, rc))
        sides = set()
        for f, wa, ha, ea, eb, ec, ra, rb, rc in sorted(candidates)[:max_mesh]:
            wb, hb = m - wa, m - ha
            a, ma = part(saved, wa, ha, ea, ra)
            b, mb = part(saved, wb, hb, eb, rb)
            c, mc = part(saved, wa, hb, ec, rc)
            q, gap = build(a, b, c, m, wa, ha, f)
            tried += 1
            nearest = max(nearest, gap)
            if len(q) != n or gap < -collide:
                continue
            sidekey = round(m + f, 9)
            if sidekey in sides:
                continue
            sides.add(sidekey)
            tag = 'c3' if gap < -1e-9 else 'p3'
            path = '%s/%d-%s-%dx%d-%.9f.csv' % (out, n, tag, wa, ha, m + f)
            fc.write_csv(path, n, q)
            with open(path + '.json', 'w') as h:
                json.dump(dict(n=n, side=m + f, A=ma, B=mb, C=mc), h, default=lambda v: v.item())
            print('START n=%d side=%.12f margin=%+.3e gap=%.3g %s' % (n, m + f, m + f - old, gap, path), flush=True)
            kept += 1
            if len(sides) >= per_n or kept >= total:
                break
    print('three meshes=%d starts=%d nearest_cross_gap=%.6g seconds=%.1f' % (tried, kept, nearest, time.time() - started), flush=True)


if __name__ == '__main__':
    main(sys.argv[:])
