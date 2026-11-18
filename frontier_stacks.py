#!/usr/bin/env python3
"""Stacks of a layout: the rigid columns its tilted arms are made of, and how each one is flush.

  frontier_stacks.py SUB.csv TARGETS.tsv OUT.tsv [N ...]

A stack is a chain of tilted squares set face to face (the next centre is one unit along the square's
own axis, to 0.02, and the tilt agrees to 0.3 degree). An arm is a row of stacks that slide along each
other. A stack of c squares at tilt t spans c cos t + sin t across the arm; it is "flush" when that span
is c - 1 + f, the room that c - 1 upright columns and the whole slack f of the side m + f leave.
Per n the table gives: tilted squares, squares in stacks of 3 or more, the two most common stack
lengths c1, c2 with their square counts and median tilts, the flush error of each (span - (c - 1 + f)),
the waste of the layout in squares (side^2 - n), the board's waste, and the difference
(the "deficit": how many squares of area the board saves at this n).
Our own code; reads data only. Run with python -I.
"""
import csv, math, os, sys, collections
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
from frontier_read import load, normal


def stacks(T):
    """-> list of index lists; each tilted square belongs to its longest chain."""
    n = len(T); th = np.radians(T[:, 2])
    best = [None] * n
    for axis in (0, 1):
        ux = np.cos(th) if axis == 0 else -np.sin(th)
        uy = np.sin(th) if axis == 0 else np.cos(th)
        nxt = [-1] * n; prv = [-1] * n
        for i in range(n):
            dx = T[:, 0] - (T[i, 0] + ux[i]); dy = T[:, 1] - (T[i, 1] + uy[i])
            j = int(np.argmin(dx * dx + dy * dy))
            if j != i and dx[j] ** 2 + dy[j] ** 2 < 0.02 ** 2 and abs(T[j, 2] - T[i, 2]) < 0.3:
                nxt[i] = j; prv[j] = i
        for i in range(n):
            if prv[i] == -1:
                ch = [i]
                while nxt[ch[-1]] != -1 and len(ch) < n: ch.append(nxt[ch[-1]])
                for q in ch:
                    if best[q] is None or len(ch) > len(best[q]): best[q] = ch
    seen = set(); out = []
    for b in best:
        if b is not None and id(b) not in seen:
            seen.add(id(b)); out.append(b)
    return out, best


def describe(sq, m):
    s, A = normal(sq)
    f = s - m
    T = A[np.abs(A[:, 2]) > 1e-4]
    if not len(T): return None
    out, best = stacks(T)
    by = collections.defaultdict(list)
    for i, b in enumerate(best):
        if b is not None and len(b) >= 3: by[len(b)].append(abs(T[i, 2]))
    top = sorted(by.items(), key=lambda kv: -len(kv[1]))[:2]
    cells = []
    for c, tl in top:
        t = math.radians(float(np.median(tl)))
        cells += [c, len(tl), '%.2f' % math.degrees(t), '%.4f' % (c * math.cos(t) + math.sin(t) - (c - 1 + f))]
    cells += [''] * (8 - len(cells))
    return s, len(T), sum(len(v) for v in by.values()), cells


def main():
    sub, targets, out = sys.argv[1:4]
    want = set(map(int, sys.argv[4:]))
    P = load(sub)
    Tg = {int(r['n']): r for r in csv.DictReader(open(targets), delimiter='\t')}
    with open(out, 'w') as h:
        h.write('n\tm\tk\tours_f\tboard_f\tshort\ttilted\tin_stacks\tc1\tsq1\ttilt1\tflush1\tc2\tsq2\ttilt2\tflush2\twaste\tboard_waste\tdeficit\n')
        for n in sorted(P):
            if n < 300 or (want and n not in want): continue
            m = math.isqrt(n - 1); k = n - m * m
            if k > m + 8: continue
            d = describe(P[n], m)
            if d is None: continue
            s, nt, ins, cells = d
            b = float(Tg[n]['target_L'])
            h.write('\t'.join(map(str, [n, m, k, '%.6f' % (s - m), '%.6f' % (b - m), Tg[n]['short'], nt, ins] + cells +
                                        ['%.3f' % (s * s - n), '%.3f' % (b * b - n), '%.3f' % (s * s - b * b)])) + '\n')


if __name__ == '__main__':
    main()
