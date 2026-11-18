#!/usr/bin/env python3
"""Finish a classfill build on its worker before the collector publishes it.

A fresh build within 2e-4 of the bar gets one sigma 0.02 scan. Certify the
best file, quench that certified copy on the worker, then certify it again.
The collector must still compare the result with every current take.
"""
import argparse
import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finesafe as floatsafe
import methods_lp as mlp

COLS = ['n', 'square_id', 'x', 'y', 'angle']


def certify(path, n):
    rows = [{k: r[k] for k in COLS} for r in csv.DictReader(open(path))]
    if len(rows) != n:
        return None
    _, fr, score, why = floatsafe.work((n, rows))
    if fr is None:
        print('REFUSED', path, why, flush=True)
        return None
    return score, fr


def write(path, rows):
    path = Path(path)
    with open(str(path) + '.tmp', 'w', newline='') as h:
        w = csv.DictWriter(h, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    os.replace(str(path) + '.tmp', path)


def finish_quench(n, result, score, fq, deadline, journal):
    """Keep each certified fq return, including sub-3e-9 side moves."""
    import hashlib
    from midm_scan import to_fq, from_fq, quench, POLISH
    start_sha = hashlib.sha256(result.read_bytes()).hexdigest()
    L, X = to_fq(mlp.load(str(result), {n})[n])
    attempts = []
    completed = 0
    best_score = score
    best_rows = None
    tmp = journal / 'fq-tmp'
    tmp.mkdir(exist_ok=True)
    for name, flags in [('default', ()), ('polish', POLISH)]:
        timeout = min(180, deadline - time.time() - 10)
        if timeout <= 0:
            break
        raw_side, Q = quench(str(Path(fq).resolve()), str(tmp), L, X, flags, timeout=timeout)
        if raw_side is None:
            attempts.append(dict(mode=name, completed=False))
            continue
        completed += 1
        P = from_fq(Q)
        raw = journal / ('quench-' + name + '.csv')
        rows = [dict(n=str(n),square_id=str(i),x=repr(float(x)),y=repr(float(y)),angle=repr(float(a))) for i,(x,y,a) in enumerate(P)]
        write(raw, rows)
        cert = certify(raw, n)
        attempts.append(dict(mode=name, completed=True, raw_side=raw_side, score=cert[0] if cert else None, sha256=hashlib.sha256(raw.read_bytes()).hexdigest()))
        if cert and cert[0] < best_score:
            best_score, best_rows = cert
        if raw_side < L:
            L, X = raw_side, Q
    if not completed:
        raise RuntimeError('no fq quench returned a completed packing')
    if best_rows is not None:
        write(result, best_rows)
    receipt=dict(input_sha256=start_sha, output_sha256=hashlib.sha256(result.read_bytes()).hexdigest(), attempts=attempts, completed=completed, before_score=score, after_score=best_score)
    (journal/'quench-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('n=%d QUENCH %.17g -> %.17g, completed %d, certified input sha256 %s' % (n,score,best_score,completed,start_sha),flush=True)
    return best_score


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('raw')
    ap.add_argument('bar')
    ap.add_argument('--tag', required=True)
    ap.add_argument('--kick', action='store_true')
    ap.add_argument('--seconds', type=float, default=360)
    ap.add_argument('--side-slack', type=float, default=0.0002,
                    help='largest starting side excess admitted for a scan')
    ap.add_argument('--seed', type=int, default=23)
    ap.add_argument('--source')
    ap.add_argument('--licence', default='own search; see results/round21-best-2026-11-13.tsv for held ancestors')
    ap.add_argument('--deadline', default='deadline')
    ap.add_argument('--fq', default='fq')
    ap.add_argument('--kicks', default=None,
                    help='comma list of kick sigmas for midm_scan (default 0.02); a worker job file queue/*/TAG.active may set "kicks"')
    a = ap.parse_args()
    if a.kicks is None:
        a.kicks = '0.02'
        for job in Path('queue').glob('*/' + a.tag + '.active'):
            a.kicks = str(json.load(open(job)).get('kicks', a.kicks))
    raw = Path(a.raw)
    if not raw.exists():
        print('NO FILE', raw, flush=True)
        return 0
    n = int(raw.name.split('-')[0].split('.')[0])
    deadline = float(Path(a.deadline).read_text())
    bar = {int(r['n']): float(r['L']) for r in csv.DictReader(open(a.bar))}[n]
    start = mlp.side(mlp.load(str(raw), {n})[n])
    if start > bar + a.side_slack:
        print('TOO FAR', n, start, bar, flush=True)
        return 0
    journal = Path('out/finish-' + a.tag)
    journal.mkdir(parents=True, exist_ok=True)
    scratch = journal / 'tmp'
    scratch.mkdir(exist_ok=True)
    tempfile.tempdir = str(scratch.resolve())
    meta = json.load(open(raw.with_suffix('.json'))) if raw.with_suffix('.json').exists() else {}
    if a.source:
        meta['finish_source'] = a.source
        meta['finish_licence'] = a.licence
    paths = [raw]
    if a.kick and time.time() < deadline - 120:
        kick = journal / 'kick'
        cmd = [sys.executable, '-I', str(Path(__file__).parent / 'midm_scan.py'), '--n', str(n),
               '--sub', str(raw), '--out', str(kick), '--fq', str(Path(a.fq).resolve()),
               '--seconds', str(min(a.seconds, deadline - time.time() - 120)), '--seed', str(a.seed),
               '--modes', 'lkick,kick', '--kicks', a.kicks, '--deadline', a.deadline]
        with open(journal / 'kick.log', 'w') as h:
            subprocess.run(cmd, stdout=h, stderr=subprocess.STDOUT, check=True)
        paths += sorted((kick / 'raw').glob('*.csv'))
    best = None
    for p in paths:
        result = certify(p, n)
        if result and (best is None or result[0] < best[0]):
            best = (*result, str(p))
    if best is None:
        return 0
    score, fr, sourcefile = best
    result = journal / (str(n) + '.csv')
    write(result, fr)
    meta['finish_start'] = str(raw)
    meta['finish_best_raw'] = sourcefile
    meta['finish_kick'] = bool(a.kick)
    meta['finish_kicks'] = a.kicks
    meta['finish_start_side'] = start
    meta['finish_side_slack'] = a.side_slack
    meta['finish_before_quench_score'] = score
    # Quench prospective wins and near files within 2e-6 of side of the bar.
    if (1 + score) * math.sqrt(n) < bar + 2e-6 and time.time() < deadline - 20:
        finish_quench(n, result, score, a.fq, deadline, journal)
        meta['finish_quench_passes'] = 1
        meta['finish_quenched'] = True
        final = certify(result, n)
        if final is None:
            raise RuntimeError('quench output failed certification')
        score, fr = final
        write(result, fr)
        out = Path(('out/final-' if (1 + score) * math.sqrt(n) < bar - 1e-10 * math.sqrt(n) else 'out/near-') + a.tag)
    else:
        meta['finish_quenched'] = False
        out = Path('out/near-' + a.tag)
    out.mkdir(exist_ok=True)
    shutil.copyfile(result, out / (str(n) + '.csv'))
    meta['finish_score'] = score
    (out / (str(n) + '.json')).write_text(json.dumps(meta, indent=2) + '\n')
    (out / 'DONE').touch()
    print('FINISHED', n, repr(score), 'margin_side', bar - (1 + score) * math.sqrt(n),
          'quenched', meta['finish_quenched'], 'path', out, flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
