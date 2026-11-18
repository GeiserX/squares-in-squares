"""Walk round 38 sources using submitted roots and frozen public shares."""
import functools
import hashlib
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['QUENCH_LIVE_ROUND'] = '38'

import forensics_held37 as held_index
import forensics_memory36 as memory
import quench_walk as walker

ROOT = Path(walker.S)
WORK = ROOT / 'take-forensics-r38/work'
FROZEN_INDEX = held_index.ROOT
WITHDRAWN_BYTES = {
    '5a4c0cdb48b0893b54b03718cb9df0a33cde2dc4e9d232e31c036c2d0349d44f',
    '94740134aabf0aeed3e34e7f743a44ca68b5f9be4d6e3d3b1d49a694fbb2d8fe',
}
WITHDRAWN_695 = ROOT / 'take-harvest-r26/695.csv'
WITHDRAWN_695_AT = walker.withdraw_time('2026-11-14T15:18:34Z')


@functools.lru_cache(maxsize=1)
def configure():
    held_index.ROOT = WORK / 'held-index'
    held_index.ROOT.mkdir(exist_ok=True)
    previous_index = held_index.index

    def index(path, size, stamp):
        key = hashlib.sha256(f'{path}|{size}|{stamp}'.encode()).hexdigest()
        cached = FROZEN_INDEX / f'{key}.json'
        if cached.is_file():
            return read_json(cached)
        return previous_index(path, size, stamp)

    @functools.lru_cache(maxsize=4096)
    def held_root(n, requested_round=None):
        for number, path in sorted(walker.submitted_gathers(), reverse=True):
            if requested_round is None or requested_round == number:
                stat = Path(path).stat()
                row = index(path, stat.st_size, stat.st_mtime_ns)['rows'].get(str(n))
                if row:
                    return f'own submitted layout, count {n}, round {number}, row sha256 {row}'
        return original_held(n, requested_round)

    original_held = walker.held
    held_index.index = index
    walker.held = held_root
    walker.held_gather = held_index.held_gather
    # The legacy centre-only comparison is neither a prefilter nor evidence.
    walker.prv_share = lambda path, n: (0.0, 0.0, 0.0, 0.0)
    walker.PRE = 0
    walker.pol_fail = frozen_share


@functools.lru_cache(maxsize=64)
def read_json(path):
    return json.loads(path.read_text())


@functools.lru_cache(maxsize=1)
def share_module():
    sys.path.insert(0, str(ROOT / 'take-assemble-r31/scripts'))
    import share31
    archives = read_json(WORK / 'share/zips.json')
    for name, digest in archives:
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'frozen comparison archive changed: {name}')
    share31.zips = lambda: [tuple(item) for item in archives]
    return share31


@functools.lru_cache(maxsize=8)
def references(n):
    import numpy as np
    share = share_module()
    held_seeds = [share.read_rows((ROOT / 'seeds' / f'{name}.csv').read_text(), {n}).get(n)
                  for name in ('samanyu_bestfit', 'samanyu_22249')]
    public = share.pub_rows({n})
    return [(name, rows[n]) for name, rows in public.items() if n in rows and not any(
        seed is not None and len(rows[n]) == len(seed) and np.abs(rows[n] - seed).max() < 1e-7
        for seed in held_seeds)]


@functools.lru_cache(maxsize=128)
def frozen_share(path, n):
    share = share_module()
    comparisons = references(n)
    if not comparisons:
        return False, ''
    candidate = share.item_rows(path, n)
    if candidate is None or len(candidate) != n:
        raise ValueError(f'missing {n} rows in public source {path}')
    for version, rows in comparisons:
        result = share.share(candidate, rows)
        if max(result[1e-3], result[1e-2]) >= 0.4:
            return True, f'1105 share {result[1e-3]:.6f} at 1e-3, {result[1e-2]:.6f} at 1e-2; {version}'
    return False, ''


def check(path):
    configure()
    result = walker.check(str(path), cap=100000)
    for source in (*walker.LAST_VIA, str(path)):
        if not isinstance(source, str) or not source.endswith('.csv'):
            continue
        if walker._through_held(source, walker.LAST_VIA):
            continue
        candidate = Path(source)
        old_695 = candidate == WITHDRAWN_695 and (
            not candidate.exists() or candidate.stat().st_mtime <= WITHDRAWN_695_AT)
        pinned = candidate.is_file() and candidate.stat().st_size < 2_000_000 and (
            walker.file_sha(source) in WITHDRAWN_BYTES)
        if old_695 or pinned:
            result['hits'].append(f'direct withdrawn input: {source}')
            result['clean'] = False
    result.pop('prv_share', None)
    return result


if __name__ == '__main__':
    memory.start_guard(sys.argv[1])
    print(json.dumps(check(Path(sys.argv[1]))), flush=True)
