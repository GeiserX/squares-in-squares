"""One spare square in a fresh rectangle pair, removed before any quench."""
from pathlib import Path
import csv
import hashlib
import json
import math
import signal
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from scipy.spatial import cKDTree
import forensics_compose as fc
import forensics_rect as rect
import forensics_geometry31 as geometry


def collisions(q, tolerance=1e-9):
    pairs = np.array(sorted(cKDTree(q[:, :2]).query_pairs(math.sqrt(2)+1e-7)), dtype=int).reshape(-1, 2)
    if not len(pairs):
        return pairs
    a, b = q[pairs[:, 0]], q[pairs[:, 1]]
    u = np.column_stack((np.cos(a[:, 2]), np.sin(a[:, 2])))
    v = np.column_stack((-np.sin(a[:, 2]), np.cos(a[:, 2])))
    x = np.column_stack((np.cos(b[:, 2]), np.sin(b[:, 2])))
    y = np.column_stack((-np.sin(b[:, 2]), np.cos(b[:, 2])))
    delta = a[:, :2]-b[:, :2]
    gaps = []
    for axis, first, second in ((u, x, y), (v, x, y), (x, u, v), (y, u, v)):
        radius = .5+.5*(np.abs(np.sum(axis*first, axis=1))+np.abs(np.sum(axis*second, axis=1)))
        gaps.append(np.abs(np.sum(delta*axis, axis=1))-radius)
    return pairs[np.max(gaps, axis=0) < -tolerance]


def single_cover(edges):
    if not len(edges):
        return []
    common = set(map(int, edges[0]))
    for edge in edges[1:]:
        common.intersection_update(map(int, edge))
    return sorted(common)


def control(path):
    squares = next(iter(rect.layouts(path).values()))
    side, q = fc.frame(squares)
    parent = np.vstack((q, q[0]))
    edges = collisions(parent)
    covers = single_cover(edges)
    assert len(edges) == 1 and set(covers) == {0, len(q)}, (edges, covers)
    for index in covers:
        child = np.delete(parent, index, axis=0)
        assert len(child) == len(q) and fc.worst_overlap(child) > -1e-9
    bad = np.delete(parent, 1, axis=0)
    assert fc.worst_overlap(bad) < -.9
    disjoint = np.array([[.5, .5, 0.], [.5, .5, 0.], [2.5, .5, 0.], [2.5, .5, 0.]])
    assert not single_cover(collisions(disjoint))
    touching = np.array([[.5, .5, 0.], [1.5, .5, math.pi/2]])
    assert len(collisions(touching)) == 0
    print(f'CONTROL {len(q)} -> {len(parent)} -> {len(q)}: one collision removal restores the packing at side {side:.12f}', flush=True)
    print('CONTROL wrong removal and two disjoint collisions refused; rotated touching pair stays separate', flush=True)


def run(jobfile):
    job = json.loads(Path(jobfile).read_text())
    signal.setitimer(signal.ITIMER_REAL, max(.01, job['deadline']-time.time()))
    parents = Path(job['parents']);out = Path(job['out'])
    parents.mkdir(parents=True, exist_ok=True);out.mkdir(parents=True, exist_ok=True)
    args = ['forensics_rect.py', job['details'], str(parents), '--cache', job['cache'],
            '--only', ','.join(map(str, job['parent_counts'])), '--keep', '8', '--per-n', '16',
            '--max-mesh', '600', '--slack', '0', '--no-single', '--collide', '1.01',
            '--fresh-only', '--fresh-start', str(job['fresh_start'])]
    rect.main(args)
    targets = {int(k): float(v) for k,v in job['targets'].items()}
    seen = set();records = [];counts = dict(parents=0, single_cover=0, valid_below=0, no_single_cover=0)
    for path in sorted(parents.glob('*.csv')):
        if time.time() >= job['deadline']-1:
            break
        squares = next(iter(rect.layouts(path).values()))
        side, q = fc.frame(squares);n = len(q)-1
        if n not in targets:
            continue
        meta = json.loads(Path(str(path)+'.json').read_text())
        counts['parents'] += 1
        edges = collisions(q);covers = single_cover(edges)
        if not len(edges):
            covers = [len(q)-1]
        if not covers:
            counts['no_single_cover'] += 1
            continue
        counts['single_cover'] += 1
        for index in covers:
            child = np.delete(q, index, axis=0)
            end, child = fc.frame(child)
            if len(child) != n or fc.worst_overlap(child) < -1e-9 or end >= targets[n]-1e-10*math.sqrt(n):
                continue
            key = (n, geometry.key(child))
            if key in seen:
                continue
            seen.add(key);dest=out/f'{n}-drop1-{len(records):04d}.csv'
            fc.write_csv(dest, n, child)
            descriptor = dict(meta, kind='rectangle spare-square deletion', n=n, side=end,
                drop_one=dict(parent_n=n+1, parent_file=str(Path(job['local_parents'])/path.name),
                              parent_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                              removed_square_id=index, collision_edges=edges.tolist()))
            Path(str(dest)+'.json').write_text(json.dumps(descriptor))
            counts['valid_below'] += 1
            records.append(dict(n=n, side=end, target=targets[n], removed=index, parent=path.name))
    result=dict(counts=counts, records=records, deadline=job['deadline'])
    (out.parent/'drop33-measurement.json').write_text(json.dumps(result,indent=2))
    print('DROP33',json.dumps(counts),flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'control':
        control(sys.argv[2])
    else:
        run(sys.argv[2])
