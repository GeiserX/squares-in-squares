#!/usr/bin/env python3
"""What a better far end would be worth: the generator of modules.py with far zones that do not exist.

  farend_ceiling.py make LIBWORK NEWWORK [--c 8,9] [--delta 0.0] [--flo 0.60] [--fhi 0.84]
  farend_ceiling.py sum  Q.tsv DETAILS.csv [--takes GLOB]

`make` gives every count class of an arm a made-up far zone. At each f its loss is the lowest loss that the library
holds for that arm in any class, less --delta. With --delta 0 the run answers: what would we gain if the dear
classes cost what the cheapest class costs. With --delta 0.2 it answers: what is a far end worth that is 0.2
squares under everything we hold. The made-up zones have lengths and counts and no squares, so they can stand in a
row of `modules.py queue --need NEWWORK/ceil-ids.txt` and never in a build.

`sum` reads the rows of that queue. For each n it takes the lowest row and the bar: the smaller of the held side
and the side of every take dir of --takes. It prints the n whose row is below the bar and the sum in score.
A row is a prediction, an upper bound of the side for that choice of modules.

Our own code. Reads the library pickles of modules.py as data and changes neither file.
"""
import csv, glob, math, os, pickle, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # python -I drops the script dir
import numpy as np
import modules as M
import farend_rows as R


def _opt(a, key, default, cast=float):
    return cast(a[a.index(key) + 1]) if key in a else default


def cmd_make(a):
    work, new = a[:2]
    cs = [int(x) for x in _opt(a, '--c', '8,9', str).split(',')]
    delta = _opt(a, '--delta', 0.0); flo = _opt(a, '--flo', 0.60); fhi = _opt(a, '--fhi', 0.84)
    lib = pickle.load(open(work + '/library.pkl', 'rb')); lens = pickle.load(open(work + '/lens.pkl', 'rb'))
    far = R.plain_far(lib, lens, cs)
    fs = np.array([float(f) for f in M.GRID if flo - 1e-9 <= f <= fhi + 1e-9])
    ids = []
    for c in cs:
        cost = np.array([c * math.cos(M.flush_tilt(c, f)) for f in fs])
        low = np.full(len(fs), np.inf)
        for q, kf, kl in far:
            if q['c'] != c: continue
            ok = (fs >= kf[0] - 1e-9) & (fs <= kf[-1] + 1e-9)
            if ok.any(): low[ok] = np.minimum(low[ok], cost[ok] * np.interp(fs[ok], kf, kl) - q['count'])
        ok = np.isfinite(low)
        print('arm %d: lowest loss of any class at f %s' % (c, ' '.join('%.2f:%.2f' % (f, v) for f, v in zip(fs[ok][::4], low[ok][::4]))))
        for r in range(c):
            cnt = 2 * c + r
            vid = 'ceil%d-r%d-d%02d.F1' % (c, r, round(delta * 100))
            ls = (cnt + low[ok] - delta) / cost[ok]
            lib['mods'].append(dict(n=0, m=0, k=0, f0=float(fs[ok][len(fs[ok]) // 2]), tag='z', ours=True, kind='far', arm=1, c=c, lean=-1,
                                    P=np.zeros((0, 3)), grp=np.zeros(0, int), rig=[], miss=[], count=cnt, len0=float(ls[len(ls) // 2]),
                                    loss0=float(low[ok][len(ls) // 2] - delta), tilt0=0.0, sig='c%d:ceiling|l0|u0' % c, id=vid,
                                    src='farend_ceiling.py: a far zone that does not exist', licence='our own'))
            lens[vid] = dict(id=vid, own=None, knots=(fs[ok].copy(), ls), lock=float(fs[ok][0]))
            ids.append(vid)
    os.makedirs(new, exist_ok=True)
    pickle.dump(lib, open(new + '/library.pkl', 'wb')); pickle.dump(lens, open(new + '/lens.pkl', 'wb'))
    open(new + '/ceil-ids.txt', 'w').write(''.join(i + '\n' for i in ids))
    print('made-up far zones: %d, delta %.2f' % (len(ids), delta))
    return 0


def cmd_sum(a):
    qp, details = a[:2]
    takes = _opt(a, '--takes', '$SCRATCH/bounties-squares/take-*-r1[79]', str)
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    bar = dict(held); who = {}
    for d in sorted(glob.glob(takes)):
        p = d + '/take.tsv'
        if not os.path.exists(p): continue
        for line in open(p):
            c = line.rstrip('\n').split('\t')
            try: n = int(c[0]); L = (1 + float(c[2])) * math.sqrt(n)
            except (ValueError, IndexError): continue
            if n in bar and L < bar[n]: bar[n] = L; who[n] = os.path.basename(d)
    best = {}
    for r in csv.DictReader(open(qp), delimiter='\t'):
        n = int(r['n']); L = float(r['predicted_side'])
        if n not in best or L < best[n][0]: best[n] = (L, r)
    tot = 0.0; rows = []
    for n in sorted(best):
        L, r = best[n]
        if L < bar[n] - 1e-9:
            g = (bar[n] - L) / math.sqrt(n); tot += g
            rows.append((n, L - held[n], L - bar[n], g, r['corner'], r['far1'], r['far2']))
    print('n with a row: %d, below the bar: %d, sum of score %.6f' % (len(best), len(rows), tot))
    print('n\trow_less_held\trow_less_bar\tscore\tcorner\tfar1\tfar2')
    for t in sorted(rows, key=lambda t: -t[3]): print('%d\t%+.6f\t%+.6f\t%.3e\t%s\t%s\t%s' % t)
    return 0


if __name__ == '__main__':
    cmd = {'make': cmd_make, 'sum': cmd_sum}.get(sys.argv[1] if len(sys.argv) > 1 else '')
    if cmd is None: print(__doc__); sys.exit(2)
    sys.exit(cmd(sys.argv[2:]))
