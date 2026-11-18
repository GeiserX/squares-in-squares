#!/usr/bin/env python3
"""bestof.py N TAG: print the packing of N with the smallest side among starts/N-TAG.csv and run/N-TAG/raw/*.csv."""
import glob, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import methods_lp as mlp


def best(n, tag):
    b = None
    for p in ['%s/starts/%d-%s.csv' % (HERE, n, tag)] + sorted(glob.glob('%s/run/%d-%s/raw/%d-*.csv' % (HERE, n, tag, n))):
        try:
            P = mlp.load(p, {n})[n]
            L = mlp.side(P) if len(P) == n else None
        except Exception:
            L = None
        if L is not None and (b is None or L < b[0]):
            b = (L, p)
    return b


if __name__ == '__main__':
    print(best(int(sys.argv[1]), sys.argv[2])[1])
