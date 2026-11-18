#!/usr/bin/env python3
"""Count rectangle windows whose origin can lie inside a packing.

forensics_interior.py control SOURCE686.csv
forensics_interior.py scan OUT SOURCE.csv W H F [--keep K]

For each left edge, interval stabbing finds the best bottom edge exactly
at the requested window size. These are packing parts, not improved per-n
results. The rectangle composer must assemble, quench and certify them.
"""
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as fr


def windows(q, width, height, keep=8):
    k = fc.corners(q)
    xmin, xmax = k[:, :, 0].min(1), k[:, :, 0].max(1)
    ymin, ymax = k[:, :, 1].min(1), k[:, :, 1].max(1)
    found = []
    for x in np.unique(xmin):
        ix = np.flatnonzero((xmin >= x - 1e-9) & (xmax <= x + width + 1e-9))
        if not len(ix):
            continue
        lo, hi = ymax[ix] - height, ymin[ix]
        valid = lo <= hi + 1e-9
        ix, lo, hi = ix[valid], lo[valid], hi[valid]
        if not len(ix):
            continue
        ys = np.unique(hi)
        counts = (np.searchsorted(np.sort(lo), ys + 1e-9, side='right') -
                  np.searchsorted(np.sort(hi), ys - 1e-9, side='left'))
        for j in np.argsort(-counts, kind='stable')[:min(2, len(ys))]:
            found.append((int(counts[j]), float(x), float(ys[j])))
    found.sort(key=lambda r: (-r[0], r[1], r[2]))
    seen = set(); out = []
    for count, x, y in found:
        ix = np.flatnonzero((xmin >= x - 1e-9) & (xmax <= x + width + 1e-9) &
                            (ymin >= y - 1e-9) & (ymax <= y + height + 1e-9))
        assert len(ix) == count
        key = tuple(ix)
        if key in seen:
            continue
        seen.add(key); out.append((count, x, y, ix))
        if len(out) >= keep:
            break
    return out


def control(path):
    side, q = fc.frame(fr.layouts(path)[686])
    r = dict(fr.sym8(q, side))[5]; k = fc.corners(r)
    ix = np.flatnonzero((k[:, :, 0].max(1) <= 9 + 12/17 + 2e-8) &
                        (k[:, :, 1].max(1) <= 18 + 12/17 + 2e-8))
    assert len(ix) == 168, len(ix)
    part = r[ix].copy(); part[:, :2] += [3, 4]
    found = windows(part, 9 + 12/17 + 2e-8, 18 + 12/17 + 2e-8)
    assert found[0][0] == 168 and found[0][1] > 2 and found[0][2] > 3
    assert windows(part[:-1], 9 + 12/17 + 2e-8, 18 + 12/17 + 2e-8)[0][0] == 167
    print('CONTROL interior 9x18+6 restored at translated origin; deleting one gives 167', flush=True)


def scan(outdir, source, w, h, f, keep):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    records = []
    data = Path(source).read_bytes()
    source_hash = hashlib.sha256(data).hexdigest()
    snapshots = outdir / 'sources'; snapshots.mkdir(exist_ok=True)
    snapshot = snapshots / (source_hash + '.csv')
    if not snapshot.exists():
        snapshot.write_bytes(data)
    for n, sq in fr.layouts(snapshot).items():
        side, q = fc.frame(sq)
        if fc.worst_overlap(q) < -1e-6:
            raise ValueError('source squares overlap')
        for g, r in fr.sym8(q, side):
            for count, x, y, ix in windows(r, w + f, h + f, keep):
                if count <= w * h:
                    continue
                _, part = fc.frame(r[ix])
                corners = fc.corners(part)
                actual_f = max(corners[:, :, 0].max() - w, corners[:, :, 1].max() - h)
                digest = hashlib.sha256(np.round(part, 10).tobytes()).hexdigest()[:16]
                path = outdir / ('%d-interior-%s.csv' % (count, digest))
                fc.write_csv(path, count, part)
                rec = dict(n=count, path=str(path), source=str(source),
                           source_snapshot=str(snapshot), source_sha256=source_hash, host_n=n, sym=g,
                           w=w, h=h, excess=count-w*h, f=float(actual_f), x=x, y=y,
                           indices=[int(i) for i in ix])
                Path(str(path) + '.json').write_text(json.dumps(rec))
                records.append(rec)
    print(json.dumps(dict(source=str(source), shape=[w,h], f=f, parts=len(records),
                         max_excess=max((r['excess'] for r in records), default=0))), flush=True)
    return records


def main(argv):
    if argv[1] == 'control':
        return control(argv[2])
    keep = int(fr.opt(argv, '--keep', '2'))
    scan(argv[2], argv[3], int(argv[4]), int(argv[5]), float(argv[6]), keep)


if __name__ == '__main__':
    main(sys.argv[:])
