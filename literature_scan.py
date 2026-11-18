#!/usr/bin/env python3
"""Scan cloned public repos for a packing whose side beats the held side of its n. Files are data: parsed, never run.

  literature_scan.py HELD_DETAILS.csv OUT_SPEC.tsv DIR [DIR ...]         (run with python -I)

Reads, under every DIR:
  *.cert     "n S" then "x y t" per square, exact rationals, t = tan(theta/2) (Evan Daniel's format; Fang, de Winter)
  *.csv      submission format (columns n, x, y, angle in radians; a leading "s" on a value is dropped)
  *.txt      "s: S" or "Final s: S" then "Square k: x=.., y=.., deg=.." (Casson, Fang)
The side of a .cert or .txt is the stated one; the side of a csv n is the bounding box of its squares.
Writes the best file per n whose side is below the held L by more than 1e-9 * L, as a SPEC for literature_take.py
(n, path, format, source, licence, side, held_L). A csv hit is first cut out to OUT_SPEC.d/<n>.csv.
"""
import csv, math, os, re, sys
from fractions import Fraction


def side_cert(path):
    with open(path) as h:
        for l in h:
            if l.strip() and not l.startswith('#'):
                p = l.split()
                if len(p) != 2:
                    return None
                return int(p[0]), float(Fraction(p[1]))
    return None


def side_txt(path):
    head = open(path, errors='replace').read(400)
    m = re.search(r'^(?:Final )?s: (\S+)', head, re.M)
    if not m or 'Square 1:' not in head:
        return None
    n = len(re.findall(r'^Square \d+:', open(path, errors='replace').read(), re.M))
    return n, float(m.group(1))


def csv_sides(path):
    import numpy as np, pandas as pd
    try:
        df = pd.read_csv(path, dtype=str)
    except Exception:
        return {}
    cols = {c.lower(): c for c in df.columns}
    if not {'n', 'x', 'y', 'angle'} <= set(cols) and not {'id', 'x', 'y', 'deg'} <= set(cols):
        return {}
    if 'n' not in cols:
        return {}
    try:
        f = lambda c: df[cols[c]].str.lstrip('s').astype(float).to_numpy()
        n, x, y, a = df[cols['n']].str.lstrip('s').astype(float).astype(int).to_numpy(), f('x'), f('y'), f('angle')
    except Exception:
        return {}
    h = (np.abs(np.cos(a)) + np.abs(np.sin(a))) / 2
    out = {}
    for k in np.unique(n):
        m = n == k
        if m.sum() != k or k > 1000:
            continue
        out[int(k)] = (float(max((x[m] + h[m]).max() - (x[m] - h[m]).min(), (y[m] + h[m]).max() - (y[m] - h[m]).min())), df[m])
    return out


def main():
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(sys.argv[1]))}
    spec, dirs = sys.argv[2], sys.argv[3:]
    best, seen = {}, {'cert': 0, 'csv': 0, 'txt': 0}
    cut = spec + '.d'
    for d in dirs:
        lic = ''
        for name in ('LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING'):
            if os.path.exists(os.path.join(d, name)):
                lic = open(os.path.join(d, name), errors='replace').readline().strip()[:40] or name
        for root, sub, files in os.walk(d):
            sub[:] = [s for s in sub if s != '.git' and s != 'node_modules']
            for fn in files:
                p = os.path.join(root, fn)
                try:
                    if fn.endswith('.cert'):
                        r = side_cert(p); seen['cert'] += 1
                        got = {r[0]: (r[1], None)} if r else {}
                        fmt = 'cert'
                    elif fn.endswith('.txt') and os.path.getsize(p) < 5e6:
                        r = side_txt(p); seen['txt'] += bool(r)
                        got = {r[0]: (r[1], None)} if r else {}
                        fmt = 'txt'
                    elif fn.endswith('.csv') and os.path.getsize(p) > 200:
                        got = csv_sides(p); seen['csv'] += bool(got)
                        fmt = 'csv'
                    else:
                        continue
                except Exception as e:
                    print('skip', p, type(e).__name__, file=sys.stderr); continue
                for n, (s, df) in got.items():
                    if n in held and s * s >= n - 1e-9 and s < held[n] - 1e-9 * held[n] and (n not in best or s < best[n][0]):
                        path = p
                        if df is not None:
                            os.makedirs(cut, exist_ok=True)
                            path = os.path.join(cut, '%d.csv' % n)
                            df.to_csv(path, index=False)
                        best[n] = (s, path, fmt, os.path.relpath(p, os.path.dirname(d.rstrip('/'))), lic or 'no licence file')
    with open(spec, 'w') as h:
        h.write('n\tpath\tformat\tsource\tlicence\tside\theld_L\n')
        for n, (s, path, fmt, src, lic) in sorted(best.items()):
            h.write('%d\t%s\t%s\t%s\t%s\t%r\t%r\n' % (n, path, fmt, 'github.com/' + src.replace('_', '/', 1), lic, s, held[n]))
            print('beats held', n, '%.12f' % s, '%.12f' % held[n], '%.3e' % (held[n] - s), src)
    print('files read', seen, ' n that beat held:', len(best))


if __name__ == '__main__':
    main()
