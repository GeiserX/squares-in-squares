"""Audit final snapshots before 00:25 and write the report after that deadline."""
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from walk import validate_job,public_job
from policy import audit
from pins import job_matches
from notices import enrich
from harvest_collect import COLS


def allowed(row,job,bars):
    n=int(row['n']);target=T/(str(n)+'.csv')
    validate_job(job)
    if hashlib.sha256(Path(job['path']).read_bytes()).hexdigest()!=job['sha256']:raise ValueError('changed input bytes')
    proof=Path(row['remote_quench'])
    if not proof.is_file():raise ValueError('missing remote receipt')
    receipt=json.loads(proof.read_text())
    if receipt['input_hash']!=job['sha256']:raise ValueError('wrong remote input hash')
    source=Path(receipt['file'])
    if not source.exists() or source.read_bytes()!=target.read_bytes():raise ValueError('changed certificate bytes')
    if float(row['new'])>=bars[n]-1e-10:raise ValueError('lower live peer')
    ok,ev=audit(list(csv.DictReader(target.open()))) if public_job(job) else (True,[])
    if not ok:raise ValueError('excluded output share')
    return True


def prepare_take():
    bars={int(r['n']):float(r['bar']) for r in table(S/'round33-briefs/bar33.tsv')}
    base_bar=dict(bars)
    for p in S.glob('take-*-r33/take.tsv'):
        if p.parent==T:continue
        for r in table(p):
            if (p.parent/(r['n']+'.csv')).exists():bars[int(r['n'])]=min(bars[int(r['n'])],float(r['new']))
    jobs=[json.loads(p.read_text()) for p in (W/'jobs').glob('*.json')]
    keep=[];audits=[]
    for row in table(T/'take.tsv'):
        n=int(row['n'])
        job=next((j for j in jobs if job_matches(row,j)),None)
        try:
            if job is None:raise ValueError('missing exact source job')
            allowed(row,job,bars)
            row=enrich(row,job)
            row['held']=repr(base_bar[n]);row['gain']=repr(base_bar[n]-float(row['new']))
            row['other_best']=repr(bars[n]);row['incremental_gain']=repr(bars[n]-float(row['new']));keep.append(row)
            audits.append(dict(n=n,allowed=True,sha256=job['sha256']))
        except Exception as e:audits.append(dict(n=n,allowed=False,reason=repr(e)))
    tmp=T/'take.tsv.tmp'
    with tmp.open('w') as f:
        writer=csv.DictWriter(f,fieldnames=COLS,delimiter='\t',extrasaction='ignore',lineterminator='\n');writer.writeheader();writer.writerows(keep)
    tmp.replace(T/'take.tsv')
    kept={int(r['n']) for r in keep}
    for path in T.glob('[0-9]*.csv'):
        if int(path.stem) not in kept:
            dest=W/'final-out';dest.mkdir(exist_ok=True);(dest/path.name).write_bytes(path.read_bytes())
    write_json(W/'final-source-audit.json',audits)
    (L/'results/harvest-r33-2026-11-17.tsv').write_bytes((T/'take.tsv').read_bytes())
    state(f'TAKE FINAL rows={len(keep)}; compared every live r33 ledger')
    return keep

