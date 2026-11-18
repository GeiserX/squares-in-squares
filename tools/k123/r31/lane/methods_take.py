#!/usr/bin/env python3
"""Certify the raw results of methods_lp.py / methods_soft.py the lane's way.

For every RAW/<n>.csv or RAW/<n>-<tag>.csv: floatsafe.work (2.2e-11 clearance, the official metric as
written and after a pandas read), then keep it only if its score is below the
held score by more than 1e-10. Same layout as angle_take.py, so
engine_assemble.py reads the take dir.

Usage: methods_take.py HELD_DETAILS.csv TAKEDIR SOURCE RAWDIR [RAWDIR ...]
  HELD_DETAILS.csv  the gate's details.csv of the held file (n, L, score, ...)
  later RAWDIRs win only when they are smaller
"""
import csv, glob, os, sys

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import finesafe as floatsafe  # noqa: E402


def main():
    held_csv, out, source, raws = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    os.makedirs(out, exist_ok=True)
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(held_csv))}
    best = {}
    for d in raws:
        for p in sorted(glob.glob(d + '/*.csv')):
            n = int(os.path.basename(p)[:-4].split('-')[0])
            rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
            if len(rows) != n:
                print('drop', n, 'rows', len(rows), p); continue
            _, fr, score, e = floatsafe.work((n, rows))
            if fr is None or not (score < held[n] - 1e-10):
                print('drop', n, score, held[n], e, p); continue
            if n not in best or score < best[n][0]:
                best[n] = (score, fr, p)
    tot = 0.0
    with open(out + '/take.tsv', 'w') as h:
        h.write('n\theld\tnew\tgain\tsource\tlicence\n')
        for n in sorted(best):
            score, fr, p = best[n]
            with open('%s/%d.csv' % (out, n), 'w', newline='') as g:
                w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
                for r in fr:
                    w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
            tot += held[n] - score
            h.write('%d\t%r\t%r\t%.3e\t%s\t%s\n' % (n, held[n], score, held[n] - score, source, 'own search'))
            print('keep', n, held[n], score, '%.3e' % (held[n] - score), p)
    print('kept', len(best), 'gain', repr(tot))


if __name__ == '__main__':
    main()
