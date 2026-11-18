#!/usr/bin/env python3
"""Complete the existing walker with a 100000-file limit and expose that limit."""
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import quench_walk as qw
import forensics_held36 as held_index
import forensics_memory36 as memory
qw.held_gather = held_index.held_gather
# Keep public-only measurements on the ten frozen round-31 archives.
sys.path.insert(0, str(Path(__file__).resolve().parent / 'tools/harvest31'))
import policy
frozen = json.loads(Path('$SCRATCH/bounties-squares/take-forensics-r36/work/share/zips.json').read_text())
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
byte_roots = {}

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
    result['sampled_physical_peak_bytes'] = max(memory.peak, memory.footprint())
    print(json.dumps(result), flush=True)
