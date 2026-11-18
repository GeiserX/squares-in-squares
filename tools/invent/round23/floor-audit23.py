import pathlib,json,csv,math,re
S=pathlib.Path('$SCRATCH/bounties-squares');out=[]
for rd in (22,23):
 W=S/f'take-invent-r{rd}/work'
 for j in json.load(open(W/'jobs.json')):
  p=W/'boxE-raw'/j['id'];logs=list(p.glob('slide-*.tsv'))
  if not logs or not(p/'done.json').exists()or j['kind']=='control':continue
  lines=logs[0].read_text().splitlines();m=re.search('start=([0-9.]+)',lines[0]);start=float(m[1]);rr=[]
  for l in lines:
   a=l.split('\t')
   if a[0].isdigit()and len(a)>4:
    try:rr.append((float(a[4]),float(a[5])))
    except ValueError:pass
  if len(rr)<6:continue
  d=json.load(open(p/'done.json'));side=(d['new']+1)*math.sqrt(j['n'])if'new'in d else start
  early=min(v for v,t in rr[:6]);old=sum(abs(v-start)<5e-9 for v,t in rr[:6])>=3 and early>=start-1e-8
  new=sum(abs(v-early)<5e-9 for v,t in rr[:6])>=3 and early>=start-1e-8
  out.append(dict(round=rd,id=j['id'],n=j['n'],old=old,new=new,step=start-side,seconds=sum(t for v,t in rr[6:]),actual_stop=any('plateau stop after'in l for l in lines)))
O=pathlib.Path(__file__).resolve().parent;(O/'floor-audit23.json').write_text(json.dumps(out,indent=2))
for rd in (22,23):
 a=[r for r in out if r['round']==rd]
 for k in ('old','new'):
  st=[r for r in a if r[k]];lost=[r for r in st if r['step']>1e-8]
  print(rd,k,'eligible',len(a),'stop',len(st),'seconds',sum(r['seconds']for r in st),'moves_lost',[(r['n'],r['step'])for r in lost])
print('actual r23 stops',sum(r['actual_stop']for r in out if r['round']==23))
