#!/usr/bin/env python3
"""Assemble a full Kaggle submission from one or more drive.py state dirs.

Usage: assemble.py <out.csv> <state> [<state> ...]
Per n, the lowest stored metric score across the states wins. Re-score the
output with score.py before submitting.
"""
import csv, sys
from pathlib import Path

out, states = sys.argv[1], [Path(p) for p in sys.argv[2:]]
idx, total = 0, 0.0
with open(out, 'w', newline='') as h:
    w = csv.writer(h, lineterminator='\n')
    w.writerow(['id', 'n', 'square_id', 'x', 'y', 'angle'])
    for n in range(1, 1001):
        cands = [(float((s / 'best' / f'{n}.score').read_text()), s) for s in states
                 if (s / 'best' / f'{n}.score').exists()]
        if not cands:
            continue
        sc, s = min(cands, key=lambda c: c[0])
        total += sc
        for r in csv.DictReader(open(s / 'best' / f'{n}.csv')):
            w.writerow([idx, r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            idx += 1
print('rows', idx, 'stored-score sum', total)
