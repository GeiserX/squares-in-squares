#!/usr/bin/env python3
"""Is a board value a small quadratic surd?  f = (p + q sqrt(d)) / r

A design made of two chains with whole coefficients that has one chain without f (a C + b S = c) puts
cos t, sin t and f in the field of sqrt(a^2 + b^2 - c^2). So a value of this form says which field the
angle lives in, with no list of chains behind it. The rigid 45 degree blocks are the case d = 2.

The test needs no design, and its chance rate is known: a random number matches about
(number of d) * 4 Q * R^2 * precision / 2 times.

Usage: forensics_surd.py VALUES.tsv [VALUES.tsv ...] [--d 30] [--q 40] [--r 150]
VALUES.tsv is the file forensics_match.py writes (label, f, precision, kind, members).
"""
import sys, math, csv, argparse
import numpy as np


def squarefree(dmax):
    out = []
    for d in range(2, dmax + 1):
        if all(d % (k * k) for k in range(2, int(math.isqrt(d)) + 1)):
            out.append(d)
    return out


def surds(f, prec, ds, Q, R):
    q = np.arange(-Q, Q + 1); q = q[q != 0]
    out = []
    for d in ds:
        rt = math.sqrt(d)
        for r in range(1, R + 1):
            x = r * f - q * rt
            p = np.rint(x)
            hit = np.abs(x - p) <= prec * r
            for k in np.nonzero(hit)[0]:
                pp, qq = int(p[k]), int(q[k])
                if math.gcd(math.gcd(abs(pp), abs(qq)), r) != 1:
                    continue
                out.append((max(abs(pp), abs(qq), r), pp, qq, d, r, (pp + qq * rt) / r - f))
    out.sort()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('values', nargs='+'); ap.add_argument('--d', type=int, default=30)
    ap.add_argument('--q', type=int, default=40); ap.add_argument('--r', type=int, default=150)
    a = ap.parse_args()
    ds = squarefree(a.d)
    seen = set(); rows = []
    for path in a.values:
        for r in csv.DictReader(open(path), delimiter='\t'):
            key = (r['kind'], r['f'])
            if key in seen:
                continue
            seen.add(key); rows.append(r)
    tally = {}
    for r in rows:
        f = float(r['f']); prec = float(r['prec'])
        hits = surds(f, prec, ds, a.q, a.r)
        kind = r['kind']
        t = tally.setdefault(kind, [0, 0]); t[0] += 1; t[1] += bool(hits)
        if hits and kind != 'decoy':
            h, p, q, d, rr, off = hits[0]
            print('%-18s %.12f  (%d %+d sqrt(%d)) / %d   off %+.1e   %s%s' % (
                r['label'], f, p, q, d, rr, off, r['members'][:60], '   (+%d more)' % (len(hits) - 1) if len(hits) > 1 else ''))
    exp = len(ds) * 4 * a.q * a.r * a.r / 2
    print()
    for kind, (n, k) in sorted(tally.items()):
        print('%-10s %4d values, %3d with a surd' % (kind, n, k))
    print('expected by chance per value at precision 2e-10: %.4f' % (exp * 2e-10))


if __name__ == '__main__':
    main()
