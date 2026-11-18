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

def last_reason(p=None):
 """r32 (r31 next item 5): the reasons of the refusals recorded for p (or the last few refusals) in source-rejections.jsonl."""
 try:lines=[json.loads(l) for l in open(W/'source-rejections.jsonl') if l.strip()]
 except (OSError,ValueError):return 'no recorded reason'
 hits=[x for x in lines if p is None or x.get('path')==str(p)] or lines[-3:]
 return '; '.join(dict.fromkeys(f"{Path(x['path']).name}: {x['why']}" for x in hits[-3:])) or 'no recorded reason'

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
 patterns=[r'ancestry-refused',r'"refused":\s',r'CC BY-SA',r'prvsiyan/squares-verified-best-of-1105',r'penguin069/squares-joegun-boxed-certified-union',r'take-harvest-r22/(?:639|691|745|858|918)(?:\D|$)',r'take-[^/]+-r23/(?:near/|work/(?:donors/|[^/]+/))?(?:639|980)(?:\D|$)',r'take-forensics-r(?:1[0-9]|2[0-3])/(?:near/|work/donors/)?918(?:\D|$)',r'take-[^/]+-r23/(?:near/|work/)?[^ ]*?/?980(?:\D|$)',r'take-forensics-r25/near/(?:540|587|539|794|491)-rect\.csv',r'take-midm-r25/near/(?:860|975)-raw-kick\.csv',r'cand-round25-1114a',r'round25-2026-11-14a\.csv',r'6d78315914dc85da2cb4',r'6d78315914dc',r'take-forensics-r24/work/donors/684-',r'take-harvest-r26/695\.csv',r'take-harvest-r26/[^ ]*814[^ ]*5a4c0cdb|5a4c0cdb',r'799-986b3b6d']  # r30 13:40Z: main 13:32:00Z names these direct public-first parents  # r28: the n684 donor of share 1.0 (invent 23:50:47Z withdrawal) and its descendants
 # r30 (brief item 3): the 801 row and every 981 built on it are ours; their patterns are gone. The prvsiyan file named
 # itself, penguin069 for 639 691 745 858 918, CC BY-SA and the r23 639/980 family still refuse.
 return next((q for q in patterns if re.search(q,text)),None)

_wd={'t':0,'m':{},'h':set()}
def withdrawn():
 # r27: every csv path named on a WITHDRAW line of handoff-r28.log, with the line time. A file at that path is
 # refused when it is gone or older than the line; a file written again after the line is walked as usual.
 if time.time()-_wd['t']>60:
  m={};line_hashes=set()
  try:
   import datetime
   events=[]
   for line in [l for h in ('handoff-r27.log','handoff-r28.log','handoff-r29.log','handoff-r30.log','handoff-r31.log','handoff-r32.log','handoff-r33.log','handoff-r34.log','handoff-r35.log','handoff-r36.log','handoff-r37.log') if (S/h).exists() for l in open(S/h,errors='replace')]:  # r28: r27 withdrawals for still-valid reasons still apply
    # r29 06:25Z: the trigger words count only in the prose of the line. Tokens holding a '/' (paths) and build ids
    # (a token with a digit and a '-' or ':', e.g. reopen:reopen-916-8dc5ae5a6839 or ...-r27reopen-871-...) are cut
    # first. r28 read the modules r27 line 'fresh build n=871 ... 871-871-r27reopen-...csv' as a withdrawal of that
    # build, which refused the whole 871 -> 812 -> 813 -> 933 -> 995 chain of stair-c and modules in round 29.
    prose=re.sub(r'\S*/\S*',' ',line);prose=re.sub(r'\S*(?=[^\s]*\d)(?=[^\s]*[-:])[^\s]*[-:][^\s]*',' ',prose)
    if not re.search(r'withdr|reinstate|re-?open|SOURCE-HOLD|SOURCE-RELEASE',prose,re.I):continue
    try:t=datetime.datetime.fromisoformat(line.split()[0].replace('Z','+00:00')).timestamp()
    except ValueError:continue
    # r28: REINSTATE / REOPEN lines and 'withdrawal lifted' or 'void' lines re-open the files they name.
    back=bool(re.search(r'(?-i:REINSTATE|REOPEN)|(?<![\w/.-])(?:re-?open(?:ed|s)?|reinstate[ds]?)\b(?![-_.\w])|withdrawals? (?:is |are )?(?:lifted|void)|lifted for this exact hash|hold (?:is )?(?:lifted|released)|SOURCE-RELEASE',prose,re.I))
    if not back and not re.search(r'withdr|SOURCE-HOLD',prose,re.I):continue  # r29: a re-open word that is not a re-open is not a withdrawal either
    if not back and re.search(r'\bnot withdrawn\b|\bno withdrawal\b',prose,re.I):continue
    # main -> all 00:19:03Z: a withdrawal made only for a prvsiyan share of our own layout or its ancestor or seed is
    # void; a withdrawal for penguin069, CC BY-SA, a missing licence or an unresolved trace still applies.
    # r30 13:40Z (main 12:40:55Z ruling): a withdrawal for a held ancestor's share is void, and so are the withdrawals that
    # followed it only because they descend from the withdrawn forensics r29 376 bytes (baeff87d90a1): backlog, midm, ours.
    if not back and (re.search(r'held[- ]ancestors?',line,re.I) or re.search(r'baeff87d90a1|forensics 376 take that forensics withdrew',line)):continue
    if not back and re.search(r'share',line,re.I) and not re.search(r'untraced|unresolved|licen|notice|penguin|joegun|areebbb|CC BY-SA|rule-a|excluded[- ]family|independent of the lifted|not the lifted|public[- ]first|public[- ]source',line,re.I):continue  # r29: a prvsiyan share of 0.4 or more on a public-first row is a valid reason (border brief r29)  # r28 01:51Z: forensics named 'the lifted own-share rule' only to say a rule-a withdrawal does not rest on it
    paths=[];hashes=[]
    # r28 brief item 6: 'not the withheld X' or 'keeps X' is a retention note, not a withdrawal; such a path is kept.
    # r28: relative names (take-backlog-r27/927.csv) count too; backlog wrote its 00:09:51Z withdrawal that way.
    for mm in re.finditer(r'(?:$SCRATCH/bounties-squares/)?(take-[A-Za-z0-9_.-]+-r\d+/[^\s,;()\'"]+?\.csv)',line):
     x=str(S/mm[1]);before=line[max(0,mm.start()-48):mm.start()]
     # only a phrase right before the path counts ('keeps every descendant of that tree out, X' is a withdrawal of X)
     if not back and re.search(r'(?:\bkeeps?|\bkept|\bnot the withheld|\bnot the|\bretains?|\bretained)\s+(?:the\s+|its\s+)?$',before,re.I):
      _wd.setdefault('kept',set()).add(x);continue
     paths.append(x)
    # r28 03:41Z: a SOURCE-HOLD line names bare build files 'under take-<lane>-r28/near/'; every file of those builds in
    # that folder is held (stair-c held 804, 995 and 997 builds pending an ancestry repair).
    if re.search(r'SOURCE-HOLD',line):
     for d in re.findall(r'under (take-[A-Za-z0-9_.-]+-r\d+/near)/',line):
      for b in re.findall(r'\d+-r\d+-([0-9a-f]{12})-',line):
       paths+=[str(q) for q in (S/d).glob(f'*{b}*.csv')]
    # r28: a withdrawal line that names a sha256 prefix withdraws those bytes wherever they sit.
    for hx in re.findall(r'sha256[^0-9a-f\n]{0,24}([0-9a-f]{12,64})',line,re.I):
     if back or not re.search(r'(?:\bkeeps?\b|\bnot the\b|\bretain\w*)',line[:line.lower().find(hx.lower())][-48:],re.I):hashes.append(hx[:12].lower());hashes+=(['tail:'+hx[-8:].lower()] if len(hx)==64 else [])  # r29 09:55Z
    events.append((t,back,paths,hashes))
   for t,back,paths,hashes in sorted(events,key=lambda e:e[0]):
    for x in paths:
     if back:m.pop(x,None)
     else:m[x]=max(m.get(x,0),t)
    for hx in hashes:
     if back:line_hashes.discard(hx)
     else:line_hashes.add(hx)
  except OSError:pass
  # r27 23:30Z: also the sha256 prefixes of the withdrawn files (from the file if it is still there, else from the
  # lpfeed and wfeed indexes), since another lane names its pinned snapshot, not the path (our 798 missed this).
  import hashlib
  hs=set(line_hashes)
  known={}
  for ix in (S/'take-border-r27/work/lp/index.json',S/'take-border-r27/work/wq/index.json',S/'take-border-r28/work/lp/index.json',S/'take-border-r28/work/wq/index.json',S/'take-border-r29/work/lp/index.json',S/'take-border-r29/work/kq/index.json',S/'take-border-r30/work/lp/index.json',S/'take-border-r30/work/kq/index.json',S/'take-border-r34/work/kq/index.json',S/'take-border-r34/work/lp/index.json',S/'take-border-r35/work/kq/index.json',S/'take-border-r36/work/kq/index.json',S/'take-border-r36/work/kqs/index.json',S/'take-border-r36/work/kql/index.json',W/'lp/index.json',W/'kqm/index.json',W/'kqs/index.json',W/'kqf/index.json',W/'kq/index.json',W/'wq/index.json'):
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
  _wd.update(t=time.time(),m=m,h={x for x in hs if not x.startswith('tail:')},tails={x[5:] for x in hs if x.startswith('tail:')})
 return _wd['m']
def audit(p,row=None,visited=None):
 p=Path(p);visited=set() if visited is None else visited
 why=bad(str(p))
 if why:return reject(p,'forbidden source path '+why)
 tw=withdrawn().get(str(p))
 if tw is not None:
  try:mt=p.stat().st_mtime
  except OSError:mt=None
  if mt is None or mt<=tw+1:return reject(p,'withdrawn on a handoff log')
 if str(p) not in _wd['m']:
  try:
   if hashlib_sha(p)[:12] in _wd['h']:return reject(p,'withdrawn on a handoff log (same sha256)')
  except OSError:pass
 if str(p) in visited:return True
 visited.add(str(p))
 if p in (S/'gather/round36-2026-11-18b.csv',S/'gather/round35-2026-11-17a.csv',S/'gather/round34-2026-11-17a.csv',S/'gather/round33-2026-11-17a.csv',S/'gather/round32-2026-11-16a.csv',S/'gather/round31-2026-11-16b.csv',S/'gather/round30-2026-11-15c.csv',S/'gather/round29-2026-11-15b.csv',S/'gather/round23-2026-11-13b.csv',S/'gather/round25-2026-11-14b.csv',S/'gather/round26-2026-11-14b.csv',S/'gather/round27-2026-11-15b.csv',S/'gather/round28-2026-11-15b.csv'):return True
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
 # r29 09:55Z: a withdrawn take csv that is gone was never checked (only near parents were); our 376 row descended from
 # the forensics 376 take withdrawn at 08:32Z through a twoshort near named 376-forensics-376-299a6d9f (its sha256 tail).
 wm=withdrawn()
 for x in set(refs):
  if x==str(p):continue
  tw=wm.get(x)
  if tw is not None:
   try:mt=Path(x).stat().st_mtime
   except OSError:mt=None
   if mt is None or mt<=tw+1:return reject(p,'names a withdrawn ancestor '+x)
 tail=next((t for t in _wd.get('tails',()) if re.search(r'(?<![0-9a-f])'+t+r'(?![0-9a-f])',text)),None)
 if tail:return reject(p,'names a withdrawn file by its sha256 tail '+tail)
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
 # r28 (invent and k123 r27 next): every complete csv ancestor named in the record gets the share test too; a share
 # of 0.4 or more refuses the descendant (the n684 donor of share 1.0 and the 742 ancestor of share 0.454 were missed).
 # main -> all 00:19:03Z: the ancestor share test is dropped (our own layouts and their descendants are ours).
 # r29: a public-first ancestor (a harvest take or near file, or a fetched public file) whose own prvsiyan 1105 share is
 # 0.4 or more refuses the descendant (round 29 brief item 3; r28 kept the 503 near miss out on such an ancestor).
 for x in set(refs+[str(p)]):
  if re.search(r'take-harvest-r\d+/|/data/nb/|/public\d*/',x) and Path(x).exists():
   sh=ancestor_share(x,n)  # r29 07:47Z: the share at the descendant's n (a whole-file test read n=1, share 1.0)
   if sh is not None and sh>=0.4:return reject(p,f'public-first ancestor {x} has prvsiyan 1105 share {sh:.3f}')
 good=any(k in data for k in ('manifest','parts','modules')) or bool(data.get('source') or data.get('donor_source'))
 if not good:return reject(p,'metadata has no source recipe')
 return True

def audit_manifest(r):
 why=bad(json.dumps(r))
 if why:return reject(r.get('id'),why)
 p=r.get('near')
 return bool(p) and audit(Path(p),{'source':r.get('donor_source',''),'licence':r.get('donor_licence','')})


def enrich_source(source, licence, n=None):
    if 'areebbb/sis-certified-union-micro-shrink-lb-22-17479' not in source:
        return source, licence
    # The canonical accepted-row table already contains the per-n upstream chain.
    if 'per_n.csv' in source:
        return source, licence
    counts=set(re.findall(r'take-harvest-r22/(\d+)\.csv', source.replace('\\','')))
    # r30 12:20Z: a chain that names the areebbb submission.csv with no harvest-r22 donor path (the rebuild 594 of r29,
    # through the k123 594 ancestry) used the areebbb row of its own count; its per_n.csv row gives the upstream.
    if not counts and n is not None and re.search(r'areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: submission\.csv', source):
        counts={str(n)}
    # r30 15:20Z: a held row whose results-table licence cell lists the areebbb file among its upstream notebooks (the held
    # 791 of round 26) also takes the per_n.csv row of the output count; the notice says so.
    own_count=False
    if not counts and n is not None and re.search(r'held n = \d+ of round', source):
        counts={str(n)}; own_count=True
    if not counts:
        raise ValueError('areebbb ancestry lacks a per-n public donor')
    public=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
    records={r['n']:r for r in csv.DictReader(open(public))}
    for count in sorted(counts,key=int):
        r=records[count]
        upstream=r['src']
        if 'penguin069/squares-joegun-boxed-certified-union' in upstream or 'prvsiyan' in upstream or int(count) in (639,691,745,858,918):
            raise ValueError('excluded areebbb upstream '+count)
        notice='areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, '+('row of the output count n=' if own_count else 'donor n=')+count+': '+json.dumps(r,sort_keys=True)
        source+=' | '+notice
        licence+='; '+notice+'; Apache 2.0 (public notebook output)'
    return source, licence


# r31 19:25Z: counts where every harvested version of the prvsiyan 1105 row equals our own Samanyu seed (main 18:46:37Z r30
# for 228; harvest 19:22:30Z r31 for 405 588 635 741 974, proof take-harvest-r31/work/public-reference-own-pose-equality.json).
OWN_REF={228,405,588,635,741,974}
def share30(n,path):
 import subprocess,tempfile,os
 d=tempfile.mkdtemp(prefix='sh30-',dir=str(W))
 try:
  json.dump([dict(label='x',path=str(path),n=int(n))],open(d+'/items.json','w'))
  r=subprocess.run(['$SCRATCH/bounties-squares/venv/bin/python','-I','$SCRATCH/bounties-squares/take-assemble-r31/scripts/share31.py',d+'/items.json',d+'/out.json'],capture_output=True,text=True,timeout=900)
  if 'CONTROLS OK' not in r.stdout:raise ValueError('share30 controls failed: '+r.stdout[-300:]+r.stderr[-300:])
  it=json.load(open(d+'/out.json'))['items'][0]
  if 'share' not in it:return 0.0 if it.get('error')=='rows' and 'tables' not in it else (_ for _ in ()).throw(ValueError('share30 '+str(it)))
  return max(float(v) for v in it['share'].values())
 finally:
  import shutil;shutil.rmtree(d,ignore_errors=True)
def prvsiyan_share(n,path):
 """r27 rule b share test: share of squares within 1e-3 of the prvsiyan 1105 row of n (classfill prvsim26.py)."""
 import subprocess
 out=subprocess.run(['$SCRATCH/bounties-squares/venv/bin/python','-I','tools/classfill/round26/prvsim26.py',f'{n}:{path}'],capture_output=True,text=True,timeout=600).stdout
 m=re.search(r'within1e-3 ([0-9.]+)',out);m2=re.search(r'within1e-2 ([0-9.]+)',out)
 # r31 override 3: a public-first row is out at a share of 0.4 or more at 1e-3 OR at 1e-2, so the larger of the two counts.
 # n = 228: every harvested version of its 1105 row equals our own Samanyu seed (main 18:46:37Z r30), a share against it
 # is a share against our own layout.
 if n in OWN_REF and m:return 0.0
 # r31 21:10Z: the assembler's share30.py (corner and centre boxes plus median-offset ICP, max over every harvested
 # version of the 1105 dataset) reads higher than prvsim26 (851: 0.464 against 0.170); the larger value counts.
 if m and m2:return max(float(m[1]),float(m2[1]),share30(n,path))
 if m:return float(m[1])
 if 'rows' in out and ' 0 ' in out.split('rows',1)[1][:12]:return 0.0  # no prvsiyan row of this n
 raise ValueError('share test failed: '+out.strip()[:200])

def hashlib_sha(p):
 import hashlib
 return hashlib.sha256(Path(p).read_bytes()).hexdigest()

_share_cache={}
def ancestor_share(q,n0=None):
 """Share test of one ancestor csv at count n0 when the file holds it (else its first counts), cached by sha256 and n;
 None when it holds no readable layout."""
 import hashlib
 try:h=hashlib.sha256(Path(q).read_bytes()).hexdigest()
 except OSError:return None
 if n0 is not None:h=h+f':s{n0}'  # r30 14:30Z: same-n test, new cache key
 if h in _share_cache:return _share_cache[h]
 cf=W/'share-cache.json'
 try:disk=json.load(open(cf))
 except (OSError,ValueError):disk={}
 if h in disk:_share_cache[h]=disk[h];return disk[h]
 try:
  ns=sorted({int(r['n']) for r in csv.DictReader(open(q)) if str(r.get('n','')).isdigit()})
 except (OSError,ValueError,KeyError):ns=[]
 v=None
 # r30 14:30Z (main 12:40:55Z ruling, quench_walk r30): only a public-first ancestor of the descendant's own n is tested; an
 # ancestor file of other counts (a module or part source) gives no share (None). r29 tested its first counts and refused
 # the midm r30 412 take through a harvest r28 805 input at share 0.414.
 if n0 is not None and n0 not in ns:pick=[]
 else:pick=[n0] if n0 is not None else [x for x in ns if x>=50][:3]  # r29: a count under 50 matches any packing of it (n=1 reads 1.0)
 for n in pick:
  try:sh=prvsiyan_share(n,str(q))
  except Exception:continue
  v=sh if v is None else max(v,sh)
 _share_cache[h]=v;disk[h]=v
 tmp=cf.with_suffix('.tmp');tmp.write_text(json.dumps(disk));tmp.replace(cf)
 return v
