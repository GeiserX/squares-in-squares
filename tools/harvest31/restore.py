"""Reprice certified prior-round snapshots without retrying unchanged near misses."""
import csv
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from policy import audit
from pins import verify
import walk as Q


def restore():
    bars={int(r['n']):float(r['bar']) for r in table(S/'round31-briefs/bar31.tsv')}
    bars=collector().bars(set(bars))
    old=S/'take-harvest-r30/work'
    jobs={p.name:json.loads(p.read_text()) for p in (old/'jobs').glob('*.json')}
    decisions=[]
    for outcome in (old/'outcomes').glob('*.json'):
        o=json.loads(outcome.read_text());n=int(o['n'])
        if 'score' not in o or 'path' not in o or o['score']>=bars[n]-1e-10:continue
        j=jobs.get(outcome.name)
        if not j:continue
        record=dict(n=n,outcome=str(outcome),score=o['score'],allowed=False)
        try:
            if j['kind']=='fresh-public' and n in (639,691,745,858,916,918):raise ValueError('unresolved public ancestry')
            Q.validate_job(j)
            if j['kind']=='fresh-follow':
                Q.load_withdrawn();verify(j,Q.WITHDRAWN_LINES,Q.samanyu_only)
            rows=list(csv.DictReader(Path(o['path']).open()));ok,ev=audit(rows) if j['kind'] in ('fresh-public','reopened-public') else (True,[])
            if not ok:raise ValueError('excluded restored output')
            meta=dict(j,n=n,kind='restored-certified',source=f'certified r30 snapshot {o["path"]}; original source {j["source"]}',inherited_job=j,inherited_outcome=str(outcome),evidence=ev)
            for k in ['path','sha256','queued','priority']:meta.pop(k,None)
            queued=enqueue(o['path'],meta,0);record.update(allowed=True,job=str(queued))
            state(f'QUEUE restored certified n={n} bar_gain={bars[n]-o["score"]:.3e} job={queued} deadline00:15Z')
        except Exception as e:record['reason']=repr(e)
        decisions.append(record)
    write_json(W/'restored.json',decisions)
    state(f'RESTORE certified snapshots repriced={len(decisions)} accepted={sum(r["allowed"] for r in decisions)}; public near misses not repeated')

if __name__=='__main__':restore()
