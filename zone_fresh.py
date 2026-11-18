#!/usr/bin/env python3
"""Kick a fresh corner or shell layout, give each raw find one leg, and quench once.

Run on a worker box. The input JSON records source and licence. The ready copy
records the float-safe file from which the final fq call started.
"""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import time

os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')
sys.path.insert(0, str(Path(__file__).resolve().parent))
import floatsafe
import methods_lp as mlp
import midm_scan


def rows(path):
    return list(csv.DictReader(open(path)))


def side(path):
    return mlp.side(next(iter(mlp.load(str(path)).values())))


def write(path, data):
    path = Path(path)
    temp = path.with_suffix('.tmp')
    with temp.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['n', 'square_id', 'x', 'y', 'angle'])
        writer.writeheader()
        writer.writerows(data)
    os.replace(temp, path)


def finish(path, meta, out, fq, deadline, seconds=240, leg_seconds=90, seed=23, kick=True):
    path, out = Path(path), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    n = int(rows(path)[0]['n'])
    start = side(path)
    dl = float(Path(deadline).read_text())
    code = Path(__file__).resolve().parent
    import subprocess

    def scan(source, target, duration, scan_seed):
        if time.time() >= dl - 20:
            return []
        with (out / (target.name + '.log')).open('w') as handle:
            subprocess.run([sys.executable, '-I', str(code / 'midm_scan.py'), '--n', str(n),
                            '--sub', str(source), '--out', str(target), '--fq', fq,
                            '--seconds', str(duration), '--seed', str(scan_seed),
                            '--modes', 'lkick,kick', '--kicks', '0.02', '--deadline', str(deadline)],
                           stdout=handle, stderr=subprocess.STDOUT, check=True)
        return sorted((target / 'raw').glob('*.csv'))

    def has_trial(target, scan_seed):
        record = target / ('scan-%d-%d.tsv' % (n, scan_seed))
        return record.exists() and any(line[:1].isdigit() for line in record.read_text().splitlines())

    candidates = [path]
    initial = scan(path, out / 'scan', seconds, seed) if kick else []
    if kick and not has_trial(out / 'scan', seed):
        print('DEADLINE initial scan unstarted', n, flush=True)
        return
    candidates.extend(initial)
    # Every saved initial find receives exactly one continuation from that raw file.
    for index, raw in enumerate(initial):
        target = out / ('leg-' + str(index))
        candidates.extend(scan(raw, target, leg_seconds, seed + 1 + index))
        if not has_trial(target, seed + 1 + index):
            print('DEADLINE raw-find leg unstarted', n, index, flush=True)
            return
    best = min(candidates, key=side)
    _, safe, score, error = floatsafe.work((n, rows(best)))
    if safe is None:
        raise RuntimeError(('float-safe start failed', n, error))
    certified = out / 'certified-start.csv'
    write(certified, safe)
    current = (score + 1) * math.sqrt(n)
    if time.time() >= dl - 5:
        print('DEADLINE no final quench', n, flush=True)
        return
    P = mlp.load(str(certified))[n]
    L, X = midm_scan.to_fq(P)
    tmp = tempfile.mkdtemp(prefix='final-', dir=out)
    try:
        Lq, Xq = midm_scan.quench(fq, tmp, L, X, (), timeout=min(240, max(1, dl-time.time()-2)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if Xq is None:
        (out / 'quench-incomplete.json').write_text(json.dumps(dict(n=n, certified=str(certified), side=current)))
        print('INCOMPLETE final quench', n, flush=True)
        return
    end = current
    if Xq is not None:
        Pq = midm_scan.from_fq(Xq)
        qr = [dict(n=str(n), square_id=str(i), x=repr(float(x)), y=repr(float(y)), angle=repr(float(a)))
              for i, (x, y, a) in enumerate(Pq)]
        _, fr, sq, err = floatsafe.work((n, qr))
        if fr is not None and sq < score:
            safe, score, end = fr, sq, (sq + 1) * math.sqrt(n)
    ready = out / 'ready'
    ready.mkdir(exist_ok=True)
    final = ready / (str(n) + '.csv')
    write(final, safe)
    record = dict(meta, n=n, fresh_start=start, built=end, score=score, quenched=True,
                  quench_start=str(certified), quench_start_side=current, quench_side=Lq,
                  initial_finds=len(initial), raw_legs=len(initial), seed=seed,
                  scan_seconds=seconds, leg_seconds=leg_seconds, remote_box=socket.gethostname(),
                  kick_scan=has_trial(out / 'scan', seed),
                  quench_start_sha256=hashlib.sha256(certified.read_bytes()).hexdigest(),
                  source_override=meta.get('source_override', meta.get('source', '')),
                  licence_override=meta.get('licence_override', meta.get('licence', '')))
    metadata_temp = final.with_suffix('.json.tmp')
    metadata_temp.write_text(json.dumps(record))
    os.replace(metadata_temp, final.with_suffix('.json'))
    print('FINISH', n, 'start', start, 'end', end, 'finds', len(initial), 'legs', len(initial), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('metadata')
    parser.add_argument('out')
    parser.add_argument('--fq', required=True)
    parser.add_argument('--deadline', required=True)
    parser.add_argument('--seconds', type=float, default=240)
    parser.add_argument('--leg-seconds', type=float, default=90)
    parser.add_argument('--seed', type=int, default=23)
    parser.add_argument('--quench-only', action='store_true')
    args = parser.parse_args()
    finish(args.input, json.load(open(args.metadata)), args.out, args.fq, args.deadline,
           args.seconds, args.leg_seconds, args.seed, not args.quench_only)


if __name__ == '__main__':
    main()
