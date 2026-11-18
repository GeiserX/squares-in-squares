#!/usr/bin/env python3
"""The far-end loss of a two-arm layout, read from its last flush stacks.

  farend_read.py HELD.csv PARTS.tsv N [N ...]

For each N the layout is cut with modules.cut. Each far zone is then measured by the exact evaluator of
zone_search.py at the layout's own f: the length is the smallest position of the last flush stack at which the
zone's squares still clear it, and the loss is c cos t * length - count. PARTS.tsv is the table of
invent_parts.py (results/round17-invent-parts.tsv), which reads the same loss with no cut and no stack: it counts
centres beyond a line near the middle of the wall. The two readings share no code. The control passes when they
agree to 0.05 squares on every far end of every N given.

Our own code. Reads packings as data only (run with python -I).
"""
import csv, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M
import zone_search as Z


def far_ends(sq, n):
    """-> [(arm, c, f, count, length, loss, loss of the cut)] or a reason"""
    d, why = M.cut(sq, n)
    if d is None: return why
    out = []
    for q in M.modules_of(d, 'held', '', 'h'):
        if q['kind'] != 'far': continue
        c, f = q['c'], d['f']
        mod = dict(c=c, lean=q['lean'], miss=q['miss'], rig=[])
        P = np.asarray(q['P'], float)
        # the exact length: bisect the stack position from the found one (the cut's lam) plus a hair
        hi = q['len0'] + 1e-6
        S, mode = M.far_state(mod, f, P, hi)
        le = Z.length(P, c, f, hi, q['lean']) if not q['miss'] else None
        ln = le[0] if le is not None else q['len0']
        out.append((q['arm'], c, f, q['count'], ln, Z.loss_of(c, f, q['count'], ln), q['loss0'], len(q['miss'])))
    return out


def main():
    heldp, partsp = sys.argv[1:3]
    ns = [int(x) for x in sys.argv[3:]]
    lay = M.read_layouts(heldp)
    parts = {}
    for r in csv.DictReader(open(partsp), delimiter='\t'):
        try: parts[int(r['n'])] = r
        except ValueError: pass
    worst = 0.0; rows = 0
    print('n\tarm\tc\tf\tcount\tlength\tloss_here\tloss_of_cut\tmiss\tloss_invent\tdiff')
    for n in ns:
        fe = far_ends(lay[n], n)
        if isinstance(fe, str):
            print('%d\tnot read: %s' % (n, fe)); continue
        r = parts.get(n)
        inv = sorted([float(r['arm1_far']), float(r['arm2_far'])]) if r and r['arm1_far'] else []
        for arm, c, f, cnt, ln, loss, loss0, miss in fe:
            near = min(inv, key=lambda v: abs(v - loss)) if inv else float('nan')
            if inv: worst = max(worst, abs(loss - near)); rows += 1
            print('%d\t%d\t%d\t%.4f\t%d\t%.6f\t%.3f\t%.3f\t%d\t%.3f\t%+.3f' % (n, arm, c, f, cnt, ln, loss, loss0, miss, near, loss - near))
    print('# far ends compared: %d, largest difference %.3f squares, control %s' % (rows, worst, 'PASS' if rows and worst <= 0.05 else 'FAIL'))
    return 0 if rows and worst <= 0.05 else 1


if __name__ == '__main__':
    sys.exit(main())
