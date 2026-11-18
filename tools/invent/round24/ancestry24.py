"""Conservative source checks for invent round24. Unresolved starts stay out."""
import csv,json,pathlib,re
csv.field_size_limit(16*1024*1024)
S=pathlib.Path('$SCRATCH/bounties-squares');R=pathlib.Path('.')
C={int(r['n']):r for r in csv.DictReader(open(R/'results/round23-best-2026-11-13.tsv'),delimiter='\t')}
PER=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
A={int(r['n']):r for r in csv.DictReader(open(PER))}
BAD={639,691,745,858,918,980,981,801}

def clean(src,lic):
 t=src+' '+lic
 if not src.strip() or not lic.strip():return False,'missing source or licence'
 for word in ['squares-verified-best-of-1105','squares-joegun-boxed-certified-union','near build recorded by','see donor ledger','unresolved ancestry walk']:
  if word in t:return False,word
 # All old mentions of these counts are quarantined. New clean candidate inputs use a marked source boundary.
 old=t.split('CLEAN ROUND23 CANDIDATE BOUNDARY')[0]
 for n in BAD:
  if re.search(r'(?<![\da-f])'+str(n)+r'(?![\da-f])',old):
   frozen=re.search(r'take-[^/\s;]+-r(?:22|23)/(?:[^;\s]*?/)?'+str(n)+r'(?:\.csv|[-/])',old)
   current_public=('take-harvest-r24' in old and 'prvsiyan/a-square-deal-research-to-verified-packings' in old and 'malyshevdanil/' in old)
   current_candidate='gather/round23-2026-11-13a.csv' in old
   if n!=801 and not frozen and (current_public or current_candidate):continue
   return False,'quarantined old count '+str(n)
 return True,'source chain recorded'

def expand(src,lic):
 # Resolve immutable near sidecars before accepting shorthand from a downstream lane.
 paths=list(dict.fromkeys(re.findall(r'(?:$SCRATCH/bounties-squares/)?(take-[^/\s<>"()]+/near/[^\s<>";,()]+\.csv)',src)))
 for ref in paths[:12]:
  p=S/ref;tag='exact near ancestry '+ref
  if tag in src:continue
  for q in (p.with_suffix('.json'),pathlib.Path(str(p)+'.json')):
   if not q.exists():continue
   try:
    d=json.load(open(q));parent=d.get('source_override') or d.get('source')
    terms=d.get('licence_override') or d.get('licence')
    if isinstance(parent,str) and isinstance(terms,str):
     src+='; '+tag+': '+parent;lic+='; '+terms
    elif d.get('modules'):
     mods=d['modules'];src+='; '+tag+': '+', '.join(m['id']+' <'+m['source']+'>' for m in mods)
     lic+='; '+'; '.join(m['licence'] for m in mods)
   except (ValueError,KeyError,TypeError):pass
   break
 # Add exact per-n rows to shorthand public input references. The source table preserves upstream notices.
 refs=[]
 # Associate each public mention with its immediately preceding packing count.
 for hit in re.finditer('areebbb/sis-certified-union-micro-shrink-lb-22-17479',src):
  before=src[:hit.start()]
  matches=list(re.finditer(r'(?:n\s*=\s*|n\s+|donor\s+|/)(\d{1,4})(?:\.csv|\b)',before))
  if matches:refs.append(int(matches[-1][1]))
 if 'areebbb/' in src:
  for n in sorted(set(refs)):
   if n not in A:continue
   a=A[n];tag=f'areebbb per_n.csv donor n={n}'
   if tag in src:continue
   # Prefer the expanded chain already accepted by the assembler.
   if n in C and 'areebbb/' in C[n]['source'] and 'per_n.csv' in C[n]['source']:
    src+='; '+tag+': '+C[n]['source'];lic+='; '+C[n]['licence']
   else:
    src+='; '+tag+' '+json.dumps(a,sort_keys=True)+'; exact record '+str(PER)
    lic+='; areebbb per_n.csv donor n='+str(n)+': '+a['src']+'; Apache 2.0 (public notebook output); upstream notices retained'
 return src.replace('|',' / '),lic.replace('|',' / ')
