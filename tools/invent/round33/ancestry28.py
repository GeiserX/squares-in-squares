"""Hash each recorded parent once and refuse excluded or unresolved roots."""
import csv,hashlib,importlib.util,json,pathlib,re,sys
from functools import lru_cache
csv.field_size_limit(32*1024*1024)
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r33/work';R=pathlib.Path('.')
sys.path.insert(0,str(R));sys.path.insert(0,str(R/'tools'))
from harvest_seeds import SeedPolicy, classify,seed_origins,source_table
from harvest_follow import source_text,refused_source,provenance_text
import forensics_sources
spec=importlib.util.spec_from_file_location('soft_provenance',R/'tools/softround/provenance.py');soft=importlib.util.module_from_spec(spec);spec.loader.exec_module(soft)
POL=SeedPolicy(S,W.parent,source_text,lambda p:[],lambda *a:None)
ORIG=seed_origins(S)
_original_held_record=POL.held_record
def owned_held_record(count,round_):
 row,ledger=_original_held_record(count,round_)
 if int(round_)>=10 and ledger==str(R/'results/harvest-best-2026-11-09.tsv'):
  angle=R/'results/angle-harvest-2026-11-10.tsv';candidate=source_table(str(angle),angle.stat().st_mtime_ns).get(int(count))if angle.is_file()else None
  if candidate and float(candidate['new'])<float(row.get('score',99)):row,ledger=candidate,str(angle)
 if row is None:
  from historical756 import resolve
  recovered=resolve(count,round_)
  if recovered:row,ledger=recovered
 if int(count)==801 and row is not None:
  row=dict(row or {},source='own construction: canonical 801 packing, authorized by main00:19Z source policy; earlier record '+str(ledger),licence='our own construction (canonical held801, main00:19Z source policy)')
 return row,ledger
POL.held_record=owned_held_record

(W/'ancestry').mkdir(exist_ok=True)
_cache={}
def rows(p):
 try:return list(csv.DictReader(open(p),delimiter='\t'))
 except (OSError,ValueError,csv.Error):return []
_meta_cache={}
_DIAGNOSTICS={'prvsiyan_shares','prvsiyan_share','prvsiyan_share_check','ancestor_share_check','share_checks','complete_parent_share_audit'}
_origin_proof_cache={};_origin_active=set();_alias_active=set()
def ancestry_only(value):
 if isinstance(value,dict):return {k:ancestry_only(v)for k,v in value.items()if k not in _DIAGNOSTICS}
 if isinstance(value,list):return [ancestry_only(v)for v in value]
 return value

def pinned_origin_metadata(path,n):
 path=pathlib.Path(path);origin=pathlib.Path(str(path)+'.origin.json')
 if not origin.is_file()or not path.is_file():return None
 try:value=json.load(open(origin))
 except (OSError,ValueError):return None
 if not value.get('verified_ancestry'):return None
 def refuse(reason):return 'unresolved ancestry: '+reason,'unresolved source',str(origin)
 if value.get('n',n)!=n or hashlib.sha256(path.read_bytes()).hexdigest()!=value.get('snapshot_sha256'):return refuse('verified-origin input hash or count mismatch')
 full=value.get('full_ancestry')
 if isinstance(full,dict)and full.get('path')and full.get('sha256'):
  proof=pathlib.Path(full['path'])
  if not proof.is_file()or not proof.resolve().is_relative_to(S):return refuse('missing verified-origin full proof')
  st=proof.stat();key=(str(proof),st.st_mtime_ns,st.st_size,full['sha256'])
  if key not in _origin_proof_cache:_origin_proof_cache[key]=hashlib.sha256(proof.read_bytes()).hexdigest()==full['sha256']
  if not _origin_proof_cache[key]:return refuse('changed verified-origin full proof')
 compact=forensics_sources.compact_ancestry(ancestry_only(value['ancestry']),origin);roots=[]
 for root in compact.get('roots',[]):
  root=dict(root)
  from held32 import resolve as held_root
  accepted_root=held_root(root)
  if accepted_root:root=accepted_root
  if not root.get('source')and '/gather/'in root.get('path',''):
   match=re.search(r'round(\d+)',root['path']);rnd=int(match[1])if match else 0
   row,ledger=POL.held_record(int(root['n']),rnd)
   if row:root.update(source=row.get('source',''),licence=row.get('licence',''),ledger=ledger)
  if not root.get('source')and root.get('path')and str(root['path'])not in _origin_active:
   from exact_root30 import resolve
   _origin_active.add(str(root['path']))
   try:resolved=resolve(root,path,metadata)
   finally:_origin_active.discard(str(root['path']))
   if resolved:root.update(source=resolved[0],licence=resolved[1],source_proof=resolved[2])
  if not root.get('source')and root.get('source_proof'):
   ref=pathlib.Path(root['source_proof']);candidate=pathlib.Path(str(ref).removesuffix('.origin.json'))
   if ref.name.endswith('.origin.json')and candidate.is_file()and candidate!=path and str(candidate)not in _origin_active:
    _origin_active.add(str(candidate))
    try:resolved=pinned_origin_metadata(candidate,int(root.get('n',n)))
    finally:_origin_active.discard(str(candidate))
    if resolved and not resolved[0].startswith('unresolved ancestry:'):root.update(source=resolved[0],licence=resolved[1],source_proof=resolved[2])
  roots.append(root)
 if not roots:return refuse('no recorded roots in verified origin')
 src=json.dumps(dict(pinned_snapshot_roots=roots,proof=str(origin),sha256=hashlib.sha256(origin.read_bytes()).hexdigest()),separators=(',',':'))
 return src,'; '.join(dict.fromkeys(v.get('licence','')for v in roots)),str(origin)

def stair_record_matches(path,record,n):
 try:
  return int(json.load(open(record))['n'])==n and hashlib.sha256(pathlib.Path(path).read_bytes()).digest()==hashlib.sha256(pathlib.Path(record).with_suffix('.csv').read_bytes()).digest()
 except (OSError,ValueError,KeyError):return False

def metadata(p,n):
 p=pathlib.Path(p)
 from held32 import projection
 held_projection=projection(p,n) if p.is_file() else None
 if held_projection:return held_projection
 if p.parent==S/'gather':
  from gather29 import accepted
  held=accepted(p,n,POL)
  if held:
   row,record=held;return row['source'],row['licence'],record
 pinned=pinned_origin_metadata(p,n)
 if pinned:return pinned
 # Frozen output bytes can retain a full source proof in a producer's pinned feed.
 if re.search(r'take-(?:soft|border|midm|invent|rebuild|classfill|modules|stair-c|k123|backlog)-r2[2-8]/',str(p))and p.is_file():
  from aliases29 import candidates
  for alias in candidates(p,n):
   if pathlib.Path(str(alias)+'.origin.json').exists():
    pinned=pinned_origin_metadata(alias,n)
    if pinned and not pinned[0].startswith('unresolved ancestry:'):
     return pinned[0]+'; exact immutable output alias '+str(alias)+' sha256 '+hashlib.sha256(p.read_bytes()).hexdigest(),pinned[1],pinned[2]
 boxed=S/'take-k123-r24/work/cc0/parts/847-licensed-parts.csv'
 local=S/'take-k123-r24/near/847-cc0-rectangle-local-proof.csv'
 if p==boxed and local.exists() and boxed.exists():
  record_local=json.load(open(str(local)+'.json'))
  if record_local.get('same_bytes_as')==str(boxed) and hashlib.sha256(boxed.read_bytes()).digest()==hashlib.sha256(local.read_bytes()).digest():return metadata(local,n)
 key=(str(p),n)
 frozen=bool(re.search(r'take-[a-z0-9-]+-r(?:[1-9]|1\d|2[0-7])(?:/|$)',str(p)))
 if frozen and key in _meta_cache:return _meta_cache[key]
 try:src,lic,rec=soft.metadata(p,n)
 except (OSError,ValueError,csv.Error):src,lic,rec='','',''
 for side in (pathlib.Path(str(p)+'.json'),pathlib.Path(p).with_suffix('.json')):
  if side.exists():
   try:
    v=json.load(open(side))
    if v.get('finish_source'):src=v['finish_source'];lic=v.get('finish_licence','');rec=str(side)
   except (OSError,ValueError):pass
 if not src and pathlib.Path(p).is_file():
  m=re.fullmatch(r'\d+-(x[0-9a-f]+)',pathlib.Path(p).stem)
  proof=pathlib.Path(p).parent/(m[1]+'-source-proof.json') if m else None
  if proof and proof.exists():
   v=json.load(open(proof))
   if hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==v.get('input_sha256'):
    src=v.get('source','');lic=v.get('licence','');rec=str(proof)
 if not src and pathlib.Path(p).stem.isdigit():
  ledger=pathlib.Path(p).parent/'take.tsv'
  row=next((v for v in rows(ledger) if v.get('n')==str(n)),None)
  if row:src=row.get('source','');lic=row.get('licence','');rec=str(ledger)
 if not src:
  origin=pathlib.Path(str(p)+'.origin.json')
  if origin.exists() and pathlib.Path(p).exists():
   value=json.load(open(origin))
   if value.get('verified_ancestry') and hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()==value.get('snapshot_sha256'):
    compact=forensics_sources.compact_ancestry(value['ancestry'],origin)
    roots=[]
    for root in compact.get('roots',[]):
     root=dict(root)
     if not root.get('source') and '/gather/' in root.get('path',''):
      match=re.search(r'round(\d+)',root['path']);rnd=int(match[1]) if match else 0
      rr,ledger=POL.held_record(int(root['n']),rnd)
      if rr:root.update(source=rr.get('source',''),licence=rr.get('licence',''),ledger=ledger)
     roots.append(root)
    if roots:
     src=json.dumps(dict(pinned_snapshot_roots=roots,proof=str(origin),sha256=hashlib.sha256(origin.read_bytes()).hexdigest()),separators=(',',':'))
     lic='; '.join(dict.fromkeys(v.get('licence','')for v in roots));rec=str(origin)
 if not src:
  root=next((v for v in pathlib.Path(p).parents if v.name.startswith('take-stair-c-r')),None)
  candidates=list((root/'work').glob('raw-*/'+pathlib.Path(p).stem+'.json'))if root else[]
  if candidates and len({hashlib.sha256(v.read_bytes()).hexdigest()for v in candidates})==1:
   value=json.load(open(candidates[0]));mods=value.get('modules',[])
   if mods:
    src='module build: '+', '.join(v['id']+' <'+v['source']+'>'for v in mods)
    lic='; '.join(v['licence']for v in mods);rec=str(candidates[0])
 if not src:
  root=next((v for v in pathlib.Path(p).parents if v.name.startswith('take-stair-c-r')),None)
  parts=pathlib.Path(p).stem.rsplit('-',1)
  if root and len(parts)==2:
   exact=root/'work/boxcopy'/parts[1]/'raw-a'/(parts[0]+'.json')
   if stair_record_matches(p,exact,n):
    value=json.load(open(exact));mods=value.get('modules',[])
    if mods:
     src='module build: '+', '.join(v['id']+' <'+v['source']+'>'for v in mods)+'; exact build record '+str(exact)
     lic='; '.join(v['licence']for v in mods);rec=str(exact)
 if not src:
  from public_archive28 import metadata as public_archive
  src,lic,rec=public_archive(p,n)
 if not src:
  from archive28 import metadata as archived
  src,lic,rec=archived(p,n)
 if not src and '/take-backlog-'in str(p)and '/work/starts/'in str(p)and str(p)not in _alias_active:
  from aliases29 import candidates
  _alias_active.add(str(p))
  try:
   for alias in candidates(p,n):
    if str(alias)in _alias_active:continue
    ps,pl,pr=metadata(alias,n)
    if ps and pl:
     src=ps+'; exact byte-identical source alias '+str(alias)+' sha256 '+hashlib.sha256(p.read_bytes()).hexdigest();lic=pl;rec=pr;break
  finally:_alias_active.discard(str(p))
 # Unrecorded inputs remain deferred. Avoid scanning every historical ledger per missing parent.

 if frozen:_meta_cache[key]=(src,lic,rec)
 return src,lic,rec

def terms_for_other(lic):return lic

def previous_round(record):
 takes=re.findall(r'take-[a-z0-9-]+-r(\d+)',record)
 tables=re.findall(r'round(\d+)-best-',record)
 return int(takes[-1]if takes else tables[-1])-1 if takes or tables else 23

def implicit_held(source,record):
 if not re.match(r'(?:fq quench of the held packing|own soft-box search .*from the held packing)',source):return None
 path=pathlib.Path(record.split(' n=',1)[0]);counts=re.findall(r'\bn=(\d+)\b',record)
 if path.parent!=R/'results'or not re.fullmatch(r'round\d+-best-[\w-]+\.tsv',path.name)or not counts or not path.is_file():return None
 count=int(counts[0]);row=source_table(str(path),path.stat().st_mtime_ns).get(count)
 if not row or row.get('source')!=source:return None
 return str(count),str(previous_round(record))

@lru_cache(maxsize=2048)
def rejected(src,lic,terminal=True):
 reason=refused_source(dict(source=src,licence=lic),str(S))
 if reason and reason!='held n801 donor':return reason
 text=src+' '+lic
 text=text.replace('samanyu1808/sis-final-packings','licensed-public/final-packings').replace('samanyu1808/sis-submit','licensed-public/sis-submit')
 if re.search(r'franciscouzo/square-packing',text,re.I)and re.search(r'\bMIT\b',text):return None
 # Round27 permits the seed ancestry that earlier rounds excluded.
 if re.search(r'unresolved ancestry|near build recorded by|see donor ledger',text,re.I):return 'unresolved source record'
 seed=bool(re.search(r'Samanyu-dev/squares_in_squares|samanyu_bestfit|921-29e12ff3|n\s*=\s*\d+\s+of\s+Samanyu',text,re.I)) or classify(text,ORIG)[0]=='yes'
 if re.search(r'no licen[cs]e|without (?:a )?licen[cs]e',text,re.I) and not seed:return 'unlicensed source'
 flag,seeds=classify(text,ORIG)
 if terminal and flag=='unknown' and not seed and 'own construction'not in text.lower():
  named=re.search(r'(?<![/\w])[A-Za-z0-9_-]+/[A-Za-z0-9_-]+',text)
  if 'Other' in lic and named:return None
  return 'unresolved root'

 return None

def captured_record(value,source,terms,fallback):
 layout=value.get('layout',{})if isinstance(value,dict)else{}
 table=layout.get('table')
 # A held wrapper can retain its donor's old table while naming its actual pinned source.
 compact=re.search(r'licensed ancestry sha256 ([0-9a-f]{64}); full source_record ([^\s;,]+\.json)',source)
 if compact and layout.get('ancestry_file')==compact[2]and layout.get('ancestry_sha256')==compact[1]:
  proof=pathlib.Path(compact[2])
  if not proof.is_file()or hashlib.sha256(proof.read_bytes()).hexdigest()!=compact[1]:return None
  inner=json.load(open(proof));inner_layout=inner.get('layout',inner)
  if layout.get('n')is not None and inner_layout.get('n')is not None and int(layout['n'])!=int(inner_layout['n']):return None
  return fallback
 if not table or re.match(r'licensed ancestry sha256 [0-9a-f]{64}; full source_record ',source):return fallback
 path=pathlib.Path(table);count=layout.get('n')
 if path.parent!=R/'results'or not re.fullmatch(r'round\d+-best-[\w-]+\.tsv',path.name):return fallback
 if path.parent!=R/'results'or not re.fullmatch(r'round\d+-best-[\w-]+\.tsv',path.name)or not path.is_file()or not isinstance(count,int):return None
 row=source_table(str(path),path.stat().st_mtime_ns).get(count)
 if not row or row.get('source')!=source or row.get('licence')!=terms:return None
 return str(path)+' n='+str(count)

def audit_unbounded(p,n,src=None,lic=None,record=None):
 p=pathlib.Path(p)
 if src is None:src,lic,rec=metadata(p,n)
 else:rec=record or str(p)
 if not src or not lic:return dict(ok=False,reason='missing exact source record',path=str(p),n=n)
 key=hashlib.sha256(('strict33-held-geometry-v1:'+hashlib.sha256(p.read_bytes()).hexdigest()+str(p)+'\0'+rec+'\0'+src+'\0'+lic).encode()).hexdigest()
 if key in _cache:return _cache[key]
 q=W/'ancestry'/f'{key}.json'
 if q.exists() and re.search(r'take-[a-z0-9-]+-r(?:[1-9]|1\d|2[0-7])/',str(p)):
  old=json.load(open(q))
  if old.get('ok') and all(rejected(v['source'],v['licence'],terminal=not v.get('parents')) is None for v in old['nodes'].values()):
   result=dict(ok=True,reason='immutable recorded parent closure',proof=str(q),hash=key,nodes=len(old['nodes']),source=src,licence=lic)
   _cache[key]=result;return result
 nodes={};active=set();reasons=[];credits=set();root_count=0;cycles=[]
 def visit(source,terms,record,depth=0):
  nonlocal root_count
  from held_geometry33 import resolve_record
  held_geometry=resolve_record(record)
  if held_geometry:source,terms,record=held_geometry['source'],held_geometry['licence'],held_geometry['ledger']+' n='+str(held_geometry['n'])
  text=source+' '+terms
  # Equal source cells at different historical versions can have different held parents.
  counts=re.findall(r'\bn=(\d+)\b',record)
  canonical_record=re.sub(r'(?: n=\d+)+$','',record)+(' n='+counts[-1]if counts else '')
  digest=hashlib.sha256((text+'\0'+canonical_record).encode()).hexdigest()
  if digest in active:cycles.append(dict(node=digest,first=nodes[digest]['record'],again=record,source=source[:500]));return digest
  if digest in nodes:return digest
  if depth>80:reasons.append('ancestry depth limit');return digest
  active.add(digest)
  node=dict(source=source,licence=terms,record=record,parents=[]);nodes[digest]=node
  # Public shorthand is resolved from its actual packing count at the per-n ledger.
  if 'areebbb/sis-certified-union-micro-shrink-lb-22-17479' in source and not re.search(r'per_n.csv|upstream per.n|per.n origin',source,re.I):
   nums=re.findall(r'n\s*=\s*(\d+)',record)
   count=int(nums[-1]) if nums else n
   preceding=re.findall(r'(?:n\s*=\s*|donor\s+|/)(\d{1,4})(?:\.csv|\b)',source.split('areebbb/')[0])
   if preceding:count=int(preceding[-1])
   public=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
   row=next((v for v in csv.DictReader(open(public)) if int(v['n'])==count),None)
   if row:
    source+='; areebbb per_n.csv donor n='+str(count)+': '+json.dumps(row,sort_keys=True)+'; exact ledger '+str(public)
    terms+='; Apache 2.0; per_n.csv upstream chain '+row['src']
    node.update(source=source,licence=terms)
  why=rejected(source,terms,terminal=False)
  if why:reasons.append(why);node['refused']=why;active.discard(digest);return digest
  if not source or not terms:reasons.append('missing source or licence');active.discard(digest);return digest
  # Follow immutable compact source records by their actual content hash.
  compact_refs=re.findall(r'licensed ancestry sha256 ([0-9a-f]{64}); full source_record ([^\s;,]+\.json)',source)
  compact_refs += [(digest,ref)for ref,digest in re.findall(r'stair-c proof ([^\s;,]+\.json) immutable sha256 ([0-9a-f]{64})',source)]
  for expected,ref in dict.fromkeys(compact_refs):
   fp=pathlib.Path(ref)
   if not fp.exists() or hashlib.sha256(fp.read_bytes()).hexdigest()!=expected:
    reasons.append('changed or missing compact source '+ref);continue
   value=json.load(open(fp));layout=value.get('layout',{})
   parent_source=value.get('source',layout.get('source',''));parent_terms=value.get('licence',layout.get('licence',''))
   if parent_source==source and parent_terms==terms:reasons.append('self-referential compact source');continue
   historical=captured_record(value,parent_source,parent_terms,str(fp))
   if historical is None:reasons.append('captured producer table differs from source '+str(fp));continue
   node['parents'].append(visit(parent_source,parent_terms,historical,depth+1))
  # Expand versioned held records through the producer's accepted history.
  h=[]
  h+=re.findall(r'held n\s*=\s*(\d+)\s+of round\s*(\d+)',text,re.I)
  h+=re.findall(r'n\s*=\s*(\d+)\s+from\s+held\s+round\s*(\d+)',text,re.I)
  # Plain held references refer to the source table immediately before this producer round.
  rnd=previous_round(record)
  h += [(c,str(rnd)) for c in re.findall(r'(?:the )?held packing of n\s*=\s*(\d+)',source,re.I)]
  implicit=implicit_held(source,record)
  if implicit:h.append(implicit)
  # A seed alias needs its own count, even if other branches are licensed.
  for count in re.findall(r'(\d{2,4})[a-z0-9_.~-]*\.[CF][12]?\s*<held:\s*seed merged0',source,re.I):
   if int(count)not in ORIG:reasons.append('unknown merged0 alias '+count)
  for count,round_ in dict.fromkeys(h):
   row,ledger=POL.held_record(int(count),int(round_))
   if row:node['parents'].append(visit(row.get('source',''),row.get('licence',''),ledger+f' n={count}',depth+1))
   else:reasons.append('missing held parent '+count+'@'+round_)
  # Exact module records retain a separate source and licence for every part.
  records=[]
  record_path=pathlib.Path(record.split(' n=',1)[0])
  if record_path.suffix=='.json' and record_path.is_file():records.append(record_path)
  records += [pathlib.Path(v)for v in re.findall(r'exact build record ([^\s;,)]+\.json)',source)]
  for module_record in dict.fromkeys(records):
   try:parts=json.load(open(module_record)).get('modules',[])
   except (OSError,ValueError):parts=[]
   for part in parts:
    if isinstance(part.get('source'),str):node['parents'].append(visit(part['source'],part.get('licence',''),str(module_record)+' module '+part.get('id',''),depth+1))
  # Follow exact per-n files and their immutable sidecars, including external root proofs.
  reference_text=re.sub(r'(take-[a-z0-9-]+-r\d+)\s+(near/)',r'\1/\2',source)
  refs=re.findall(r'((?:$SCRATCH/bounties-squares/)?take-[^/\s<>";,()]+/(?:[^/\s<>";,()]+/)*?(\d{1,4})(?:-[^/\s<>";,()]+)?\.csv)',reference_text)
  folders=re.findall(r'((?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/near)(?=[\s;,]|$)',text)
  context=text+' '+record
  for rp in records:
   try:context+=' '+json.dumps(json.load(open(rp)))
   except (OSError,ValueError):pass
  roots=re.findall(r'((?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+)(?=/)',context)
  bare=re.findall(r'(?<![/\w-])(\d{1,4}-[^/\s()<>\";,]+\.csv)',source)
  for name in dict.fromkeys(bare):
   if not 1<=int(name.split('-')[0])<=1000:continue
   options=[pathlib.Path(v)/name if pathlib.Path(v).is_absolute()else S/v/name for v in folders]
   options += [(pathlib.Path(v) if pathlib.Path(v).is_absolute()else S/v)/folder/name for v in dict.fromkeys(roots) for folder in ('near','work/starts','work/donors')]
   existing=[]
   for v in dict.fromkeys(options):
    if v.exists() or metadata(v,int(name.split('-')[0]))[0]:existing.append(v)
   if existing:refs.extend((str(v),int(name.split('-')[0]))for v in existing)
   elif name!=p.name and not any(pathlib.Path(ref).name==name for ref,_ in refs):
    if 'pinned donor ancestry: 'not in source and not ('\"A\"' in source and '\"B\"'in source):reasons.append('unresolved bare parent '+name)
  retained={}
  def structured(value):
   if isinstance(value,dict):
    v=value.get('source')
    if isinstance(v,list)and len(v)==2 and isinstance(v[0],str)and isinstance(v[1],int):
     key=(v[0],v[1]);refs.append(key)
     if isinstance(value.get('source_record'),str):
      ps,pl,pr=metadata(pathlib.Path(v[0]),v[1])
      retained[key]=(ps,pl,pr) if ps else (value['source_record'],value.get('licence',''),'recorded source snapshot '+v[0])
    for key,v in value.items():
     if key not in ('policy','controls','excluded','rejected'):structured(v)
   elif isinstance(value,list):
    for v in value:structured(v)
  decoder=json.JSONDecoder()
  # Direct module/rectangle/join records select actual parents before inherited notices.
  direct=False
  if 'pinned donor ancestry: ' in source:
   tail=source.split('pinned donor ancestry: ',1)[1]
   groups=None
   for candidate in (tail,tail.replace('\\"','"')):
    try:groups,_=decoder.raw_decode(candidate);break
    except ValueError:pass
   if not isinstance(groups,list):reasons.append('unreadable pinned donors')
   else:
    direct=True;refs=[]
    for group in groups:
     if not isinstance(group,dict) or not group.get('n'):reasons.append('invalid pinned donor');continue
     af=group.get('ancestry_file')
     if af:
      fp=pathlib.Path(af)
      if not fp.exists() or hashlib.sha256(fp.read_bytes()).hexdigest()!=group.get('ancestry_sha256'):
       reasons.append('changed or missing pinned ancestry '+str(af));continue
      saved=json.load(open(fp));layout=saved.get('layout',{})
      if int(layout.get('n',group['n']))!=int(group['n']):reasons.append('pinned donor count mismatch');continue
      gs=saved.get('source',layout.get('source',''));gl=saved.get('licence',layout.get('licence',''))
      historical=captured_record(saved,gs,gl,str(fp)+' n='+str(group['n']))
      if historical is None:reasons.append('captured donor table differs from source '+str(fp));continue
      node['parents'].append(visit(gs,gl,historical,depth+1))
     elif group.get('source') and group.get('licence'):
      node['parents'].append(visit(group['source'],group['licence'],str(group.get('evidence',group.get('origin','pinned donor')))+' n='+str(group['n']),depth+1))
     else:reasons.append('missing pinned donor source')
  parsed=[];pos=0
  while True:
   pos=source.find('{',pos)
   if pos<0:break
   try:value,length=decoder.raw_decode(source[pos:]);parsed.append(value);pos+=length
   except ValueError:pos+=1
  if not direct:
   special=next((v for v in parsed if isinstance(v,dict) and 'pinned_snapshot_roots'in v),None)
   rectangle=next((v for v in parsed if isinstance(v,dict) and all(isinstance(v.get(t),dict)and isinstance(v[t].get('source'),list)for t in ('A','B'))),None)
   if special:
    direct=True;refs=[]
    for root_record in special['pinned_snapshot_roots']:
     if not root_record.get('source')or not root_record.get('licence'):reasons.append('unresolved pinned root');continue
     node['parents'].append(visit(root_record['source'],root_record['licence'],str(root_record.get('ledger',root_record.get('source_proof',record)))+' n='+str(root_record.get('n',n)),depth+1))
   elif rectangle:
    direct=True;refs=[];structured(rectangle)
   else:
    for record_file in dict.fromkeys(records):
     try:
      record_value=json.load(open(record_file))
      structured(record_value.get('layout',record_value) if isinstance(record_value,dict) else record_value)
     except (OSError,ValueError):pass
    for value in parsed:structured(value)
  for ref,count in dict.fromkeys(refs):
   parent=pathlib.Path(ref);parent=parent if parent.is_absolute() else S/parent
   if parent==p and (ref,count)not in retained:continue
   # Hash graph snapshots preserve provenance even after a producer removes a non-winning CSV.
   ps,pl,pr=retained.get((ref,count),(None,None,None))
   if ps is None:ps,pl,pr=metadata(parent,int(count))
   if not ps:
    from archived_credit28 import resolve as archived_credit
    resolved=archived_credit(source,terms,record,parent,int(count))
    if resolved:ps,pl,pr=resolved
   if not ps:
    reasons.append('missing exact parent '+ref);continue
   if ps==source and pl==terms:continue
   node['parents'].append(visit(ps,pl,pr+f' n={count}',depth+1))
  for ref in re.findall(r'source metadata ([^)\s;]+\.json)',source):
   parent=pathlib.Path(ref)
   if parent.exists() and parent.resolve().is_relative_to(S):
    try:
     v=json.load(open(parent));ps=provenance_text(v)
     if ps and ps!=text:node['parents'].append(visit(ps,terms,str(parent),depth+1))
    except (ValueError,OSError):reasons.append('unreadable metadata '+ref)
   else:reasons.append('missing metadata '+ref)
  # An areebbb donor must retain its exact per-n chain, not just the notebook licence.
  if 'areebbb/sis-certified-union-micro-shrink-lb-22-17479' in source:
   if not re.search(r'per_n.csv|upstream per.n|per.n origin|Upstream per-n records',source,re.I):reasons.append('areebbb chain missing per-n ledger')
  if not node['parents']:
   root_count+=1
   why=rejected(source,terms)
   if why:reasons.append(why);node['refused']=why
  active.discard(digest)
  return digest
 root=visit(src,lic,rec)
 # Frozen histories can refer back to a prior result through copied origin
 # records. Every such component still needs a path to a real source root.
 from exact_root30 import unanchored_cycles
 if unanchored_cycles(nodes,cycles):reasons.append('ancestry cycle without a source root')
 proof=dict(cycles=cycles,policy='strict28v1',path=str(p),n=n,root=root,nodes=nodes,ok=not reasons,reason='recorded parent closure' if not reasons else '; '.join(dict.fromkeys(reasons)),root_count=root_count)
 q=W/'ancestry'/f'{key}.json';q.write_text(json.dumps(proof,separators=(',',':')))
 # Published notices preserve unique source texts. Search queues contain only the hash reference.
 proof_short=dict(ok=proof['ok'],reason=proof['reason'],proof=str(q),hash=key,nodes=len(nodes),source=src,licence=lic)
 _cache[key]=proof_short
 return proof_short

def published(a):
 d=json.load(open(a['proof']));notices=[];terms=[]
 for node in d['nodes'].values():
  notices.append(node['source']);terms.append(node['licence'])
  if not node.get('parents')and 'Other'in node['licence']:terms.append('upstream Other terms: '+node['source']+' ('+node['licence']+')')
 return ('source metadata '+a['proof']+'; '+' / '.join(dict.fromkeys(notices))).replace('|',' / '),'; '.join(dict.fromkeys(terms)).replace('|',' / ')


def audit(p,n,src=None,lic=None,record=None):
 import signal
 def expired(*unused):raise TimeoutError('source graph exceeded 30 wall seconds')
 previous=signal.signal(signal.SIGALRM,expired);signal.alarm(30)
 try:return audit_unbounded(p,n,src,lic,record)
 except TimeoutError as error:return dict(ok=False,reason=str(error)+'; deferred',path=str(p),n=n)
 finally:signal.alarm(0);signal.signal(signal.SIGALRM,previous)
