#!/usr/bin/env python3
"""Convert between our per-n Kaggle rows and Evan Daniel's packer text format.

Evan's format (https://github.com/evand/square-packing, MIT): first line `n s`, then
one `x y deg` per square (centres, angle in degrees, box [0, s]^2). Ours: Kaggle CSV
rows with x, y centres and the angle in radians.

  evconv.py to   <submission.csv> <n> <out.txt> [--drop K]   # --drop: remove square K (controls)
  evconv.py from <in.txt> <out_rows.csv>                     # rows for one n, Kaggle columns minus id
"""
import csv, math, sys


def half(t):
    return (abs(math.cos(t)) + abs(math.sin(t))) / 2


def to_txt(sub, n, out, drop=None):
    rows = [r for r in csv.DictReader(open(sub)) if int(r['n']) == n]
    P = [(float(r['x']), float(r['y']), float(r['angle'])) for r in rows]
    x0 = min(x - half(t) for x, y, t in P)
    y0 = min(y - half(t) for x, y, t in P)
    P = [(x - x0, y - y0, t) for x, y, t in P]
    s = max(max(x + half(t), y + half(t)) for x, y, t in P)
    if drop is not None:
        P.pop(drop)
    with open(out, 'w') as h:
        h.write(f'{len(P)} {s!r}\n')
        for x, y, t in P:
            h.write(f'{x!r} {y!r} {math.degrees(t)!r}\n')
    return s


def from_txt(inp, out):
    L = [l.split() for l in open(inp) if l.strip() and not l.startswith('#')]
    n = int(L[0][0])
    with open(out, 'w', newline='') as h:
        w = csv.writer(h)
        w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for i, q in enumerate(L[1:n + 1]):
            w.writerow([n, i, q[0], q[1], repr(math.radians(float(q[2])))])


if __name__ == '__main__':
    if sys.argv[1] == 'to':
        d = int(sys.argv[sys.argv.index('--drop') + 1]) if '--drop' in sys.argv else None
        print(to_txt(sys.argv[2], int(sys.argv[3]), sys.argv[4], d))
    else:
        from_txt(sys.argv[2], sys.argv[3])
