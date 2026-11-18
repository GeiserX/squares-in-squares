#!/usr/bin/env python3
"""Merge every harvested packing into a per-n best, checked by the official metric.

  python3 harvest_merge.py --harvest DIR --base seeds/merged0.csv --base-tsv seeds/merged0.tsv \
      [--state state-boxA ...] --out DIR/merged [--procs 4]

Walks DIR for .csv and .json files (also inside .zip and .gz). A zip is not one
work item: its members are scheduled in small batches (ZIP_BATCH_BYTES of
uncompressed data, ZIP_BATCH_MEMBERS at most), so a big archive spreads over
the workers and cannot hold one of them for long. The workers also share the
best side the metric has accepted per n so far (SHARED), so a packing that no
longer beats it by more than 1e-13 is not scored again: forty copies of one
public merge cost one scoring, not forty. CSVs: columns
n, square_id, x, y, angle (case-insensitive; an 's' prefix on values is
stripped); without an n column, n comes from the file name (n=0001.csv); diff
files use their after_x, after_y, after_angle columns. JSON: any object with
N (or n) and packing = [[x, y, angle], ...]; the angle unit (radians or degrees)
is the one whose bounding side matches the object's L. For each n, a cheap float bounding side is compared with the best so
far; only a candidate that could win is scored with kaggle_metric's
evaluate_single_puzzle, on the original decimal strings. "Could win" means a side
below the base side by more than 1e-10 * sqrt(n), which is 1e-10 of score, the
least the take step keeps: a public copy of a packing we hold, which reads 5e-11
of its side smaller because our copy carries the float-safe dilation, is not scored. The winner per n is
written to OUT/best/<n>.csv; OUT/best.tsv has n, score, L, source and licence,
OUT/sources.tsv one row per file read (rows, puzzles, wins).
Where the winner of an n comes from a source whose licence angle_take.accepted()
refuses, the best packing from an accepted source is kept too, in OUT/alt/<n>.csv
and OUT/alt.tsv (same columns), so the take step has a second choice. A source
with an accepted licence is therefore measured against the accepted sources only.
"""
import argparse, csv, gzip, io, json, math, multiprocessing as mp, os, pathlib, re, sys, zipfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kaggle_metric as km  # noqa: E402
from angle_take import accepted  # noqa: E402  (the licence allow-list lives at the take step)

COLS = ('n', 'square_id', 'x', 'y', 'angle')
PACKED = ('.csv', '.csv.gz', '.json')
ZIP_BATCH_BYTES = 32 << 20          # uncompressed bytes per zip work item
ZIP_BATCH_MEMBERS = 8               # members per zip work item, at most


def side_est(rows):
    xs, ys = [], []
    for r in rows:
        x, y, t = float(r['x']), float(r['y']), float(r['angle'])
        e = 0.5 * (abs(math.cos(t)) + abs(math.sin(t)))
        xs += [x - e, x + e]; ys += [y - e, y + e]
    return max(max(xs) - min(xs), max(ys) - min(ys))


def zip_batches(path):
    """Member-name batches of a zip, in archive order; [] for a broken zip."""
    try:
        infos = zipfile.ZipFile(path).infolist()
    except (zipfile.BadZipFile, OSError):
        return []
    out, cur, size = [], [], 0
    for i in infos:
        if not i.filename.lower().endswith(PACKED):
            continue
        if cur and (size + i.file_size > ZIP_BATCH_BYTES or len(cur) >= ZIP_BATCH_MEMBERS):
            out.append(cur); cur, size = [], 0
        cur.append(i.filename); size += i.file_size
    if cur:
        out.append(cur)
    return out


def iter_texts(path, members=None):
    """(name, text-stream) for every csv in a file, zip or gz; members limits a zip to those names."""
    p = str(path)
    if p.endswith('.zip'):
        try:
            z = zipfile.ZipFile(p)
        except zipfile.BadZipFile:
            return
        for m in (z.namelist() if members is None else members):
            if m.lower().endswith(PACKED):
                raw = z.open(m)
                if m.lower().endswith('.gz'):
                    raw = gzip.open(raw)
                yield f'{p}!{m}', io.TextIOWrapper(raw, encoding='utf-8', errors='replace')
    elif p.endswith('.csv') or p.endswith('.json'):
        yield p, open(p, encoding='utf-8', errors='replace')
    elif p.endswith('.csv.gz'):
        yield p, io.TextIOWrapper(gzip.open(p), encoding='utf-8', errors='replace')


def read_json(stream):
    try:
        data = json.load(stream)
    except Exception:
        return None
    out = {}
    stack = [data]
    while stack:
        o = stack.pop()
        if isinstance(o, list):
            stack.extend(x for x in o if isinstance(x, (list, dict)))
        elif isinstance(o, dict):
            n, pk = o.get('N', o.get('n')), o.get('packing')
            if isinstance(n, int) and isinstance(pk, list) and len(pk) == n and 1 <= n <= 1000 \
                    and all(isinstance(t, list) and len(t) >= 3 for t in pk):
                rows = [dict(n=str(n), square_id=str(i), x=repr(float(t[0])), y=repr(float(t[1])),
                             angle=repr(float(t[2]))) for i, t in enumerate(pk)]
                L = o.get('L')
                if isinstance(L, (int, float)) and abs(side_est(rows) - L) > 1e-6:
                    deg = [dict(r, angle=repr(math.radians(float(r['angle'])))) for r in rows]
                    if abs(side_est(deg) - L) < 1e-6:
                        rows = deg
                out.setdefault(n, []).append(rows)
            else:
                stack.extend(v for v in o.values() if isinstance(v, (list, dict)))
    return out or None


def read_puzzles(stream, name=''):
    """{n: [rows, ...]} (a file may hold several packings of one n)."""
    if name.lower().endswith('.json'):
        return read_json(stream)
    rd = csv.reader(stream)
    try:
        head = [h.strip().lower() for h in next(rd)]
    except StopIteration:
        return None
    if all(c in head for c in ('after_x', 'after_y', 'after_angle')):
        head = [{'after_x': 'x', 'after_y': 'y', 'after_angle': 'angle', 'x': '_x', 'y': '_y', 'angle': '_a'}.get(h, h)
                for h in head]
    fixed_n = None
    if 'n' not in head:
        m = re.search(r'(?:^|[^a-z])n[=_]?0*(\d+)\.csv$', name.lower().rsplit('/', 1)[-1])
        if not m:
            return None
        fixed_n = int(m.group(1))
    need = [c for c in COLS if c != 'n' or fixed_n is None]
    if not all(c in head for c in need):
        return None
    idx = {c: head.index(c) for c in need}
    out = {}
    for row in rd:
        try:
            vals = {c: row[i].strip().lstrip('s') for c, i in idx.items()}
            n = fixed_n if fixed_n is not None else int(float(vals['n']))
            vals['n'] = str(n)
        except (IndexError, ValueError):
            continue
        if not 1 <= n <= 1000:
            continue
        out.setdefault(n, [[]])[0].append({c: vals[c] for c in COLS})
    return out


SHARED = None                       # best side per n the metric accepted so far, in any worker: index n over
                                    # every source, index 1001 + n over the sources with an accepted licence


def share(arr):
    global SHARED
    SHARED = arr


def work(args):
    path, members, bestL, okl = args
    off = 1001 if okl else 0        # an accepted source only has to beat the accepted ones
    res = []
    for name, stream in iter_texts(path, members):
        try:
            puzzles = read_puzzles(stream, name)
        except Exception as e:
            res.append((name, 'error', str(e)[:80], []))
            continue
        if puzzles is None:
            res.append((name, 'skip', 'no packing columns', []))
            continue
        wins = []
        for n, packs in puzzles.items():
            for rows in packs:
                if len(rows) != n:
                    continue
                try:
                    L = side_est(rows)
                except ValueError:
                    continue
                if L >= bestL.get(n, math.inf) - 1e-10 * math.sqrt(n) or (SHARED is not None and L >= SHARED[off + n] - 1e-13):
                    continue
                _, s, Ls, why = km.evaluate_single_puzzle(n, rows)
                if why == 'ok':
                    wins.append((n, s, Ls, rows))
                    bestL[n] = (s + 1) * math.sqrt(n)
                    for o in ((0, 1001) if okl else (0,)):
                        if SHARED is not None and bestL[n] < SHARED[o + n]:
                            SHARED[o + n] = bestL[n]
        res.append((name, 'ok', f'{len(puzzles)} puzzles', wins))
    return res


def licence_of(path, root):
    rel = pathlib.Path(path).resolve().relative_to(root.resolve()).parts
    meta = root.joinpath(*rel[:2], 'meta.json')
    if meta.exists():
        m = json.loads(meta.read_text())
        return m.get('ref', ''), m.get('license', '')
    return '', ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--harvest', required=True, type=pathlib.Path)
    ap.add_argument('--base', required=True)
    ap.add_argument('--base-tsv', required=True)
    ap.add_argument('--state', nargs='*', default=[])
    ap.add_argument('--out', required=True, type=pathlib.Path)
    ap.add_argument('--procs', type=int, default=4)
    a = ap.parse_args()
    best = {}                                   # n -> (score, L, source, licence, rows)
    base_scores = {int(r['n']): r for r in csv.DictReader(open(a.base_tsv), delimiter='\t')}
    base_rows = {}
    for r in csv.DictReader(open(a.base)):
        base_rows.setdefault(int(r['n']), []).append({c: r[c] for c in COLS})
    for n, r in base_scores.items():
        if r['reason'] == 'ok':
            best[n] = (float(r['score']), r['L'], 'seed merged0', 'see README', base_rows[n])
    for st in a.state:
        for f in pathlib.Path(st, 'best').glob('*.score'):
            n = int(f.stem); s = float(f.read_text())
            if s < best.get(n, (math.inf,))[0]:
                rows = list(csv.DictReader(open(f.with_suffix('.csv'))))
                best[n] = (s, f'{(s + 1) * math.sqrt(n)!r}', f'our search ({st})', 'ours', rows)
    total0 = sum(best[n][0] for n in best) + sum(km.infeasible_score(n) for n in range(1, 1001) if n not in best)
    print(f'base total {total0:.10f}', flush=True)
    files = sorted(p for p in a.harvest.rglob('*') if p.is_file() and
                   (p.suffix.lower() in ('.csv', '.zip', '.json') or p.name.lower().endswith('.csv.gz')))
    bestL = {n: (v[0] + 1) * math.sqrt(n) for n, v in best.items()}
    a.out.mkdir(parents=True, exist_ok=True)
    srcrows = []
    items = []
    alt = {}                                    # n -> best from an accepted licence, same tuple as best
    for f in files:
        okl = accepted(licence_of(f, a.harvest)[1])
        if f.suffix.lower() == '.zip':
            items += [(f, b, bestL, okl) for b in zip_batches(f)]
        else:
            items.append((f, None, bestL, okl))
    print(f'{len(files)} files, {len(items)} work items', flush=True)
    shared = mp.Array('d', [math.inf] * 2002, lock=False)
    with mp.Pool(a.procs, initializer=share, initargs=(shared,)) as pool:
        for res in pool.imap_unordered(work, items):
            for name, status, info, wins in res:
                ref, lic = licence_of(name.split('!')[0], a.harvest)
                won = 0
                for n, s, Ls, rows in wins:
                    row = (s, Ls, f'{ref} :: {pathlib.Path(name).name}', lic, rows)
                    if accepted(lic) and s < alt.get(n, (math.inf,))[0] - 1e-13:
                        alt[n] = row
                    if s < best.get(n, (math.inf,))[0] - 1e-13:
                        best[n] = row; won += 1
                srcrows.append((name, ref, lic, status, info, won))
                print(f'{status} {name[-90:]} {info} wins={won}', flush=True)
    total = sum(best[n][0] for n in best) + sum(km.infeasible_score(n) for n in range(1, 1001) if n not in best)
    alt = {n: v for n, v in alt.items() if not accepted(best[n][3]) and best[n][2] != 'seed merged0'}
    for sub, table in (('best', best), ('alt', alt)):
        (a.out / sub).mkdir(exist_ok=True)
        with open(a.out / f'{sub}.tsv', 'w') as h:
            h.write('n\tscore\tL\tsource\tlicence\n')
            for n in sorted(table):
                s, Ls, src, lic, rows = table[n]
                h.write(f'{n}\t{s!r}\t{Ls}\t{src}\t{lic}\n')
                with open(a.out / sub / f'{n}.csv', 'w', newline='') as g:
                    w = csv.writer(g, lineterminator='\n'); w.writerow(COLS)
                    for r in rows:
                        w.writerow([n, r['square_id'], r['x'], r['y'], r['angle']])
    print(f'{len(alt)} n won by a source outside the licence allow-list have a second choice in alt/', flush=True)
    with open(a.out / 'sources.tsv', 'w') as h:
        h.write('file\tref\tlicence\tstatus\tinfo\twins_when_read\n')
        for row in srcrows:
            h.write('\t'.join(str(x) for x in row) + '\n')
    print(f'total {total0:.10f} -> {total:.10f} (gain {total0 - total:.10f})', flush=True)


if __name__ == '__main__':
    main()
