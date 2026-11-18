#!/usr/bin/env python3
"""quench: list near files whose bounding side sits within WINDOW of the bar.

Usage: quench_near.py BAR.tsv WINDOW OUT.tsv NEARDIR [NEARDIR ...]
  The side is the bounding square of the rows as written (no overlap check:
  a raw near file may overlap, and fq is what resolves it).
  OUT.tsv: side_margin (side - bar side), n, side, path, sorted by margin.
"""
import csv, glob, math, os, sys

import numpy as np


def side(path):
    xs, ys, a = [], [], []
    with open(path, newline='') as h:
        for r in csv.DictReader(h):
            xs.append(float(r['x'])); ys.append(float(r['y'])); a.append(float(r['angle']))
            n = int(r['n'])
    x, y, a = np.array(xs), np.array(ys), np.array(a)
    loc = np.array([(-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)])
    c, s = np.cos(a), np.sin(a)
    CX = x[:, None] + c[:, None] * loc[:, 0] - s[:, None] * loc[:, 1]
    CY = y[:, None] + s[:, None] * loc[:, 0] + c[:, None] * loc[:, 1]
    return n, len(xs), max(CX.max() - CX.min(), CY.max() - CY.min())


def main():
    bar_tsv, win, out, dirs = sys.argv[1], float(sys.argv[2]), sys.argv[3], sys.argv[4:]
    bar = {int(r['n']): float(r['side']) for r in csv.DictReader(open(bar_tsv), delimiter='\t')}
    rows = []
    for d in dirs:
        for p in glob.glob(d + '/*.csv'):
            try:
                n, k, s = side(p)
            except (ValueError, KeyError, UnboundLocalError):
                continue
            if k != n:
                continue
            m = s - bar[n]
            if m < win:
                rows.append((m, n, s, p))
    rows.sort()
    with open(out, 'w') as h:
        h.write('side_margin\tn\tside\tpath\n')
        for m, n, s, p in rows:
            h.write('%.6e\t%d\t%r\t%s\n' % (m, n, s, p))
    print(len(rows), 'near files within', win)


if __name__ == '__main__':
    main()
