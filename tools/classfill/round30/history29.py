from common29 import *

import trace_base as H
H.E=W/'evidence';H.E.mkdir(exist_ok=True)
PIN_RECORDS={}
def pinned_evidence(path):
 p=Path(path)
 if not p.is_file():return None
 pin=blob(p);PIN_RECORDS[(str(p),pin['sha256'])]=pin
 return Path(pin['snapshot'])
H.evidence=pinned_evidence
# Round 26: the assembler r25 tracer loads round tables up to round 23 only, so 'held n of round 25' resolved to an older table
# (907 -> round20-best, a prvsiyan descendant; 790 -> round 21, a Samanyu descendant). Add the round 25 b table.
for _round in [25,26,27,28,29]:
 for _p in R.glob(f'results/round{_round}-best-*.tsv'):H.T[_round]=(_p.name,H.tab(H.evidence(_p)))
assert 25 in H.T,'round25 table missing'

AREEB=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
AREEB_ROWS={int(r['n']):r for r in csv.DictReader(open(AREEB))}
ORIGINAL_PUBLIC=H.Trace.public
def public_with_upstream(self,ref,n,text):
    key=('classfill_areebbb',ref,n)
    if ref!='areebbb/sis-certified-union-micro-shrink-lb-22-17479' or key in self.seen:
        return ORIGINAL_PUBLIC(self,ref,n,text)
    self.seen.add(key)
    ORIGINAL_PUBLIC(self,ref,n,text)
    row=AREEB_ROWS.get(n)
    if not row:
        self.issues.append('areebbb missing per_n row '+str(n));return
    source=row['src']
    self.parts.append('areebbb per_n.csv donor n = '+str(n)+': '+source)
    m=re.match(r'(notebooks|datasets)/([^/]+/[^/]+)(?:/(.*))?',source.split('|',1)[0])
    if not m:
        self.issues.append('areebbb unresolved upstream '+source);return
    upstream=m[2]
    notice=H.LIC.get(upstream)
    if notice is None and m[1]=='notebooks':notice='Apache 2.0 (Kaggle default for public notebooks)'
    if notice is None:
        self.issues.append('areebbb upstream licence missing '+upstream);return
    self.lic.append('areebbb/sis-certified-union-micro-shrink-lb-22-17479 per_n.csv n='+str(n)+' -> '+source+': '+notice)
    if upstream in H.LIC:self.public(upstream,n,source)
H.Trace.public=public_with_upstream
H.LIC['Samanyu-dev/squares_in_squares']='Own-discovered seed, confirmed by round27 brief'


ORIGINAL_NEAR=H.Trace.near
def near_with_archive(self,path):
    p=Path(path)
    if not p.is_absolute():p=S/p
    marker=('classfill_archive_near',str(p))
    if marker in self.seen:return
    self.seen.add(marker)
    if not re.match(r'\d+',p.name):return
    root=next((q for q in p.parents if re.match(r'take-.*-r\d+$',q.name)),None)
    donor_match=re.search(r'from(.+)\.csv$',p.name)
    if root is not None and donor_match:
        donor=donor_match[1]
        for name in ['work/sources-all.tsv','work/sources.tsv']:
            ledger=root/name
            if not ledger.is_file():continue
            found=next((q for q in rows(ledger) if q.get('donor')==donor),None)
            if found:
                self.seen.add(('near',str(p)))
                H.evidence(ledger)
                parent_n=int(re.match(r'\d+',donor)[0])
                self.add(found['source'],parent_n,'near parent '+donor)
                self.lic.append(found.get('licence',''))
                break
    ORIGINAL_NEAR(self,str(p))
    if root is None:return
    metadata=[]
    origin=Path(str(p)+'.origin.json')
    if origin.is_file():
        obj=json.loads(H.evidence(origin).read_text())
        expected=obj.get('snapshot_sha256')
        if expected and expected!=hashlib.sha256(p.read_bytes()).hexdigest():
            self.issues.append('changed origin snapshot '+str(p));return
        self.obj(obj,int(re.match(r'\d+',p.name)[0]))
        m=re.search(r'gather/round(\d+)-',obj.get('path',''))
        if m:self.hist(int(m[1]),int(obj['n']))
        metadata.append(origin)
    for sub in ['raw-a','raw-n','raw-s','archive/n/raw-a','archive/s/raw-a','archive/a/raw-a']:
        q=root/'work'/sub/(p.stem+'.json')
        if q.is_file():metadata.append(q)
    for q in metadata:
        self.obj(json.loads(H.evidence(q).read_text()),int(re.match(r'\d+',p.name)[0]))
    if metadata:
        issue='near without metadata '+str(p)
        self.issues[:]=[q for q in self.issues if q!=issue]
H.Trace.near=near_with_archive


# Round 26: the tracer's daily step reads PATHS['kmmmvs/squares-public-merge-daily'], loaded last from
# take-harvest-r24/work/public2, whose meta says its files were carried and whose merge_report.json is gone.
# Every closure then carried 'missing daily report' and named a gone file (twoshort quench_walk refused it).
# Walk both round 26 copies instead (06:03Z and 13:54Z runs); walking both only adds checks.
DAILY26=[S/'take-harvest-r26/work/public/data/nb/kmmmvs__squares-public-merge-daily',S/'take-harvest-r26/work/public2/data/nb/kmmmvs__squares-public-merge-daily']
# 15:55Z: an older input (an areebbb per_n row of round 22 credits the daily merge for 552 and 601) used an older run.
# Walk every kept copy of the report (2026-11-07 to 2026-11-14), so the run the input used is among them.
DAILY26+=sorted({d for d in list(S.glob('harvest*/nb/kmmmvs__squares-public-merge-daily'))+list(S.glob('take-harvest-r2*/work/*/data/nb/kmmmvs__squares-public-merge-daily')) if (d/'merge_report.json').is_file()}-set(DAILY26))
for _d in DAILY26:assert (_d/'merge_report.json').is_file(),_d
ORIGINAL_DAILY=H.Trace.daily
def daily26(self,n,old=False):
    if old:return ORIGINAL_DAILY(self,n,old)
    for d in DAILY26:
        key=('daily26',n,str(d))
        if key in self.seen:continue
        self.seen.add(key);self.seen.discard(('daily',n,False))
        H.PATHS['kmmmvs/squares-public-merge-daily']=d
        ORIGINAL_DAILY(self,n,False)
H.Trace.daily=daily26

def trace(src,lic,meta,n):
 # Reuse the assembler's historical resolver, with all writes redirected here.
 PIN_RECORDS.clear()
 for rnd in ['r23','r24','r25','r26','r27','r28','r29']:
  for p in S.glob(f'take-*-{rnd}/take.tsv'):
   if 'assemble' in p.parent.name:continue
   H.SN[p.parent.name]={int(r['n']):r for r in rows(p)}
 tr=H.Trace(n);tr.add(src,n);tr.lic.append(lic);tr.obj(meta,n)
 for path in sorted(meta.get('unresolved_csv',[]),key=lambda p:('/collector/certified/' not in p,p)):tr.near(path)
 text='\n'.join(tr.parts+tr.lic)
 bad=BAD.search(source_text(text))
 return dict(parts=tr.parts,licences=tr.lic,issues=tr.issues,public=tr.checked,excluded=bad.group() if bad else None,snapshots=list(PIN_RECORDS.values()))

ORIGINAL_FILE=H.Trace.file
def file_with_origin(self,path,n,source=None):
 p=Path(path)
 if not p.is_absolute():p=S/p
 origin=Path(str(p)+'.origin.json')
 if origin.is_file():
  key=('pinned-origin',str(p),n)
  if key in self.seen:return
  self.seen.add(key);obj=json.loads(H.evidence(origin).read_text())
  if not p.is_file() or obj.get('snapshot_sha256')!=hashlib.sha256(p.read_bytes()).hexdigest():
   self.issues.append('changed or missing pinned origin '+str(p));return
  self.obj(obj,n)
  m=re.search(r'gather/round(\d+)-',obj.get('path',''))
  if m:self.hist(int(m[1]),int(obj.get('n',n)))
  return
 return ORIGINAL_FILE(self,path,n,source)
H.Trace.file=file_with_origin

# Archived twoshort run jobs identify the raw outputs of their exact run tag.
ORIGINAL_NEAR27=H.Trace.near
def near_with_run(self,path):
 p=Path(path)
 m=re.search(r'(take-twoshort-r25/work/boxE25)/runs/(.+)-s(\d+)/raw/(\d+)-sl\3-\d+\.csv$',str(p))
 if m and p.is_file():
  candidates=sorted((S/m[1]/'jobs').glob('*'+m[2]+'-'+m[3]+'.json'))
  exact=[q for q in candidates if q.name.startswith('000-00-leg-')]
  if exact:candidates=exact
  if len(candidates)==1:
   key=('twoshort-run27',str(p))
   if key in self.seen:return
   self.seen.add(key);j=json.loads(H.evidence(candidates[0]).read_text())
   self.obj(j,int(m[4]));return
 return ORIGINAL_NEAR27(self,path)
H.Trace.near=near_with_run

# The k123 queue saved the exact harvested866 row before its seed-only withdrawal.
PREVIOUS_FILE27=H.Trace.file
def file_with_retained866(self,path,n,source=None):
 if str(path)==str(S/'take-harvest-r23/866.csv') and n==866:
  key=('retained-harvest866',866)
  if key in self.seen:return
  self.seen.add(key)
  ledger=S/'take-k123-r23/work/fresh2060/sources-fresh2060.json'
  item=json.loads(H.evidence(ledger).read_text())['866']
  assert item['origin']==str(path) and int(item['row']['n'])==866
  self.obj(item['row'],866);return
 return PREVIOUS_FILE27(self,path,n,source)
H.Trace.file=file_with_retained866

EARLIER_NEAR27=H.Trace.near
def near_with_exact_archives(self,path):
 p=Path(path)
 if p==S/'take-polish-r22/work/candidates/416.csv':
  archive=S/'take-harvest-r22/work/public/starts/416'
  if p.read_bytes()!=(archive/'416.csv').read_bytes():
   self.issues.append('polish416 archive identity changed');return
  key=('exact-public416',str(p))
  if key in self.seen:return
  self.seen.add(key)
  row=next(q for q in rows(archive/'take.tsv') if int(q['n'])==416)
  H.evidence(p);H.evidence(archive/'416.csv');H.evidence(archive/'take.tsv');self.obj(row,416);return
 if '/take-rebuild-r27/work/r27/pins/' in str(p):
  record=p.parent.parent/'records'/(p.stem+'.json')
  if record.is_file():
   key=('rebuild-r27-pin',str(p))
   if key in self.seen:return
   self.seen.add(key);j=json.loads(H.evidence(record).read_text())
   if j['sha256']!=hashlib.sha256(p.read_bytes()).hexdigest():self.issues.append('changed rebuild pin '+str(p));return
   if Path(j['start']).read_bytes()!=p.read_bytes():self.issues.append('rebuild original differs from pin '+str(p));return
   H.evidence(p);self.file(j['start'],int(j['n']));return
 return EARLIER_NEAR27(self,path)
H.Trace.near=near_with_exact_archives

# Resolve hash-named harvest certificates and their exact raw public row.
BEFORE_HARVEST_COPY=H.Trace.near
def near_harvest_copy(self,path):
 p=Path(path)
 if re.search(r'/take-harvest-r\d+/work/(?:collector/certified|public\d+/quick-starts)/',str(p)) and p.is_file():
  marker=('harvest-exact-copy28',str(p))
  if marker in self.seen:return
  self.seen.add(marker)
  try:
   from harvest_copy29 import resolve
   with p.open() as f:parent_n=int(next(csv.DictReader(f))['n'])
   result=resolve(p,parent_n)
   if result:
    if not hasattr(self,'certificate_copies'):self.certificate_copies={}
    self.certificate_copies[hashlib.sha256(p.read_bytes()).hexdigest()]=(str(p),parent_n)
    for q in result['pins']:H.evidence(q)
    self.parts.append('exact harvest copy '+str(p)+'; producer pins '+json.dumps(result['pins'])+'; maximum coordinate error '+str(result['max_coordinate_error']))
    self.add(result['source'],parent_n,'resolved harvest row');self.lic.append(result['licence'])
    if result.get('metadata'):self.obj(result['metadata'],parent_n)
    return
  except Exception as e:self.issues.append('harvest copy resolver '+str(p)+' '+repr(e));return
 return BEFORE_HARVEST_COPY(self,path)
H.Trace.near=near_harvest_copy

# Preserve exact input snapshots and their producer records through moved own files.
BEFORE_PIN_OBJECT=H.Trace.obj
BEFORE_PIN_ADD=H.Trace.add
BEFORE_PIN_NEAR=H.Trace.near
def obj_with_pins(self,q,context=None):
 if not hasattr(self,'packing_pins'):self.packing_pins={};self.original_pins={}
 if isinstance(q,dict):
  if q.get('input_file_snapshot'):
   p=Path(q['input_file_snapshot']);expected=q.get('input_file_sha256')
   if p.is_file() and expected and hashlib.sha256(p.read_bytes()).hexdigest()==expected:
    self.packing_pins[str(p)]=q
    origin=q.get('origin')
    if isinstance(origin,str) and Path(origin).is_file() and hashlib.sha256(Path(origin).read_bytes()).hexdigest()==expected:self.packing_pins[origin]=q
  if isinstance(q.get('source'),list) and len(q['source'])==2:
   p=Path(q.get('snapshot') or q['source'][0]);original=q.get('original_file')
   if not p.is_absolute():p=S/p
   if original and p.is_file():
    sha=hashlib.sha256(p.read_bytes()).hexdigest();m=re.match(r'\d+-([0-9a-f]{16,64})',p.name)
    if m and sha.startswith(m[1]):self.original_pins[str(original)]=(str(p),sha)
 return BEFORE_PIN_OBJECT(self,q,context)
def add_with_pin_list(self,s,n=None,label=''):
 if s:
  marker=('pinned-list28',hashlib.sha256(s.encode()).hexdigest(),n)
  if marker not in self.seen:
   self.seen.add(marker)
   for match in re.finditer(r'pinned donor ancestry:\s*',s):
    try:
     obj,_=json.JSONDecoder().raw_decode(s[match.end():]);self.obj(obj,n)
    except (ValueError,TypeError):pass
 return BEFORE_PIN_ADD(self,s,n,label)
def near_with_pins(self,path):
 p=Path(path)
 if not p.is_absolute():p=S/p
 key=('resolved-pin28',str(p))
 if key in self.seen:return
 record=getattr(self,'packing_pins',{}).get(str(p))
 if record:
  self.seen.add(key);H.evidence(p);n=int(record['n'])
  for original,pin in record.get('input_record_snapshots',{}).items():
   q=Path(pin['snapshot']);assert hashlib.sha256(q.read_bytes()).hexdigest()==pin['sha256'];H.evidence(q)
   if q.suffix=='.json':self.obj(json.loads(q.read_text()),n)
   elif q.suffix=='.tsv':self.obj(next(r for r in rows(q) if int(r['n'])==n),n)
  self.add(record.get('source',''),n,'pinned input source');self.lic.append(record.get('licence',''))
  self.parts.append('verified input snapshot '+str(p)+' sha256 '+record['input_file_sha256'])
  self.issues[:]=[q for q in self.issues if q!='near without metadata '+str(p)];return
 root=next((d for d in p.parents if re.match(r'take-k123-r\d+$',d.name)),None)
 if root and '/near/' in str(p) and not p.exists():
  expected=getattr(self,'original_pins',{}).get(str(p));archive=root/'work/withdrawn-near-ancestor-share'/p.name;side=Path(str(archive)+'.json')
  if expected and archive.is_file() and side.is_file() and hashlib.sha256(archive.read_bytes()).hexdigest()==expected[1]:
   self.seen.add(key);H.evidence(archive);self.obj(json.loads(H.evidence(side).read_text()),int(re.match(r'\d+',p.name)[0]));self.parts.append('exact archived own near '+str(archive)+' matches pinned '+expected[0]+' sha256 '+expected[1]);return
 return BEFORE_PIN_NEAR(self,str(p))
H.Trace.obj=obj_with_pins
H.Trace.add=add_with_pin_list
H.Trace.near=near_with_pins

# Run tags and seeds remain stable across the archive layout of rounds24-26.
BEFORE_OLD_RUN_NEAR=H.Trace.near
def near_archived_runs(self,path):
 p=Path(path)
 m=re.search(r'(take-twoshort-r(\d+)/work/boxE\2)/runs/(.+)-s(\d+)/raw/(\d+)-sl\4-\d+\.csv$',str(p))
 if m and p.is_file():
  jobs=sorted((S/m[1]/'jobs').glob('*'+m[3]+'-'+m[4]+'.json'))
  leg=[q for q in jobs if q.name.startswith('000-00-leg-')]
  if leg:jobs=leg
  if len(jobs)==1:
   j=json.loads(H.evidence(jobs[0]).read_text());assert j['n']==int(m[5]) and j['seed']==int(m[4]) and j.get('source')
   key=('archive-run28',str(p))
   if key in self.seen:return
   self.seen.add(key);H.evidence(p);self.obj(j,int(m[5]));self.parts.append('archived raw '+str(p)+' matched unique job '+str(jobs[0])+' by tag, seed and count');return
 if '/take-backlog-' in str(p) and '/work/starts/' in str(p) and p.is_file():
  sha=hashlib.sha256(p.read_bytes()).hexdigest();match=getattr(self,'certificate_copies',{}).get(sha)
  if match:
   key=('exact-backlog-copy28',str(p))
   if key in self.seen:return
   self.seen.add(key);H.evidence(p);self.parts.append('backlog exact copy '+str(p)+' sha256 '+sha+' matches certificate '+match[0]);return
 return BEFORE_OLD_RUN_NEAR(self,str(p))
H.Trace.near=near_archived_runs

# Resolve old daily aliases only with a unique registered ref and an exact file hash.
BASE_DAILY28=ORIGINAL_DAILY
def daily_alias28(self,n,old=False):
 path=S/'harvest-2026-11-10/nb/kmmmvs__squares-public-merge-daily/merge_report.json' if old else H.PATHS['kmmmvs/squares-public-merge-daily']/'merge_report.json'
 q=json.loads(H.evidence(path).read_text());row=q.get('replaced_groups',{}).get(str(n),{});src=row.get('source','')
 if src and not src.startswith(('datasets/','notebooks/','squares-in-squares-starter-notebook/')):
  slug,fn=src.split('/',1);refs=[ref for ref in H.LIC if ref.split('/')[-1]==slug];entries=[v for v in q.get('sources',[]) if v.get('source')==src]
  if len(refs)==len(entries)==1:
   ref=refs[0];sha=entries[0].get('sha256');tag=ref.replace('/','__');metas=list(S.glob('harvest*/nb/'+tag+'/meta.json'))+list(S.glob('take-harvest-r*/work/public*/data/nb/'+tag+'/meta.json'))
   matches=[]
   for meta in metas:
    mj=json.loads(meta.read_text())
    for f in mj.get('files',[]):
     name=f.get('file') if isinstance(f,dict) else f[0]
     if name!=fn:continue
     p=meta.parent/name
     if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==sha:matches.append((meta,p));break
    if matches:break
   if matches:
    meta,p=matches[0];H.evidence(meta);H.evidence(p);self.seen.add(('daily',n,old));self.add(f'kmmmvs daily exact alias donor n = {n}: {ref} :: {fn}; file {p} sha256 {sha}',n);self.public(ref,n,src);return
 return BASE_DAILY28(self,n,old)
ORIGINAL_DAILY=daily_alias28

# Harvest's parent records bind copied ancestry files to their exact originals.
BEFORE_HARVEST_PARENT_OBJ=H.Trace.obj
BEFORE_HARVEST_PARENT_NEAR=H.Trace.near
def obj_harvest_parent(self,q,context=None):
 if isinstance(q,dict) and all(k in q for k in ['original','snapshot','sha256']):
  p=Path(q['snapshot']);original=Path(q['original'])
  if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==q['sha256']:
   if not hasattr(self,'harvest_parent_copies'):self.harvest_parent_copies={}
   self.harvest_parent_copies[str(p)]=(str(original),q['sha256'])
   marker=('harvest-parent-json28',str(p),q['sha256'])
   if p.suffix=='.json' and marker not in self.seen:
    self.seen.add(marker);data=json.loads(H.evidence(p).read_text())
    if isinstance(data,dict) and data and all(str(k).isdigit() for k in data):
     selected=str(context or self.n)
     if selected in data:self.obj(data[selected],int(selected))
     else:self.issues.append('copied source index missing count '+selected+' '+str(p))
    else:self.obj(data,context)
 return BEFORE_HARVEST_PARENT_OBJ(self,q,context)
def near_harvest_parent(self,path):
 p=Path(path)
 if not p.is_absolute():p=S/p
 match=getattr(self,'harvest_parent_copies',{}).get(str(p))
 if match and p.suffix=='.csv':
  original=Path(match[0]);marker=('harvest-parent-csv28',str(p))
  if marker in self.seen:return
  if original.is_file() and hashlib.sha256(original.read_bytes()).hexdigest()==match[1]:
   self.seen.add(marker);H.evidence(p)
   counts=set()
   with p.open() as f:
    for row in csv.DictReader(f):
     counts.add(int(row['n']))
     if len(counts)>1:break
   self.parts.append('verified ancestry copy '+str(p)+' equals original '+str(original)+' sha256 '+match[1])
   if len(counts)>1:return  # Its count-specific source index and join descriptors supply the donor counts.
   n=next(iter(counts))
   alternatives=[Path(v[0]) for v in getattr(self,'harvest_parent_copies',{}).values() if v[1]==match[1] and '/near/' in v[0] and Path(v[0]).is_file() and hashlib.sha256(Path(v[0]).read_bytes()).hexdigest()==match[1]]
   if alternatives:self.near(str(alternatives[0]));return
   if re.match(r'\d+',original.name) and '/work/' in str(original):self.near(str(original));return
   self.file(str(original),n);return
 return BEFORE_HARVEST_PARENT_NEAR(self,str(p))
H.Trace.obj=obj_harvest_parent
H.Trace.near=near_harvest_parent

# Older forensics origins store a framed geometry digest, not a byte SHA.
BEFORE_LEGACY_DIGEST_FILE=H.Trace.file
def file_legacy_digest(self,path,n,source=None):
 p=Path(path)
 if not p.is_absolute():p=S/p
 origin=Path(str(p)+'.origin.json')
 if origin.is_file():
  obj=json.loads(origin.read_text())
  if obj.get('digest') and not obj.get('snapshot_sha256'):
   marker=('legacy-frame-digest28',str(p),n)
   if marker in self.seen:return
   self.seen.add(marker)
   try:
    import numpy as np,forensics_compose as fc
    from light29 import load
    from geometry_zero_control29 import key
    assert int(obj['n'])==n and p.is_file()
    a=load(str(p),{n})[n];_,framed=fc.frame(np.asarray(a,dtype=np.float64))
    assert hashlib.sha256(np.round(framed,12).tobytes()).hexdigest()==obj['digest'],'archived geometry digest differs'
    original=Path(obj['path'])
    if not original.is_absolute():original=S/original
    assert original.is_file(),'recorded original is missing'
    b=load(str(original),{n})[n]
    assert key(a,12)==key(b,12),'recorded original geometry changed'
    H.evidence(p);H.evidence(origin);H.evidence(original)
    self.parts.append('legacy framed digest verified '+str(p)+' '+obj['digest']+'; original geometry matches '+str(original))
    self.file(str(original),n);return
   except Exception as e:
    self.issues.append('legacy origin unresolved '+str(p)+' '+repr(e));return
 return BEFORE_LEGACY_DIGEST_FILE(self,str(p),n,source)
H.Trace.file=file_legacy_digest

# Pin the source tables used by the resolver, including tables cached at import.
BEFORE_TABLE_PIN_HIST29=H.Trace.hist
def hist_with_table_pin29(self,k,n):
 filename,_=H.held(k,n)
 table=R/'results'/filename
 if table.is_file():H.evidence(table)
 else:
  for table in [S/'seeds/merged0.tsv',S/'seeds/couzo.tsv']:
   if table.is_file():H.evidence(table)
 return BEFORE_TABLE_PIN_HIST29(self,k,n)
H.Trace.hist=hist_with_table_pin29
BEFORE_NOTICE_PIN_PUBLIC29=H.Trace.public
def public_with_notice_pin29(self,ref,n,text):
 parent=H.PATHS.get(ref)
 if parent and (Path(parent)/'meta.json').is_file():H.evidence(Path(parent)/'meta.json')
 for table in R.glob('results/harvest-sources-*.tsv'):H.evidence(table)
 if ref=='Samanyu-dev/squares_in_squares':
  for table in [S/'seeds/merged0.tsv',S/'seeds/couzo.tsv']:
   if table.is_file():H.evidence(table)
 return BEFORE_NOTICE_PIN_PUBLIC29(self,ref,n,text)
H.Trace.public=public_with_notice_pin29

# The r29 brief identifies the held801 as our layout. A missing historical row
# must not assign it the unrelated public-first row from the old harvest index.
BEFORE_OWN801_HELD29=H.held
def held_own801_29(k,n):
 filename,row=BEFORE_OWN801_HELD29(k,n)
 if n==801 and filename=='harvest-best-2026-11-07.tsv' and 'prvsiyan/squares-verified-best-of-1105' in row.get('source',''):
  return 'round29 own801 declaration',dict(source='own held packing n = 801, original own-discovered Samanyu-dev/squares_in_squares seed',licence='Own layout and original seed, round29 brief rule3')
 return filename,row
H.held=held_own801_29

# Early frozen take rows are not in the round25 assembler's SN snapshot.
BEFORE_EARLY_TAKE_FILE29=H.Trace.file
def file_early_take29(self,path,n,source=None):
 p=Path(path)
 if not p.is_absolute():p=S/p
 m=re.fullmatch(r'take-[a-z0-9-]+-r(\d+)',p.parent.name)
 if source is None and m and int(m[1])<=22 and p.name==f'{n}.csv':
  ledger=p.parent/'take.tsv'
  if ledger.is_file():
   selected=next((row for row in rows(ledger) if int(row['n'])==n),None)
   if selected:
    marker=('early-frozen-take29',str(p),n)
    if marker in self.seen:return
    self.seen.add(marker);H.evidence(ledger)
    self.add(selected['source'],n,f'{p.parent.name} archived donor n = {n}')
    self.lic.append(selected.get('licence',''));return
 return BEFORE_EARLY_TAKE_FILE29(self,str(p),n,source)
H.Trace.file=file_early_take29

# Round23 kept kick inputs with a sibling TAG-source-proof.json.
def own23_source29(path,proof):
 q=json.loads(Path(proof).read_text())
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==q['input_sha256'],'archived classfill input hash differs'
 assert q.get('source') and q.get('licence'),'archived classfill source missing'
 return q
BEFORE_OWN23_NEAR29=H.Trace.near
def near_own23_29(self,path):
 p=Path(path)
 if not p.is_absolute():p=S/p
 match=re.search(r'/take-classfill-r23/work/(\d+)-(x[0-9a-f]+)\.csv$',str(p))
 if match:
  proof=p.parent/(match[2]+'-source-proof.json')
  if p.is_file() and proof.is_file():
   marker=('classfill-input23',str(p))
   if marker in self.seen:return
   self.seen.add(marker)
   try:q=own23_source29(p,proof)
   except AssertionError as e:self.issues.append(str(e)+' '+str(p));return
   H.evidence(p);H.evidence(proof);self.add(q['source'],int(match[1]),'exact classfill r23 input');self.lic.append(q['licence']);return
 return BEFORE_OWN23_NEAR29(self,str(p))
H.Trace.near=near_own23_29

BEFORE_926_ARCHIVE_NEAR29=H.Trace.near
def near_926_archives29(self,path):
 from archive926_29 import legacy_record,exact_wire
 p=Path(path)
 if not p.is_absolute():p=S/p
 if p.parent==S/'take-forensics-r23/work/donors' and p.name.startswith('989-'):
  record=legacy_record(p)
  if record:
   marker=('exact989-archive29',str(p))
   if marker in self.seen:return
   self.seen.add(marker)
   for q in record['pins']:H.evidence(q)
   self.add(record['source'],989,'hash-verified archived989');self.lic.append(record['licence']);return
 wires={str(S/'take-family-r23/work/unread/926-fon23.csv'):(926,S/'take-forensics-r23/work/received/raw-933cf8da1fd48e336b5691e8.csv'),str(S/'take-forensics-r24/near/989-rect.csv'):(989,S/'take-forensics-r24/work/received/raw-2eb3b536ca89f23d466039c5.csv')}
 if str(p) in wires:
  marker=('exact926-wire29',str(p))
  if marker in self.seen:return
  self.seen.add(marker);n,wire=wires[str(p)]
  actual=p if p.exists() else S/'take-forensics-r24/work/quarantine/989-rect.csv'
  record=exact_wire(actual,n,wire)
  for q in record['pins']:H.evidence(q)
  self.obj(record['metadata'],n);return
 if p==S/'take-family-r22/work/unread/807-fon22.csv':
  other=S/'take-forensics-r22/near/807-rect.csv'
  assert p.read_bytes()==other.read_bytes(),'807 unread copy changed'
  marker=('exact807-alias29',str(p))
  if marker in self.seen:return
  self.seen.add(marker);H.evidence(p);H.evidence(other);self.near(str(other));return
 return BEFORE_926_ARCHIVE_NEAR29(self,str(p))
H.Trace.near=near_926_archives29

BEFORE_PUBLISHED989_FILE29=H.Trace.file
def file_published989_29(self,path,n,source=None):
 p=Path(path)
 if not p.is_absolute():p=S/p
 if source is None and n==989 and p==S/'take-family-r23/989.csv':
  marker=('published-family989-first29',989)
  if marker in self.seen:return
  self.seen.add(marker)
  receipt=S/'take-family-r23/work/published-989-first.json';packing=S/'take-family-r23/work/certified/989.csv';row=json.loads(receipt.read_text())
  from archive926_29 import framed
  from light29 import load,side
  assert int(row['n'])==989 and abs(side(load(str(packing),{989})[989])/math.sqrt(989)-1-float(row['new']))<1e-14
  assert framed(packing,989)=='ee7c3cd24175bdd05a9865a475560fc0698dc0d592eb58b17854102781238fd0'
  for q in [receipt,packing]:H.evidence(q)
  for raw in row.get('remote_quench_files',[]):
   q=S/'take-family-r23/work'/raw
   assert q.is_file() and framed(q,989)==framed(packing,989)
   H.evidence(q)
  self.add(row['source'],989,'published family989 exact archive');self.lic.append(row['licence']);return
 return BEFORE_PUBLISHED989_FILE29(self,str(p),n,source)
H.Trace.file=file_published989_29

BEFORE_INTAKE_SIDECAR_FILE29=H.Trace.file
def file_intake_sidecar29(self,path,n,source=None):
 p=Path(path)
 if not p.is_absolute():p=S/p
 side=Path(str(p)+'.json')
 if source is None and p.is_file() and side.is_file():
  data=json.loads(side.read_text())
  expected=data.get('origin_sha256_at_intake') if isinstance(data,dict) else None
  if expected and data.get('source') and data.get('licence'):
   assert int(data['n'])==n and hashlib.sha256(p.read_bytes()).hexdigest()==expected,'intake sidecar hash or count differs'
   marker=('intake-sidecar29',str(p),expected)
   if marker in self.seen:return
   self.seen.add(marker);H.evidence(p);H.evidence(side);self.obj(data,n);return
 return BEFORE_INTAKE_SIDECAR_FILE29(self,str(p),n,source)
H.Trace.file=file_intake_sidecar29
BEFORE_412_COPY_NEAR29=H.Trace.near
def near_412_intake_copy29(self,path):
 p=Path(path)
 if not p.is_absolute():p=S/p
 target=S/'take-harvest-r29/work/ancestry-inputs/412-rect-5781aaf118f57d11.csv'
 if p==target:
  other=S/'take-twoshort-r29/work/starts/forensics-412-8df61918.csv'
  assert p.read_bytes()==other.read_bytes(),'412 intake alias bytes differ'
  H.evidence(p);self.file(str(other),412);return
 return BEFORE_412_COPY_NEAR29(self,str(p))
H.Trace.near=near_412_intake_copy29
