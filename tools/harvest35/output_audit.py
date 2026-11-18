"""Check still-published straight fq/kick descendants of the six public roots."""
import csv
import hashlib
import io
import json
from pathlib import Path
import signal
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,T,W,state,hand,write_json
from policy import audit
from crops import resume_finalizer
ROOT=W/'output-audit'


def timed_out(*args):raise TimeoutError('bounded output audit reached120s')


def main():
    records=[];started=time.monotonic()
    signal.signal(signal.SIGALRM,timed_out);signal.setitimer(signal.ITIMER_REAL,120)
    try:
        import rpc
        from fetch import H
        items=rpc.get(H.API+'/datasets/list?search=squares-verified-best-of-1105&page=1')
        current=[{k:r.get(k) for k in ['ref','lastUpdated','licenseName','currentVersionNumber']} for r in items if r.get('ref')=='prvsiyan/squares-verified-best-of-1105']
        write_json(ROOT/'comparison-current.json',current)
        assert len(current)==1 and current[0]['currentVersionNumber']==24 and current[0]['lastUpdated']=='2026-11-13T18:12:52.360Z','comparison archive changed; refresh before auditing'
        public_refs=set();wanted=set()
        for job in (W/'jobs').glob('*.json'):
            record=json.loads(job.read_text())
            if record.get('kind')=='fresh-public':
                public_refs.add(record['source'].split(' ::',1)[0])
                wanted.add(int(record['n']))
        for lane in ['quench','backlog','midm','rebuild','invent']:
            ledger=S/f'take-{lane}-r35/take.tsv'
            if not ledger.exists():continue
            ledger_bytes=ledger.read_bytes()
            for row in csv.DictReader(io.StringIO(ledger_bytes.decode()),delimiter='\t'):
                n=int(row['n'])
                if n not in wanted:continue
                # These engine-only descendants retain the complete public
                # source in their ledger. An independent held rebuild is owned.
                source=row['source']
                if 'take-quench-r35/work/harvest/' not in source or not any(ref+' ::' in source for ref in public_refs):
                    records.append(dict(n=n,lane=lane,status='not a recorded descendant of our public roots; no share gate applied'))
                    continue
                if not source.startswith(('quench lane:','quench lane kick:','backlog lane:')) or re.search(r'take-(?:forensics|k123|modules|stair-c|twoshort|classfill|invent|border|rebuild)-r34/',source):
                    records.append(dict(n=n,lane=lane,status='construction needs its own ancestry classification; no output share gate applied'))
                    continue
                path=ledger.parent/f'{n}.csv';raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
                snapshot=ROOT/f'{lane}-{n}-{sha[:16]}.csv';snapshot.write_bytes(raw)
                rows=list(csv.DictReader(io.StringIO(raw.decode())))
                assert len(rows)==n and all(int(row['n'])==n for row in rows),'output count differs from ledger'
                ok,evidence=audit(rows)
                still_current=(ledger.read_bytes()==ledger_bytes and path.read_bytes()==raw)
                record=dict(n=n,lane=lane,path=str(path),snapshot=str(snapshot),sha256=sha,allowed=ok,still_current=still_current,source=source,share1e3=max((r['share1e3'] for r in evidence),default=0.),share1e2=max((r['share1e2'] for r in evidence),default=0.),evidence=evidence)
                records.append(record)
                if not ok and still_current:
                    hand(f'WITHDRAW public-first engine output n={n}, sha256={sha}, {path}; independent frozen share31 check share1e3={record["share1e3"]:.17g} share1e2={record["share1e2"]:.17g}; straight descendant of our public root, keep last source-cleared checkpoint. Exact bytes only.')
                state(f'OUTPUT AUDIT {lane} n={n} allowed={ok} still_current={still_current} share1e3={record["share1e3"]:.12g} share1e2={record["share1e2"]:.12g}')
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        try:write_json(ROOT/'results.json',dict(seconds=time.monotonic()-started,records=records))
        finally:resume_finalizer('public output audit')

if __name__=='__main__':main()
