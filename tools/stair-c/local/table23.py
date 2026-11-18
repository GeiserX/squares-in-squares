import collections,csv,datetime,glob,json,math,os,pathlib,statistics,hashlib
S=pathlib.Path('$SCRATCH/bounties-squares');T=S/'take-stair-c-r23';W=T/'work';L=pathlib.Path('.')
H={int(r['n']):float(r['L']) for r in csv.DictReader(open(S/'gate/cand-round21-1113a/details.csv'))};B=dict(H)
for p in list(S.glob('take-*-r22/take.tsv'))+list(S.glob('take-*-r23/take.tsv')):
 if p==T/'take.tsv':continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  n=int(r['n']);B[n]=min(B[n],(1+float(r['new']))*math.sqrt(n))
records=[];bad=[]
for p in sorted(W.glob('boxcopy/*/raw-a/*.json')):
 try:
  j=json.load(open(p))
  if j.get('built') is None:continue
  n=int(j['n']);ids=[m['id'] for m in j.get('modules',[])]+['']*3;st=j.get('stacks',[0,0]);side=float(j['built']);early=bool(j.get('early_stage'))
  records.append(dict(n=n,m=math.isqrt(n-1),k=n-math.isqrt(n-1)**2,box=p.parent.parent.name,name=p.stem,stage='early_slp' if early else 'final',corner=ids[0],far1=ids[1],far2=ids[2],stacks1=st[0],stacks2=st[1],predicted_side=j.get('predicted',''),built_side=side,round21_side=H[n],other_take_side=B[n],built_minus_round21=side-H[n],built_minus_other_takes=side-B[n],seconds=sum(j.get('seconds',{}).values()),method='asymmetric_interlock' if 'intrusion' in j else j.get('squeeze','family'),record=str(p)))
 except Exception as exc:bad.append(dict(path=str(p),error=str(exc)))
cols=['n','m','k','box','name','stage','corner','far1','far2','stacks1','stacks2','predicted_side','built_side','round21_side','other_take_side','built_minus_round21','built_minus_other_takes','seconds','method','record']
out=L/'results/stair-c-r23-2026-11-13.tsv'
with open(str(out)+'.tmp','w',newline='') as f:
 writer=csv.DictWriter(f,fieldnames=cols,delimiter='\t',lineterminator='\n');writer.writeheader();writer.writerows(sorted(records,key=lambda r:(r['n'],r['built_side'],r['name'])))
os.replace(str(out)+'.tmp',out)
full=[r for r in records if r['stage']=='final'];early=[r for r in records if r['stage']=='early_slp']
nostarts=[]
for p in W.glob('boxcopy/*/raw-a/*.nostart'):
 try:nostarts.append(json.load(open(p)))
 except Exception:pass
contributions=[]
for p in S.glob('take-*-r23/take.tsv'):
 if p==T/'take.tsv':continue
 for r in csv.DictReader(open(p),delimiter='\t'):
  src=r.get('source','')
  if any(q in src for q in ('take-stair-c-r23','sc23zip51','stair-c round23')):contributions.append(dict(n=int(r['n']),take=str(p),source=src,score=float(r['new'])))
history=W/'contribution-history.jsonl'
known={json.loads(line)['key'] for line in history.read_text().splitlines()} if history.exists() else set()
with open(history,'a') as h:
 for row in contributions:
  key=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
  if key not in known:h.write(json.dumps(dict(key=key,asof=datetime.datetime.now(datetime.timezone.utc).isoformat(),**row))+'\n')
summary=dict(asof=datetime.datetime.now(datetime.timezone.utc).isoformat(),completed_builds=len(full),early_exports=len(early),n_built=len({r['n'] for r in full}),n_any_stage=len({r['n'] for r in records}),nostarts=len(nostarts),no_start_reasons=collections.Counter(j.get('why','') for j in nostarts),full_below_round21=sum(r['built_minus_round21']<-1e-9 for r in full),full_below_live=sum(r['built_minus_other_takes']<-1e-9 for r in full),closest_full=sorted(full,key=lambda r:r['built_minus_other_takes'])[:12],contributions=contributions,bad=bad)
json.dump(summary,open(W/'measurements.json','w'),indent=2)
print(json.dumps({k:summary[k] for k in ['asof','completed_builds','early_exports','n_built','nostarts','full_below_round21','full_below_live']}),flush=True)
