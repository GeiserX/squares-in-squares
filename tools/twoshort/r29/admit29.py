import os
"""Walk source records, reject unlicensed seeds, and retain each closure once by hash."""
from pathlib import Path
import sys,json,hashlib,csv,re
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent
sys.path.insert(0,'.');sys.path.insert(0,str(W))
import nosamanyu29
import forensics_sources as FS,forensics_policy as FP
from source29 import allowed
sys.path.insert(0,'tools')
from harvest_follow import provenance_text,nonancestral_key
from ancestry_index29 import held_same,owner,reader_credit
from functools import lru_cache
@lru_cache(maxsize=8192)
def digest_cached(name,mtime,size):return hashlib.sha256(Path(name).read_bytes()).hexdigest()
def digest(path):
 st=path.stat();return digest_cached(str(path),st.st_mtime_ns,st.st_size)
def stamp(path):
 st=path.stat();return dict(path=str(path),sha256=digest(path),mtime_ns=st.st_mtime_ns,size=st.st_size)
def unchanged(r):
 p=Path(r['path'])
 if not p.exists():return False
 st=p.stat()
 if st.st_mtime_ns==r.get('mtime_ns') and st.st_size==r.get('size'):return True
 if digest(p)!=r['sha256']:return False
 r.update(mtime_ns=st.st_mtime_ns,size=st.st_size);return True
PATHS=re.compile(r'$DATA/[^\s,;<>"\)\\]+\.(?:csv|json)')
FIELDS={'source','src','licence','modules','parts','parent','donor','inputs','source_metadata','source_record','parent_path','admission','evidence','record','original_file','A','B','C','input_ancestry_proof','ancestry','origin','source_before_enrichment','license','licences','licenses','source_ref','source_file','donor_source','donor_licence','parent_file','input_file'}
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for k,v in x.items():
   if nonancestral_key(k):continue
   if k in FIELDS or isinstance(v,(dict,list)) or k.endswith(('_source','_metadata','_record','_path')):yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
def plain_credit(path,n):
 p=Path(path);txt=p.with_suffix('.source.txt')
 if not txt.exists():return None
 text=txt.read_text();m=re.search(r'held n=(\d+) of gather/(round23-2026-11-13b|round25-2026-11-14b|round26-2026-11-14b|round27-2026-11-15b).csv',text)
 if not m or int(m[1]) in (907,):return None
 gate={'round23-2026-11-13b':'cand-round23-1113b','round25-2026-11-14b':'cand-round25-1114b','round26-2026-11-14b':'cand-round26-1114b','round27-2026-11-15b':'cand-round27-1115b'}[m[2]]
 donor=int(m[1]);base={int(r['n']):float(r['L']) for r in csv.DictReader(open(B/'gate'/gate/'details.csv'))}
 for name in re.findall(r'results/(round\d+-best-[0-9-]+\.tsv)',text):
  table=Path('results')/name
  if not table.exists():continue
  row=next((r for r in csv.DictReader(open(table),delimiter='\t') if int(r['n'])==donor),None)
  if row and abs(float(row['L'])-base[donor])<1e-7:
   return dict(source=str(p)+'; '+text+'; results/'+name+': '+row['source']+'; '+str(B/'gather'/(m[2]+'.csv')),licence='our original transformation; '+row['licence'],record=str(txt),parent_n=donor)
 return None
@lru_cache(maxsize=3)
def reader_state(path):return json.load(open(path))
# Round 26: a parent named by a bare file name (921-29e12ff3.csv) escaped the path walk in round 25.
BARE=re.compile(r'(?<![A-Za-z0-9/._-])(\d{2,4}[-_][A-Za-z0-9._-]*\.csv)\b')
BANNED_FILES=re.compile(r'(?!x)x')  # round 27: 863-0f92c19d-n was banned only because it reaches merged0 seed 983 (Samanyu-dev; invent 2026-11-14T01:27:36Z)
# Round 27: the Samanyu-dev seed is allowed. Its 'no licence' note, and the seed merged0 (each n from Couzo, MIT, or
# Samanyu-dev; take-assemble-r21/bin/seedsrc.py), no longer refuse. 'no licence' on any other source still does.
SAMANYU_NOLIC=re.compile(r'Samanyu(?:-dev)?(?:/squares_in_squares)?[^;|<>]{0,80}?(?:no licen[cs]e|unlicensed)(?:\s*\([^)]*\))?|(?:no licen[cs]e|unlicensed)[^;|<>]{0,40}?Samanyu(?:-dev)?|seed merged0',re.I)  # round 27: 921-29e12ff3 back in (Samanyu rule lifted)
BARE_INDEX=W/'bare-index.txt'
def bare_index(force=False):
 import subprocess,time,os
 # Round 27: a full find of the scratch tree took over 300 s at load; the index is refreshed by bareindex29.sh in the background.
 if not BARE_INDEX.exists():
  tmp=BARE_INDEX.with_name('bare-index.'+str(os.getpid())+'.tmp')
  with open(tmp,'w') as out:subprocess.run(['find',str(B),'-maxdepth','5','-path','*/take-*','-name','[0-9]*.csv','-type','f'],stdout=out,stderr=subprocess.DEVNULL,timeout=300)
  tmp.replace(BARE_INDEX)
_BARE_MAP={}
def _bare_map(force=False):
 """Round 26: one in-memory map of the bare-name index per process, instead of one grep of 57 MB per name."""
 import time
 bare_index(force)
 st=BARE_INDEX.stat();key=(st.st_mtime_ns,st.st_size)
 if _BARE_MAP.get('key')!=key:
  m={}
  with open(BARE_INDEX) as f:
   for line in f:
    line=line.rstrip('\n');m.setdefault(line.rsplit('/',1)[-1],[]).append(line)
  _BARE_MAP.clear();_BARE_MAP.update(key=key,map=m)
 return _BARE_MAP['map']
@lru_cache(maxsize=4096)
def bare_hits(name,_retry=True):
 import time
 out=[Path(x) for x in _bare_map().get(name,[])]
 if not out and _retry and time.time()-BARE_INDEX.stat().st_mtime>1800:
  _bare_map(True);return bare_hits.__wrapped__(name,False)
 return tuple(sorted(set(out)))
def invent_credit(p):
 """Round 26: an invent start file keeps its record in its lane's work/jobs.json (by id and input hash) and a content-addressed ancestry file."""
 p=Path(p)
 if p.suffix!='.csv' or p.parent.name!='starts' or not p.is_file():return None
 root=next((q for q in p.parents if re.fullmatch(r'take-invent-r\d+',q.name)),None)
 if root is None or p.parent!=root/'work/starts':return None
 jobs=root/'work/jobs.json'
 if not jobs.is_file():return None
 try:entries=json.load(open(jobs))
 except ValueError:return None
 entry=next((e for e in entries if isinstance(e,dict) and e.get('id')==p.stem),None) if isinstance(entries,list) else None
 if not entry or entry.get('refused') or entry.get('input_sha256')!=digest(p):return None
 ap=Path(entry.get('ancestry',''))
 if not ap.is_file():return None
 try:ad=json.load(open(ap))
 except ValueError:return None
 if ad.get('ok') is not True or ad.get('path')!=str(p) or not isinstance(ad.get('nodes'),dict):return None
 return ap,ad
def own_kick_credit(p):
 # Round 28: our own kicks of rounds 26 and 27 are credited from their local mirrors as well.
 for _R in (Path(__file__).resolve().parent/'boxE29',B/'take-twoshort-r28/work/boxE28',B/'take-twoshort-r27/work/boxE27',B/'take-twoshort-r26/work/boxE26-final'):
  _r=_own_kick_credit(p,_R)
  if _r:return _r
 return None
def _own_kick_credit(p,R):
 """Round 26: a raw or quenched file of our own boxE kick, in the local mirror work/boxE29, is credited by the
 job record that made it (same tag, seed and n) when that job's input proof is admitted and its snapshot is unchanged."""
 p=Path(p)
 m=re.fullmatch(re.escape(str(R))+r'/(runs|q)/(.+)-s(\d+)/(?:raw/)?(\d+)-(?:sl\d+-\d+|best)\.csv',str(p))
 if not m or not p.is_file():return None
 tag,seed,count=m[2],m[3],int(m[4])
 for jp in sorted((R/'jobs').glob('*-'+tag+'-'+seed+'.json')):
  try:j=json.load(open(jp))
  except ValueError:continue
  if j.get('tag')!=tag or str(j.get('seed'))!=seed or int(j.get('n',0))!=count or not j.get('source') or not j.get('licence'):continue
  pp=j.get('input_ancestry_proof')
  if not pp or not Path(pp).is_file():continue
  try:proof=json.load(open(pp))
  except ValueError:continue
  snap=Path(proof.get('snapshot',''))
  if proof.get('admitted') is True and snap.is_file() and digest(snap)==proof.get('sha256'):return jp,j
 return None
def public_notebook_credit(p):
 """Round 26: a public notebook output downloaded by the harvest lane is credited by a harvest take.tsv row that names the same notebook and member."""
 p=Path(p);m=re.search(r'/take-harvest-r\d+/work/public\d*/data/nb/([A-Za-z0-9_-]+?)__([A-Za-z0-9_.-]+)/([^/]+\.csv)$',str(p))
 if not m or not p.is_file():return None
 owner,slug,member=m[1],m[2],m[3].replace('__','/');ref=owner+'/'+slug+' :: '+member
 for sp in sorted(B.glob('take-harvest-r2[2-9]/work/starts/*.csv.json'),reverse=True):
  try:r=json.load(open(sp))
  except ValueError:continue
  if not isinstance(r,dict) or r.get('src')!=str(p):continue
  src=r.get('source','');lic=r.get('licence','')
  if not src.startswith(ref) or not lic or lic.startswith(('see ','unresolved')) or not allowed(src,lic) or FP.classify_text(src+' '+lic)['status']!='none':continue
  return dict(source='public notebook output '+ref+', credited by harvest start record '+str(sp),licence=lic),sp
 for tp in sorted(B.glob('take-harvest-r2[2-9]/take.tsv'),reverse=True):
  for r in csv.DictReader(open(tp),delimiter='\t'):
   src=r.get('source','');lic=r.get('licence','')
   if ('from '+ref) not in src and (ref+' ') not in src:continue
   if not lic or lic.startswith(('see ','unresolved')) or not allowed(src,lic):continue
   if FP.classify_text(src+' '+lic)['status']!='none':continue
   return dict(source='public notebook output '+ref+', credited by '+str(tp)+' row n='+r['n'],licence=lic),tp
 return None
def walk(record,start=None,n=None):
 seen=set();records=[];errors=[];roots=[];metadata_records=[];contexts=[];registry_selected={};verified_a=set()
 aliases={}
 for name in PATHS.findall(json.dumps(record)):
  ip=Path(name)
  if ip.parent not in (W/'intake',B/'take-twoshort-r25/work/intake',B/'take-twoshort-r26/work/intake',B/'take-twoshort-r27/work/intake',B/'take-twoshort-r28/work/intake') or ip.stem.endswith('-ancestry') or not ip.exists():continue
  ap=ip.with_name(ip.stem+'-ancestry.json')
  if not ap.exists():continue
  im=json.load(open(ip));am=json.load(open(ap));snapshot=Path(am.get('snapshot',''))
  if am.get('admitted') and snapshot.is_file() and digest(snapshot)==im.get('sha256')==am.get('sha256') and am.get('ancestry',{}).get('admitted') and isinstance(am['ancestry'].get('record'),dict):
   aliases[im.get('origin','')]=(ip,ap,snapshot,am['ancestry']['record'])

 def old_held_allowed(count):
  if count is None or int(count) in {639,691,745,858,907,918}:return False
  if not held_same(int(count)):return False
  verified_a.add(int(count));return True
 def inspect(d,p):
  hint=d.get('n') if isinstance(d,dict) else None
  lead=re.match(r'\d+',Path(str(p)).stem)
  try:hint=int(hint) if hint is not None else int(lead[0]) if lead else contexts[-1][0] if contexts else n
  except (ValueError,TypeError):hint=contexts[-1][0] if contexts else n
  contexts.append((hint,owner(p)))
  def bindings(x,field=None):
   if field=='metadata_records':
    for entry in x if isinstance(x,list) else []:
     if not metadata_unchanged(entry):errors.append([entry.get('path',str(p)),'pinned ancestor metadata differs'])
    return
   if isinstance(x,dict):
    path=x.get('path','');count=x.get('n')
    if isinstance(path,str):
     if path.endswith('/gather/round23-2026-11-13a.csv') and not old_held_allowed(count):errors.append([path,'untrusted older aggregate root'])
     original=x.get('original_file','');src=x.get('source')
     if isinstance(original,str) and original.endswith('/gather/round23-2026-11-13a.csv') and isinstance(src,(list,tuple)) and len(src)==2 and not old_held_allowed(int(src[1])):errors.append([original,'untrusted older aggregate part'])
     if path.endswith('/gather/round23-2026-11-13b.csv') and count in (907,):errors.append([path,'excluded held donor root'])
     if path.endswith('/gather/round25-2026-11-14b.csv') and count in (907,):errors.append([path,'excluded held donor root'])
     if path.endswith('/gather/round25-2026-11-14a.csv'):errors.append([path,'withdrawn round25 a aggregate'])
     if re.search(r'take-(?:harvest|polish)-r22/(?:work/public/starts/)?(?:639|691|745|858|918)(?:/|\.csv)',path):errors.append([path,'excluded old public root'])
     if re.search(r'take-forensics-r(?:19|20|21|22|23)/(?:near/)?918(?:[-/.]|$)',path):errors.append([path,'excluded old forensics root'])
     if re.search(r'take-(?:invent|midm)-r23/(?:near/)?639(?:[-/.]|$)|take-forensics-r23/(?:near/)?(?:980|981)(?:[-/.]|$)',path):errors.append([path,'excluded round23 descendant'])
    for pathkey,hashkey in [('path','sha256'),('snapshot','sha256'),('parent_path','parent_sha256')]:
     name=x.get(pathkey);want=x.get(hashkey)
     if isinstance(name,str) and name.startswith('$DATA/') and isinstance(want,str) and len(want)==64:
      q=Path(name)
      if not q.exists() or digest(q)!=want:errors.append([name,'pinned ancestor hash differs'])
    for k,v in x.items():
     if nonancestral_key(k) and k!='seed_policy':continue
     bindings(v,k)
   elif isinstance(x,list):
    for v in x:bindings(v)
  bindings(d)
  ss=list(strings(d));text=provenance_text(d)+' '+' '.join(ss)
  text=PATHS.sub('',text)
  if re.search(r'penguin069/squares-joegun-boxed|squares-verified-best-of-1105|CC BY-SA|seed merged0|no licen[cs]e|unlicensed',SAMANYU_NOLIC.sub(' ',text),re.I):errors.append([str(p),'excluded or unresolved root'])
  if re.search(r'take-harvest-r22(?:/| n=)(?:639|691|745|858|918)\b|take-forensics-r(?:22|23)(?:/| n=)918\b',text):errors.append([str(p),'excluded old version'])
  if re.search(r'(?:staircase corner|taper enumeration).*?our own design|own construction|our own design|CC0|Apache|CC BY 4.0|MIT',text):roots.append(str(p))
  for s in ss:
   for name,want in re.findall(r'($DATA/[^\s,;<>"\)\\]+\.csv) (?:immutable )?sha256 ([0-9a-f]{64})',s):
    q=Path(name)
    if not q.exists() or digest(q)!=want:errors.append([name,'recorded ancestor hash differs'])
   for match in PATHS.findall(s):visit(Path(match))
   rel=re.sub(r'(take-[a-z-]+-r\d+) (near/)',r'\1/\2',s)
   for name in re.findall(r'(?<![A-Za-z0-9/])(take-[a-z-]+-r\d+/[^\s,;<>"\)\\]+\.(?:csv|json))',rel):visit(B/name)
   for lane,count in re.findall(r'\b(take-[a-z-]+-r\d+) n\s*=\s*(\d+)\b',s):visit(B/lane/(count+'.csv'))
   for name in re.findall(r'(?<![A-Za-z0-9/])gather/(round2[3-7]-2026-11-1[3-5][ab])\.csv',s):visit(B/'gather'/(name+'.csv'))
   bare_text=re.sub(r'(?<![A-Za-z0-9/])take-[a-z-]+-r\d+/[^\s,;<>"\)\\]+','',PATHS.sub('',rel))
   for name in BARE.findall(bare_text):
    hits=bare_hits(name)
    if not hits:errors.append([name,'unresolved bare ancestor name']);continue
    for q in hits:visit(q)
  contexts.pop()
 def visit(p):
  if BANNED_FILES.search(str(p)):errors.append([str(p),'named unlicensed seed file']);return
  context,context_owner=contexts[-1] if contexts else (n,None)
  seenkey=str(p)+(':'+str(context) if p.suffix=='.json' else '')
  if seenkey in seen:return
  seen.add(seenkey)
  if not p.exists():
   alias=aliases.get(str(p))
   if alias:
    ip,ap,snapshot,retained=alias;records.extend([stamp(ip),stamp(ap),stamp(snapshot)]);inspect(retained,snapshot);return
   errors.append([str(p),'missing recorded ancestor']);return
  if p.suffix=='.json':
   try:d=json.load(open(p))
   except ValueError:errors.append([str(p),'invalid source record']);return
   if isinstance(d,dict) and d and all(str(k).isdigit() for k in d):
    key=str(context)
    if key not in d:
     if registry_selected.get(str(p)) and owner(p)!=context_owner:return
     errors.append([str(p),'source registry count unresolved']);return
    registry_selected.setdefault(str(p),set()).add(key);entry=d[key];metadata_records.append(dict(kind='json',path=str(p),n=int(key),sha256=hashlib.sha256(json.dumps(entry,sort_keys=True).encode()).hexdigest()));inspect(entry,p);return
   if p.name=='follow.json' and 'take-readers-' in str(p):
    if any(r.get('kind')=='reader' and r['path']==str(p) for r in metadata_records):return
    errors.append([str(p),'reader registry version unresolved']);return
   records.append(stamp(p));inspect(d,p)
  elif p.suffix=='.csv':
   if str(p) in ('$SCRATCH/bounties-squares/seeds/merged0.csv','$SCRATCH/bounties-squares/seeds/samanyu_bestfit.csv','$SCRATCH/bounties-squares/seeds/samanyu_22249.csv','$SCRATCH/bounties-squares/seeds/couzo.csv'):roots.append(str(p)+' original seed file (Couzo MIT, or the Samanyu-dev seed that round 29 rules 2 and 3 make ours)');return
   if p.parent.name=='gather':
    if p.name=='round23-2026-11-13b.csv':roots.append(str(p));return
    if p.name in ('round25-2026-11-14b.csv','round26-2026-11-14b.csv','round27-2026-11-15b.csv'):
     if context in (907,):errors.append([str(p),'excluded held donor root']);return
     roots.append(str(p));return
    if p.name=='round23-2026-11-13a.csv' and (old_held_allowed(context) or verified_a):roots.append(str(p)+' verified unchanged licensed per-n version');return
    # Round 28: an older held aggregate is a root for any count outside the excluded ones; the walk the assembler runs
    # (quench_walk via qwalk29) applies the prvsiyan share test and the withdrawals. Forensics r28 rectangles reach round20 a.
    if re.fullmatch(r'round\d+-2026-11-\d+[a-c]?\.csv',p.name) and p.name!='round25-2026-11-14a.csv' and (context is None or int(context) not in {639,691,745,858,907,918,980}):roots.append(str(p)+' older held aggregate, round 28 rule');return
    errors.append([str(p),'older aggregate needs per-n clean ancestry']);return
   if p.parent.name in {'take-forensics-r22','take-forensics-r23'} and p.stem=='918':errors.append([str(p),'excluded old forensics918']);return
   if p.parent.name=='take-harvest-r22' and p.stem in {'639','691','745','858','918'}:errors.append([str(p),'excluded public layout']);return
   match=re.search(r'from(\d+-r(\d+)h([0-9a-f]+))',p.name) or re.match(r'(\d+-r(\d+)h([0-9a-f]+))',p.stem)
   if match and 'take-readers-' in str(p) and int(match[2])<=25:
    statepath=B/('take-readers-r'+match[2]+'/work/follow.json');donor=match[1];snapshot=statepath.parent/'box/donors'/(donor+'.csv')
    if statepath.exists() and snapshot.exists() and digest(snapshot).startswith(match[3]):
     credit=reader_credit(statepath,donor,digest(snapshot))
     if credit:
      records.extend([stamp(p),stamp(snapshot)]);metadata_records.append(dict(kind='reader',path=str(statepath),donor=donor,snapshot=str(snapshot),sha256=hashlib.sha256(json.dumps(credit,sort_keys=True).encode()).hexdigest()));inspect(dict(source=credit[0],licence=credit[1]),snapshot);return
   own=own_kick_credit(p)
   if own:
    jp,j=own;records.extend([stamp(p),stamp(jp)]);inspect(dict(n=int(j['n']),source=j['source'],licence=j['licence']),jp);return
   pub=public_notebook_credit(p)
   if pub:
    d0,tp=pub;records.extend([stamp(p)]);inspect(d0,p);return
   credit=invent_credit(p)
   if credit:
    ap,ad=credit;records.extend([stamp(p),stamp(ap)]);inspect(dict(n=ad.get('n'),nodes=ad['nodes'],policy=ad.get('policy')),ap);return
   alias=re.match(r'(\d+)-(x[0-9a-f]+)',p.stem)
   if alias and 'take-classfill-' in str(p):
    root=next(q for q in p.parents if q.name.startswith('take-classfill-'));proofpath=root/'work'/(alias[2]+'-source-proof.json')
    if proofpath.exists():
     md=json.load(open(proofpath))
     if md.get('input_sha256')==digest(p):
      import io
      row=next((r for r in csv.DictReader(io.StringIO(md.get('producer_take_tsv','')),delimiter='\t') if r.get('n')==alias[1]),None)
      if row:
       records.extend([stamp(p),stamp(proofpath)]);inspect(dict(n=int(alias[1]),source=md['source'],licence=md['licence'],producer_row=row,input_root=dict(path=md.get('path',''),n=int(alias[1]))),p);return
   count=int(re.match(r'\d+',p.stem)[0]) if re.match(r'\d+',p.stem) else n or 0
   rec,ledger=FS.record(p,count)
   if rec is not None:metadata_records.append(dict(path=str(p),n=count,sha256=hashlib.sha256(json.dumps(rec,sort_keys=True).encode()).hexdigest()))
   records.append(stamp(p))
   if rec is None:
    rec=plain_credit(p,n)
   if rec is None:
    credits=p.parent/('sources-'+p.stem+'.json')
    if credits.exists():
     cr=json.load(open(credits));groups={}
     for row in csv.DictReader(open(p)):groups.setdefault(row['n'],[]).append(tuple(float(row[k]) for k in ['x','y','angle']))
     verified=True
     for count,rows in groups.items():
      origin=Path(cr.get(count,{}).get('origin',''))
      if not origin.is_file():verified=False;break
      expected=[tuple(float(row[k]) for k in ['x','y','angle']) for row in csv.DictReader(open(origin)) if row['n']==count]
      if sorted(rows)!=sorted(expected):verified=False;break
      records.append(stamp(origin))
     if verified:
      records.append(stamp(credits));rec={count:cr[count] for count in groups}
   if rec is None:
    root=next((q for q in p.parents if re.fullmatch(r'take-.+-r\d+',q.name)),None)
    if root:
     raw=list((root/'work').glob('raw*/'+p.stem+'.json'))
     if len(raw)==1:
      records.append(stamp(raw[0]));rec=json.load(open(raw[0]))
   if rec is not None:inspect(rec,p)
   else:
    origins=[Path(str(p)+'.origin.json'),Path(str(p)+'.source-0.json')]
    found=False
    for q in origins:
     if q.exists():visit(q);found=True
    if not found:errors.append([str(p),'missing source record'])
 inspect(record,start or 'record')
 return not errors and bool(roots),dict(records=records,metadata_records=metadata_records,errors=errors,roots=sorted(set(roots)))
def save_proof(dest,d):
 import os
 temp=dest.with_name(dest.name+'.'+str(os.getpid())+'.tmp');temp.write_text(json.dumps(d,indent=2));temp.replace(dest)
def metadata_unchanged(entry):
 try:
  if entry.get('kind')=='json':rec=json.load(open(entry['path'])).get(str(entry['n']))
  elif entry.get('kind')=='reader':rec=reader_credit(Path(entry['path']),entry['donor'],digest(Path(entry['snapshot'])))
  else:rec,_=FS.record(Path(entry['path']),entry['n'])
 except (ValueError,OSError):return False
 return rec is not None and hashlib.sha256(json.dumps(rec,sort_keys=True).encode()).hexdigest()==entry['sha256']
def store(record,start=None,n=None):
 if not allowed(record.get('source',''),record.get('licence','')):return False,dict(admitted=False,record=record,closure=dict(records=[],metadata_records=[],errors=[['record','unresolved or excluded source notice']],roots=[]))
 key=hashlib.sha256(('v29b:'+json.dumps([record,n],sort_keys=True)).encode()).hexdigest();dest=W/'proofs'/(key+'.json');d=None
 if dest.exists():
  try:d=json.load(open(dest))
  except ValueError:pass
 if d is not None:
  before=json.dumps(d,sort_keys=True)
  retry=not all(metadata_unchanged(r) for r in d['closure'].get('metadata_records',[]))
  for name,reason in d['closure']['errors']:
   p=Path(name)
   if reason=='missing recorded ancestor' and p.exists():retry=True
   if reason=='missing source record' and p.exists():
    count=int(re.match(r'\d+',p.stem)[0]) if re.match(r'\d+',p.stem) else n or 0
    try:rec,_=FS.record(p,count)
    except (ValueError,OSError):rec=None
    retry=retry or rec is not None or ('take-readers-r23/work/box/donors/' in str(p)) or invent_credit(p) is not None or public_notebook_credit(p) is not None or own_kick_credit(p) is not None
  if not retry:
   if all(unchanged(r) for r in d['closure']['records']):
    if json.dumps(d,sort_keys=True)!=before:save_proof(dest,d)
    return d['admitted'],d
   return False,dict(d,admitted=False,changed_ancestor=True)
 ok,closure=walk(record,start,n);d=dict(admitted=ok,record_sha256=key,record=record,closure=closure);save_proof(dest,d);return ok,d
def trace_input(path,n):
 rec,_=FS.record(path,n)
 if rec is None:rec=plain_credit(path,n)
 if rec is None:return False,dict(reason='missing source record')
 if isinstance(rec,dict) and not rec.get('source') and isinstance(rec.get('parts'),dict):
  # Round 26: a rectangle composition record names its parts but has no top-level source cell.
  lics=sorted({v.get('licence') for v in rec['parts'].values() if isinstance(v,dict) and isinstance(v.get('licence'),str)})
  rec=dict(rec,source='rectangle composition of recorded parts '+json.dumps(rec['parts'],sort_keys=True),licence='; '.join(lics) or 'unresolved: parts without licence')
 if isinstance(rec,dict) and not rec.get('source') and isinstance(rec.get('modules'),list) and rec['modules']:
  # Round 26: a modules build record lists its modules, each with its own source and licence, and has no top-level source cell.
  mods=rec['modules']
  if not all(isinstance(m,dict) and isinstance(m.get('source'),str) and isinstance(m.get('licence'),str) and m['source'] and m['licence'] for m in mods):
   return False,dict(reason='module without source or licence')
  rec=dict(rec,source='module composition of recorded modules '+json.dumps([dict(id=m.get('id'),source=m['source']) for m in mods],sort_keys=True),licence='; '.join(sorted({m['licence'] for m in mods})))
 return store(rec,str(path),n)
def module_allowed(m):
 if not allowed(m.get('src',m.get('source','')),m.get('licence','')):return False
 return store(dict(source=m.get('src',m.get('source','')),licence=m.get('licence','')),n=m.get('n'))[0]
def store_lenient(record,n=None):
 """Round 26: a cached proof is revoked when any stamped live file changes, and our own intake proofs pin
 live ledgers (take.tsv, near sidecars) that other lanes rewrite every few minutes. Re-walk fresh; accept
 when the only errors left are stale pins. Every caller also runs quench_walk.py on the file before it counts."""
 ok,d=store(record,n=n)
 if ok:return True,d
 if not allowed(record.get('source',''),record.get('licence','')):return False,d
 ok2,closure=walk(record,None,n);errs=closure['errors']
 if ok2:return True,dict(admitted=True,record=record,closure=closure,fresh=True)
 if errs and closure['roots'] and all(e[1] in ('pinned ancestor hash differs','pinned ancestor metadata differs') for e in errs):return True,dict(admitted=True,record=record,closure=closure,lenient='stale pins only')
 if frozen_missing_only(closure):return True,dict(admitted=True,record=record,closure=closure,lenient='round 27: only files moved out of frozen r20-r28 take dirs are missing; quench_walk (qwalk29) must also pass')
 return False,dict(d,admitted=False,fresh_closure=closure)
FROZEN=re.compile(r'/take-[a-z0-9-]+-r(?:[1-9]|1[0-9]|2[0-8])/')
def frozen_missing_only(closure):
 """Round 27: lanes moved withdrawn files out of their round 26 dirs, and those dirs are frozen now. When the only errors
 are records that are gone from frozen take dirs (no hash mismatch, no excluded root), the walk is left to quench_walk,
 the walk the assembler runs, which every caller runs next."""
 errs=closure.get('errors',[])
 # Round 28: a hash that differs on a file in a frozen dir is also left to quench_walk, which refuses a start whose
 # sha-pinned parent was rewritten after its producer traced it (stair-c r28 near files reach corners-r25 985 and invent-r25 860).
 return bool(errs) and bool(closure.get('roots')) and all((e[1] in ('missing recorded ancestor','missing source record','pinned ancestor metadata differs','recorded ancestor hash differs','pinned ancestor hash differs') and FROZEN.search(str(e[0]))) or live_snapshot_unrecorded(e) for e in errs)
# Round 27: live lanes pin their own starts as snapshots (work/.../starts|pins|cert/<n>-<hash>.csv) and record the source
# in their ledger, not in a sidecar. Such a snapshot that exists counts like a frozen gone record: quench_walk decides.
LIVE_SNAP=re.compile(r'/take-[a-z0-9-]+-r2[89]/work/(?:[^/]+/)*(?:starts|pins|cert|donors|input-snapshots)/[^/]+\.csv$|/take-[a-z0-9-]+-r29/work/.+\.csv$')
OWN_TAKE=re.compile(r'^($SCRATCH/bounties-squares/take-twoshort-r29)/(\d+)\.csv$')
def live_snapshot_unrecorded(e):
 p=str(e[0])
 if e[1]=='missing source record' and bool(LIVE_SNAP.search(p)) and os.path.isfile(p):return True
 # Our prune moves a superseded take csv to near/<n>-superseded.csv with its record; another lane's row may name the old path.
 m=OWN_TAKE.match(p)
 if e[1]=='missing recorded ancestor' and bool(m) and os.path.isfile(m.group(1)+'/near/'+m.group(2)+'-superseded.json'):return True
 # A live lane removes its top-level take csv when a lower row supersedes it; quench_walk reads withdrawals from the handoff log.
 return e[1] in ('missing recorded ancestor','pinned ancestor hash differs','pinned ancestor metadata differs','recorded ancestor hash differs') and bool(LIVE_TAKE.match(p) or LIVE_NEAR.match(p))
LIVE_NEAR=re.compile(r'^$SCRATCH/bounties-squares/take-[a-z0-9-]+-r29/near/[^/]+$')
LIVE_TAKE=re.compile(r'^$SCRATCH/bounties-squares/take-[a-z0-9-]+-r29/\d+\.csv$')
def trace_input_lenient(path,n):
 ok,d=trace_input(path,n)
 if ok:return ok,d
 cl=d.get('closure') if isinstance(d,dict) else None
 if isinstance(cl,dict) and frozen_missing_only(cl):return True,dict(d,admitted=True,lenient='round 27 frozen-missing only')
 return ok,d
