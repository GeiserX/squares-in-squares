#!/usr/bin/env python3
"""Where the take dirs of rounds 16 and 17 stand at m 28 to 31, against the board and the design of 979.

For each n whose board f is from 0.60 to 0.77: the held f, the best f of any round 16 or 17 take dir, the board f and
the f of the design of 979 (class (11, 9) at m = 31, (10, 9) at m = 28 to 30, both with the end loss of 979, E = 1.109).

Usage: invent_now.py OUT.tsv
"""
import csv, glob, math, os, sys
S = '$SCRATCH/bounties-squares'
sys.path.insert(0, '.')
import invent_census as ic
G = {}
for r in csv.DictReader(open(S + '/main-r17/gap-by-n.tsv'), delimiter='\t'):
    G[int(r['n'])] = (int(r['m']), int(r['k']), float(r['ours_L']), float(r['board_L']))
best = {}
for d in glob.glob(S + '/take-*-r16') + glob.glob(S + '/take-*-r17'):
    p = d + '/take.tsv'
    if not os.path.exists(p): continue
    for r in csv.DictReader(open(p), delimiter='\t'):
        try: n = int(r['n']); s = float(r['new'])
        except Exception: continue
        if not os.path.exists('%s/%d.csv' % (d, n)): continue
        if n not in best or s < best[n][0]: best[n] = (s, os.path.basename(d)[5:])
E = 1.109; rows = []
for n in sorted(G):
    m, k, hl, bl = G[n]
    if not 28 <= m <= 31: continue
    hf, bf = hl - m, bl - m
    if not 0.60 <= bf <= 0.77: continue
    c = (11, 9) if m == 31 else (10, 9)
    pf = ic.f_for(m, c[0], c[1], E, k); pf1 = ic.f_for(m, c[0], c[1], E, k - 1)
    if pf is None or pf1 is None: continue
    sq = pf - pf1
    nl = (1 + best[n][0]) * math.sqrt(n) if n in best else hl
    nf = min(nl, hl) - m
    rows.append((n, m, k, hf, nf, bf, pf, (hf - bf) / sq, (nf - bf) / sq, (pf - bf) / sq, best[n][1] if n in best and nl < hl else '', (nf - bf) / math.sqrt(n)))
with open(sys.argv[1], 'w') as h:
    h.write('n\tm\tk\theld_f\tnow_f\tboard_f\tf_of_979_design\theld_behind_board_squares\tnow_behind_board_squares\tdesign_minus_board_squares\ttake_dir_of_now\tscore_gap_now\n')
    for x in rows: h.write('%d\t%d\t%d\t%.6f\t%.6f\t%.6f\t%.6f\t%.2f\t%.2f\t%+.2f\t%s\t%.3e\n' % x)
import collections
by = collections.defaultdict(list)
for x in rows: by[x[1]].append(x)
for m in sorted(by):
    v = by[m]; mv = [x for x in v if x[10]]
    print('m %d: %d n, held behind board %.2f squares (mean), now %.2f, design minus board %+.2f (mean abs %.2f); gap now %.5f of score; %d n moved since round 15'
          % (m, len(v), sum(x[7] for x in v) / len(v), sum(x[8] for x in v) / len(v), sum(x[9] for x in v) / len(v), sum(abs(x[9]) for x in v) / len(v), sum(x[11] for x in v), len(mv)))
print('all: %d n, gap now %.5f' % (len(rows), sum(x[11] for x in rows)))
