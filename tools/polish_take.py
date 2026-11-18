#!/usr/bin/env python3
"""Step 4 of daily_polish.sh: certify what one polish run found and add it to a take dir.

  polish_take.py HELD_DETAILS.csv WORK_DIR OUT_TAKE_DIR NS TAKE_DIR [TAKE_DIR ...]

WORK_DIR   the work dir of the run: base.csv (the start file), fq/<n>.csv and soft/raw/<n>-*.csv
NS         the n of the run, comma separated
TAKE_DIRs  the take dirs the start file was built from, in the order engine_assemble.py got them (the last
           one that holds an n is the packing that n started from); they give each start its source and licence

An n is kept when floatsafe certifies it at 2.2e-11 and its score is more than 1e-10 below the held score and
more than 1e-10 below the packing it started from. A start that is the held packing gets the source and licence
that the newest results table (results/round*-best-*.tsv, then results/harvest-best-*.tsv) gives that packing.
OUT_TAKE_DIR may already hold a take: several runs add to one dir, also at the same time, and per n the lower
score stays. Each csv is written first and take.tsv is replaced by rename.
"""
import csv, fcntl, glob, os, sys
LANE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402

det, work, out, ns, takes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:]
COLS = ('n', 'held', 'new', 'gain', 'source', 'licence', 'start', 'polish_gain')
ns = [int(x) for x in ns.split(',')]
held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(det))}


def lineage(n):
    """source and licence of the held packing of n, from the newest results table that holds its score"""
    tabs = sorted(glob.glob(LANE + '/results/round*-best-*.tsv'),
                  key=lambda p: int(os.path.basename(p)[5:].split('-')[0]), reverse=True)
    tabs += sorted(glob.glob(LANE + '/results/harvest-best-*.tsv'), reverse=True)
    for t in tabs:
        for r in csv.DictReader(open(t), delimiter='\t'):
            try:
                if int(r['n']) == n and abs(float(r['score']) - held[n]) < 1e-10:
                    return r['source'], r['licence']
            except (KeyError, ValueError, TypeError):
                continue
    return 'seed merged0', 'see README'


origin = {}                                   # where the start packing of an n came from (later dirs are on top)
for t in takes:
    for r in csv.DictReader(open(t + '/take.tsv'), delimiter='\t'):
        origin[int(r['n'])] = (r['source'], r.get('licence') or '')
start = {}                                    # the certified score of the packing each polish started from
for r in csv.DictReader(open(work + '/base.csv')):
    if int(r['n']) in ns:
        start.setdefault(int(r['n']), []).append({k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')})
start = {n: floatsafe.work((n, rows))[2] for n, rows in start.items()}
best = {}
for step, pat in (('fq quench', work + '/fq/%d.csv'), ('fq quench and soft-box search', work + '/soft/raw/%d-*.csv')):
    for n in ns:
        for p in sorted(glob.glob(pat % n)):
            rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(p))]
            if len(rows) != n:
                print('drop', n, 'rows', len(rows), p); continue
            _, fr, score, e = floatsafe.work((n, rows))
            if fr is None or not (score < held[n] - 1e-10) or not (score < start[n] - 1e-10):
                print('drop', n, score, 'held', held[n], 'start', start[n], e, p); continue
            if n not in best or score < best[n][0]:
                best[n] = (score, fr, step)

os.makedirs(out, exist_ok=True)
lock = open(out + '/.take.lock', 'w'); fcntl.flock(lock, fcntl.LOCK_EX)      # one writer of take.tsv at a time
rows = {}
if os.path.exists(out + '/take.tsv'):
    rows = {int(r['n']): r for r in csv.DictReader(open(out + '/take.tsv'), delimiter='\t')}
tot, kept = 0.0, []
for n in sorted(best):
    score, fr, step = best[n]
    if n in rows and not (score < float(rows[n]['new'])):
        print('stays', n, 'the dir holds', rows[n]['new'], 'this run', score); continue
    with open('%s/%d.csv.tmp' % (out, n), 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in fr:
            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    os.replace('%s/%d.csv.tmp' % (out, n), '%s/%d.csv' % (out, n))
    if n in origin:
        src, lic = '%s of %s' % (step, origin[n][0]), origin[n][1]
    else:
        src, lic = lineage(n); src = '%s of the held packing (%s)' % (step, src)
    rows[n] = dict(zip(COLS, ('%d' % n, repr(held[n]), repr(score), '%.3e' % (held[n] - score), src, lic,
                              repr(start[n]), '%.3e' % (start[n] - score))))
    tot += start[n] - score; kept.append(n)
    print('keep', n, 'held', held[n], 'start', start[n], 'new', score, 'polish gain %.3e' % (start[n] - score), step)
with open(out + '/take.tsv.tmp', 'w') as h:
    h.write('\t'.join(COLS) + '\n')
    for n in sorted(rows):
        h.write('\t'.join(rows[n].get(k) or '' for k in COLS) + '\n')
os.replace(out + '/take.tsv.tmp', out + '/take.tsv')
print('the take dir now holds %d n, %.10f below held' % (len(rows), sum(float(r['held']) - float(r['new']) for r in rows.values())))
print('kept %d of %d n, polish gain %.10f on top of the start file: %s' % (len(kept), len(ns), tot, ' '.join(map(str, kept))))
