#!/usr/bin/env python3
"""rigidsoft_lone.py FILE.csv N [MAXROWS]: the rows of the block of N that stand against their neighbours: every band of rows of
one sense that is at most MAXROWS (3) rows long and has a band of the other sense on both sides, or at one end of
the block. Prints the --from list for rigidsoft_hop.py --moves flip (r5,r6,..) and, on stderr, the senses."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rigidsoft as RS, rigidsoft_band as BD
f, n = sys.argv[1], int(sys.argv[2]); mx = int(sys.argv[3]) if len(sys.argv) > 3 else 3
s, X = RS.normalize(RS.load(f, {n})[n]); idx, row, dev = BD.main_block(X); nr = int(row.max()) + 1
d = [float(dev[row == r].mean()) if (row == r).any() else 0.0 for r in range(nr)]
sg = ''.join('+' if v > 0.02 else '-' if v < -0.02 else '0' for v in d)
out = []; r = 0
while r < nr:
    e = r
    while e + 1 < nr and sg[e + 1] == sg[r]:
        e += 1
    if e - r + 1 <= mx and not (r == 0 and e == nr - 1):
        out += ['r%d' % k for k in range(max(r - 1, 0), e + 1)]
    r = e + 1
print(','.join(dict.fromkeys(out)))
print('%.9f %s' % (s, sg), file=sys.stderr)
