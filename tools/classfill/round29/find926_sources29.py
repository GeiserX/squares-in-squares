from common29 import *
from light29 import load
import numpy as np
import forensics_compose as fc
wanted={'48bc58a09300393ecd144867bca054a9ec51ddd5c69ebb0a6033975ed4de9007','56c1c121990850a4dddf0d3a5a3e42c449b4b8a5e23e03e8062d67c394a328f5','ee7c3cd24175bdd05a9865a475560fc0698dc0d592eb58b17854102781238fd0'}
seen={};matches={};count=0
for rnd in [23,24]:
 for d in S.glob(f'take-*-r{rnd}'):
  if 'assemble' in d.name:continue
  for p in d.rglob('989*.csv'):
   if time.time()>=SEARCH_END:break
   try:
    data=p.read_bytes();sha=hashlib.sha256(data).hexdigest()
    if sha in seen:digest=seen[sha]
    else:
     a=load(str(p),{989}).get(989)
     if not a or len(a)!=989:continue
     _,framed=fc.frame(np.asarray(a));digest=hashlib.sha256(np.round(framed,12).tobytes()).hexdigest();seen[sha]=digest;count+=1
    if digest in wanted:matches.setdefault(digest,[]).append(str(p))
   except (OSError,ValueError,KeyError,csv.Error):pass
atomic(W/'926-archive-matches.json',dict(unique_arrays=count,matches=matches));print(json.dumps(dict(unique_arrays=count,matches=matches),indent=1),flush=True)
