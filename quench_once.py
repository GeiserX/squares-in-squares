#!/usr/bin/env python3
"""quench: finish a certified result with its one fq quench.

  quench_once.py prep CERT.csv JOBDIR [--raw-ok] [--no-cert]
      floatsafe the file again (--raw-ok: a start that does not certify goes
      to fq as raw rows; --no-cert: a start above the bar skips the floatsafe
      pass and goes to fq as raw rows), write JOBDIR/cert.csv (the certified rows),
      JOBDIR/in.txt (fq text) and JOBDIR/meta.json
  quench_once.py take JOBDIR BAR.tsv
      read JOBDIR/out.txt from quench_box.sh, floatsafe it, keep the lower of
      the certified input and the quenched file, write JOBDIR/final.csv and
      JOBDIR/result.json with the margin against the bar

The bar rule is the lane's: floatsafe at 2.2e-11 and below the bar by more
than 1e-10 (methods_take.py).
"""
import csv, hashlib, json, math, os, sys

import numpy as np

LANE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, LANE)
import floatsafe  # noqa: E402
# Round 29: certify with the border lane's bisected dilation (tools/border/r28/finesafe.py, imported unchanged; on a
# box it sits in the copied lane dir). Border measured 3.0e-10 to 8.2e-10 of side lower than the ladder on 19 fq outputs.
sys.path.insert(1, os.path.join(LANE, 'tools', 'border', 'r28'))
try:
    import finesafe  # noqa: E402
except ImportError:
    finesafe = None
import methods_lp as mlp  # noqa: E402
from midm_scan import to_fq, from_fq  # noqa: E402

KEYS = ('n', 'square_id', 'x', 'y', 'angle')


def rows_of(path):
    return [{k: r[k] for k in KEYS} for r in csv.DictReader(open(path))]


def write_rows(path, fr):
    with open(path + '.tmp', 'w', newline='') as g:
        w = csv.writer(g); w.writerow(list(KEYS))
        for r in fr:
            w.writerow([r[k] for k in KEYS])
    os.replace(path + '.tmp', path)


def certify(n, rows):
    _, fr, score, e = (finesafe or floatsafe).work((n, rows))
    return fr, score, e


def prep(src, job, raw_ok=False, no_cert=False):
    os.makedirs(job, exist_ok=True)
    rows = rows_of(src); n = int(rows[0]['n'])
    if len(rows) != n:
        raise SystemExit('rows %d != n %d' % (len(rows), n))
    fr, score, e = (None, None, None) if no_cert else certify(n, rows)
    if fr is None:
        if not raw_ok:
            raise SystemExit('not certifiable: %s' % src)
        # a raw start (a near design that overlaps): fq starts from the raw rows,
        # and only the quenched file can count
        fr, score = rows, float('inf')
    write_rows(job + '/cert.csv', fr)
    P = mlp.load(job + '/cert.csv', {n})[n]
    s, X = to_fq(P)
    with open(job + '/in.txt', 'w') as h:
        h.write('%d %r\n' % (len(X), float(s)))
        for x, y, g in X:
            h.write('%r %r %r\n' % (float(x), float(y), float(g)))
    meta = {'n': n, 'source_file': os.path.abspath(src),
            'source_sha256': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
            'cert_score': score, 'cert_dilation': e, 'fq_side_in': s}
    json.dump(meta, open(job + '/meta.json', 'w'), indent=1)
    print('prep', n, 'cert', repr(score), 'side', repr(s))


def take(job, bar_tsv):
    meta = json.load(open(job + '/meta.json')); n = meta['n']
    bar = {int(r['n']): float(r['score']) for r in csv.DictReader(open(bar_tsv), delimiter='\t')}
    best = (meta['cert_score'], rows_of(job + '/cert.csv'), 'certified input')
    if not math.isfinite(best[0]):
        best = (float('inf'), None, 'raw start, not certified')
    q = None
    # round 29: best.txt (quench_box.sh) is the lowest raw side of any fq try, kept even when the gain was under the
    # 3e-9 loop threshold; both files are certified and the lower certified score counts
    for f, what in (('out.txt', 'fq quench of the certified input'), ('best.txt', 'fq quench of the certified input (lowest raw try)')):
        if not os.path.exists(job + '/' + f):
            continue
        L = [l.split() for l in open(job + '/' + f) if l.strip() and not l.startswith('#')]
        X = np.array([[float(v) for v in t[:3]] for t in L[1:int(L[0][0]) + 1]])
        Q = from_fq(X)
        raw = [{'n': str(n), 'square_id': str(i), 'x': repr(float(x)), 'y': repr(float(y)),
                'angle': repr(float(a))} for i, (x, y, a) in enumerate(Q)]
        fr, score, e = certify(n, raw)
        if fr is not None and (q is None or score < q):
            q = score
        if fr is not None and score < best[0]:
            best = (score, fr, what)
    if best[1] is not None:
        write_rows(job + '/final.csv', best[1])
    res = {'n': n, 'cert_score': meta['cert_score'], 'quenched_score': q, 'final_score': best[0],
           'kept': best[2], 'bar': bar[n], 'margin': bar[n] - best[0],
           'counts': best[0] < bar[n] - 1e-10,
           'done': open(job + '/done').read().strip() if os.path.exists(job + '/done') else None}
    json.dump(res, open(job + '/result.json', 'w'), indent=1)
    print(json.dumps(res))


if __name__ == '__main__':
    if not sys.flags.isolated:
        os.execv(sys.executable, [sys.executable, '-I', os.path.abspath(__file__)] + sys.argv[1:])
    if sys.argv[1] == 'prep':
        no_cert = '--no-cert' in sys.argv[4:]
        prep(sys.argv[2], sys.argv[3], '--raw-ok' in sys.argv[4:] or no_cert, no_cert)
    else:
        take(sys.argv[2], sys.argv[3])
