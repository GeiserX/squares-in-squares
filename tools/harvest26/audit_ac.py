"""Audit public rows by n: certified score (floatsafe), and geometry distance to excluded layouts.

  python -I audit_ac.py N[,N...] FILE [FILE ...]
Data files are read only. Prints, per n and file: rows, certified score, base bar, gain, and the
smallest symmetric centre distance to each excluded layout of remaining exclusions that exists for that n.
"""
import csv, io, math, sys, zipfile
from pathlib import Path
import numpy as np
L = '.'
sys.path.insert(0, L)
import floatsafe
S = Path('$SCRATCH/bounties-squares')
csv.field_size_limit(1 << 26)
bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv'))}


def norm(r):
    k = {str(kk).strip().lower(): v for kk, v in r.items()}
    if 'x' not in k or 'y' not in k:
        return {'n': ''}
    n = str(k.get('n', k.get('id', ''))).lstrip('s')
    return {'n': n, 'x': str(k['x']).lstrip('s'), 'y': str(k['y']).lstrip('s'), 'angle': str(k.get('angle', k.get('deg', '0'))).lstrip('s')}


def read(path, want):
    out = {n: [] for n in want}
    if path.endswith('.zip'):
        with zipfile.ZipFile(path) as z:
            for name in z.namelist():
                if name.endswith('.csv'):
                    for r in csv.DictReader(io.StringIO(z.read(name).decode('utf-8-sig'))):
                        r = norm(r)
                        if r['n'].isdigit() and int(r['n']) in out:
                            out[int(r['n'])].append(r)
        return out
    with open(path) as f:
        rd = csv.DictReader(f)
        for r in rd:
            if 'id' in r and 'n' not in r:
                n = int(r['id'].split('_')[0])
                if n in out:
                    out[n].append(norm({'n': n, 'x': r['x'], 'y': r['y'], 'angle': r.get('deg', r.get('angle'))}))
                continue
            r = norm(r)
            if r['n'].isdigit() and int(r['n']) in out:
                out[int(r['n'])].append(r)
    return out


def centres(rows):
    a = np.array([[float(r['x']), float(r['y'])] for r in rows])
    return a - (a.min(0) + a.max(0)) / 2


def distance(a, b):
    if len(a) != len(b):
        return math.inf
    best = math.inf
    for sw in (False, True):
        for sx in (1, -1):
            for sy in (1, -1):
                c = a[:, ::-1] if sw else a
                c = c * np.array([sx, sy])
                d = np.sqrt(((c[:, None, :] - b[None, :, :]) ** 2).sum(-1)).min(1).max()
                best = min(best, d)
    return float(best)


def excluded(n):
    out = []
    if n in (639, 691, 745, 858, 918):
        for p in (S/f'take-harvest-r22/{n}.csv', S/f'take-harvest-r22/work/public/starts/{n}/{n}.csv'):
            if p.exists():
                out.append((str(p), read(str(p), [n])[n]))
        sub = S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/submission.csv'
        if sub.exists():
            out.append(('areebbb submission.csv', read(str(sub), [n])[n]))
    if n == 980 and (S/'take-forensics-r23/980.csv').exists():
        out.append(('take-forensics-r23/980.csv', read(str(S/'take-forensics-r23/980.csv'), [n])[n]))
    z = S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
    if z.exists():
        out.append(('prvsiyan 1105 (CC BY-SA)', read(str(z), [n])[n]))
    return [(l, r) for l, r in out if len(r) == n]


def main():
  ns = [int(x) for x in sys.argv[1].split(',')]
  files = sys.argv[2:]
  data = {f: read(f, ns) for f in files}
  for n in ns:
      ex = [(l, centres(r)) for l, r in excluded(n)]
      for f in files:
          rows = data[f][n]
          if len(rows) != n:
              print(n, Path(f).name, 'rows', len(rows)); continue
          rr = [{'n': str(n), 'square_id': str(i), 'x': r['x'], 'y': r['y'], 'angle': r['angle']} for i, r in enumerate(rows)]
          _, fr, sc, e = floatsafe.work((n, rr))
          c = centres(rows)
          ds = ' '.join(f'{l[:40]}={distance(c, b):.3g}' for l, b in ex)
          print(n, Path(f).parent.name[:30] + '/' + Path(f).name, 'cert', sc, 'eps', e, 'bar', bar[n], 'gain', bar[n] - sc, '| excl:', ds or 'none', flush=True)


if __name__ == '__main__':
    main()
