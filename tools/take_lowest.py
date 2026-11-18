#!/usr/bin/env python3
"""The start of a polish over several take dirs: per n, the lowest certified file of all of them, as one take dir.

  take_lowest.py HELD_DETAILS.csv OUT_TAKE_DIR TAKE_DIR [TAKE_DIR ...] [--ns "a b c"] [--seen SEEN.tsv]

A file counts when floatsafe certifies it at 2.2e-11 and its score is more than 1e-10 below the held score.
OUT_TAKE_DIR gets the per-n csv of each lowest file and a take.tsv whose source names the take dir it came
from, so daily_polish.sh can read it as its TAKE_DIR. A take dir with no take.tsv yet is skipped.

  --ns    only these n
  --seen  a table (n, score) of the starts already handed out. An n is written only when its lowest file is
          more than 1e-10 below the score the table holds for it, and the table is updated after. With it the
          same command, run every few minutes on take dirs that other runs still write, gives only what is new.
"""
import argparse, csv, os, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import floatsafe  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('det'); ap.add_argument('out'); ap.add_argument('dirs', nargs='+')
ap.add_argument('--ns', default=''); ap.add_argument('--seen')
a = ap.parse_args()
only = set(int(x) for x in a.ns.replace(',', ' ').split())
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.det))}
seen = {}
if a.seen and os.path.exists(a.seen):
    seen = {int(r['n']): float(r['score']) for r in csv.DictReader(open(a.seen), delimiter='\t')}
best = {}
for d in a.dirs:
    d = d.rstrip('/')
    if not os.path.exists(d + '/take.tsv'):
        print('no take.tsv yet in', d); continue
    for r in csv.DictReader(open(d + '/take.tsv'), delimiter='\t'):
        n = int(r['n']); p = '%s/%d.csv' % (d, n)
        if only and n not in only:
            continue
        if not os.path.exists(p):
            print('no file', p); continue
        if float(r['new']) >= seen.get(n, 9.0) - 1e-10:      # the table's own score says it is not new: skip the check
            continue
        rows = [{k: q[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for q in csv.DictReader(open(p))]
        if len(rows) != n:
            print('drop', n, 'rows', len(rows), p); continue
        _, fr, score, e = floatsafe.work((n, rows))
        if fr is None or not (score < held[n] - 1e-10):
            print('not below held', n, score, held[n], e, p); continue
        if abs(score - float(r['new'])) > 1e-12:
            print('note: take.tsv says', r['new'], 'floatsafe says', score, p)
        if not (score < seen.get(n, 9.0) - 1e-10):
            continue
        if n not in best or score < best[n][0] - 1e-13:
            best[n] = (score, p, r['source'], r.get('licence') or '', os.path.basename(d))
os.makedirs(a.out, exist_ok=True)
for n in sorted(best):
    shutil.copyfile(best[n][1], '%s/%d.csv' % (a.out, n))
with open(a.out + '/take.tsv.tmp', 'w') as h:
    h.write('n\theld\tnew\tgain\tsource\tlicence\n')
    for n in sorted(best):
        score, p, src, lic, d = best[n]
        h.write('%d\t%r\t%r\t%.3e\t%s (%s)\t%s\n' % (n, held[n], score, held[n] - score, src, d, lic))
        print('start', n, held[n], score, '%.3e' % (held[n] - score), d)
os.replace(a.out + '/take.tsv.tmp', a.out + '/take.tsv')    # the csv files first, the table by rename
if a.seen:
    seen.update({n: best[n][0] for n in best})
    with open(a.seen + '.tmp', 'w') as h:
        h.write('n\tscore\n')
        for n in sorted(seen):
            h.write('%d\t%r\n' % (n, seen[n]))
    os.replace(a.seen + '.tmp', a.seen)
print('start dir holds %d n, %.10f below held: %s' % (len(best), sum(held[n] - best[n][0] for n in best), ' '.join(map(str, sorted(best)))))
