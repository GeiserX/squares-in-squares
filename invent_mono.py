#!/usr/bin/env python3
"""The monotone check across the live take dirs: a layout of n + j with j squares removed is a layout of n.

Usage: invent_mono.py DETAILS.csv SCRATCH OUTDIR [--write] [--top J]
  DETAILS.csv  the gate details of the held file (n, L, score)
  SCRATCH      the scratch dir with the take-*-r17 dirs
  OUTDIR       with --write: one csv for each n that a larger n beats (the layout of n + j less j squares)

Each lane takes the lowest file of its own n. No lane looks at n + 1. When a lane brings n + j below the best side
of n, the same file with j squares removed is a legal layout of n at that side. This tool lists every such n over the
held file and every live take, and writes the start files. The squares it removes are the ones nearest the centre of
the box: any square will do, and the quench that follows may use the room.

Our own code. It reads take.tsv and the per-n csv of every take dir (x, y, angle rows of the lane's format).
"""
import csv, glob, math, os, sys

a = [x for x in sys.argv[1:] if not x.startswith('--')]
details, S, out = a[0], a[1], a[2]
write = '--write' in sys.argv
top = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 4

best = {}
for r in csv.DictReader(open(details)):
    best[int(r['n'])] = (float(r['L']), 'held', None)
for d in sorted(glob.glob(S + '/take-*-r17')):
    p = d + '/take.tsv'
    if not os.path.exists(p): continue
    for r in csv.DictReader(open(p), delimiter='\t'):
        try: n = int(r['n']); new = float(r['new'])
        except Exception: continue
        f = '%s/%d.csv' % (d, n)
        if not os.path.exists(f): continue
        L = (new + 1) * math.sqrt(n)
        if L < best[n][0]: best[n] = (L, os.path.basename(d), f)

rows = []
for n in sorted(best):
    for j in range(1, top + 1):
        if n + j not in best: break
        gain = best[n][0] - best[n + j][0]
        if gain > 1e-9: rows.append((n, j, best[n][0], best[n + j][0], gain / math.sqrt(n), best[n][1], best[n + j][1], best[n + j][2]))
print('n\tj\tbest_side_n\tside_n_plus_j\tgain_of_score\tlane_n\tlane_n_plus_j')
for r in rows: print('%d\t%d\t%.12f\t%.12f\t%.3e\t%s\t%s' % r[:7])
print('# %d (n, j) with a larger n below the best side of n; n checked: %d' % (len(rows), len(best)))
if write:
    os.makedirs(out, exist_ok=True)
    done = set()
    for n, j, L0, L1, g, l0, l1, f in sorted(rows, key=lambda r: -r[4]):
        if n in done or f is None: continue
        R = list(csv.DictReader(open(f)))
        key = lambda r: (float(str(r['x']).lstrip('s')) - L1 / 2) ** 2 + (float(str(r['y']).lstrip('s')) - L1 / 2) ** 2
        cx = sum(float(str(r['x']).lstrip('s')) for r in R) / len(R); cy = sum(float(str(r['y']).lstrip('s')) for r in R) / len(R)
        key = lambda r: (float(str(r['x']).lstrip('s')) - cx) ** 2 + (float(str(r['y']).lstrip('s')) - cy) ** 2
        keep = sorted(R, key=key)[j:]
        with open('%s/%d-from%d.csv' % (out, n, n + j), 'w', newline='') as h:
            w = csv.DictWriter(h, fieldnames=R[0].keys()); w.writeheader()
            for r in keep: w.writerow(r)
        done.add(n)
    print('# wrote %d start files to %s' % (len(done), out))
