"""Blocks with one tight direction against the held sides (avenues/k123.md, section 6).

A block of b rows of a squares, turned by phi. Direction a (odd corridor A) is on its falling line j = -1. Direction b
is on its own line (j = 0 for an even corridor B, j = +1 for an odd one), which rises. f(phi) is the larger of the two,
and the model takes its lowest point: the crossing, or the bottom of line a.
Count: m*m + g with g = a*b - ceil((A*B + A + B)/2). The exact refill agrees on 13 x 8..13, 10 x 22 and 6 x 25.
The model is an upper bound: held blocks stop at smaller turns than it allows (146 at 5.35 degrees, model 8.11).

usage: k123_model.py GAP_BY_N.tsv      (columns n, ours_L, board_L)"""
import math, csv, sys
R2 = math.sqrt(2)
held = {}; board = {}
for r in csv.DictReader(open(sys.argv[1]), delimiter='\t'):
    n = int(r['n']); held[n] = float(r['ours_L']); board[n] = float(r['board_L'])
def fa_(a, A, phi): return ((R2 * a - math.sin(phi)) / math.cos(phi) - A) / 2
def fb_(b, B, phi): return ((R2 * b + (math.sin(phi) if B % 2 else 0.0)) / math.cos(phi) - B) / 2
out = []
for a in range(2, 40):
    for A in range(int(R2 * a) - 2, int(R2 * a) + 1):
        if A % 2 == 0 or A < 1: continue
        ps = math.asin(1 / (R2 * a))
        for b in range(1, 45):
            for B in range(max(0, int(R2 * b) - 2), int(R2 * b) + 1):
                # best phi in (0, ps]
                best = None
                for q in range(1, 401):
                    phi = ps * q / 400
                    f = max(fa_(a, A, phi), fb_(b, B, phi))
                    if best is None or f < best[0]: best = (f, phi)
                f, phi = best
                if not (0.0 < f < 1.0): continue
                f0 = max(fa_(a, A, 0), fb_(b, B, 0))
                g = a * b - math.ceil((A * B + A + B) / 2)
                if g < 1: continue
                mfit = math.ceil((a + b) / R2 + 1.0)
                for m in range(mfit, 32):
                    for k in range(1, g + 1):
                        n = m * m + k
                        if n > 1000 or n not in held: continue
                        if m + f < held[n] - 1e-4:
                            out.append((held[n] - m - f, n, m, k, a, b, A, B, g, f, math.degrees(phi), held[n] - m, board[n] - m, f0))
best = {}
for o in out:
    if o[1] not in best or o[0] > best[o[1]][0]: best[o[1]] = o
tot = 0
for n in sorted(best):
    d, n, m, k, a, b, A, B, g, f, phi, fh, fbd, f0 = best[n]
    tot += d / math.sqrt(n)
    print('n %d m %d k %d: block %dx%d A %d B %d g %d: f %.6f at %.3f deg (rigid %.6f), held %.6f, board %.6f, side gain %.5f score %.2e' % (n, m, k, a, b, A, B, g, f, phi, f0, fh, fbd, d, d / math.sqrt(n)))
print(len(best), 'n, score', tot)
