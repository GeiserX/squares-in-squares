#!/usr/bin/env python3
"""Per-n best of several scored submissions.

Usage: merge.py <out.csv> <a.csv> <a.tsv> [<b.csv> <b.tsv> ...]

Each csv comes with the per-n tsv score.py wrote for it. For every n the
feasible packing with the lowest score wins (earlier inputs win ties). The
output is a full Kaggle submission; re-score it before submitting.
"""
import csv, sys
from collections import defaultdict

out, pairs = sys.argv[1], sys.argv[2:]
best = {}  # n -> (score, src index)
for i in range(0, len(pairs), 2):
    for r in csv.DictReader(open(pairs[i + 1]), delimiter='\t'):
        if r['reason'] != 'ok':
            continue
        n, s = int(r['n']), float(r['score'])
        if n not in best or s < best[n][0]:
            best[n] = (s, i)
rows = defaultdict(list)
for i in range(0, len(pairs), 2):
    want = {n for n, (_, j) in best.items() if j == i}
    for r in csv.DictReader(open(pairs[i])):
        if int(r['n']) in want:
            rows[int(r['n'])].append(r)
idx = 0
with open(out, 'w', newline='') as h:
    w = csv.writer(h, lineterminator='\n')
    w.writerow(['id', 'n', 'square_id', 'x', 'y', 'angle'])
    for n in range(1, 1001):
        for r in sorted(rows.get(n, []), key=lambda r: int(r['square_id'])):
            w.writerow([idx, n, r['square_id'], r['x'], r['y'], r['angle']])
            idx += 1
src = defaultdict(int)
for n, (_, j) in best.items():
    src[pairs[j]] += 1
print('rows', idx, 'n covered', len(best), dict(src), 'sum', sum(s for s, _ in best.values()))
