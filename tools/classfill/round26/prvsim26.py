"""How much of a layout matches the prvsiyan best-of-1105 row of the same n (rule b of round 26).

  python -I prvsim26.py N:FILE [N:FILE ...]

FILE is a csv (n,x,y,angle or id,x,y,deg) or a zip of such csvs. Data files are read only.
Centres are centred on their bounding box. Under the best of the 8 symmetries of the square, each square
gets the distance to the nearest prvsiyan centre. Printed per layout:
  max          the largest of those distances (the harvest 'max centre distance' measure)
  within1e-3   share of squares whose centre is within 1e-3 of a prvsiyan centre
  within1e-2   the same within 1e-2 (mostly the shared unit grid; it does not separate designs)
  tilted-match share of tilted squares within 1e-2 of a prvsiyan square with the same angle mod 90 (0.06 deg)
Round 26 measures: harvest 818 0.004, harvest 706 0.001, harvest 971 0.000; the round 25 b base 818 0.573,
706 0.527, 971 0.483; the harvest rows withdrawn at 15:18 UTC 0.42 to 0.76.
"""
import csv, io, sys, zipfile
import numpy as np

PRV = '$SCRATCH/bounties-squares/take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
csv.field_size_limit(1 << 26)


def rows_of(text, n):
    out = []
    for r in csv.DictReader(io.StringIO(text)):
        k = {str(a).strip().lower(): v for a, v in r.items()}
        if 'x' not in k or 'y' not in k:
            continue
        if 'n' in k:
            m = str(k['n']).lstrip('s')
        else:
            m = str(k.get('id', '')).split('_')[0]
        if m.isdigit() and int(m) == n:
            out.append((float(str(k['x']).lstrip('s')), float(str(k['y']).lstrip('s')),
                        float(str(k.get('angle', k.get('deg', '0'))).lstrip('s'))))
    return out


def read(path, n):
    if path.endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            for name in sorted(z.namelist(), key=lambda name: name != "submission.csv"):
                if name.endswith('.csv'):
                    r = rows_of(z.read(name).decode('utf-8-sig'), n)
                    if r:
                        return r
        return []
    return rows_of(open(path).read(), n)


def arr(rows):
    a = np.array([[x, y] for x, y, _ in rows])
    return a - (a.min(0) + a.max(0)) / 2, np.array([t for _, _, t in rows]) % 90.0


def sim(a, b):
    (ca, aa), (cb, ab) = a, b
    best = None
    tilt = np.minimum(aa % 90, 90 - aa % 90) > 1e-3
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                c = (ca[:, ::-1] if sw else ca) * np.array([sx, sy])
                ang = aa.copy()
                if sw:
                    ang = (90 - ang) % 90
                if sx * sy < 0:
                    ang = (90 - ang) % 90
                d = np.sqrt(((c[:, None, :] - cb[None, :, :]) ** 2).sum(-1))
                j = d.argmin(1)
                dm = d.min(1)
                da = np.abs(((ang - ab[j]) + 45) % 90 - 45)
                r = (dm.max(), (dm < 1e-3).mean(), (dm < 1e-2).mean(), int(tilt.sum()),
                     ((dm < 1e-2) & (da < 0.06) & tilt).sum() / max(1, tilt.sum()))
                if best is None or (r[1], r[2]) > (best[1], best[2]):
                    best = r
    return best


for spec in sys.argv[1:]:
    n, path = spec.split(':', 1)
    n = int(n)
    p, q = read(PRV, n), read(path, n)
    if len(p) != n or len(q) != n:
        print(n, path, 'rows', len(p), len(q))
        continue
    r = sim(arr(q), arr(p))
    print(f'{n} {path}: max {r[0]:.3f} within1e-3 {r[1]:.3f} within1e-2 {r[2]:.3f} tilted {r[3]} tilted-match {r[4]:.3f}', flush=True)
