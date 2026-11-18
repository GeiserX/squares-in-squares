"""Walk source records, reject unlicensed seeds, and retain each closure once by hash."""
from pathlib import Path
import sys,json,hashlib,csv,re
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent
sys.path.insert(0,'.');sys.path.insert(0,str(W))
import forensics_sources as FS,forensics_policy as FP
from source25 import allowed
sys.path.insert(0,'tools')
from harvest_follow import provenance_text,nonancestral_key
from ancestry_index25 import held_same,owner,reader_credit
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
 text=txt.read_text();m=re.search(r'held n=(\d+) of gather/round23-2026-11-13b.csv',text)
 if not m or int(m[1]) in (801,907):return None
 donor=int(m[1]);base={int(r['n']):float(r['L']) for r in csv.DictReader(open(B/'gate/cand-round23-1113b/details.csv'))}
 for name in re.findall(r'results/(round\d+-best-[0-9-]+\.tsv)',text):
  table=Path('results')/name
  if not table.exists():continue
  row=next((r for r in csv.DictReader(open(table),delimiter='\t') if int(r['n'])==donor),None)
  if row and abs(float(row['L'])-base[donor])<1e-7:
   return dict(source=str(p)+'; '+text+'; results/'+name+': '+row['source']+'; '+str(B/'gather/round23-2026-11-13b.csv'),licence='our original transformation; '+row['licence'],record=str(txt),parent_n=donor)
 return None
@lru_cache(maxsize=3)
def reader_state(path):return json.load(open(path))
def walk(record,start=None,n=None):
 seen=set();records=[];errors=[];roots=[];metadata_records=[];contexts=[];registry_selected={};verified_a=set()
 aliases={}
 for name in PATHS.findall(json.dumps(record)):
  ip=Path(name)
  if ip.parent!=W/'intake' or ip.stem.endswith('-ancestry') or not ip.exists():continue
  ap=ip.with_name(ip.stem+'-ancestry.json')
  if not ap.exists():continue
  im=json.load(open(ip));am=json.load(open(ap));snapshot=Path(am.get('snapshot',''))
  if am.get('admitted') and snapshot.is_file() and digest(snapshot)==im.get('sha256')==am.get('sha256') and am.get('ancestry',{}).get('admitted') and isinstance(am['ancestry'].get('record'),dict):
   aliases[im.get('origin','')]=(ip,ap,snapshot,am['ancestry']['record'])

 def old_held_allowed(count):
  if count is None or int(count) in FP.RELAXED|{639,691,745,801,858,907,918,981}:return False
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
     if re.search(r'take-[a-z-]+-r23/\d+\.csv$',path) and count in FP.RELAXED:errors.append([path,'withdrawn round23 seed root'])
     if path.endswith('/gather/round23-2026-11-13a.csv') and not old_held_allowed(count):errors.append([path,'untrusted older aggregate root'])
     original=x.get('original_file','');src=x.get('source')
     if isinstance(original,str) and original.endswith('/gather/round23-2026-11-13a.csv') and isinstance(src,(list,tuple)) and len(src)==2 and not old_held_allowed(int(src[1])):errors.append([original,'untrusted older aggregate part'])
     if path.endswith('/gather/round23-2026-11-13b.csv') and count in (801,907):errors.append([path,'excluded held donor root'])
     if re.search(r'take-(?:harvest|polish)-r22/(?:work/public/starts/)?(?:639|691|745|858|918)(?:/|\.csv)',path):errors.append([path,'excluded old public root'])
     if re.search(r'take-forensics-r(?:19|20|21|22|23)/(?:near/)?918(?:[-/.]|$)',path):errors.append([path,'excluded old forensics root'])
     if re.search(r'take-(?:invent|midm)-r23/(?:near/)?639(?:[-/.]|$)|take-forensics-r23/(?:near/)?(?:980|981)(?:[-/.]|$)',path):errors.append([path,'excluded round23 descendant'])
     if re.search(r'take-border-r2[34]/(?:.*/)?(?:735|790|228)\b|take-k123-r24/.*(?:735r-790|790-968|/968[-.]|/489[-.])',path):errors.append([path,'withdrawn unlicensed parent tree'])
    for pathkey,hashkey in [('path','sha256'),('snapshot','sha256'),('parent_path','parent_sha256')]:
     name=x.get(pathkey);want=x.get(hashkey)
     if isinstance(name,str) and name.startswith('$DATA/') and isinstance(want,str) and len(want)==64:
      q=Path(name)
      if not q.exists() or digest(q)!=want:errors.append([name,'pinned ancestor hash differs'])
    for k,v in x.items():
     if nonancestral_key(k) and k!='seed_policy':continue
     if k=='seed_policy' and isinstance(v,dict) and v.get('status') not in (None,'none'):errors.append([str(p),'recorded seeded ancestry policy'])
     bindings(v,k)
   elif isinstance(x,list):
    for v in x:bindings(v)
  bindings(d)
  ss=list(strings(d));text=provenance_text(d)+' '+' '.join(ss)
  text=PATHS.sub('',text)
  if FP.classify_text(text)['status']!='none':errors.append([str(p),'unlicensed or unresolved Samanyu ancestry'])
  if re.search(r'penguin069/squares-joegun-boxed|squares-verified-best-of-1105|CC BY-SA|seed merged0|no licen[cs]e|unlicensed',text,re.I):errors.append([str(p),'excluded or unresolved root'])
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
  contexts.pop()
 def visit(p):
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
   if p.parent.name=='gather':
    if p.name=='round23-2026-11-13b.csv':roots.append(str(p));return
    if p.name=='round23-2026-11-13a.csv' and (old_held_allowed(context) or verified_a):roots.append(str(p)+' verified unchanged licensed per-n version');return
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
 key=hashlib.sha256(('v25q:'+json.dumps([record,n],sort_keys=True)).encode()).hexdigest();dest=W/'proofs'/(key+'.json');d=None
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
    retry=retry or rec is not None or ('take-readers-r23/work/box/donors/' in str(p))
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
 return store(rec,str(path),n)
def module_allowed(m):
 if not allowed(m.get('src',m.get('source','')),m.get('licence','')):return False
 return store(dict(source=m.get('src',m.get('source','')),licence=m.get('licence','')),n=m.get('n'))[0]
