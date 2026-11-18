"""Measure retained source rows against the announced base and clean live takes."""
import csv,json,pathlib,math,collections,os,time
from provenance24 import W,S,mlp,credit
T=W.parent
base={int(r['n']):float(r['score']) for r in csv.DictReader(open(W/'details-base25.csv'))}
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));out=[];other_rejected=[]
for row in rows:
 n=int(row['n']);P=mlp.load(str(T/f'{n}.csv'),{n})[n]
 if not credit(n,P,str(T/f'{n}.csv')):raise RuntimeError(f'untraced own source {n}')
 others=[]
 for p in S.glob('take-*-r25/take.tsv'):
  if p.parent==T:continue
  for r in csv.DictReader(open(p),delimiter='\t'):
   if int(r['n'])!=n:continue
   path=p.parent/f'{n}.csv'
   try:
    Q=mlp.load(str(path),{n})[n]
    if credit(n,Q,str(path)):others.append((float(r['new']),str(p)))
    else:other_rejected.append([n,str(p)])
   except (OSError,KeyError,ValueError):other_rejected.append([n,str(p)])
 score=float(row['new']);bar=min([base[n]]+[s for s,_ in others]);gain=base[n]-score;exclusive=max(0.,bar-score) if bar-score>1e-10 else 0.
 out.append(dict(n=n,side=mlp.side(P),base_score=base[n],score=score,gain=gain,gain_beyond_others=exclusive,lowest=exclusive>0,other_bar=bar,other_rows=others,source=row['source'],licence=row['licence']))
records=[]
for l in (W/'records.jsonl').read_text().splitlines():
 try:records.append(json.loads(l))
 except ValueError:pass
kinds=collections.Counter('rebuild' if r['pool'].startswith('rebuild') else 'licensed' if r['pool'].startswith('licensed') else 'fresh' if r['pool'].startswith('fresh') else 'deferred' if r['pool'].startswith('defer') else 'saved' for r in records)
result=dict(measured_at=time.strftime('%FT%TZ',time.gmtime()),source_rows=len(out),lowest_n=[r['n'] for r in out if r['lowest']],gain_against_base=sum(r['gain'] for r in out),gain_beyond_others=sum(r['gain_beyond_others'] for r in out),rows=out,other_rejected=other_rejected,attempts=len(records),counts=len({r['n'] for r in records}),attempt_groups=dict(kinds),errors=[r for r in records if r.get('error')],timeouts=sum(any(r.get(k)==-2 for k in ['code','fq2code']) for r in records))
(W/'metrics25.tmp').write_text(json.dumps(result,indent=2));(W/'metrics25.tmp').replace(W/'metrics25.json')
print(json.dumps({k:v for k,v in result.items() if k not in ['rows','errors','other_rejected']}),flush=True)
