"""Read final public CSVs with bounded column memory before solver admission."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from policy import audit
sys.path.insert(0,str(L/'tools'))
from harvest_follow import public_origin,refused_source
from angle_take import accepted
from public_records import inspect as inspect_records,VERSION as RECORDS_VERSION
import numpy as np
import pandas as pd


def read(path):
    head=pd.read_csv(path,nrows=0).columns
    if not {'n','x','y'}.issubset(head):return None
    angle='angle' if 'angle' in head else 'deg' if 'deg' in head else None
    if angle is None:return None
    df=pd.read_csv(path,usecols=['n','x','y',angle],float_precision='round_trip')
    if angle!='angle':df=df.rename(columns={angle:'angle'})
    for col in df:
        if df[col].dtype=='object':df[col]=pd.to_numeric(df[col].str.lstrip('s'),errors='coerce')
    df=df.dropna()
    df=df.assign(n=df['n'].astype(int))
    a=df['angle'].to_numpy()
    extent=.5*(np.abs(np.cos(a))+np.abs(np.sin(a)))
    bounds=pd.DataFrame({'n':df['n'],'xmin':df['x']-extent,'xmax':df['x']+extent,
                         'ymin':df['y']-extent,'ymax':df['y']+extent})
    g=bounds.groupby('n').agg(xmin=('xmin','min'),xmax=('xmax','max'),ymin=('ymin','min'),ymax=('ymax','max'),count=('n','size'))
    sides=np.maximum(g['xmax']-g['xmin'],g['ymax']-g['ymin'])
    return df,{int(n):(float(side)/math.sqrt(n)-1,float(side),int(g.loc[n,'count'])) for n,side in sides.items() if 1<=n<=1000}


def plan(root):
    data=root/'data';selected=root/'selected'
    bars={int(r['n']):float(r['bar']) for r in table(S/'round33-briefs/bar33.tsv')}
    for ledger in S.glob('take-*-r33/take.tsv'):
        for r in table(ledger):
            if (ledger.parent/(r['n']+'.csv')).exists():bars[int(r['n'])]=min(bars[int(r['n'])],float(r['new']))
    revision=hashlib.sha256(b''.join(p.read_bytes() for p in [Path(__file__),Path(__file__).parent/'policy.py',Path(__file__).parent/'public_records.py',L/'tools/harvest_follow.py'])).hexdigest()
    progress=root/'screen-progress.json'
    saved=json.loads(progress.read_text()) if progress.exists() else {}
    if saved.get('revision')!=revision:saved={}
    decisions=saved.get('decisions',[]);files=saved.get('files',0);seen=set();completed=set(saved.get('completed',[]))
    for src in sorted(selected.glob('*/*/*.csv')):
        if str(src) in completed:continue
        meta=json.loads((src.parent/'meta.json').read_text())
        if not accepted(meta.get('license','')):continue
        try:
            result=read(src)
            if result is None:continue
            df,scores=result;files+=1
            for n,(score,side,count) in scores.items():
                if count!=n or score>=bars[n]-1e-10:continue
                part=df[df['n']==n]
                rows=[dict(n=str(n),square_id=str(i),x=repr(float(x)),y=repr(float(y)),angle=repr(float(a)))
                      for i,(x,y,a) in enumerate(part[['x','y','angle']].itertuples(index=False,name=None))]
                ok,evidence=audit(rows)
                origin=public_origin(data,dict(n=str(n),score=repr(score),L=repr(side),source=meta['ref']+' :: '+src.name,licence=meta['license']))
                reason=refused_source(origin,S)
                record_pins=[]
                try:record_pins=inspect_records(data/src.relative_to(selected),origin['source'],capture=True)
                except ValueError as exc:reason=reason or str(exc)
                if not ok:reason='excluded shared-square geometry'
                if n==916:reason=reason or 'inherited public source chain lacks per-n clearance'
                if n in (639,691,745,858,918):reason=reason or 'public union-sensitive count lacks a complete independent source trace'
                record=dict(n=n,score_estimate=score,bar=bars[n],source=origin['source'],licence=origin['licence'],share_audit=evidence,refusal=reason)
                decisions.append(record)
                if reason:continue
                key=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
                if key in seen:continue
                seen.add(key);p=root/'quick-starts'/f'{n}-{key[:16]}.csv';p.parent.mkdir(exist_ok=True)
                rows_write(p,rows)
                enqueue(p,dict(n=n,kind='fresh-public',source=f'public {origin["source"]}; harvested {data}; raw file {data}/{src.parent.parent.name}/{src.parent.name}/{src.name}; estimate {score!r}',
                               licence=origin['licence'],evidence=evidence,score_estimate=score,parents=record_pins,public_records_checked=RECORDS_VERSION),1)
                state(f'QUEUE quick public n={n} estimate={score} live_gain={bars[n]-score:.3e}; floatsafe and remote proof pending')
            state(f'READ quick final CSV {meta["ref"]}/{src.name} puzzles={len(scores)}')
            completed.add(str(src))
            write_json(progress,dict(revision=revision,completed=sorted(completed),decisions=decisions,files=files))
            from dispatch import drain
            drain(limit=8)
        except Exception as e:
            state(f'SKIP quick CSV {src} error={repr(e)}')
    write_json(root/'decisions.json',decisions)
    state(f'PUBLIC quick files={files} estimated_candidates={len(decisions)} eligible={sum(not r["refusal"] for r in decisions)}')


if __name__=='__main__':
    p=S/'take-harvest-r28/work/public01/data/nb/alexchilton__squares-101-the-starter-kit-12-100-downloads/submission.csv'
    df,scores=read(p)
    assert scores[972][2]==972 and abs(scores[972][0]-0.015593904057188412)<1e-12,scores[972]
    print('CONTROL quick reader: real public 972 side estimate matches its official raw score within 1e-12; 1000 puzzles read',flush=True)
