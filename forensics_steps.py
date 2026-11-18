#!/usr/bin/env python3
"""Where each repeated board value sits in (m, k), and which steps keep it.

For every repeated value v of forensics_match.py values:
  - its members (n, m, k), the team, and the f we hold at the same n;
  - the steps (dm, dk) between members, and the rate dk/dm: the squares the design gains per unit of side;
  - for each m, the largest k the board holds at a side of m + v or less, and the same for the held file.
    A row of this table is the count of the design as m grows, so it shows where its squares sit.

Usage: forensics_steps.py VALUES.tsv BOARD.json HELD_DETAILS.csv OUT.tsv
"""
import sys, csv, json
from fractions import Fraction


def main():
    values, board, held, out = sys.argv[1:5]
    B = {}
    team = {}
    for x in json.load(open(board)):
        B[x['n']] = float(x['L']); team[x['n']] = x['team']
    H = {int(r['n']): float(r['L']) for r in csv.DictReader(open(held))}

    def cell(src, m, v):
        """Largest k with side(m*m + k) <= m + v in src, for k >= 0."""
        best = None
        for k in range(0, 2 * m + 1):
            n = m * m + k
            if n in src and src[n] <= m + v + 2e-9:
                best = k
        return best

    rows = []
    for ln in open(values).read().splitlines()[1:]:
        lab, f, prec, kind, mem = ln.split('\t')
        if kind != 'board':
            continue
        v = float(f)
        ms = []
        for tok in mem.split():
            n = int(tok.split('(')[0]); m, k = (int(z) for z in tok.split('(')[1].rstrip(')').split(','))
            ms.append((m, k, n))
        ms.sort()
        if ms[-1][0] < 16:
            continue
        steps = []
        for a, b in zip(ms, ms[1:]):
            dm, dk = b[0] - a[0], b[1] - a[1]
            steps.append('(%d,%d)' % (dm, dk))
        dm, dk = ms[-1][0] - ms[0][0], ms[-1][1] - ms[0][1]
        rate = '%s' % Fraction(dk, dm) if dm else '-'
        print('\n%s  v = %.12f  rate dk/dm = %s  steps %s' % (lab, v, rate, ' '.join(steps)))
        for m, k, n in ms:
            hf = H[n] - m
            print('   n=%d (m=%d, k=%d) %-18s held f %.6f  %s' % (
                n, m, k, team[n][:18], hf, 'held' if hf <= v + 1e-7 else 'side gap %.5f, score gap %.2e' % (hf - v, (hf - v) / n ** 0.5)))
        line_b, line_h = [], []
        for m in range(max(8, ms[0][0] - 3), 32):
            kb, kh = cell(B, m, v), cell(H, m, v)
            mark = '*' if any(mm == m for mm, _, _ in ms) else ' '
            line_b.append('%d:%s%s' % (m, kb, mark)); line_h.append('%d:%s' % (m, kh))
            rows.append((lab, '%.12f' % v, m, kb, kh, mark.strip()))
        print('   board k at side m + v:', ' '.join(line_b))
        print('   held  k at side m + v:', ' '.join(line_h))
    with open(out, 'w') as h:
        h.write('value\tf\tm\tboard_k\theld_k\tmember\n')
        for r in rows:
            h.write('\t'.join(str(z) for z in r) + '\n')


if __name__ == '__main__':
    main()
