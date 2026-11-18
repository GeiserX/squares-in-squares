"""Measure complete packing files from incomplete fetches without admitting them."""
import csv
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,W,state,table,write_json


def scan(root):
    from driver import packing_csv
    from quick import read
    from policy import audit
    seen_path=W/'partial-seen.json'
    seen=json.loads(seen_path.read_text()) if seen_path.exists() else {}
    bars={int(r['n']):float(r['bar']) for r in table(S/'round34-briefs/bar34.tsv')}
    records=[]
    for path in sorted((root/'fetch-failed').glob('*/*.csv')):
        if not packing_csv(path):continue
        sha=hashlib.sha256(path.read_bytes()).hexdigest()
        if sha in seen:continue
        result=read(path)
        if result is None:continue
        df,scores=result;checks=[]
        for n,(score,side,count) in scores.items():
            if count!=n or score>=bars[n]-1e-10:continue
            part=df[df['n']==n]
            rows=[dict(n=n,x=float(x),y=float(y),angle=float(a))
                  for x,y,a in part[['x','y','angle']].itertuples(index=False,name=None)]
            allowed,evidence=audit(rows)
            checks.append(dict(n=n,score_estimate=score,share_pass=allowed,
                share1e3=max((v['share1e3'] for v in evidence),default=0.),
                share1e2=max((v['share1e2'] for v in evidence),default=0.)))
        record=dict(path=str(path),sha256=sha,checks=checks,admitted=False,
                    reason='incomplete fetch; source proof unavailable')
        records.append(record);seen[sha]=str(path)
        state(f'PARTIAL diagnostic {path.parent.name}/{path.name}: raw_crossings={len(checks)} share_pass={sum(c["share_pass"] for c in checks)}; incomplete source, nothing admitted')
        write_json(root/'partial-diagnostic.json',records)
        write_json(seen_path,seen)
    if not (root/'partial-diagnostic.json').exists():write_json(root/'partial-diagnostic.json',records)


def control():
    import tempfile
    from unittest.mock import patch
    import fetch
    import download_parts
    from public_records import inspect
    kernel=dict(ref='example/changed-packings',lastRunTime='2026-11-16T19:00:00Z')
    files=[dict(fileName='a-checkpoints.zip',url='https://data.invalid/kf/123/a'),
           dict(fileName='a-wide-stats.csv',url='https://data.invalid/kf/123/stats'),
           dict(fileName='submission.csv',url='https://data.invalid/kf/123/z')]
    calls=[]
    def get(url):
        if '/kernels/list?' in url:return [kernel] if url.endswith('page=1') else []
        return dict(files=files)
    def download(url,path):
        calls.append(Path(path).name)
        if Path(path).name!='submission.csv':raise ValueError('public file exceeds bounded download')
        Path(path).write_text('n,square_id,x,y,angle\n1,0,0,0,0\n')
    with tempfile.TemporaryDirectory(dir=W) as name:
        root=Path(name);cache={}
        with patch.object(download_parts,'ROOT',root/'parts'),patch.object(fetch,'FIRST',[]),patch.object(fetch.rpc,'get',side_effect=get),patch.object(fetch.rpc,'download',side_effect=download):
            fetch.fetch(root/'first/data',cache)
            assert calls==['submission.csv','a-wide-stats.csv'],calls
            packing=root/'first/fetch-failed/example__changed-packings/submission.csv'
            assert packing.is_file()
            try:inspect(packing,'example/changed-packings :: submission.csv')
            except ValueError as exc:assert 'fetch incomplete' in str(exc)
            else:raise AssertionError('incomplete source was admitted')
            calls.clear();fetch.fetch(root/'same/data',cache);assert calls==[]
            kernel['lastRunTime']='2026-11-16T19:01:00Z'
            files[0]['url']='https://data.invalid/kf/124/a';files[1]['url']='https://data.invalid/kf/124/stats';files[2]['url']='https://data.invalid/kf/124/z'
            fetch.fetch(root/'changed/data',cache)
            assert calls==['submission.csv','a-wide-stats.csv'],calls
    order=['example/slow','example/fresh']
    kernels={'example/slow':dict(lastRunTime='old'),'example/fresh':dict(lastRunTime='new')}
    notes={'example/slow':dict(run='old')}
    assert fetch.defer_dry(order,kernels,notes)==list(reversed(order))
    kernels['example/slow']['lastRunTime']='changed'
    assert fetch.defer_dry(order,kernels,notes)==order
    print('CONTROL measured dry run moves behind fresh sources; changed geometry run regains its original priority',flush=True)
    print('CONTROL final CSV precedes wide diagnostic CSV and archive refusal; complete CSV retained; incomplete source admission refused; same version does not download again; changed run and session retry',flush=True)

if __name__=='__main__':
    control()
    from download_parts import control as checkpoint_control
    checkpoint_control()
