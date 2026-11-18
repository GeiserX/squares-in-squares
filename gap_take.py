#!/usr/bin/env python3
"""gap lane: write the take dir from finished files (avenues/gap.md).

  gap_take.py DETAILS.csv TAKEDIR SCRATCH FILE:DONORS:HOW [FILE:DONORS:HOW ...]
    FILE    a finished per-n csv (gap_grow.py finish: floatsafe, one fq quench from the certified file, floatsafe)
    DONORS  the held n whose tilted squares started the layout, comma separated
    HOW     a short tag of the tool and start (the walk tag)

Each file is scored again with floatsafe. It counts when it is below the base bar by more than 1e-10 and below the
same n in every live take-*-r25 dir and every frozen take-*-r24 dir (all r24 rows count as bar, clean or not,
which is stricter than the base rule). The source cell names each donor row with its own source and licence, read
from the newest results table whose score matches the held score of that n to 1e-12. A donor with no matching row,
or with a source that names an excluded upstream, keeps the row out. Writes TAKEDIR/<n>.csv first, then take.tsv
by rename. Rows already in take.tsv stay unless a new file of the same n is lower.
Our own code. Imports floatsafe of this lane.
"""
import csv, glob, os, re, sys
csv.field_size_limit(1 << 30)
LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402

OUT = ('samanyu-dev', 'penguin069', 'prvsiyan/squares-verified-best-of-1105', 'squares-joegun-boxed')


def tables():
    R = os.path.join(LANE, 'results')
    def key(p):
        b = os.path.basename(p)
        m = re.match(r'round(\d+)-best', b)
        return (1, int(m.group(1)), b) if m else (0, 0, b)
    return sorted(glob.glob(R + '/*-best-*.tsv'), key=key, reverse=True)


def donor_source(n, score, T):
    for p in T:
        for r in csv.DictReader(open(p), delimiter='\t'):
            try:
                if int(r['n']) == n and abs(float(r['score']) - score) < 1e-12:
                    return r['source'], r.get('licence', ''), os.path.relpath(p, LANE)
            except (ValueError, KeyError):
                pass
    return None


def live_best(scratch, n):
    best = None
    for t in glob.glob(scratch + '/take-*-r25/take.tsv') + glob.glob(scratch + '/take-*-r24/take.tsv'):
        if '/take-gap-r25/' in t: continue
        try:
            for r in csv.DictReader(open(t), delimiter='\t'):
                if r.get('n', '').strip() == str(n):
                    v = float(r['new']); best = v if best is None or v < best else best
        except (OSError, ValueError, KeyError):
            pass
    return best


def main():
    details, take, scratch = sys.argv[1:4]
    held = {int(r['n']): float(r['score']) for r in csv.DictReader(open(details))}
    T = tables()
    rows = {}
    tp = take + '/take.tsv'
    if os.path.exists(tp):
        for r in csv.DictReader(open(tp), delimiter='\t'): rows[int(r['n'])] = r
    for spec in sys.argv[4:]:
        f, donors, how = spec.split(':', 2)
        raw = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(f))]
        n = len(raw)
        _, fr, score, e = floatsafe.work((n, raw))
        if fr is None or not score < held[n] - 1e-10:
            print('drop', n, 'floatsafe or bar', score, held[n], e); continue
        lb = live_best(scratch, n)
        if lb is not None and not score < lb:
            print('drop', n, 'a live r25 take is lower', lb, score); continue
        if n in rows and float(rows[n]['new']) <= score:
            print('keep old', n); continue
        srcs, lics = [], []
        bad = None
        for d in [int(x) for x in donors.split(',')]:
            ds = donor_source(d, held[d], T)
            if ds is None: bad = 'donor %d has no matching results row' % d; break
            if any(o in (ds[0] + ds[1]).lower() for o in OUT): bad = 'donor %d names an excluded upstream' % d; break
            srcs.append('held n = %d of gather/round23-2026-11-13b.csv (%s: %s)' % (d, ds[2], ds[0]))
            lics.append(ds[1] or 'own work')
        if bad: print('drop', n, bad); continue
        p = '%s/%d.csv' % (take, n)
        with open(p + '.tmp', 'w', newline='') as h:
            w = csv.writer(h); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
            for r in fr: w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
        os.replace(p + '.tmp', p)
        rows[n] = dict(n=str(n), held=repr(held[n]), new=repr(score), gain='%.3e' % (held[n] - score),
                       source='%s, from %s; floatsafe, one fq quench from the certified file' % (how, '; '.join(srcs)),
                       licence='; '.join(sorted(set(lics))))
        print('keep', n, held[n], score, held[n] - score)
    with open(tp + '.tmp', 'w', newline='') as h:
        w = csv.writer(h, delimiter='\t'); w.writerow(['n', 'held', 'new', 'gain', 'source', 'licence'])
        for n in sorted(rows):
            r = rows[n]; w.writerow([r['n'], r['held'], r['new'], r['gain'], r['source'], r['licence']])
    os.replace(tp + '.tmp', tp)
    print('take rows', len(rows))


if __name__ == '__main__':
    main()
