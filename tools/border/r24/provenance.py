from pathlib import Path
import json,csv,re,sys,time
S=Path('$SCRATCH/bounties-squares');W=Path(__file__).parent;T=W.parent
sys.path.insert(0,'.')
import border_sweep as b
changed={int(r['n']) for r in json.load(open(S/'gate/cand-round23-1113a/gate.json'))['moved']}
cache={};rejected=set()
def reject(p,why):
 key=(str(p),why)
 if key not in rejected:
  rejected.add(key)
  with open(W/'source-rejections.jsonl','a') as f:f.write(json.dumps(dict(path=str(p),why=why,time=time.time()))+'\n')
 return False

def metadata(p):
 p=Path(p)
 for q in [p.with_suffix('.json'),Path(str(p)+'.json')]:
  if q.exists():
   try:
    data=json.load(open(q))
    if isinstance(data,dict):
     if data.get('source_override'):data.setdefault('source',data['source_override'])
     if data.get('licence_override'):data.setdefault('licence',data['licence_override'])
    return data
   except (ValueError,OSError):pass
 override=W/'provenance-overrides.json'
 if override.exists():
  j=json.load(open(override))
  if str(p) in j:return j[str(p)]
 if p.stem.isdigit() and (p.parent/'take.tsv').exists():
  return next((r for r in csv.DictReader(open(p.parent/'take.tsv'),delimiter='\t') if r['n']==p.stem),{})
 # Import the reader lane's ancestry walker for its versioned near endpoints.
 if 'take-readers-' in str(p) and p.parent.name=='near':
  match=re.search(r'from(\d+-r\d+h[0-9a-f]+)',p.name)
  if match:
   for rnd in (24,23,22):
    state=S/f'take-readers-r{rnd}/work/follow.json'
    if not state.exists():continue
    try:
     import readers_sources
     st=readers_sources.archived_state(str(state)) if rnd<24 else json.load(open(state))
     donor=match[1]
     if donor not in st.get('sources',{}):continue
     src,lic=st['sources'][donor];n=int(next(csv.DictReader(open(p)))['n'])
     ok,ev=readers_sources.audit((p,n,rnd,True,src,lic),S,st)
     if ok:return dict(source='layer walk from '+donor+'; '+src,licence=lic,reader_evidence=ev)
    except (OSError,ValueError,KeyError,RecursionError):continue
 return {}

def bad(text):
 text=text.replace('\\','')
 # A fresh clean layout can have an excluded count. Refuse the old source paths, not the output n.
 patterns=[r'CC BY-SA',r'prvsiyan/squares-verified-best-of-1105',r'penguin069/squares-joegun-boxed-certified-union',r'take-harvest-r22/(?:639|691|745|858|918)(?:\D|$)',r'take-[^/]+-r23/(?:near/|work/(?:donors/|[^/]+/))?(?:639|980|981)(?:\D|$)',r'take-forensics-r(?:1[0-9]|2[0-3])/(?:near/|work/donors/)?918(?:\D|$)',r'(?:held|gather/[^ ]+)\s+(?:n\s*[=:]?\s*)?801\b']
 return next((q for q in patterns if re.search(q,text)),None)

def audit(p,row=None,visited=None):
 p=Path(p);visited=set() if visited is None else visited
 why=bad(str(p))
 if why:return reject(p,'forbidden source path '+why)
 if str(p) in visited:return True
 visited.add(str(p))
 if p==S/'gather/round23-2026-11-13a.csv':return True
 try:
  n=int(next(csv.DictReader(open(p)))['n'])
 except (OSError,ValueError,KeyError,StopIteration):return reject(p,'unreadable')
 if p.parent.name.endswith('-r23') and p.stem.isdigit() and n in changed:return True
 data=dict(row) if row else metadata(p)
 if not data:return reject(p,'no ancestry metadata')
 text=json.dumps(data);why=bad(text)
 if why:return reject(p,'forbidden ancestry '+why)
 # Resolve every upstream near lacking inline ancestry. Metadata contains recipes, parts, or modules on traced inputs.
 refs=re.findall(r'$SCRATCH/bounties-squares/[^\s"<>;,]+\.csv',text.replace('\\',''))
 parents=[Path(x) for x in refs if '/near/' in x and x!=str(p)]
 for q in set(parents):
  if not q.exists():return reject(p,'missing ancestor '+str(q))
  if not audit(q,visited=visited):return reject(p,'unresolved ancestor '+str(q))
 good=any(k in data for k in ('manifest','parts','modules')) or bool(data.get('source') or data.get('donor_source'))
 if not good:return reject(p,'metadata has no source recipe')
 return True

def audit_manifest(r):
 why=bad(json.dumps(r))
 if why:return reject(r.get('id'),why)
 p=r.get('near')
 return bool(p) and audit(Path(p),{'source':r.get('donor_source',''),'licence':r.get('donor_licence','')})


def enrich_source(source, licence):
    if 'areebbb/sis-certified-union-micro-shrink-lb-22-17479' not in source:
        return source, licence
    # The canonical accepted-row table already contains the per-n upstream chain.
    if 'per_n.csv' in source:
        return source, licence
    counts=set(re.findall(r'take-harvest-r22/(\d+)\.csv', source.replace('\\','')))
    if not counts:
        raise ValueError('areebbb ancestry lacks a per-n public donor')
    public=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
    records={r['n']:r for r in csv.DictReader(open(public))}
    for count in sorted(counts,key=int):
        r=records[count]
        upstream=r['src']
        if 'penguin069/squares-joegun-boxed-certified-union' in upstream:
            raise ValueError('excluded areebbb upstream '+count)
        notice='areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n='+count+': '+json.dumps(r,sort_keys=True)
        source+=' | '+notice
        licence+='; '+notice+'; Apache 2.0 (public notebook output)'
    return source, licence
