#!/usr/bin/env python3
"""Collect fq follow results against a frozen round and the current live takes.

A remote fq quench runs once per certified candidate before publication. The
original certified file stays if the remote file is worse or fails clearance.
All output files precede the atomic take.tsv replacement. Both the held margin
and the margin over other takes are recorded. polish_gain keeps the actual
margin of the local follow over its start file.
"""
import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import floatsafe
from engine_lib import normalize
from engine_fq import write_txt, read_txt
from engine_polish import to_rows

csv.field_size_limit(16 * 1024 * 1024)

COLS = ('n', 'held', 'new', 'gain', 'source', 'licence', 'start',
        'polish_gain', 'other_best', 'incremental_gain', 'remote_quench')


def table(path):
    try:
        with open(path) as f:
            return list(csv.DictReader(f, delimiter='\t'))
    except FileNotFoundError:
        return []


def rows_write(path, rows):
    temp = path.with_suffix('.csv.tmp')
    with temp.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=('n', 'square_id', 'x', 'y', 'angle'))
        w.writeheader()
        w.writerows(rows)
    os.replace(temp, path)


class Collector:
    def __init__(self, args):
        self.args = args
        self.work = Path(args.work)
        self.work.mkdir(parents=True, exist_ok=True)
        self.cache_dir = self.work / 'certified'
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_path = self.work / 'cache.json'
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}
        self.floor_path = self.work / 'competitor-floors.json'
        self.floors = {int(n): float(v) for n, v in json.loads(self.floor_path.read_text()).items()} if self.floor_path.exists() else {}
        with open(args.details) as f:
            self.held = {int(r['n']): float(r['score']) for r in csv.DictReader(f)}

    def cert(self, path, n):
        raw = Path(path).read_bytes()
        key = hashlib.sha256(raw).hexdigest()
        if key not in self.cache:
            with open(path) as f:
                rows = [{k: r[k] for k in ('n', 'square_id', 'x', 'y', 'angle')} for r in csv.DictReader(f)]
            if len(rows) != n or any(int(r['n']) != n for r in rows):
                self.cache[key] = None
            else:
                _, fr, score, error = floatsafe.work((n, rows))
                if fr is None:
                    self.cache[key] = None
                else:
                    rows_write(self.cache_dir / (key + '.csv'), fr)
                    self.cache[key] = score
        score = self.cache[key]
        if score is None:
            return None
        return score, self.cache_dir / (key + '.csv'), key

    def bars(self, ns, limits=None, force=()):
        bars = {n: self.held[n] for n in ns}
        entries = []
        for pattern in self.args.live:
            for directory in sorted(glob.glob(pattern)):
                if str(Path(directory).resolve()) in self.args.out + self.args.exclude:
                    continue
                for r in table(Path(directory) / 'take.tsv'):
                    n = int(r['n'])
                    if n in ns and (not hasattr(self, 'peer_allowed') or self.peer_allowed(r)):
                        path = Path(directory) / (str(n) + '.csv')
                        if path.exists():
                            entries.append((n, path, float(r['new'])))
        # A cache shortcut requires a byte-identical file still in a live take.
        # A removed competitor must not prevent a valid result from returning.
        stale = set()
        if limits is not None:
            for n, path, advertised in sorted(entries, key=lambda x: x[2]):
                if n in force or n in stale:
                    continue
                try:
                    key = hashlib.sha256(path.read_bytes()).hexdigest()
                except FileNotFoundError:
                    continue
                score = self.cache.get(key)
                if score is not None and score <= limits[n] + 1e-10:
                    bars[n] = score
                    stale.add(n)
        for n, path, advertised in entries:
            if n in stale or advertised >= bars[n]:
                continue
            try:
                result = self.cert(path, n)
            except FileNotFoundError:
                continue
            if result and result[0] < bars[n]:
                bars[n] = result[0]
        for n in ns:
            self.floors[n] = min(self.floors.get(n, self.held[n]), bars[n])
        return bars

    def remote(self, cert, n):
        score, path, key = cert
        target = self.work / ('remote-' + key)
        proof = target.with_suffix('.json')
        if proof.exists():
            data = json.loads(proof.read_text())
            result = self.cert(data['file'], n)
            return result, str(proof)
        sq = []
        with path.open() as f:
            for r in csv.DictReader(f):
                sq.append((float(r['x']), float(r['y']), float(r['angle'])))
        side, a = normalize(sq)
        input_path = target.with_suffix('.txt')
        output_path = target.with_suffix('.out')
        write_txt(input_path, side, a)
        remote_dir = self.args.remote_dir
        stem = str(n) + '-' + key[:16]
        remote_input, remote_output = stem + '.txt', stem + '.out'
        def call(cmd, **kw):
            return subprocess.run(cmd, check=True, timeout=150, **kw)
        t0 = time.time()
        with target.with_suffix('.log').open('w') as log:
            call(['scp', '-q', str(input_path), self.args.host + ':' + remote_dir + '/' + remote_input], stdout=log, stderr=log)
            cmd = ('cd ' + shlex.quote(remote_dir) + ' && nice -n 5 /usr/bin/python3 remote_run.py '
                   + shlex.quote(remote_input) + ' ' + shlex.quote(remote_output))
            call(['ssh', '-n', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', self.args.host, cmd], stdout=log, stderr=log)
            call(['scp', '-q', self.args.host + ':' + remote_dir + '/' + remote_output, str(output_path)], stdout=log, stderr=log)
        if not output_path.is_file():
            raise RuntimeError('remote quench did not return its output')
        remote_side, remote_a = read_txt(output_path)
        remote_csv = target.with_suffix('.csv')
        rows_write(remote_csv, to_rows(n, remote_a))
        recert = self.cert(remote_csv, n)
        chosen = recert if recert and recert[0] < score else cert
        proof.write_text(json.dumps({'n': n, 'host': self.args.host, 'input_hash': key,
                                    'input_score': score, 'remote_side': remote_side,
                                    'remote_score': recert[0] if recert else None,
                                    'file': str(chosen[1]), 'seconds': time.time() - t0}, indent=2) + '\n')
        return chosen, str(proof)

    def publish(self, best, handed):
        handed_path = self.work / 'near-exported.json'
        # Builders can write a better result while the remote quench is running.
        bars = self.bars(set(best))
        best = {n: (p, dict(r, other_best=repr(bars[n]), incremental_gain=repr(bars[n] - float(r['new']))))
                for n, (p, r) in best.items() if float(r['new']) < bars[n] - 1e-10}
        handed.update(r['_candidate_hash'] for p, r in best.values())
        for directory in self.args.out:
            out = Path(directory)
            out.mkdir(parents=True, exist_ok=True)
            old = {int(r['n']): r for r in table(out / 'take.tsv')}
            for n, (path, row) in best.items():
                with path.open() as f:
                    rows_write(out / (str(n) + '.csv'), list(csv.DictReader(f)))
            tmp = out / 'take.tsv.tmp'
            with tmp.open('w') as f:
                w = csv.DictWriter(f, fieldnames=COLS, delimiter='\t', extrasaction='ignore')
                w.writeheader()
                w.writerows(best[n][1] for n in sorted(best))
            os.replace(tmp, out / 'take.tsv')
            for path in out.glob('[0-9]*.csv'):
                if int(path.stem) not in best:
                    path.unlink()
            if self.args.handoff and directory == self.args.out[0]:
                for n, (_, row) in best.items():
                    if n not in old or float(row['new']) < float(old[n]['new']) - 1e-10:
                        with open(self.args.handoff, 'a') as f:
                            f.write(f'{dt.datetime.now(dt.timezone.utc).isoformat()} harvest -> all: certified fq follow n={n}, score={row["new"]}, polish gain={row.get("polish_gain")}, remote quench={self.args.host}, {out}/{n}.csv\n')
                        print('handoff', n, row['new'], flush=True)
        temp_handed = handed_path.with_suffix('.tmp')
        temp_handed.write_text(json.dumps(sorted(handed)) + '\n')
        os.replace(temp_handed, handed_path)
        self.floor_path.write_text(json.dumps(self.floors) + '\n')
        self.cache_path.write_text(json.dumps(self.cache) + '\n')
        return best

    def run(self):
        own = {}
        for directory in self.args.own:
            for r in table(Path(directory) / 'take.tsv'):
                n = int(r['n'])
                result = self.cert(Path(directory) / (str(n) + '.csv'), n)
                if result and result[0] < self.held[n] - 1e-10:
                    if n not in own or result[0] < own[n][0][0]:
                        own[n] = result, r
        provenance_path = self.work / 'provenance.json'
        provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else {}
        best = {}
        handed_path = self.work / 'near-exported.json'
        handed = set(json.loads(handed_path.read_text())) if handed_path.exists() else set()
        per_run_history = self.work.parent / 'run-near-exported.json'
        if per_run_history.exists():
            handed.update(json.loads(per_run_history.read_text()))
        # Seed a legacy work directory whose remote proofs were already published.
        if not handed_path.exists():
            for proof_path in self.work.glob('remote-*.json'):
                handed.add(json.loads(proof_path.read_text())['input_hash'])
        pending_near = {n for n, (cert, row) in own.items() if cert[2] not in handed and float(row.get('start') or cert[0]) - cert[0] > 1e-8}
        bars = self.bars(set(own), limits={n: cert[0] for n, (cert, row) in own.items()}, force=pending_near)
        # Keep already certified rows while a newer version waits for its quench.
        for row in table(Path(self.args.out[0]) / 'take.tsv'):
            n = int(row['n'])
            proof = Path(row.get('remote_quench') or '')
            if n not in own or not proof.is_file():
                continue
            cert = self.cert(Path(self.args.out[0]) / (str(n) + '.csv'), n)
            if not cert or cert[0] >= bars[n] - 1e-10:
                continue
            old = dict(row, new=repr(cert[0]), gain=repr(self.held[n] - cert[0]))
            old['_candidate_hash'] = json.loads(proof.read_text())['input_hash']
            best[n] = cert[1], old
        best = self.publish(best, handed)
        # Largest margin on the held bar first, so the best rows get their remote proof first.
        for n, (cert, row) in sorted(own.items(), key=lambda kv: (kv[1][0][0] - self.held[kv[0]], kv[0])):
            row = dict(row, **provenance.get(cert[2], {}))
            if cert[0] >= bars[n] - 1e-10:
                polish_gain = float(row.get('start') or cert[0]) - cert[0]
                if (not self.args.control and cert[2] not in handed
                        and polish_gain > 1e-8 and cert[0] <= bars[n] + 2e-5):
                    near = Path(self.args.out[0]) / 'near'
                    near.mkdir(parents=True, exist_ok=True)
                    target = near / (str(n) + '-fq-' + cert[2][:16] + '.csv')
                    with cert[1].open() as f:
                        rows_write(target, list(csv.DictReader(f)))
                    meta = dict(row, score=cert[0], other_best=bars[n],
                                over_bar=cert[0] - bars[n], polish_gain=polish_gain,
                                certified_candidate=str(cert[1]))
                    Path(str(target) + '.json').write_text(json.dumps(meta, indent=2) + '\n')
                    if self.args.handoff:
                        with open(self.args.handoff, 'a') as f:
                            f.write(f'{dt.datetime.now(dt.timezone.utc).isoformat()} harvest -> all: fq near n={n}, over bar={cert[0]-bars[n]:.3e}, polish gain={polish_gain:.3e}, source and licence in sidecar, {target}\n')
                    handed.add(cert[2])
                    print('near handoff', n, str(target), flush=True)
                print('drop', n, 'own', cert[0], 'bar', bars[n], flush=True)
                continue
            if self.args.control:
                result, proof = cert, 'control only'
            else:
                try:
                    result, proof = self.remote(cert, n)
                except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
                    print('remote failed', n, repr(exc), flush=True)
                    continue
            score, path, key = result
            row = dict(row, **provenance.get(cert[2], {}))
            row = dict(row, n=n, held=repr(self.held[n]), new=repr(score),
                       gain=repr(self.held[n] - score), other_best=repr(bars[n]),
                       incremental_gain=repr(bars[n] - score), remote_quench=proof)
            if row.get('start'):
                row['polish_gain'] = repr(float(row['start']) - score)
            row['_candidate_hash'] = cert[2]
            if n not in best or score < float(best[n][1]['new']):
                best[n] = path, row
            best = self.publish(best, handed)
        best = self.publish(best, handed)
        print(json.dumps({'improved_n': len(best),
                          'held_gain': sum(self.held[n] - float(r['new']) for n, (p, r) in best.items()),
                          'incremental_gain': sum(float(r['incremental_gain']) for p, r in best.values()),
                          'polish_gain': sum(float(r.get('polish_gain') or 0) for p, r in best.values()),
                          'n': sorted(best)}), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('details')
    ap.add_argument('--own', nargs='+', required=True)
    ap.add_argument('--live', nargs='*', default=[])
    ap.add_argument('--out', nargs='+', required=True)
    ap.add_argument('--work', required=True)
    ap.add_argument('--host', default='boxD')
    ap.add_argument('--remote-dir', default='scratch/squares-harvest/r22')
    ap.add_argument('--handoff')
    ap.add_argument('--exclude', nargs='*', default=[])
    ap.add_argument('--control', action='store_true', help='skip remote quench; for fixture checks only')
    args = ap.parse_args()
    args.out = [str(Path(x).resolve()) for x in args.out]
    args.exclude = [str(Path(x).resolve()) for x in args.exclude]
    Collector(args).run()


if __name__ == '__main__':
    main()
