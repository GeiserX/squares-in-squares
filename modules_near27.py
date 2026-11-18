"""Export traced take rows and near designs for the module cut, changed files only (round 27).

Round 27: made from modules_near25.py. The trace is modules_policy27.trace27 (the Samanyu-dev rule is lifted), the
cache is new (near27-cache.json), so files refused only for Samanyu ancestry are traced again, and every exported
source names the sha256 of the bytes it copied.

Round 24 traced every take row and near file on every pass, and the last two
near scans hit their 120-second limit. This reader keeps one cache keyed by
file content, so each pass traces only files that are new or changed. Take
rows come before near files, and round 25 dirs come before round 24 dirs.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
import modules_policy27  # noqa: F401  (patches modules_sources24.trace_file)
from modules_near23 import side
from modules_sources24 import trace_file, clean_text

csv.field_size_limit(2**30)
CACHE = Path('near27-cache.json')


def _load():
    return json.loads(CACHE.read_text()) if CACHE.exists() else {}


def _save(cache):
    CACHE.with_suffix('.tmp').write_text(json.dumps(cache))
    os.replace(CACHE.with_suffix('.tmp'), CACHE)


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _trace(cache, path, n):
    key = f'{path}:{_digest(path)}'
    if key not in cache:
        proof = trace_file(path, n)
        cache[key] = dict(ok=bool(proof['ok']), source=proof.get('source', ''),
                          licence=proof.get('licence', ''), record=proof.get('record', ''))
    return cache[key]


def stage_take_cached(directory, out):
    """Same output as modules_sources24.stage_take, tracing only changed rows."""
    table = directory / 'take.tsv'
    if not table.exists():
        return None
    cache = _load()
    dest = out / directory.name
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in csv.DictReader(table.open(), delimiter='\t'):
        if not r.get('n', '').isdigit():
            continue
        n = int(r['n'])
        path = directory / f'{n}.csv'
        if not path.exists() or not clean_text(r.get('source', '') + ' ' + r.get('licence', '')):
            continue
        if not _trace(cache, path, n)['ok']:
            continue
        target = dest / path.name
        if not target.exists() or target.read_bytes() != path.read_bytes():
            target.write_bytes(path.read_bytes())
        rows.append(dict(n=n, source=f'{path} (sha256 {_digest(path)}): {r.get("source", "")}', licence=r.get('licence', '')))
    _save(cache)
    text = '\n'.join(['n\tsource\tlicence'] + [f"{x['n']}\t{x['source']}\t{x['licence']}" for x in rows]) + '\n'
    old = (dest / 'take.tsv').read_text() if (dest / 'take.tsv').exists() else None
    if old != text:
        with (dest / 'take.tsv.tmp').open('w', newline='') as h:
            w = csv.DictWriter(h, ['n', 'source', 'licence'], delimiter='\t')
            w.writeheader()
            w.writerows(rows)
        os.replace(dest / 'take.tsv.tmp', dest / 'take.tsv')
    return dest


def export(out, directories):
    out.mkdir(exist_ok=True, parents=True)
    cache = _load()
    traced = accepted = 0
    for directory in directories:
        lane, rnd = directory.name[5:].rsplit('-r', 1)
        for path in sorted((directory / 'near').glob('*.csv'), key=lambda p: -p.stat().st_mtime):
            dest = out / ('n' + lane.replace('-', '') + '-r' + rnd + 'v' + hashlib.sha1(str(path).encode()).hexdigest()[:8])
            try:
                n, length = side(path)
                if n < 300:
                    continue
                before = len(cache)
                proof = _trace(cache, path, n)
                traced += len(cache) > before
                if not proof['ok'] or not clean_text(proof['source'] + ' ' + proof['licence']):
                    continue
                accepted += 1
                target = dest / f'{n}.csv'
                if target.exists() and target.read_bytes() == path.read_bytes():
                    continue
                dest.mkdir(exist_ok=True)
                target.write_bytes(path.read_bytes())
                row = dict(n=n, source=f'{path} (sha256 {_digest(path)}, snapshot {target}): {proof["source"]}; ancestry record {proof["record"]}',
                           licence=proof['licence'] or f'own {lane}, sources in results/round23-best-2026-11-13.tsv')
                with (dest / 'take.tsv.tmp').open('w', newline='') as h:
                    w = csv.DictWriter(h, ['n', 'source', 'licence'], delimiter='\t')
                    w.writeheader()
                    w.writerow(row)
                os.replace(dest / 'take.tsv.tmp', dest / 'take.tsv')
            except (ValueError, TypeError, KeyError, IndexError, OSError):
                continue
            if traced and traced % 20 == 0:
                _save(cache)
    _save(cache)
    print('near files newly traced', traced, 'accepted', accepted, flush=True)


if __name__ == '__main__':
    export(Path(sys.argv[1]), list(map(Path, sys.argv[2:])))
