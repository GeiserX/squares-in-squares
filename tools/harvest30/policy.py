"""Round 28 geometry policy. Public data stays separate from executable code."""
import csv
import functools
import hashlib
import json
import os
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L / 'tools/harvest26'))
import audit_ac as A
S = Path('$SCRATCH/bounties-squares')


def share(a, b):
    tree = cKDTree(b)
    best = (0., 0., 0., float('inf'))
    for swap in (False, True):
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = (a[:, ::-1] if swap else a) * [sx, sy]
                d = tree.query(c)[0]
                r = (float((d < 1e-6).mean()), float((d < 1e-3).mean()), float((d < 1e-2).mean()), float(d.max()))
                if r[1:3] > best[1:3] or (r[1:3] == best[1:3] and r[3] < best[3]):
                    best = r
    return best


@functools.lru_cache(maxsize=1)
def prvsiyan():
    p = S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
    import io, zipfile
    coords = {}
    with zipfile.ZipFile(p) as z:
        with z.open('submission.csv') as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding='utf-8-sig')):
                coords.setdefault(int(r['n']), []).append((float(r['x']), float(r['y'])))
    result = {}
    for n, rows in coords.items():
        a = np.array(rows)
        result[n] = a - (a.min(0)+a.max(0))/2
    return result


@functools.lru_cache(maxsize=1000)
def excluded(n):
    centres = prvsiyan().get(n, [])
    out = [('prvsiyan 1105', centres)] if len(centres) == n else []
    if n in (639, 691, 745, 858, 918, 980):
        out += [(label, A.centres(rows)) for label, rows in A.excluded(n) if not label.startswith('prvsiyan')]
    return out


def audit(rows):
    n = int(rows[0]['n'])
    c = A.centres(rows)
    result = [{'label': label, 'share1e6': (s := share(c, e))[0], 'share1e3': s[1], 'maxd': s[3]} for label, e in excluded(n)]
    return not any(r['share1e3'] >= .4 for r in result), result


def snapshot(src, directory):
    src = Path(src)
    raw = src.read_bytes()
    key = hashlib.sha256(raw).hexdigest()
    dst = Path(directory)/f'{src.stem}-{key[:16]}{src.suffix}'
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if hashlib.sha256(dst.read_bytes()).hexdigest()!=key:raise ValueError('existing snapshot bytes differ from their hash')
    else:
        temporary=Path(str(dst)+'.tmp-'+str(os.getpid()))
        try:
            temporary.write_bytes(raw);temporary.replace(dst)
        finally:
            if temporary.exists():temporary.unlink()
    return dst, key


def control():
    p = S/'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
    rows = A.read(str(p), [858])[858]
    ok, evidence = audit(rows)
    assert not ok and evidence[0]['share1e3'] == 1., evidence
    p = S/'take-harvest-r26/work/cand/453.csv'
    ok2, evidence2 = audit(list(csv.DictReader(p.open())))
    assert ok2 and evidence2[0]['share1e3'] < .02, evidence2
    print('CONTROL exact prvsiyan 858 excluded share=1.000; independent 453 accepted share='+str(evidence2[0]['share1e3']), flush=True)
    return evidence, evidence2


if __name__ == '__main__':
    control()
