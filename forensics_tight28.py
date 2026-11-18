"""Test rigid changes to rectangle crops from pinned round 28 starts."""
from pathlib import Path
import hashlib
import json
import math
import os
import signal
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as fc
import forensics_rect as rect


def tighten(q, w, h, angle=0.):
    q = q.copy()
    co, si = math.cos(angle), math.sin(angle)
    q[:, :2] = q[:, :2] @ np.array([[co, si], [-si, co]])
    q[:, 2] += angle
    bounds = fc.corners(q)
    origin = bounds.min((0, 1))
    q[:, :2] -= origin
    span = bounds.max((0, 1)) - origin
    return q, max(0., span[0] - w, span[1] - h), origin


def build(a, b, wa, ha, wb, hb, side):
    a = a.copy()
    b = b.copy()
    a[:, 1] = side - a[:, 1]
    a[:, 2] *= -1
    b[:, 0] = side - b[:, 0]
    b[:, 2] *= -1
    grid = [(i + .5, j + .5, 0.) for i in range(wa) for j in range(hb)]
    grid += [(side - .5 - i, side - .5 - j, 0.)
             for i in range(wb) for j in range(ha)]
    return np.r_[a, b, np.asarray(grid).reshape((-1, 3))]


def best_angle(q, w, h, bound):
    from scipy.optimize import minimize_scalar
    objective = lambda angle: tighten(q, w, h, angle)[1]
    result = minimize_scalar(objective, bounds=(-bound, bound), method='bounded',
                             options=dict(xatol=1e-11, maxiter=100))
    return min((0., -bound, bound, float(result.x)), key=objective)


def control():
    q = np.array([[.625, .75, 0.], [1.625, .75, 0.]])
    actual, fraction, origin = tighten(q, 2, 1)
    expected = np.array([[.5, .5, 0.], [1.5, .5, 0.]])
    assert np.max(np.abs(actual - expected)) < 1e-14
    assert fraction == 0. and np.max(np.abs(origin - [.125, .25])) < 1e-14
    bad = q.copy()
    bad[1, 0] += .01
    altered, _, _ = tighten(bad, 2, 1)
    assert np.max(np.abs(altered - expected)) > .009
    a = expected[:1]
    x = build(a, a, 1, 1, 1, 1, 2.)
    assert len(x) == 4 and fc.worst_overlap(x) >= -1e-12
    rotated = expected.copy()
    angle = .01
    co, si = math.cos(angle), math.sin(angle)
    rotated[:, :2] = rotated[:, :2] @ np.array([[co, si], [-si, co]])
    rotated[:, 2] += angle
    found = best_angle(rotated, 2, 1, .025)
    assert abs(found + angle) < 1e-8, found
    assert tighten(rotated, 2, 1, found)[1] < 2e-8
    assert tighten(rotated, 2, 1, angle)[1] > .03
    print('CONTROL removes margin (.125,.25), preserves two-unit crop, '
          'rejects .01 relative shift, builds four touching squares, '
          'recovers -.01 rotation and rejects opposite sign', flush=True)


def main(root, job_path):
    control()
    root = Path(root)
    job = json.loads(Path(job_path).read_text())
    signal.setitimer(signal.ITIMER_REAL, max(.1, job['deadline'] - time.time()))
    (root / 'scanner.pid').write_text(str(os.getpid()))
    out = root / job.get('output_tag', 'scan-tight-owned') / 'raw'
    out.mkdir(parents=True, exist_ok=True)
    variants = [(0., 0.), (-.0002, 0.), (.0002, 0.),
                (0., -.0002), (0., .0002), (-.0001, .0001), (.0001, -.0001)]
    candidates = []
    tested = shifted = 0
    seen = set()
    worst_reconstruction = 0.
    optimized_parts = 0
    for item in job['inputs']:
        p = root / 'tight-inputs' / item['name']
        assert hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256']
        meta = item['meta']
        n = meta['n']
        if 'A' not in meta or 'B' not in meta:
            continue
        ma, mb = meta['A'], meta['B']
        wa, ha, wb, hb = ma['w'], ma['h'], mb['w'], mb['h']
        assert wa + wb == ha + hb == math.isqrt(n)
        ca, cb = wa * ha + ma['excess'], wb * hb + mb['excess']
        _, q = fc.frame(rect.layouts(p)[n])
        side0 = meta['side']
        a, b = q[:ca].copy(), q[ca:ca + cb].copy()
        a[:, 1] = side0 - a[:, 1]
        a[:, 2] *= -1
        b[:, 0] = side0 - b[:, 0]
        b[:, 2] *= -1
        check = build(a, b, wa, ha, wb, hb, side0)
        error = float(np.max(np.abs(check - q)))
        worst_reconstruction = max(worst_reconstruction, error)
        assert error < 1e-10, (p.name, error)
        item_variants = variants
        if job.get('angle_bound'):
            aa = best_angle(a, wa, ha, job['angle_bound'])
            ab = best_angle(b, wb, hb, job['angle_bound'])
            optimized_parts += int(abs(aa) > 1e-8) + int(abs(ab) > 1e-8)
            item_variants = [(0., 0.), (aa, 0.), (0., ab), (aa, ab), (.5*aa, .5*ab)]
        for aa, ab in item_variants:
            ta, fa, oa = tighten(a, wa, ha, aa)
            tb, fb, ob = tighten(b, wb, hb, ab)
            side = math.isqrt(n) + max(fa, fb)
            if side > job['bars'][str(n)] + .004:
                continue
            if max(np.max(np.abs(oa)), np.max(np.abs(ob)), abs(aa), abs(ab)) < 1e-8:
                continue
            tested += 1
            if not aa and not ab:
                shifted += 1
            x = build(ta, tb, wa, ha, wb, hb, side)
            assert len(x) == n
            bounds = fc.corners(x)
            assert bounds.min() >= -1e-10 and bounds.max() <= side + 1e-10
            overlap = fc.worst_overlap(x)
            if overlap < -.06:
                continue
            sig = hashlib.sha256(np.round(x, 8).tobytes()).hexdigest()
            if sig in seen:
                continue
            seen.add(sig)
            candidate = dict(n=n, side=side, margin=side - job['bars'][str(n)],
                             overlap=overlap, angles=[aa, ab], shifts=[oa.tolist(), ob.tolist()],
                             input_sha256=item['sha256'], input_path=item['source'],
                             signature=sig, meta=meta)
            candidates.append((candidate, x))
    counts = {}
    rows = []
    for record, x in sorted(candidates, key=lambda pair: (pair[0]['margin'], -pair[0]['overlap'])):
        n = record['n']
        if counts.get(n, 0) >= 3:
            continue
        counts[n] = counts.get(n, 0) + 1
        kind = 'c' if record['overlap'] < -1e-9 else 'p'
        p = out / f"{n}-{kind}tight-{record['signature'][:12]}.csv"
        fc.write_csv(p, n, x)
        meta = dict(record.pop('meta'))
        meta.update(n=n, side=record['side'], kind='rigid cropped-part bounds and angle probe',
                    parent_raw_sha256=record['input_sha256'])
        for i, tag in enumerate(('A', 'B')):
            meta[tag] = dict(meta[tag], rigid_rotation=record['angles'][i],
                            bounds_origin=record['shifts'][i])
        Path(str(p) + '.json').write_text(json.dumps(meta))
        record.update(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        rows.append(record)
        if len(rows) >= 120:
            break
    result = dict(inputs=len(job['inputs']), tested=tested, shifted_starts=shifted,
                  admissible_variants=len(candidates), worst_reconstruction=worst_reconstruction,
                  angle_bound=job.get('angle_bound'), optimized_parts=optimized_parts,
                  starts=rows)
    (root / job.get('measurement', 'tight-measurement28.json')).write_text(json.dumps(result, indent=2))
    print('TIGHT FINISH', json.dumps({k: v for k, v in result.items() if k != 'starts'}),
          'exports', len(rows), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['--control']:
        control()
    else:
        main(*sys.argv[1:])
