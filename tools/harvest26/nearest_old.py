"""For each n: the public layouts closest to our take row by share of squares within 1e-3 (data, read only).

  python -I nearest_old.py TAKEDIR N[,N...] OUT.tsv ROOT [ROOT ...]
Every csv/json (also in zip/gz) under the roots is streamed. For each n, every packing with n squares whose float
side is within 2e-3 of the take row's side is compared with the take row (share at 1e-3 and 1e-2, max centre
distance, best of 8 symmetries). Rows of OUT: n, file, licence, updated, share1e3, share1e2, maxd, dside.
The prvsiyan 1105 layout and our held layout are compared the same way, so one table shows whether a row is
closer to a layout of rule b than to clean older layouts.
"""
import csv, json, math, pathlib, re, sys
sys.path.insert(0, '.')
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import harvest_merge as hm  # noqa: E402
import audit_ac as A  # noqa: E402
from share_ac import share  # noqa: E402
csv.field_size_limit(1 << 26)
S = '$SCRATCH/bounties-squares/'
take, ns, out, roots = pathlib.Path(sys.argv[1]), [int(x) for x in sys.argv[2].split(',')], sys.argv[3], sys.argv[4:]
want = set(ns)
ref = {}
for n in ns:
    rows = list(csv.DictReader(open(take / f'{n}.csv')))
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
        m = re.search(r'(?:^|[^a-z])n[=_]?0*(\d+)\.csv$', name.lower().rsplit('/', 1)[-1])
        if not m or int(m.group(1)) not in want:
            return {}
        fixed = int(m.group(1))
    need = ['x', 'y', 'angle'] + ([] if fixed else ['n'])
    if not all(c in head for c in need):
        return {}
    ix = {c: head.index(c) for c in need}
    res = {}
    for row in rd:
        try:
            n = fixed or int(float(row[ix['n']].strip().lstrip('s')))
            if n in want:
                res.setdefault(n, [[]])[0].append({c: row[ix[c]].strip().lstrip('s') for c in ('x', 'y', 'angle')})
        except (ValueError, IndexError):
            continue
    return res


def meta_of(path):
    p = pathlib.Path(path.split('!')[0])
    for d in [p.parent] + list(p.parents)[:4]:
        m = d / 'meta.json'
        if m.exists():
            try:
                j = json.load(open(m)); return j.get('license', ''), j.get('updated', j.get('lastRun', ''))
            except Exception:
                return '', ''
    return '', ''


seen = set()
with open(out, 'w') as fo:
    fo.write('n\tfile\tlicence\tupdated\tshare1e3\tshare1e2\tmaxd\tdside\n')
    extra = [(S + 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip', 'RULE-B prvsiyan 1105'),
             (S + 'gather/round25-2026-11-14b.csv', 'HELD r25b')]
    for path, label in extra:
        got = A.read(path, ns)
        for n in ns:
            if len(got[n]) == n:
                s = share(ref[n][1], A.centres(got[n]))
                fo.write(f'{n}\t{label}\t\t\t{s[1]:.3f}\t{s[2]:.3f}\t{s[3]:.3g}\t\n'); fo.flush()
    for root in roots:
        for p in sorted(x for x in pathlib.Path(root).rglob('*') if x.is_file() and x.suffix in ('.csv', '.json', '.zip', '.gz') and x.name != 'meta.json'):
            try:
                for name, st in hm.iter_texts(p):
                    for n, packs in stream(st, name).items():
                        for rows in packs:
                            if len(rows) != n:
                                continue
                            try:
                                L = hm.side_est(rows)
                            except ValueError:
                                continue
                            if abs(L - ref[n][0]) > 2e-3:
                                continue
                            key = (n, round(L, 11))
                            if key in seen:
                                continue
                            seen.add(key)
                            s = share(ref[n][1], A.centres(rows))
                            lic, up = meta_of(name)
                            fo.write(f'{n}\t{name}\t{lic}\t{up}\t{s[1]:.3f}\t{s[2]:.3f}\t{s[3]:.3g}\t{L - ref[n][0]:.3e}\n'); fo.flush()
            except Exception as e:
                print('err', p, e, file=sys.stderr)
        print('root done', root, file=sys.stderr, flush=True)
