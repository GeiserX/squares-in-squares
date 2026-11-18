"""Targeted public cycles. Each fetched pass and queue input is immutable."""
import csv
import hashlib
import json
import math
from pathlib import Path
import signal
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from policy import audit
sys.path.insert(0,str(L/'tools'))
from harvest_follow import public_origin,refused_source
from angle_take import accepted
PYTHON=str(S/'venv/bin/python')


def scan_handoffs():
    p=S/'handoff-r27.log'
    text=p.read_text() if p.exists() else ''
    (W/'handoff-last-read.txt').write_text(text)
    rows=[]
    for t in sorted(S.glob('take-*-r27/take.tsv')):
        if t.parent==T: continue
        rows+=table(t)
    write_json(W/'live-last-read.json',rows)
    state(f'SCAN live r27 takes rows={len(rows)} handoff lines={len(text.splitlines())}; fresh public cycle follows')
    if time.time()<END-900:
        import follow,importlib
        importlib.reload(follow)
        follow.scan()


def run(cmd,log,limit):
    with log.open('w') as f:
        p=subprocess.Popen(cmd,stdout=f,stderr=f,start_new_session=True)
        state(f'START pid={p.pid} command={cmd} log={log} deadline 23:45Z')
        start=time.time();last=0
        while p.poll() is None:
            if time.time()>=END-60 or time.time()-start>limit:
                __import__('os').killpg(p.pid,signal.SIGKILL);p.wait()
                state(f'KILL child {p.pid} limit/deadline');return False
            if time.time()-last>300:
                scan_handoffs();last=time.time()
            time.sleep(10)
        state(f'FINISH pid={p.pid} exit={p.returncode} log={log}')
        return p.returncode==0


def credits(data):
    # Older metadata points to its frozen credit tables. It is never merged again.
    old=S/'take-harvest-r26/work'
    for root in [old/'public3/data',old/'public2/data',old/'public/data']:
        for src in root.glob('*/*/meta.json'):
            dst=data/src.relative_to(root)
            if not dst.exists():
                dst.parent.mkdir(parents=True,exist_ok=True)
                m=json.loads(src.read_text());m['carried']=str(root)
                dst.write_text(json.dumps(m)+'\n')


def select_outputs(data, selected):
    # Final submissions carry the same candidate wins without parsing thousands
    # of archived checkpoints in fetched research ZIPs.
    names={'submission.csv','submission_merged.csv','submission_ours.csv',
           'effective_pandas_roundtrip.csv','improvements.csv','best_current.csv','c0.csv','best.csv'}
    import os
    count=0
    for src in data.glob('nb/*/*.csv'):
        if src.name not in names:continue
        dst=selected/src.relative_to(data);dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():os.link(src,dst)
        meta=json.loads((src.parent/'meta.json').read_text())
        meta['carried']=str(data)
        (dst.parent/'meta.json').write_text(json.dumps(meta)+'\n')
        count+=1
    state(f'SELECT final public output files={count}; archived checkpoint ZIPs remain unexecuted data')
    return count


def plan(root):
    data=root/'data'; merged=root/'merged'
    decisions=[]
    for name in ('best','alt'):
        for r in table(merged/f'{name}.tsv'):
            n=int(r['n']);bar=float(BAR[n])
            if r['source']=='seed merged0' or float(r['score'])>=bar-1e-10:continue
            p=merged/name/f'{n}.csv'
            if not p.exists():continue
            rows=list(csv.DictReader(p.open()))
            ok,ev=audit(rows)
            origin=public_origin(data,r)
            reason=refused_source(origin,S)
            if not accepted(r['licence']): reason=reason or 'public licence outside allow-list'
            if not ok:reason='excluded shared-square geometry'
            decision=dict(r,share_audit=ev,origin=origin,refusal=reason,path=str(p))
            decisions.append(decision)
            if reason:continue
            # Keep exact source output bytes and credits in this immutable pass.
            source=f'public {origin["source"]}; harvested {data}; source metadata {data}/nb/'+r['source'].split(' :: ')[0].replace('/','__')+'/meta.json'
            enqueue(p,dict(n=n,kind='fresh-public',source=source,licence=origin['licence'],evidence=ev),1)
            state(f'QUEUE public n={n} bar_gain={bar-float(r["score"]):.3e} source={r["source"]}')
    write_json(root/'decisions.json',decisions)
    state(f'PUBLIC plan winners={len(decisions)} accepted={sum(not x["refusal"] for x in decisions)} in {root}')


BAR={int(r['n']):r['bar'] for r in table(S/'round27-briefs/bar27.tsv')}
index=2 if (W/'public01/decisions.json').exists() else 1
# The initial fetch is already running. Adopt it by its recorded PID.
initial=13442
while time.time()<END-900:
    root=W/f'public{index:02d}';root.mkdir(exist_ok=True)
    if index==1:
        while True:
            try: __import__('os').kill(initial,0)
            except ProcessLookupError:break
            if (W/'fetch-cache.json').exists():break
            time.sleep(10)
    elif not (root/'fetch.log').exists() or 'CHANGED' not in (root/'fetch.log').read_text():
        if not run([PYTHON,'-I',str(L/'tools/harvest27/fetch.py'),str(root/'data'),str(W/'fetch-cache.json')],root/'fetch.log',600):
            index+=1;continue
    credits(root/'data')
    if select_outputs(root/'data',root/'selected'):
        if (root/'decisions.json').exists():
            state('ADOPT completed public pass '+str(index))
        else:
            from quick import plan as quick_plan
            quick_plan(root)
    next_at=time.time()+1200
    state(f'WAIT public cycle complete {index}; next targeted listing in 20 minutes')
    while time.time()<min(next_at,END-900):
        scan_handoffs();time.sleep(min(300,max(0,next_at-time.time())))
    index+=1
state('STOP public driver: reserved last 15 minutes for certification and cleanup')
