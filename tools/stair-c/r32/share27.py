"""Round 27 rule b: the prvsiyan SHARE test.

A layout is out if 0.4 or more of its squares lie within 1e-3 of the prvsiyan
best-of-1105 row of the same n. Centres are centred on their bounding box, and the
best of the 8 symmetries of the square is kept (the measure of harvest share_ac.py and
classfill prvsim26.py). The data file is read only.
  python -I share27.py N:FILE [N:FILE ...]
"""
import csv, functools, io, sys, zipfile
import numpy as np

PRV = '$SCRATCH/bounties-squares/take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
LIMIT = 0.4
csv.field_size_limit(1 << 26)


def centred(a):
    a = np.asarray(a, float)[:, :2]
    return a - (a.min(0) + a.max(0)) / 2


@functools.lru_cache(None)
def prv_rows():
    """Every version of each n in the zip (each csv apart), each centred on its own box.
    The test takes, for each square, the nearest centre over all versions: at least the
    share of harvest audit_ac (all csvs pooled) and of classfill prvsim26 (first csv)."""
    out = {}
    with zipfile.ZipFile(PRV) as z:
        for name in z.namelist():
            if not name.endswith('.csv'):
                continue
            rows = {}
            for r in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))):
                k = {str(a).strip().lower(): v for a, v in r.items()}
                if 'x' not in k or 'y' not in k:
                    continue
                m = str(k['n']).lstrip('s') if 'n' in k else str(k.get('id', '')).split('_')[0]
                if m.isdigit():
                    rows.setdefault(int(m), []).append((float(str(k['x']).lstrip('s')), float(str(k['y']).lstrip('s'))))
            for n, v in rows.items():
                out.setdefault(n, []).append(centred(np.array(v, float)))
    return out


@functools.lru_cache(None)
def tree(n):
    from scipy.spatial import cKDTree
    refs = prv_rows().get(int(n))
    return cKDTree(np.vstack(refs)) if refs else None


def share(n, xy):
    """Largest share of squares within 1e-3 of a prvsiyan centre over the 8 symmetries.
    The nearest centre over the union of the separately centred versions is the minimum
    over versions, so one tree per n serves every version."""
    t = tree(n)
    if t is None or len(xy) == 0:
        return 0.0
    a = centred(xy)
    best = 0.0
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                c = (a[:, ::-1] if sw else a) * np.array([sx, sy])
                d, _ = t.query(c, k=1)
                best = max(best, float((d < 1e-3).mean()))
    return best


def out(n, xy):
    return share(n, xy) >= LIMIT


def control():
    rows = prv_rows()
    n = 818
    ref = rows[n][-1]
    assert share(n, ref) == 1.0 and out(n, ref)
    flipped = ref.copy(); flipped[:, 0] = -flipped[:, 0]
    assert share(n, flipped) == 1.0
    moved = ref.copy(); moved[: len(moved) * 7 // 10] += 0.37
    assert not out(n, moved), share(n, moved)
    print('CONTROL share27: prvsiyan 818 against itself 1.000 (out), mirrored 1.000 (out), 70% moved', round(share(n, moved), 3), '(in)', flush=True)


if __name__ == '__main__':
    control()
    for spec in sys.argv[1:]:
        n, path = spec.split(':', 1)
        n = int(n)
        xy = np.array([[float(str(r['x']).lstrip('s')), float(str(r['y']).lstrip('s'))] for r in csv.DictReader(open(path)) if int(r['n']) == n])
        print(n, path, 'share1e-3', round(share(n, xy), 4), 'OUT' if out(n, xy) else 'in', flush=True)
