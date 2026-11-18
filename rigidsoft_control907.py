#!/usr/bin/env python3
"""Undo the middle fault of held 907 and test extra-inside recovery.

Usage: rigidsoft_control907.py WORK FQ FIRST.csv MIDDLE.csv HELD.csv

FIRST precedes TL13:26. MIDDLE follows it. HELD also has TL15:24.
Run on one worker. WORK/deadline bounds all quenches, including polish.
The plain TL15:24 control runs first. The inverse must then quench to a
different layout before fault2 may try to recover the held side.
"""
import csv
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from scipy.optimize import linear_sum_assignment

import rigidsoft as RS
import rigidsoft_band as RB
import rigidsoft_fault2 as F2


def write_csv(path, X):
    with open(path, 'w', newline='') as h:
        w = csv.writer(h)
        w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for q, (x, y, angle) in enumerate(X):
            w.writerow([907, q, repr(float(x)), repr(float(y)),
                        repr(math.radians(float(angle)))])


def match(A, B):
    """Map template indices to relaxed indices, with a bounded displacement."""
    d = np.linalg.norm(A[:, None, :2] - B[None, :, :2], axis=2)
    tilted_a = np.abs(A[:, 2]) >= 3
    tilted_b = np.abs(B[:, 2]) >= 3
    cost = d + 10 * (tilted_a[:, None] != tilted_b[None, :])
    rows, cols = linear_sum_assignment(cost)
    assert np.array_equal(rows, np.arange(len(A)))
    assert np.array_equal(tilted_a, tilted_b[cols]), 'square type changed'
    worst = float(d[rows, cols].max())
    assert worst < 0.35, ('ambiguous reference match', worst)
    return cols, worst


def inverse_middle(s, held, first, middle):
    """Reverse TL13:26 while retaining the later TL15:24 extra squares.

    Reference faults identify the transferred teeth. Assignment matches those
    identities through relaxation and the later fault. All current band squares
    move back, including the later extras, rather than just the original band.
    """
    a = RB.fault(RS.side(first), first, 13, 26, 'TL')
    b = RB.fault(RS.side(middle), middle, 15, 24, 'TL')
    assert a is not None and b is not None, 'reference fault unavailable'
    p, da = match(a[0], middle)
    q, db = match(b[0], held)
    ids = q[p]
    _, idx, row, _, _, full = RB.read_teeth(s, held)
    extras = [r for r in range(13, 26) if int((row == r).sum()) > full]
    assert extras == [14, 24], ('later extras missing', extras)
    out = held.copy()
    band = idx[(row >= 13) & (row < 26)]
    out[band, :2] += [0.5, -0.5]
    ends = idx[(row == 12) | (row == 26)]
    out[ends, :2] += [-0.15 / math.sqrt(2), 0.15 / math.sqrt(2)]
    changed = np.linalg.norm(a[0][:, :2] - first[:, :2], axis=1) > 0.2
    teeth = np.where((np.abs(first[:, 2]) < 3) & changed)[0]
    assert len(teeth) >= 2
    out[ids[teeth]] = first[teeth]
    _, _, newrow, _, _, newfull = RB.read_teeth(s, out)
    assert int((newrow == 12).sum()) == newfull
    assert int((newrow == 26).sum()) == newfull
    remaining = [r for r in range(13, 26) if int((newrow == r).sum()) > newfull]
    assert remaining == [14, 24], ('inverse lost later extras', remaining)
    return out, {'match_middle': da, 'match_held': db,
                 'restored_teeth': len(teeth), 'extra_inside': remaining}


def main():
    work, fq, first_csv, middle_csv, held_csv = sys.argv[1:]
    work = Path(work)
    (work / 'tmp').mkdir(parents=True, exist_ok=True)
    deadline = float((work / 'deadline').read_text())
    result = {'passed': False, 'measurements': []}

    def record(**row):
        result['measurements'].append(row)
        print(json.dumps(row), flush=True)
        (work / 'measurement.json').write_text(json.dumps(result, indent=2) + '\n')

    def quench(tag, s, X, fs):
        remaining = deadline - time.time()
        assert remaining > 1, 'common deadline reached'
        side, Y, seconds = RS.fq(fq, str(work / 'tmp'), s, X,
                                  RS.FLAGSETS[fs], timeout=min(150, remaining))
        record(tag=tag, settings=fs, side=side, seconds=seconds)
        if Y is not None:
            write_csv(work / (tag + '.csv'), Y)
        return side, Y

    try:
        sm, middle = RS.normalize(RS.load(middle_csv, {907})[907])
        sh, held = RS.normalize(RS.load(held_csv, {907})[907])
        _, first = RS.normalize(RS.load(first_csv, {907})[907])
        result['held_side'] = sh
        plain = RB.fault(sm, middle, 15, 24, 'TL')
        assert plain is not None and plain[0] is not None, 'plain start missing'
        side, Y = quench('plain-positive', sm + 0.003, plain[0], 'alm0')
        if side is not None:
            sp, Yp = quench('plain-positive-polish', side, Y, 'pol')
            if sp is not None and sp < side:
                side = sp
        assert side is not None and abs(side - sh) < 1e-6, 'plain control RED'
        record(tag='plain-positive-verdict', passed=True, info=plain[1])

        inverse, info = inverse_middle(sh, held, first, middle)
        write_csv(work / 'inverse-start.csv', inverse)
        record(tag='inverse-topology', **info)
        si, inverse = quench('inverse-quenched', sh, inverse, 'alm0')
        assert si is not None and si > sh + 1e-6, 'inverse is not a distinct higher layout'
        _, _, row, _, _, full = RB.read_teeth(si, inverse)
        extras = [r for r in range(13, 26) if int((row == r).sum()) > full]
        assert extras == [14, 24], ('inverse quench changed later extras', extras)
        got = F2.fault2(si, inverse, 907, 13, 26, 'TL', rm=0.2)
        record(tag='extra-inside-start', feasible=got is not None and got[0] is not None,
               info=None if got is None else got[1])
        assert got is not None and got[0] is not None, 'extra-inside count failed'
        write_csv(work / 'recovery-start.csv', got[0])
        best = None
        for fs in ('alm0', 'round31', 'round32', 'round2', 'round3', 'round'):
            side, Y = quench('recovery-' + fs, si, got[0], fs)
            if side is not None and (best is None or side < best[0]):
                best = (side, Y)
        if best is not None:
            side, Y = quench('recovery-polish', best[0], best[1], 'pol')
            if side is not None and side < best[0]:
                best = (side, Y)
        result['recovered_side'] = None if best is None else best[0]
        assert best is not None and abs(best[0] - sh) < 1e-6, 'held-side recovery RED'
        result['passed'] = True
    except AssertionError as e:
        result['failure'] = str(e)
    (work / 'measurement.json').write_text(json.dumps(result, indent=2) + '\n')
    print('HELD-SIDE CONTROL', 'GREEN' if result['passed'] else 'RED',
          result.get('failure', ''), flush=True)


if __name__ == '__main__':
    main()
