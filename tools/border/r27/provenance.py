from pathlib import Path
import json,csv,re,sys,time
S=Path('$SCRATCH/bounties-squares');W=Path(__file__).parent;T=W.parent
sys.path.insert(0,'.')
import border_sweep as b
changed={int(r['n']) for r in json.load(open(S/'gate/cand-round25-1114b/gate.json'))['moved']}
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
 # r26 revive: a walked row records its max centre distance to each excluded file as "prvsiyan 1105 (CC BY-SA)=0.647".
 # The label alone is not a CC BY-SA input: drop it so only a distance below 0.5 refuses, and catch a labelled low distance.
 text=re.sub(r'(prvsiyan 1105) \(CC BY-SA\)',r'\1',text)
 text=re.sub(r'(?:prvsiyan 1105|samanyu_\w+)[^=,;\]]{0,40}=\s*[0-9.]+','',text)  # r27: a recorded distance is no longer a test
 # A fresh clean layout can have an excluded count. Refuse the old source paths, not the output n.
 # r27: the Samanyu rule is lifted (round 27 brief item 2): the Samanyu-dev seed names, the bare 29e12ff3, 747r joins,
 # the held 921 modules, the stair-c 985 and the 735/790 seed-365 trees no longer refuse. The prvsiyan max centre
 # distance cut is dropped too (item 3); prvsiyan_share() below applies the share test to the layout itself.
 patterns=[r'ancestry-refused',r'"refused":\s',r'CC BY-SA',r'prvsiyan/squares-verified-best-of-1105',r'penguin069/squares-joegun-boxed-certified-union',r'take-harvest-r22/(?:639|691|745|858|918)(?:\D|$)',r'take-[^/]+-r23/(?:near/|work/(?:donors/|[^/]+/))?(?:639|980|981)(?:\D|$)',r'take-forensics-r(?:1[0-9]|2[0-3])/(?:near/|work/donors/)?918(?:\D|$)',r'(?:held|gather/[^ ]+)\s+(?:n\s*[=:]?\s*)?801\b',r'take-[^/]+-r23/(?:near/|work/)?[^ ]*?/?980(?:\D|$)',r'take-forensics-r25/near/(?:540|587|539|794|491)-rect\.csv',r'take-midm-r25/near/(?:860|975)-raw-kick\.csv',r'cand-round25-1114a',r'round25-2026-11-14a\.csv']
 return next((q for q in patterns if re.search(q,text)),None)

_wd={'t':0,'m':{},'h':set()}
def withdrawn():
 # r27: every csv path named on a WITHDRAW line of handoff-r27.log, with the line time. A file at that path is
 # refused when it is gone or older than the line; a file written again after the line is walked as usual.
 if time.time()-_wd['t']>60:
  m={}
  try:
   import datetime
   for line in open(S/'handoff-r27.log'):
    if 'WITHDRAW' not in line:continue
    try:t=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
    except ValueError:continue
    for x in re.findall(r'$SCRATCH/bounties-squares/[^\s,;]+?\.csv',line):m[x]=max(m.get(x,0),t)
  except OSError:pass
  # r27 23:30Z: also the sha256 prefixes of the withdrawn files (from the file if it is still there, else from the
  # lpfeed and wfeed indexes), since another lane names its pinned snapshot, not the path (our 798 missed this).
  import hashlib
  hs=set()
  known={}
  for ix in (W/'lp/index.json',W/'wq/index.json'):
   try:
    for k,v in json.load(open(ix)).items():
     if v.get('sha256'):known[v['path']]=v['sha256']
     elif '-' in k:known[v['path']]=k.split('-')[-2] if k.startswith('z') else k.split('-')[0]
   except (OSError,ValueError):pass
  for x in m:
   h=None
   try:
    import os
    h=hashlib.sha256(open(x,'rb').read()).hexdigest() if os.path.getmtime(x)<=m[x]+1 else None  # rewritten after the line: not the withdrawn bytes
   except OSError:h=known.get(x)
   if h:hs.add(h[:12])
  _wd.update(t=time.time(),m=m,h=hs)
 return _wd['m']
def audit(p,row=None,visited=None):
 p=Path(p);visited=set() if visited is None else visited
 why=bad(str(p))
 if why:return reject(p,'forbidden source path '+why)
 tw=withdrawn().get(str(p))
 if tw is not None:
  try:mt=p.stat().st_mtime
  except OSError:mt=None
  if mt is None or mt<=tw+1:return reject(p,'withdrawn on handoff-r27.log')
 if str(p) not in _wd['m']:
  try:
   if hashlib_sha(p)[:12] in _wd['h']:return reject(p,'withdrawn on handoff-r27.log (same sha256)')
  except OSError:pass
 if str(p) in visited:return True
 visited.add(str(p))
 if p in (S/'gather/round23-2026-11-13b.csv',S/'gather/round25-2026-11-14b.csv'):return True
 try:
  n=int(next(csv.DictReader(open(p)))['n'])
 except (OSError,ValueError,KeyError,StopIteration):return reject(p,'unreadable')
 data=dict(row) if row else metadata(p)
 if not data:return reject(p,'no ancestry metadata')
 text=json.dumps(data);why=bad(text)
 if why:return reject(p,'forbidden ancestry '+why)
 hit=next((h for h in _wd['h'] if h in text),None)
 if hit:return reject(p,'names a withdrawn file by sha256 '+hit)
 # Resolve every upstream near lacking inline ancestry. Metadata contains recipes, parts, or modules on traced inputs.
 refs=re.findall(r'$SCRATCH/bounties-squares/[^\s"<>;,]+\.csv',text.replace('\\',''))
 parents=[Path(x) for x in refs if '/near/' in x and x!=str(p)]
 for q in set(parents):
  if not q.exists():return reject(p,'missing ancestor '+str(q))
  if not audit(q,visited=visited):return reject(p,'unresolved ancestor '+str(q))
 # r26: a parent that is a take csv of another lane is checked through its take.tsv row (the row holds the walked
 # ancestry text, e.g. the max centre distance to the excluded files).
 for x in set(refs):
  m=re.search(r'/(take-[^/]+-r\d+)/(\d+)\.csv$',x)
  if not m or x==str(p):continue
  try:trow={r['n']:r for r in csv.DictReader(open(S/m[1]/'take.tsv'),delimiter='\t')}.get(m[2])
  except (OSError,KeyError):trow=None
  if trow and not audit(Path(x),row=trow,visited=visited):return reject(p,'unresolved take ancestor '+x)
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


def prvsiyan_share(n,path):
 """r27 rule b share test: share of squares within 1e-3 of the prvsiyan 1105 row of n (classfill prvsim26.py)."""
 import subprocess
 out=subprocess.run(['$SCRATCH/bounties-squares/venv/bin/python','-I','tools/classfill/round26/prvsim26.py',f'{n}:{path}'],capture_output=True,text=True,timeout=600).stdout
 m=re.search(r'within1e-3 ([0-9.]+)',out)
 if m:return float(m[1])
 if 'rows' in out and ' 0 ' in out.split('rows',1)[1][:12]:return 0.0  # no prvsiyan row of this n
 raise ValueError('share test failed: '+out.strip()[:200])

def hashlib_sha(p):
 import hashlib
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()
