"""Find every public copy of a reference layout per n (data only, read with -I).

  python -I origin_scan.py REFDIR N[,N...] OUT.tsv ROOT [ROOT ...]
REFDIR holds <n>.csv reference layouts (merge output). Every csv/json (also in zip/gz) under the roots
is streamed; for each n in the list the float side is compared with the reference side, and every
packing within 1e-7 of side gets its symmetric centre distance to the reference. Output rows:
n, file, side - ref side, centre distance, licence, updated (from the source dir meta.json).
"""
import csv, json, math, pathlib, sys
sys.path.insert(0, '.')
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import harvest_merge as hm  # noqa: E402
import audit_ac as A  # noqa: E402
csv.field_size_limit(1 << 26)

refdir, ns, out, roots = pathlib.Path(sys.argv[1]), [int(x) for x in sys.argv[2].split(',')], sys.argv[3], sys.argv[4:]
want = set(ns)
ref = {}
for n in ns:
    rows = list(csv.DictReader(open(refdir / f'{n}.csv')))
    ref[n] = (hm.side_est(rows), A.centres(rows))


def stream(st, name):
    if name.lower().endswith('.json'):
        return hm.read_json(st) or {}
    rd = csv.reader(st)
    try:
        head = [h.strip().lower() for h in next(rd)]
    except StopIteration:
        return {}
    if all(c in head for c in ('after_x', 'after_y', 'after_angle')):
        head = [{'after_x': 'x', 'after_y': 'y', 'after_angle': 'angle', 'x': '_x', 'y': '_y', 'angle': '_a'}.get(h, h) for h in head]
    fixed = None
    if 'n' not in head:
        import re
        m = re.search(r'(?:^|[^a-z])n[=_]?0*(\d+)\.csv$', name.lower().rsplit('/', 1)[-1])
        if not m:
            return {}
        fixed = int(m.group(1))
        if fixed not in want:
            return {}
    need = ['x', 'y', 'angle'] + ([] if fixed else ['n'])
    if not all(c in head for c in need):
        return {}
    ix = {c: head.index(c) for c in need}
    res = {}
    for row in rd:
        try:
            n = fixed or int(float(row[ix['n']].strip().lstrip('s')))
        except (ValueError, IndexError):
            continue
        if n in want:
            try:
                res.setdefault(n, [[]])[0].append({'x': row[ix['x']].strip().lstrip('s'), 'y': row[ix['y']].strip().lstrip('s'), 'angle': row[ix['angle']].strip().lstrip('s')})
            except IndexError:
                pass
    return res


def meta_of(path):
    p = pathlib.Path(path.split('!')[0])
    for d in [p.parent] + list(p.parents)[:4]:
        m = d / 'meta.json'
        if m.exists():
            try:
                j = json.load(open(m))
                return j.get('license', ''), j.get('updated', j.get('lastRun', ''))
            except Exception:
                return '', ''
    return '', ''


with open(out, 'w') as fo:
    fo.write('n\tfile\tdside\tdist\tlicence\tupdated\n')
    for root in roots:
        files = sorted(p for p in pathlib.Path(root).rglob('*') if p.is_file() and (p.suffix in ('.csv', '.json', '.zip', '.gz')))
        for p in files:
            try:
                for name, st in hm.iter_texts(p):
                    try:
                        pz = stream(st, name)
                    except Exception as e:
                        print('err', name, e, file=sys.stderr); continue
                    for n, packs in pz.items():
                        if n not in want:
                            continue
                        for rows in packs:
                            if len(rows) != n:
                                continue
                            try:
                                L = hm.side_est(rows)
                            except ValueError:
                                continue
                            dL = L - ref[n][0]
                            if abs(dL) < 1e-7:
                                d = A.distance(ref[n][1], A.centres(rows))
                                lic, up = meta_of(name)
                                fo.write(f'{n}\t{name}\t{dL:.3e}\t{d:.3e}\t{lic}\t{up}\n'); fo.flush()
            except Exception as e:
                print('err', p, e, file=sys.stderr)
        print('root done', root, file=sys.stderr, flush=True)
