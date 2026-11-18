#!/usr/bin/env python3
"""Complete the existing walker with a 100000-file limit and expose that limit."""
import hashlib
import json
import os
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ['QUENCH_LIVE_ROUND'] = '37'
import quench_walk as qw
import forensics_held37 as held_index
import forensics_memory36 as memory
qw.held_gather = held_index.held_gather
# Keep public-only measurements on the ten frozen round-31 archives.
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools/harvest31'))
import policy
frozen = json.loads(Path('$SCRATCH/bounties-squares/take-forensics-r37/work/share/zips.json').read_text())
def frozen_paths():
    paths = []
    for name, digest in frozen:
        path = Path(name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('frozen share archive changed')
        paths.append(path)
    return tuple(paths)
policy.archive_paths = frozen_paths
original = qw.walk
original_held = qw.held
original_jtext = qw.jtext
original_norm = qw.norm
byte_roots = {}
resolved_aliases = {}
source_aliases = {
    'harvest/near/683-public34-502b5af49b6fe836.csv': (
        '$SCRATCH/bounties-squares/take-quench-r37/work/harvest/near/683-public34-502b5af49b6fe836.csv',
        '5a1aa967b2da7ec23dd7b6b90d524cee18b57d412ca4cdca9d399231cb7f84b4'),
}
audit_pointer = re.compile(r'(?:$SCRATCH/bounties-squares/)?take-forensics-r\d+/work/walks/[A-Za-z0-9_.-]+\.json')


def source_path(path):
    alias = path.removeprefix(qw.S)
    if alias in source_aliases:
        target, expected = source_aliases[alias]
        candidate = Path(target)
        if candidate.is_file() and hashlib.sha256(candidate.read_bytes()).hexdigest() == expected:
            resolved_aliases[alias] = dict(path=target, sha256=expected)
            return target
    return original_norm(path)


def source_text(path, n):
    return audit_pointer.sub('[walk audit omitted]', original_jtext(path, n))


qw.jtext = source_text
qw.norm = source_path

def held_root(n, k=None):
    if not 1 <= n <= 1000:
        return None
    candidates = [(rk, path) for rk, path in qw.submitted_gathers() if k is None or rk == k]
    for rk, path in sorted(candidates, reverse=True):
        stat = Path(path).stat()
        entry = held_index.index(path, stat.st_size, stat.st_mtime_ns)
        row_hash = entry['rows'].get(str(n))
        if row_hash:
            byte_roots[(n, k)] = dict(n=n, requested_round=k, submitted_round=rk,
                                     gather_sha256=entry['sha256'], numeric_row_sha256=row_hash)
            return f'own submitted held root n={n}, round={rk}, numeric row sha256 {row_hash}'
    return original_held(n, k)


def full_walk(start, n, cap=100000):
    # A submitted layout is an owned root. Its historical credits are not new inputs.
    qw.held = held_root
    try:
        return original(start, n, cap=cap)
    finally:
        qw.held = original_held
qw.walk = full_walk
for path in sys.argv[1:]:
    memory.start_guard(path)
    result = qw.check(path, cap=100000)
    result['capped'] = result.get('files', 0) >= 100000
    result['cap'] = 100000
    result['indexed_submitted_roots'] = list(byte_roots.values())
    result['matched_numeric_ancestors'] = held_index.matched
    result['resolved_source_aliases'] = resolved_aliases
    result['sampled_physical_peak_bytes'] = max(memory.peak, memory.footprint())
    print(json.dumps(result), flush=True)
