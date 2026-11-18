import csv,json,math
csv.field_size_limit(16*1024*1024)
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');T=S/'take-border-r24';W=T/'work'
held={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round23-1113a/details.csv'))};bars=dict(held)
for pat in ['take-*-r24']:
 for t in S.glob(pat):
  if t==T or not(t/'take.tsv').exists():continue
  try:
   for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t'):bars[int(r['n'])]=min(bars[int(r['n'])],float(r['new']))
  except (ValueError,KeyError):pass
man={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')};pairs={}
for p in (W/'q').glob('*.k0.json'):
 ident=p.name.removesuffix('.k0.json');r=man.get(ident)
 if not r:continue
 try:j=json.load(open(p))
 except ValueError:continue
 key=(int(r['donor']),int(r['n']),r['kind']);v=pairs.setdefault(key,[])
 v.append(dict(giveback=j['s_start']-j['s_final'],margin=j['s_final']-(bars[key[1]]+1)*math.sqrt(key[1]),round=j['round'],seconds=j['secs']))
with open(W/'measure.tsv','w') as f:
 w=csv.writer(f,delimiter='\t');w.writerow(['donor','n','kind','starts','giveback','end_minus_bar','seconds'])
 for k,v in sorted(pairs.items(),key=lambda kv:min(a['margin'] for a in kv[1])):
  w.writerow([*k,len(v),max(a['giveback'] for a in v),min(a['margin'] for a in v),sum(a['seconds'] for a in v)])
for p in ['take.tsv','work/measure.tsv']:
 print(p)
 for r in list(csv.DictReader(open(T/p),delimiter='\t'))[:12]:print({k:v for k,v in r.items() if k not in ['source','licence']})
