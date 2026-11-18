#!/usr/bin/env python3
"""Export near layouts as take directories for the modules cut.

CSV angles are radians. Keep the best archived layout per n, and every distinct
round 23 side, so an older smaller near file cannot hide a new construction.
"""
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import re


def side(path):
    rows = list(csv.DictReader(path.open()))
    n = int(rows[0]['n'])
    if len(rows) != n:
        raise ValueError('wrong count')
    lo = [math.inf, math.inf]
    hi = [-math.inf, -math.inf]
    for row in rows:
        x, y, a = (float(str(row[k]).lstrip('s')) for k in ('x', 'y', 'angle'))
        e = .5 * (abs(math.cos(a)) + abs(math.sin(a)))
        for axis, value in enumerate((x, y)):
            lo[axis] = min(lo[axis], value - e)
            hi[axis] = max(hi[axis], value + e)
    return n, max(hi[0] - lo[0], hi[1] - lo[1])


def export(out, directories):
    out.mkdir(parents=True, exist_ok=True)
    written = 0
    for directory in directories:
        if directory.name.startswith('take-modules-'):
            continue
        lane, rnd = directory.name[5:].rsplit('-r', 1)
        candidates = {}
        for path in sorted((directory / 'near').glob('*.csv')):
            try:
                n, length = side(path)
                if n < 300:
                    continue
            except (ValueError, TypeError, KeyError, IndexError, OSError):
                continue
            key = (n, round(length, 7)) if rnd == '23' else (n,)
            if key not in candidates or length < candidates[key][0]:
                candidates[key] = (length, path, n)
        groups = {}
        for length, path, n in candidates.values():
            variant = ('v' + hashlib.sha1(str(path).encode()).hexdigest()[:8]) if rnd == '23' else ''
            dest = out / ('n' + lane.replace('-', '') + '-r' + rnd + variant)
            groups.setdefault(dest, []).append((length, path, n))
        for dest, values in groups.items():
            dest.mkdir(exist_ok=True)
            rows = []
            for length, path, n in sorted(values):
                target = dest / f'{n}.csv'
                data = path.read_bytes()
                if not target.exists() or target.read_bytes() != data:
                    target.with_suffix('.csv.tmp').write_bytes(data)
                    os.replace(str(target) + '.tmp', target)
                    written += 1
                source = f'{directory.name} near/{path.name} (side {length:.9f})'
                licence = f'ours ({lane}), on sources in results/round21-best-2026-11-13.tsv and {directory}/take.tsv'
                for sidecar in (Path(str(path) + '.json'), path.with_suffix('.json')):
                    if not sidecar.exists():
                        continue
                    try:
                        metadata = json.loads(sidecar.read_text())
                    except (ValueError, OSError):
                        continue
                    if metadata.get('source'):
                        source += ': ' + str(metadata['source'])
                    if metadata.get('licence'):
                        licence = str(metadata['licence'])
                    source += '; sidecar ' + str(sidecar)
                    break
                source_table = directory / 'work/sources-all.tsv'
                donor = re.search(r'from(\d+-r\d+h[a-zA-Z0-9]+)', path.stem)
                if donor and source_table.exists():
                    for record in csv.DictReader(source_table.open(), delimiter='\t'):
                        if record.get('donor') == donor[1]:
                            source += ': ' + record.get('source', '')
                            licence = record.get('licence') or licence
                            break
                    source += '; donor source table ' + str(source_table)
                near_table = directory / 'near/near.tsv'
                if near_table.exists():
                    source += '; near source table ' + str(near_table)
                rows.append(dict(n=n, source=source, licence=licence))
            with (dest / 'take.tsv.tmp').open('w', newline='') as h:
                writer = csv.DictWriter(h, ['n', 'source', 'licence'], delimiter='\t')
                writer.writeheader()
                writer.writerows(rows)
            os.replace(dest / 'take.tsv.tmp', dest / 'take.tsv')
    print('near layouts written', written)


if __name__ == '__main__':
    export(Path(sys.argv[1]), list(map(Path, sys.argv[2:])))
