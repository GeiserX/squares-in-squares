"""Audit pinned take versions and bind every packing to its final quench."""
import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import floatsafe
import importlib.util
spec = importlib.util.spec_from_file_location("border_finesafe", "$SCRATCH/bounties-squares/take-border-r28/work/finesafe.py")
fine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fine)
import forensics_compose as fc
import forensics_round30 as sources

csv.field_size_limit(16*1024*1024)
FIELDS = ['n', 'square_id', 'x', 'y', 'angle']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(rows):
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows({k: row[k] for k in FIELDS} for row in rows)
    return out.getvalue().encode()


def pin(work):
    take = work.parent
    for attempt in range(30):
        data = (take/'take.tsv').read_bytes()
        rows = list(csv.DictReader(io.StringIO(data.decode()), delimiter='\t'))
        payloads = {int(r['n']): (take/(r['n']+'.csv')).read_bytes() for r in rows}
        stable = data == (take/'take.tsv').read_bytes()
        for r in rows:
            n = int(r['n'])
            rr = list(csv.DictReader(io.StringIO(payloads[n].decode())))
            if len(rr) != n:
                stable = False
                break
            side, _ = fc.frame([(float(v['x']), float(v['y']), float(v['angle'])) for v in rr])
            if abs(side/math.sqrt(n)-1-float(r['new'])) > 2e-12:
                stable = False
                break
        if stable:
            ledger_hash = digest(data)
            root = work/'audit-snapshots'/ledger_hash
            root.mkdir(parents=True, exist_ok=True)
            (root/'take.tsv').write_bytes(data)
            for n, payload in payloads.items():
                (root/(str(n)+'.csv')).write_bytes(payload)
            return rows, payloads, ledger_hash, root
        time.sleep(1)
    raise RuntimeError('take kept changing while pinning audit input')


def quench_proof(work, n, parts, packing_hash, proofs):
    for receipt, meta in reversed(proofs):
        if meta['n'] != n or meta.get('parts') != parts or meta.get('end') is None:
            continue
        certified = work/'certified'/meta['certfile']
        cert_hash = digest(certified.read_bytes())
        assert receipt.stem == 'final-'+cert_hash[:24]
        assert digest((work/'inputs'/(receipt.stem+'.csv')).read_bytes()) == cert_hash
        archive = work/'boxE-final/inputs'/(receipt.stem+'.csv')
        if archive.exists():
            assert digest(archive.read_bytes()) == cert_hash
        for candidate in [certified, receipt.with_suffix('.csv')]:
            rr = list(csv.DictReader(open(candidate)))
            _, fr, score, error = fine.work((n, rr))
            if fr is not None and digest(encoded(fr)) == packing_hash:
                return dict(receipt=str(receipt), certified_input=str(certified),
                            input_sha256=cert_hash, worker=meta['worker'], end=meta['end'],
                            seconds=meta['seconds'], published_from=str(candidate),
                            certificate_reproduced=True)
    raise ValueError('no final quench reproduces the published packing: n='+str(n))


def audit(work, new_only=False):
    take = work.parent
    policy_hash = sources.source_policy_hash()
    old = json.loads((work/'final-audit.json').read_text()) if (work/'final-audit.json').exists() else {'rows': []}
    old = {r['sha256']: r for r in old['rows']}
    rows, payloads, ledger_hash, snapshot = pin(work)
    proofs = [(p, json.loads(p.read_text())) for p in sorted((work/'received').glob('final-*.json'))]
    out = []
    for row in rows:
        n = int(row['n'])
        payload = payloads[n]
        packing_hash = digest(payload)
        notice_hash = digest((row['source']+'\0'+row['licence']).encode())
        cached = old.get(packing_hash)
        if (new_only and cached and cached.get('source_policy_sha256') == policy_hash and cached.get('notice_sha256') == notice_hash and
                cached.get('quench_proof', {}).get('certificate_reproduced') and
                abs(cached['score']-float(row['new'])) < 2e-12):
            out.append(dict(cached, reused_complete_audit=True))
            continue
        rr = list(csv.DictReader(io.StringIO(payload.decode())))
        score, direct = floatsafe.check(n, rr)
        pandas_score, pandas = floatsafe.check(n, floatsafe.via_pandas(rr))
        clearance = floatsafe.clearance(rr)
        output_share = sources.share_gate(snapshot/(str(n)+'.csv'), n)
        assert output_share < .4, ('excluded output share', n, output_share)
        parts = json.JSONDecoder().raw_decode(row['source'][row['source'].index('{'):])[0]
        ok, ancestry = sources.check_parts(parts, work.parents[1], fresh=True)
        assert ok, ('unclean ancestry', n)
        (work/'certified'/('audit-ancestry-%d.json'%n)).write_text(json.dumps(ancestry, indent=2))
        proof = quench_proof(work, n, parts, packing_hash, proofs)
        record = dict(n=n, rows=len(rr), unique_ids=len({r['square_id'] for r in rr}),
                      score=score, pandas_score=pandas_score, direct=direct, pandas=pandas,
                      clearance=clearance, sha256=packing_hash, notice_sha256=notice_hash, source_policy_sha256=policy_hash,
                      recorded_score=float(row['new']), held_gain=float(row['held'])-score,
                      ancestry_ok=ok, prvsiyan_share=output_share, quench_proof=proof, snapshot=str(snapshot/(str(n)+'.csv')))
        record['ok'] = (len(rr) == n and record['unique_ids'] == n and direct == pandas == 'ok' and
                        clearance >= 2.2e-11 and abs(score-float(row['new'])) < 2e-12 and record['held_gain'] > 1e-10)
        assert record['ok'], record
        out.append(record)
        print('AUDITED', n, score, clearance, 'certificate reproduced', flush=True)
    result = dict(asof=dt.datetime.now(dt.timezone.utc).isoformat(), ledger_sha256=ledger_hash,
                  snapshot=str(snapshot), rows=out, all_ok=all(r['ok'] for r in out))
    path = work/'final-audit.json'
    path.with_suffix('.tmp').write_text(json.dumps(result, indent=2))
    path.with_suffix('.tmp').replace(path)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('work', nargs='?', default='$SCRATCH/bounties-squares/take-forensics-r30/work')
    parser.add_argument('--new-only', action='store_true')
    args = parser.parse_args()
    result = audit(Path(args.work), args.new_only)
    print('ALL_OK', result['all_ok'], 'rows', len(result['rows']), flush=True)
