#!/usr/bin/env python3
"""Put one quenched modules result into the round 27 take, by the lane's take rule.

The row counts when floatsafe certifies it at 2.2e-11 (floatsafe.work, as methods_take.py does), its score is below
the round 27 bar (round27-briefs/bar27.tsv) by more than 1e-10, and it is lower than the same n in every other live take-*-r27 dir. The per-n csv is
written first and take.tsv is replaced by rename. The source and licence cells come from a JSON sidecar
({"source": ..., "licence": ...}), which must already name the full upstream chain.

usage: modules_publish27.py CAND.csv SIDECAR.json N [--take DIR] [--dry]
"""
import csv
import glob
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import floatsafe  # noqa: E402

csv.field_size_limit(2**30)
ROOT = Path('$SCRATCH/bounties-squares')
FIELDS = ['n', 'held', 'new', 'gain', 'source', 'licence']


def opt(args, name, default):
    return args[args.index(name) + 1] if name in args else default


def live_best(n, take):
    """The lowest score of n in every other live round 27 take, and the dir that holds it."""
    best = (float('inf'), None)
    for d in sorted(glob.glob(str(ROOT / 'take-*-r27'))):
        if Path(d).resolve() == take.resolve():
            continue
        p = Path(d) / 'take.tsv'
        if not p.exists():
            continue
        try:
            for r in csv.DictReader(p.open(), delimiter='\t'):
                if r.get('n', '').strip() == str(n) and r.get('new'):
                    best = min(best, (float(r['new']), Path(d).name))
        except (OSError, ValueError, csv.Error):
            continue
    return best


def main(a):
    cand, side, n = a[0], a[1], int(a[2])
    take = Path(opt(a, '--take', str(ROOT / 'take-modules-r27')))
    bar = {int(r['n']): float(r['bar']) for r in csv.DictReader(open(ROOT / 'round27-briefs/bar27.tsv'), delimiter='\t')}[n]
    meta = json.loads(Path(side).read_text())
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(cand))]
    if len(rows) != n or any(int(r['n']) != n for r in rows):
        print('refuse', n, 'rows', len(rows)); return 2
    _, fr, score, e = floatsafe.work((n, rows))
    other, where = live_best(n, take)
    tsv = take / 'take.tsv'
    if tsv.exists():
        for r in csv.DictReader(tsv.open(), delimiter='\t'):
            if r.get('n') == str(n) and r.get('new') and float(r['new']) < other:
                other, where = float(r['new']), take.name + ' (own row)'
    print(f'n={n} certified={fr is not None} score={score!r} dilation={e} bar={bar!r} '
          f'margin={bar - score:.6e} live={other!r} ({where})')
    if fr is None or not score < bar - 1e-10:
        print('refuse: not below the base bar by more than 1e-10'); return 1
    if not score < other:
        print('refuse: not lower than the live take', where); return 1
    if '--dry' in a:
        return 0
    take.mkdir(parents=True, exist_ok=True)
    out = take / f'{n}.csv'
    with open(str(out) + '.tmp', 'w', newline='') as h:
        w = csv.writer(h)
        w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in fr:
            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    os.replace(str(out) + '.tmp', out)
    kept = [r for r in csv.DictReader(tsv.open(), delimiter='\t')] if tsv.exists() else []
    kept = [r for r in kept if r.get('n') != str(n)]
    kept.append(dict(n=str(n), held=repr(bar), new=repr(score), gain='%.3e' % (bar - score),
                     source=meta['source'], licence=meta['licence']))
    kept.sort(key=lambda r: int(r['n']))
    with open(str(tsv) + '.tmp', 'w', newline='') as h:
        w = csv.DictWriter(h, FIELDS, delimiter='\t')
        w.writeheader()
        w.writerows(kept)
    os.replace(str(tsv) + '.tmp', tsv)
    print('keep', n, repr(score), 'gain %.6e' % (bar - score), out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
