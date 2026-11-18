#!/usr/bin/env python3
"""The border step, as a scan and a builder.

A packing of n squares in side s gives one of n + 2*floor(s) + 1 squares in side s + 1: add a row of
floor(s + 1) upright squares above it and a column of floor(s) upright squares to its right. Deleting a
square gives L(n - 1) <= L(n). This closes the held sides under both rules and builds every n the border
rule improves.

  literature_border.py HELD.csv HELD_DETAILS.csv OUT_DIR [TAKE_DIR ...]

HELD.csv is the submitted file. TAKE_DIR are take dirs whose per-n files replace the held n first (so a
win of this round can seed a border step). Writes OUT_DIR/<n>.csv and appends to OUT_DIR/take.tsv.
Each result goes through floatsafe and is kept only when it scores below the held score by more than 1e-10.
Run it with python -I.
"""
import csv, math, os, sys
from pathlib import Path

LANE = str(Path(__file__).resolve().parent)
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402

GAP = 3e-11  # between the old packing and the new row and column; floatsafe wants 2.2e-11


def bbox(rows):
    xs, ys = [], []
    for r in rows:
        x, y, a = float(r['x']), float(r['y']), float(r['angle'])
        c, s = math.cos(a), math.sin(a)
        for u, v in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
            xs.append(x + c * u - s * v); ys.append(y + s * u + c * v)
    return min(xs), min(ys), max(xs), max(ys)


def border(rows):
    """rows of n squares -> rows of n + 2*floor(s) + 1 squares in side s + 1 + GAP."""
    x0, y0, x1, y1 = bbox(rows)
    s = max(x1 - x0, y1 - y0)
    top, right = math.floor(s + 1), math.floor(s)
    out = [(repr(float(r['x']) - x0), repr(float(r['y']) - y0), r['angle']) for r in rows]
    S = s + 1 + GAP
    for i in range(top):      # row above, spread over the new side
        out.append((repr(0.5 + i * (S - 1) / (top - 1)), repr(s + GAP + 0.5), '0.0'))
    for i in range(right):    # column to the right, below the row
        out.append((repr(s + GAP + 0.5), repr(0.5 + i * (s - 1) / (right - 1)), '0.0'))
    return out


def main():
    held_csv, details, out, takes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    os.makedirs(out, exist_ok=True)
    score = {int(r['n']): float(r['score']) for r in csv.DictReader(open(details))}
    P = {}
    for r in csv.DictReader(open(held_csv)):
        P.setdefault(int(r['n']), []).append(r)
    new = {}
    for t in takes:
        for r in csv.DictReader(open(os.path.join(t, 'take.tsv')), delimiter='\t'):
            n = int(r['n'])
            if float(r['new']) < new.get(n, score[n]):
                new[n] = float(r['new']); P[n] = list(csv.DictReader(open(os.path.join(t, '%d.csv' % n))))
    L = {n: (new.get(n, score[n]) + 1) * math.sqrt(n) for n in score}
    mono = [n for n in range(1, 1000) if L[n] > L[n + 1] + 1e-12]
    print('monotonicity violations (L(n) > L(n+1)):', mono)
    tsv = os.path.join(out, 'take.tsv')
    fresh = not os.path.exists(tsv)
    kept, tot, tried = 0, 0.0, 0
    with open(tsv, 'a') as h:
        if fresh:
            h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for n in range(1, 1001):   # ascending, so a new n can seed the next shell
            m = n + 2 * math.floor(L[n]) + 1
            if m > 1000 or not (L[n] + 1 + GAP < L[m] - 1e-9 * L[m]):
                continue
            tried += 1
            sq = border(P[n])
            assert len(sq) == m, (n, m, len(sq))
            rows = [{'n': str(m), 'square_id': str(i), 'x': x, 'y': y, 'angle': a} for i, (x, y, a) in enumerate(sq)]
            _, fr, sc, e = floatsafe.work((m, rows))
            if fr is None or not (sc < score[m] - 1e-10) or not (sc < new.get(m, 9)):
                print('drop', m, 'from', n, sc, score[m], e); continue
            with open(os.path.join(out, '%d.csv' % m), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in fr:
                    w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            print('keep', m, 'from', n, 'L %.12f -> %.12f' % (L[m], (sc + 1) * math.sqrt(m)), 'gain %.3e' % (score[m] - sc), 'dilation', e)
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (m, score[m], sc, score[m] - sc,
                    'border step from held n=%d (literature_border.py)' % n, 'ours, on the held n=%d' % n))
            new[m] = sc; L[m] = (sc + 1) * math.sqrt(m); P[m] = fr; kept += 1; tot += score[m] - sc
    print('border steps tried', tried, 'kept', kept, 'gain', repr(tot))


if __name__ == '__main__':
    main()
