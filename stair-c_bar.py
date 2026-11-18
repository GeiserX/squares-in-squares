#!/usr/bin/env python3
"""The rows of the generator next to the bar: the lowest side that held or any live take dir has for the same n.

  stair-c_bar.py Q.tsv [Q.tsv ...] [--details DETAILS.csv] [--takes GLOB]

Q.tsv is a queue table of `modules.py queue`. For the lowest row of each n the tool prints the predicted side less held,
the bar less held with the take that sets it, and the margin (the row less the bar). The side of a take row is
(1 + score) sqrt(n). The builds of two 9-arms end 0.0002 to 0.0064 of side below their row, so a margin up to 0.003 is
worth a build. The rows are sorted by margin, the nearest first.
"""
import csv, glob, math, os, sys

S = '$SCRATCH/bounties-squares'


def opt(a, name, default):
    return a[a.index(name) + 1] if name in a else default


def main():
    a = sys.argv[1:]
    if not a or a[0].startswith('--'): print(__doc__); return 1
    details = opt(a, '--details', S + '/gate/cand-round16-1112a/details.csv')
    takes = opt(a, '--takes', S + '/take-*-r17')
    files = []
    i = 0
    while i < len(a):
        if a[i] in ('--details', '--takes'): i += 2; continue
        files.append(a[i]); i += 1
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    bar = {}
    for d in sorted(glob.glob(takes)):
        p = d + '/take.tsv'
        if not os.path.exists(p): continue
        for line in open(p):
            c = line.rstrip('\n').split('\t')
            try: n = int(c[0]); s = float(c[2])
            except (ValueError, IndexError): continue
            L = (1 + s) * math.sqrt(n)
            if n not in bar or L < bar[n][0]: bar[n] = (L, os.path.basename(d))
    best = {}
    for p in files:
        for r in csv.DictReader(open(p), delimiter='\t'):
            try: n = int(r['n']); d = float(r['predicted_minus_held'])
            except (ValueError, KeyError, TypeError): continue
            if n not in best or d < best[n][0]: best[n] = (d, r)
    below = lambda n: min(0.0, bar[n][0] - held[n]) if n in bar else 0.0
    for n in sorted(best, key=lambda n: best[n][0] - below(n)):
        d, r = best[n]; bd = below(n)
        print('%d row %+.6f bar %+.6f (%s) margin %+.6f  %s %s %s %s,%s' % (n, d, bd, bar[n][1] if bd < 0 else 'held', d - bd, r['corner'], r['far1'],
              r['far2'], r['stacks1'], r['stacks2']))
    return 0


if __name__ == '__main__':
    sys.exit(main() or 0)
