"""Save each completed module target before starting the next one."""
import csv
import json
import math
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules as M

FIELDS = 'n m held_side predicted_side predicted_minus_held stop rank corner far1 far2 stacks1 stacks2 f'.split()


def save(path, value):
    path = Path(path)
    path.with_suffix(path.suffix + '.tmp').write_text(json.dumps(value))
    os.replace(str(path) + '.tmp', path)


def export(path, record):
    with open(str(path) + '.tmp', 'w', newline='') as h:
        w = csv.writer(h, delimiter='\t')
        w.writerow(FIELDS)
        for n in record['done']:
            w.writerows(record['rows'][str(n)])
    os.replace(str(path) + '.tmp', path)


def targets(ns, record, solve, checkpoint, out):
    """A failed solve leaves its target pending. Empty results still complete it."""
    for n in ns:
        if n in record['done']:
            continue
        rows = solve(n)
        record['rows'][str(n)] = rows
        record['done'].append(n)
        save(checkpoint, record)
        export(out, record)
        print('completed target', n, 'choices', len(rows), flush=True)


def queue(a):
    work, details, out = a[:3]
    def option(name, default):
        return a[a.index(name) + 1] if name in a else default
    top = int(option('--top', 3))
    slack = float(option('--slack', .003))
    need = set(Path(option('--need', '')).read_text().split()) if '--need' in a else None
    depth = float(option('--depth', .05))
    floor = float(option('--min-margin', -.005))
    held = {int(r['n']): float(r['L']) for r in csv.DictReader(open(details))}
    lib = M.Library(work, only=M.usable)
    ns = [n for n in sorted(held) if n >= 300 and held[n] < math.isqrt(n-1)+1-1e-9]
    if '--ns' in a:
        ns = [int(x) for x in Path(option('--ns', '')).read_text().split() if int(x) in held]
    cp = Path(option('--checkpoint', str(out) + '.checkpoint.json'))
    record = json.loads(cp.read_text()) if cp.exists() else dict(done=[], rows={})
    export(out, record)
    def solve(n):
        m = math.isqrt(n-1)
        rows = []
        for rank, (f, stop, c, f1, f2, s1, s2) in enumerate(lib.best(
                n, top=top, below=held[n]-m+slack, need=need, distinct=True,
                foreign='--foreign' in a, depth=depth, above=held[n]-m+floor)):
            rows.append([n, m, held[n], m+f, m+f-held[n], stop, rank+1,
                         c['id'], f1['id'], f2['id'], s1, s2, f])
        return rows
    targets(ns, record, solve, cp, out)
    print('done', len(ns), flush=True)
