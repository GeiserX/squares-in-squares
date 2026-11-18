"""Expand saved near sidecars and exact reader donor ledgers before publication."""
import pathlib,re,csv,json,functools
from provenance24 import W,S,banned,key,mlp,base
@functools.lru_cache(None)
def reader_rows(path):
 try:return {r['donor']:r for r in csv.DictReader(open(path),delimiter='\t')}
 except (OSError,KeyError):return {}
@functools.lru_cache(None)
def per_n():
 p=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
 return {int(r['n']):r for r in csv.DictReader(open(p))}
@functools.lru_cache(None)
def malyshev():
 p=S/'take-harvest-r22/work/public/data/nb/malyshevdanil__squares-in-squares-living-atlas-of-tight-packings/submission_sources.csv'
 return {int(r['n']):r for r in csv.DictReader(open(p))}
def pieces(j):
 if isinstance(j,dict):
  if isinstance(j.get('modules'),list):return [(z.get('source',''),z.get('licence','own')) for z in j['modules']]
  if isinstance(j.get('parts'),dict):return [(json.dumps(j['parts']), ' | '.join(z.get('licence','own') for z in j['parts'].values() if isinstance(z,dict)))]
  if j.get('source') or j.get('source_record'):return [(str(j.get('source',j.get('source_record',''))),str(j.get('licence','source terms in sidecar')))]
 return []
def expand(c):
 c=dict(c);queue=[(c.get('source',''),c.get('n'),0)];seen=set();extra=[];lic=[];up=set()
 while queue:
  text,nn,depth=queue.pop(0)
  if depth>7:continue
  if 'areebbb/sis-certified-union-micro-shrink-lb-22-17479' in text and 'per_n.csv' not in text and not re.search(r'family_|modules\.py|k123_join|rectangle|stair-c|zone_',text) and nn and nn not in up:
   up.add(nn);row=per_n().get(nn)
   if row:
    chain='areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n = '+str(nn)+': '+json.dumps(row,separators=(',',':'))
    terms='areebbb/sis-certified-union-micro-shrink-lb-22-17479 (donor n = '+str(nn)+'), Apache 2.0 (Kaggle default for public notebooks)'
    if 'malyshevdanil/squares-in-squares-living-atlas-of-tight-packings' in row['src']:
     record=malyshev().get(nn,{})
     chain+=' -> malyshevdanil/squares-in-squares-living-atlas-of-tight-packings :: submission.csv -> submission_sources.csv, donor n = '+str(nn)+': '+json.dumps(record,separators=(',',':'))
     if not record.get('source','').startswith('sub:'):c['clean']=False
     terms+='; malyshevdanil/squares-in-squares-living-atlas-of-tight-packings :: submission.csv, submission_merged.csv (donor n = '+str(nn)+'), Apache 2.0 (Kaggle default for public notebooks)'
    elif 'penguin069/squares-joegun-boxed-certified-union' in row['src']:c['clean']=False
    else:
     # Reuse the accepted table's full per-n upstream record when available.
     cache=json.load(open(W/'base-credit24.json'))
     candidates=[z for z in cache.values() if z['n']==nn and z['origin']=='candidate round23' and 'per_n.csv' in z['source']]
     if candidates:chain+=' | accepted per-n chain: '+candidates[0]['source'];terms+=' | '+candidates[0]['licence']
     else:c['clean']=False;chain+='; unresolved upstream terms'
    extra.append(chain);lic.append(terms)
  paths=set(re.findall(r'($DATA/[^\s,;<>"\\]+\.csv)',text))
  for name in sorted(paths):
   p=pathlib.Path(name)
   if '/near/' not in name:
    old=re.search(r'take-[^/]+-r([0-9]+)/([0-9]+)\.csv$',name)
    if old and int(old[1])<=23:
     lp=p.parent/'take.tsv';token=str(lp)+':'+old[2]
     if token not in seen and lp.exists():
      seen.add(token)
      try:
       row=next(z for z in csv.DictReader(open(lp),delimiter='\t') if z['n']==old[2])
       if p.exists():
        nn=int(old[2]);A=mlp.load(str(p),{nn})[nn];canonical=base().get(key(nn,A))
        if canonical:row={**row,'source':canonical['source'],'licence':canonical['licence']}
      except (KeyError,StopIteration):row=None
      if row:
       extra.append(token+': '+row['source']);lic.append(row.get('licence','own'));queue.append((row['source'],int(old[2]),depth+1))
    continue
   m=re.search(r'from(\d+)-(r\d+h[0-9a-f]+)',p.stem)
   if m and 'take-readers-' in name:
    donor=m[1]+'-'+m[2];lp=p.parent.parent/'work/sources-all.tsv';token=str(lp)+':'+donor
    if token not in seen:
     seen.add(token);row=reader_rows(str(lp)).get(donor)
     if row:
      extra.append(token+': '+row['source']);lic.append(row.get('licence','own'));queue.append((row['source'],int(m[1]),depth+1))
   for sidecar in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json')]:
    token=str(sidecar)
    if token in seen or not sidecar.exists():continue
    seen.add(token)
    try:j=json.load(open(sidecar))
    except (ValueError,OSError):continue
    for src,terms in pieces(j):
     if src:
      extra.append(token+': '+src);lic.append(terms);queue.append((src,int(j.get('n',nn)) if j.get('n',nn) else None,depth+1))
 if extra:c['source']+=' | expanded recorded ancestry: '+' | '.join(dict.fromkeys(extra));c['licence']+=' | '+' | '.join(dict.fromkeys(lic))
 c['expanded_records']=len(extra)
 if c.get('origin')!='candidate round23' and banned(json.dumps(c)):c['clean']=False
 return c
