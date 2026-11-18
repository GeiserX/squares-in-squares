#!/usr/bin/env python3
"""quench: the per-n bar a quench result must beat.

Usage: quench_bar.py DETAILS.csv OUT.tsv [TAKE.tsv ...]
  DETAILS.csv  the gate's details.csv of the base file (n, L, score, ...)
  TAKE.tsv     take.tsv files whose rows lower the bar (new score per n)

The bar is strict: every take row lowers it, clean or not. A result that
beats this bar also beats the clean bar. OUT.tsv has n, score, side, origin.
"""
import csv, math, sys

csv.field_size_limit(1 << 30)


def main():
    det, out, takes = sys.argv[1], sys.argv[2], sys.argv[3:]
    bar = {}
    for r in csv.DictReader(open(det)):
        n = int(r['n']); bar[n] = (float(r['score']), 'base')
    for t in takes:
        try:
            rows = list(csv.DictReader(open(t), delimiter='\t'))
        except OSError:
            continue
        for r in rows:
            try:
                n, s = int(r['n']), float(r['new'])
            except (KeyError, TypeError, ValueError):
                continue  # a take being written or in another layout: skip the row
            if n in bar and s < bar[n][0]:
                bar[n] = (s, t)
    with open(out + '.tmp', 'w') as h:
        h.write('n\tscore\tside\torigin\n')
        for n in sorted(bar):
            s, o = bar[n]
            h.write('%d\t%r\t%r\t%s\n' % (n, s, (s + 1) * math.sqrt(n), o))
    import os
    os.replace(out + '.tmp', out)
    print('bar', len(bar), 'rows; lowered by takes:', sum(1 for v in bar.values() if v[1] != 'base'))


if __name__ == '__main__':
    main()
