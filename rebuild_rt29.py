"""rt29.py: rebuild round 29 cert and live helpers. cert() is rebuild_take.cert with border's finesafe.work (the
floatsafe test, 2.2e-11 clearance, the metric as written and after a pandas read, with a bisected dilation) in place of
floatsafe.work. live() is rebuild_take.live with SQ_ROUND=29. Imports both unchanged (finesafe.py is a byte copy of
take-border-r28/work/finesafe.py, sha256 e35eac45cc52ffb4)."""
import csv, math, os, sys
sys.path.insert(0, '.')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'tools/border/r28')   # border finesafe.py, sha256 e35eac45cc52ffb4 (the take copy is byte-identical)
os.environ['SQ_ROUND'] = '29'
import rebuild_take as _rt  # noqa: E402
import finesafe  # noqa: E402
csv.field_size_limit(1 << 28)
live = _rt.live


def cert(n, raw, out, bar):
    rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(open(raw)) if int(r['n']) == n]
    if len(rows) != n:
        print('drop', n, 'rows', len(rows)); return None
    _, fr, score, e = finesafe.work((n, rows))
    if fr is None or not score < bar - 1e-10:
        print('drop', n, score, bar, e); return None
    with open(out, 'w', newline='') as g:
        w = csv.writer(g); w.writerow(['n', 'square_id', 'x', 'y', 'angle'])
        for r in fr:
            w.writerow([r['n'], r['square_id'], r['x'], r['y'], r['angle']])
    print('ok', n, repr(score), '%.12f' % ((score + 1) * math.sqrt(n)), e)
    return score
