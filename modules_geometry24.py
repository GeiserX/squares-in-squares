"""Compare complete module builds before repeating a kick."""
import csv
import hashlib
import json
import math
from pathlib import Path


def key(path):
    values = []
    for r in csv.DictReader(Path(path).open()):
        values.append(tuple(float(str(r[k]).lstrip('s')) for k in ('x', 'y', 'angle')))
    # Quarter turns and translations describe the same geometry.
    variants = []
    for turn in range(4):
        p = []
        for x, y, a in values:
            for _ in range(turn):
                x, y = -y, x
            p.append((x, y, a % (math.pi/2)))
        x0 = min(v[0] for v in p)
        y0 = min(v[1] for v in p)
        variants.append(sorted((round(x-x0, 7), round(y-y0, 7), round(a, 7)) for x, y, a in p))
    return hashlib.sha256(json.dumps(min(variants), separators=(',', ':')).encode()).hexdigest()
