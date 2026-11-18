"""Public near misses: layouts of new public files that sit just above the held bar (data, read only).

  python -I near_scan.py OUTDIR WINDOW DIR [DIR ...]
Every csv/json (also in zip/gz) under the DIRs whose source licence angle_take.accepted() takes is
streamed. Per n, a layout counts when its float score lies in (bar + 2e-10, bar + WINDOW] and its side
is more than 1e-8 away from the public winner of work/public/merged/best.tsv (so neither a copy of the
held layout nor a copy of a winner). Distinct sides (1e-10) are kept, best 2 per n, certified with
floatsafe, and written to OUTDIR/<n>-<k>.csv; OUTDIR/queue.tsv lists n, certified score, bar, gap,
file, licence, updated, ordered by gap.
"""
import csv, json, math, pathlib, sys
L = '.'
sys.path.insert(0, L)
import harvest_merge as hm  # noqa: E402
import floatsafe  # noqa: E402
from angle_take import accepted  # noqa: E402
csv.field_size_limit(1 << 26)
S = pathlib.Path('$SCRATCH/bounties-squares')
W = S / 'take-harvest-r26/work'
out, window, dirs = pathlib.Path(sys.argv[1]), float(sys.argv[2]), sys.argv[3:]
out.mkdir(parents=True, exist_ok=True)
bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(S / 'gate/cand-round25-1114b/details.csv'))}
win = {int(r['n']): float(r['L']) for r in csv.DictReader(open(W / 'public/merged/best.tsv'), delimiter='\t')}


def meta(path):
    p = pathlib.Path(str(path).split('!')[0])
    for d in [p.parent] + list(p.parents)[:4]:
        m = d / 'meta.json'
        if m.exists():
            j = json.load(open(m))
            return j.get('license', ''), j.get('updated') or j.get('lastRun') or ''
    return '', ''


cands = {}   # n -> {side_key: (side, file, licence, updated, rows)}
for d in dirs:
    for p in sorted(pathlib.Path(d).rglob('*')):
        if not p.is_file() or p.name == 'meta.json' or not (p.suffix.lower() in ('.csv', '.zip', '.json') or p.name.endswith('.csv.gz')):
            continue
        lic, up = meta(p)
        if not accepted(lic):
            continue
        for name, st in hm.iter_texts(p):
            try:
                pz = hm.read_puzzles(st, name) or {}
            except Exception as e:
                print('err', name, e, file=sys.stderr); continue
            for n, packs in pz.items():
                if n not in bar:
                    continue
                for rows in packs:
                    if len(rows) != n:
                        continue
                    try:
                        side = hm.side_est(rows)
                    except ValueError:
                        continue
                    s = side / math.sqrt(n) - 1
                    if not (bar[n] + 2e-10 < s <= bar[n] + window) or abs(side - win.get(n, -1)) < 1e-8:
                        continue
                    k = round(side, 10)
                    c = cands.setdefault(n, {})
                    if k not in c:
                        c[k] = (side, name, lic, up, rows)
            print('read', name[-100:], flush=True)
q = []
for n, c in sorted(cands.items()):
    for i, (side, name, lic, up, rows) in enumerate(sorted(c.values(), key=lambda t: t[0])[:2]):
        rr = [{'n': str(n), 'square_id': str(j), 'x': r['x'], 'y': r['y'], 'angle': r['angle']} for j, r in enumerate(rows)]
        _, fr, sc, e = floatsafe.work((n, rr))
        if fr is None:
            continue
        f = out / f'{n}-{i}.csv'
        with open(f, 'w', newline='') as g:
            w = csv.DictWriter(g, fieldnames=('n', 'square_id', 'x', 'y', 'angle')); w.writeheader(); w.writerows(fr)
        q.append((sc - bar[n], n, sc, bar[n], str(f), name, lic, up))
q.sort()
with open(out / 'queue.tsv', 'w') as g:
    g.write('n\tscore\tbar\tgap\tstart\tfile\tlicence\tupdated\n')
    for gap, n, sc, b, f, name, lic, up in q:
        g.write(f'{n}\t{sc!r}\t{b!r}\t{gap:.3e}\t{f}\t{name}\t{lic}\t{up}\n')
print('queue', len(q), 'starts on', len({x[1] for x in q}), 'n', flush=True)
