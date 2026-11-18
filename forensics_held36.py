"""Index submitted held rows without retaining whole submissions in memory."""
import csv
import functools
import hashlib
import json
import os
from pathlib import Path
import quench_walk as qw

ROOT = Path('$SCRATCH/bounties-squares/take-forensics-r36/work/held-index')
ROOT.mkdir(parents=True, exist_ok=True)
matched = {}


def digest(rows):
    values = sorted(tuple(0.0 if float(r[k]) == 0 else float(r[k]) for k in ('x', 'y', 'angle')) for r in rows)
    return hashlib.sha256(repr(values).encode()).hexdigest()


@functools.lru_cache(maxsize=64)
def index(path, size, stamp):
    key = hashlib.sha256(f'{path}|{size}|{stamp}'.encode()).hexdigest()
    target = ROOT / f'{key}.json'
    if target.exists():
        return json.loads(target.read_text())
    groups = {}
    for row in csv.DictReader(open(path)):
        n = int(row['n'])
        groups.setdefault(n, []).append(tuple(0.0 if float(row[k]) == 0 else float(row[k]) for k in ('x', 'y', 'angle')))
    output = {str(n): hashlib.sha256(repr(sorted(rows)).encode()).hexdigest() for n, rows in groups.items() if len(rows) == n}
    record = dict(path=path, size=size, stamp=stamp, sha256=qw.file_sha(path), rows=output)
    temporary = target.with_name(target.name + f'.{os.getpid()}.tmp')
    temporary.write_text(json.dumps(record))
    os.replace(temporary, target)
    return record


@functools.lru_cache(maxsize=32768)
def lookup(path, size, stamp, n):
    rows = list(csv.DictReader(open(path)))
    if len(rows) != n or any(int(row['n']) != n for row in rows):
        return None
    actual = digest(rows)
    for k, gather in sorted(qw.submitted_gathers(), reverse=True):
        st = os.stat(gather)
        record = index(gather, st.st_size, st.st_mtime_ns)
        if record['rows'].get(str(n)) == actual:
            return k, os.path.basename(gather)
    return None


def held_gather(path, n):
    if not isinstance(path, str) or not path.endswith('.csv') or '/gather/' in path:
        return None
    try:
        st = os.stat(path)
        if st.st_size > 2_000_000:
            return None
        first = next(csv.DictReader(open(path)), None)
        actual_n = int(first['n']) if first else 0
        if not 1 <= actual_n <= 1000:
            return None
        result = lookup(path, st.st_size, st.st_mtime_ns, actual_n)
        if result:
            matched[path] = dict(n=actual_n, submitted_round=result[0], numeric_row_sha256=digest(list(csv.DictReader(open(path)))))
        return result
    except (OSError, ValueError, KeyError, TypeError, csv.Error):
        return None
