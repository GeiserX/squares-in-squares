"""State whether recorded ancestry reaches an unlicensed Samanyu seed."""
import pathlib,csv,json,re
from decimal import Decimal
from provenance24 import W,S

def seed_origin(n):
 p=W/'seed-origin24.json';cache=json.load(open(p)) if p.exists() else {}
 if str(n) in cache:return cache[str(n)]
 def rows(path):
  a=[]
  for r in csv.DictReader(open(path)):
   if int(r['n'])==n:a.append(tuple(Decimal(r[k]) for k in ('x','y','angle')))
  if not a:return []
  x=min(z[0] for z in a);y=min(z[1] for z in a);return sorted((a-x,b-y,c) for a,b,c in a)
 merged=rows(S/'seeds/merged0.csv');origin='unresolved'
 for name in ['samanyu_bestfit.csv','samanyu_22249.csv']:
  if merged and merged==rows(S/'seeds'/name):origin='samanyu';break
 if origin=='unresolved' and merged==rows(S/'seeds/couzo.csv'):origin='couzo'
 cache[str(n)]=origin;p.with_suffix('.tmp').write_text(json.dumps(cache));p.with_suffix('.tmp').replace(p);return origin

def notice(source,licence):
 text=source+' '+licence
 explicit=set(map(int,re.findall(r'\bn\s*=\s*(\d+) of Samanyu-dev',text)))
 for values in re.findall(r'Samanyu-dev seed ancestry: yes; seed n = ([0-9,]+)',text):explicit.update(map(int,values.split(',')))
 text=text.replace('Samanyu-dev seed ancestry: no; recorded ancestry has no Samanyu-dev seed layout','').replace('Samanyu-dev seed ancestry: no','')
 merged=set(map(int,re.findall(r'\b(\d+)h\w*\.[CF]\d*\s*<held:\s*seed merged0',text)))
 merged|=set(map(int,re.findall(r'held\s+(\d+)[^.;]{0,45}\bis seed merged0',text)))
 def bound_seeds(value,depth=0):
  if depth>12:return set()
  out=set()
  if isinstance(value,dict):
   if value.get('source_record')=='seed merged0' or value.get('source')=='seed merged0':
    nn=value.get('n');ss=value.get('source')
    if isinstance(ss,list) and len(ss)==2:nn=ss[1]
    if nn is not None:out.add(int(nn))
   for v in value.values():out|=bound_seeds(v,depth+1)
  elif isinstance(value,list):
   for v in value:out|=bound_seeds(v,depth+1)
  elif isinstance(value,str) and value.lstrip().startswith(('{','[')):
   try:out|=bound_seeds(json.JSONDecoder().raw_decode(value.lstrip())[0],depth+1)
   except ValueError:pass
  return out
 try:merged|=bound_seeds(json.loads(source.split('; pinned donor ancestry:')[-1]))
 except ValueError:pass
 seeds=set(explicit);unresolved=[]
 for n in merged:
  origin=seed_origin(n)
  if origin=='samanyu':seeds.add(n)
  elif origin!='couzo':unresolved.append(n)
 if seeds:
  return 'Samanyu-dev seed ancestry: yes; seed n = '+','.join(map(str,sorted(seeds)))+'; no licence stated upstream',True,sorted(seeds)
 if unresolved or 'Samanyu-dev' in text or ('seed merged0' in text and not merged) or re.search(r'each donor source and licence|see the k123 take dir|see source|held source notices',text):
  return 'Samanyu-dev seed ancestry: unresolved; recorded seed n = '+','.join(map(str,unresolved)),None,unresolved
 return 'Samanyu-dev seed ancestry: no; recorded ancestry has no Samanyu-dev seed layout',False,[]
