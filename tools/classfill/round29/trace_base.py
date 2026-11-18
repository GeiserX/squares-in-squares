import csv,json,re,sys,shutil,hashlib
from pathlib import Path
csv.field_size_limit(10**9)
S=Path('$SCRATCH/bounties-squares');O=S/'take-assemble-r25'/'trace';R=Path('results');E=Path('$SCRATCH/bounties-squares/take-classfill-r29/work/evidence');E.mkdir(exist_ok=True)
APA='Apache 2.0 (Kaggle default for public notebooks)'
def tab(p):return {int(r['n']):r for r in csv.DictReader(p.open(),delimiter='\t')}
T={int(re.search(r'round(\d+)',p.name)[1]):(p.name,tab(p)) for p in R.glob('round*-best-*.tsv') if int(re.search(r'round(\d+)',p.name)[1])<=23}
H={name:tab(R/name) for name in ['harvest-best-2026-11-07.tsv','harvest-best-2026-11-09.tsv','angle-harvest-2026-11-10.tsv','harvest-best-2026-11-11.tsv']}
SN={d.name:tab(d/'take.tsv') for d in (S/'take-assemble-r25'/'snap').glob('take-*') if (d/'take.tsv').exists()}
sys.path.insert(0,str(S/'take-assemble-r21/bin'))
from seedsrc import src as seedfile
NUM=re.compile(r'(?:n\s*=\s*(\d+)|\b(\d+)[a-z]+\d*[a-z]*\.[A-Z]|held (\d+)\b|held n\s*=\s*(\d+)|of n = (\d+)|donor(\d+)|seed(\d+))')
META={};LIC={};PATHS={}
for p in sorted(R.glob('harvest-sources-*.tsv')):
 for r in csv.DictReader(p.open(),delimiter='\t'):LIC[r['ref']]=r['licence']
for b in sorted(S.glob('harvest*'))+[S/'take-harvest-r22/work/public/data',S/'take-harvest-r23/work/public/data',S/'take-harvest-r24/work/public/data',S/'take-harvest-r24/work/public2/data']:
 if not b.is_dir():continue
 for k in ['nb','ds']:
  for p in (b/k).glob('*/meta.json'):
   try:m=json.loads(p.read_text());ref=m['ref'];LIC[ref]=m['license'];META[ref]=m;PATHS[ref]=p.parent
   except (KeyError,ValueError):pass
LIC.update({'franciscouzo/square-packing':'MIT','Samanyu-dev/squares_in_squares':'no licence stated upstream (inherited seed coordinates; source credited)'})
def evidence(p):
 p=Path(p)
 if not p.is_file():return None
 tag=hashlib.sha256(str(p).encode()).hexdigest()[:12]+'-'+p.name
 dest=E/tag
 if not dest.exists():shutil.copy2(p,dest)
 return dest

def held(k,n):
 for j in sorted(T,reverse=True):
  if j<=k and n in T[j][1]:return T[j][0],T[j][1][n]
 for name in ['harvest-best-2026-11-11.tsv','angle-harvest-2026-11-10.tsv','harvest-best-2026-11-09.tsv','harvest-best-2026-11-07.tsv']:
  if n in H[name] and H[name][n]['source']!='seed merged0':return name,H[name][n]
 return 'original seed',dict(source=f'n = {n} of {seedfile(n)}',licence=seedfile(n))
SEED=re.compile(r'seed merged0(?: \(Couzo\x27s MIT catalogue or Samanyu-dev/squares_in_squares, results/harvest-best-2026-11-09\.tsv\)| \(Couzo, MIT; Samanyu-dev, no licence; README, Outside data\)|, see README \(Couzo MIT; Samanyu-dev, no licence\)| \(Couzo MIT; Samanyu-dev, no licence\)|, see README| \(see README\))?')
def fixseed(text,n):
 out=[];last=0
 for m in SEED.finditer(text):
  ms=list(NUM.finditer(text[:m.start()]));k=int(next(g for g in ms[-1].groups() if g)) if ms else n
  f,r=('original seed',dict(source=f'n = {k} of {seedfile(k)}',licence=seedfile(k))) if k in [503,504,934] else held(9,k);out.extend([text[last:m.start()],f"{r['source']} [{r['licence']}; {f}, donor n = {k}]"]);last=m.end()
 out.append(text[last:]);return ''.join(out)

class Trace:
 def __init__(self,n):self.n=n;self.parts=[];self.seen=set();self.refs=set();self.lic=[];self.issues=[];self.checked=[]
 def add(self,s,n=None,label=''):
  if not s:return
  n=self.n if n is None else n
  s=fixseed(s,n)
  s=re.sub(r'ahead of the best public file \"[^\"]*\"','',s)
  key=('text',n,s)
  if key in self.seen:return
  self.seen.add(key)
  if len(self.seen)>1500:raise RuntimeError('trace explosion')
  self.parts.append((label+': ' if label else '')+s)
  # Structured window manifests preserve the donor n independently of the target n.
  for m in re.finditer(r'(?:rectangle windows |rectangle windows: )(?=\{)',s):
   try:q,_=json.JSONDecoder().raw_decode(s[m.end():]);self.obj(q)
   except (ValueError,TypeError):pass
  # Explicit held references.
  pats=[(r'round (\d+) packing of n\s*=\s*(\d+)',False),(r'n\s*=\s*(\d+) from held round\s*(\d+)',True),(r'held n\s*=\s*(\d+) of round (\d+)',True),(r'n\s*=\s*(\d+) of round (\d+)',True),(r'held round\s*(\d+) n\s*(\d+)',False)]
  for pat,flip in pats:
   for a,b in re.findall(pat,s):self.hist(int(b) if flip else int(a),int(a) if flip else int(b))
  for nn,kk in re.findall(r'\b(\d+)h(\d*)\.[A-Z]',s):
   if not kk and int(nn) in [503,504,934] and 'original seed' in s:
    self.add(f'n = {nn} of {seedfile(int(nn))}',int(nn),'original seed module')
   else:self.hist(int(kk) if kk else 9,int(nn))
  for nn in re.findall(r'the held (?:packing of )?n\s*=\s*(\d+)',s):
   # Earlier donor labels are resolved by their own module or retained table.
   pass
  for nn,d in re.findall(r'n\s*=\s*(\d+) from (?:$SCRATCH/bounties-squares/)?(take-[a-z0-9-]+-r[0-9]+)/[^ /,;)]+\.csv',s):
   if d in SN and int(nn) in SN[d]:
    q=SN[d][int(nn)];self.add(q['source'],int(nn),f'{d} donor n = {nn}');self.lic.append(q.get('licence',''))
   else:self.file(str(S/d/f'{nn}.csv'),int(nn))
  # Near copies and module inputs require their retained sidecars or source ledger.
  for p in re.findall(r'(?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/(?:near|work/unread)/[^\s<>;,()"\]]+\.csv',s):self.near(p)
  for d,p in re.findall(r'(take-[a-z0-9-]+-r\d+) (near/[^\s<>;,()"\]]+\.csv)',s):self.near(d+'/'+p)
  # Match real registered refs only. This excludes paths and citation-only refs.
  proofns=[]
  for pp in re.findall(r'(?:$SCRATCH/bounties-squares/)?take-harvest-r22/work/collector/remote-[a-f0-9]+\.json',s):
   pp=Path(pp);pp=pp if pp.is_absolute() else S/pp
   if pp.is_file():proofns.append(int(json.loads(evidence(pp).read_text())['n']))
  for ref in LIC:
   if ref=='jonathan1506/joegun-squares-packings':continue
   if re.search(re.escape(ref)+r'(?![A-Za-z0-9_.-])',s):
    self.refs.add(ref)
    for m in re.finditer(re.escape(ref)+r'(?![A-Za-z0-9_.-])',s):
     ms=list(NUM.finditer(s[:m.start()]));dn=int(next(g for g in ms[-1].groups() if g)) if ms else (proofns[0] if len(set(proofns))==1 else n)
     walk=list(re.finditer(r'from(\d+)-r\d+h',s[:m.start()]))
     nums=list(NUM.finditer(s[:m.start()]))
     if walk and (not nums or walk[-1].start()>nums[-1].start()):dn=int(walk[-1][1])
     if ref=='areebbb/sis-certified-union-micro-shrink-lb-22-17479':
      proof=re.search(r'(?:$SCRATCH/bounties-squares/)?take-harvest-r22/work/collector/remote-[a-f0-9]+\.json',s[m.end():m.end()+650])
      if proof:
       pp=Path(proof[0]);pp=pp if pp.is_absolute() else S/pp
       if pp.is_file():dn=int(json.loads(evidence(pp).read_text())['n'])
     self.public(ref,dn,s)
 def hist(self,k,n):
  if not 1<=n<=1000:return
  key=('held',k,n)
  if key in self.seen:return
  self.seen.add(key);f,r=held(k,n);self.lic.append(r['licence']);self.add(r['source'],n,f'held n = {n} of round {k} ({f})')
 def obj(self,q,context=None):
  if isinstance(q,list):
   for v in q:self.obj(v,context)
  elif isinstance(q,dict):
   n=q.get('n',context or self.n)
   try:n=int(n)
   except (ValueError,TypeError):n=context or self.n
   if isinstance(q.get('source'),list) and len(q['source'])==2:
    path,dn=q['source'];dn=int(dn);n=dn;original=q.get('original_file',path)
    self.file(original,dn,q.get('source_record'))
   if isinstance(q.get('source'),str):
    mm=re.match(r'(\d+)',str(q.get('id','')))
    dn=int(mm[1]) if mm and 1<=int(mm[1])<=1000 else n
    self.add(q['source'],dn,q.get('id','module'))
   if isinstance(q.get('source_record'),str):self.add(q['source_record'],n,'retained source')
   if isinstance(q.get('licence'),str):self.lic.append(q['licence'])
   for k,v in q.items():
    if k not in ['source','source_record','licence']:self.obj(v,n)
 def file(self,path,n,source=None):
  if source:self.add(source,n,f'file {path}, donor n = {n}');return
  m=re.search(r'gather/round(\d+)-',str(path))
  if m:self.hist(int(m[1]),n);return
  if '/near/' in path or '/work/unread/' in path:self.near(path);return
  m=re.search(r'(take-[a-z0-9-]+-r[0-9]+)/(\d+)\.csv',str(path))
  if m and m[1] in SN and n in SN[m[1]]:
   q=SN[m[1]][n];self.add(q['source'],n,f'{m[1]} donor n = {n}');self.lic.append(q.get('licence',''));return
  if m and m[1] in ['take-polish-r22','take-harvest-r22']:
   p=S/f'take-harvest-r22/work/public/starts/{n}/take.tsv'
   if p.is_file():
    q=tab(evidence(p))[n];self.add(q['source'],n,f'archived public donor n = {n}');return
  if m and m[1]=='take-family-r22' and n==807:
   q=SN['take-midm-r22'][807];self.add(q['source'],807,'retained midm source for family 807');return
  self.issues.append(f'unresolved file n={n} {path}')
 def near(self,path):
  p=Path(path)
  if not p.is_absolute():p=S/p
  key=('near',str(p))
  if key in self.seen:return
  self.seen.add(key)
  dn=int(re.match(r'(\d+)',p.name)[1]);found=False
  maps=json.loads((O/'geometry-matches.json').read_text()) if (O/'geometry-matches.json').exists() else {}
  rel=str(p.relative_to(S))
  if rel in maps:
   self.obj(json.loads(evidence(maps[rel]).read_text()),dn);found=True
  specials={'take-family-r22/work/unread/810-rdn22.csv':'take-readers-r22/near/810-up1c1from753-r22h283ff6534a341951.csv','take-stair-c-r22/near/815-748fa00d-s.csv':'take-stair-c-r22/work/archive/s/raw-a/815-748fa00d.json','take-stair-c-r22/near/863-0f92c19d-n.csv':'take-stair-c-r22/work/archive/n/raw-a/863-0f92c19d.json','take-stair-c-r22/near/875-cd3a87ed-s.csv':'take-stair-c-r22/work/archive/s/raw-a/875-cd3a87ed.json','take-modules-r20/near/338-338-418hCt-3-4-plus7.9e-05.csv':'take-modules-r20/work/boxD-raw/338-418hCt-3-4.json'}
  if rel in specials:
   q=S/specials[rel]
   if q.suffix=='.json':self.obj(json.loads(evidence(q).read_text()),dn)
   else:self.near(str(q))
   found=True
  if '/work/unread/796-hv22.csv' in str(p):self.add('areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: submission.csv (donor n = 796, notebook run 369173112)',796);found=True
  if '/work/unread/793-mm22.csv' in str(p):
   q=SN['take-midm-r22'][793];self.add(q['source'],793,'midm donor 793');found=True
  for q in [p.with_suffix('.json'),Path(str(p)+'.json')]:
   if q.is_file():
    try:self.obj(json.loads(evidence(q).read_text()),dn);found=True
    except (ValueError,TypeError):pass
  d=next((x for x in p.parents if re.match('take-.*-r[0-9]+$',x.name)),None)
  if d:
   for name in ['near.tsv','work/near.tsv','work/sources-all.tsv','work/sources.tsv']:
    q=d/name
    if q.is_file():
     try:
      for r in csv.DictReader(evidence(q).open(),delimiter='\t'):
       if r.get('file')==p.name or r.get('donor')==p.stem or r.get('path')==str(p) or ('from' in p.stem and r.get('donor')==p.stem.split('from',1)[1]):
        if r.get('source'):self.add(r['source'],dn,f'near donor {p.name}');self.lic.append(r.get('licence',''));found=True
     except (ValueError,KeyError):pass
  if rel=='take-k123-r22/near/753-initial-809r-870.csv':
   self.add(SN['take-k123-r22'][753]['source'],753,'753 join record retained in snapshot');found=True
  if rel=='take-family-r22/work/unread/807-mmx22.csv':
   self.add(SN['take-midm-r22'][807]['source'],807,'midm 807 donor record');found=True
  if rel=='take-forensics-r20/near/644-win696-c0-25.8476303480.csv':self.hist(20,696);self.add('forensics_rect.py corner crop, n = 644 cut from held n = 696 of round 20; near-235854/list.tsv records the crop',696);evidence(S/'take-forensics-r20/work/near-235854/list.tsv');found=True
  if rel=='take-forensics-r20/near/697-win751-c0-26.8604007376.csv':self.hist(20,751);self.add('forensics_rect.py corner crop, n = 697 cut from held n = 751 of round 20; near-235854/list.tsv records the crop',751);evidence(S/'take-forensics-r20/work/near-235854/list.tsv');found=True
  if not found:self.issues.append(f'near without metadata {p}')
 def public(self,ref,n,text):
  key=('public',ref,n)
  if key in self.seen:return
  self.seen.add(key);self.checked.append((ref,n));self.lic.append(ref+', '+LIC[ref])
  # The original held far-zone chain uses its original notebook run.
  if ref=='prvsiyan/a-square-deal-research-to-verified-packings':
   p=S/'harvest-2026-11-10/nb/prvsiyan__a-square-deal-research-to-verified-packings/per_n_source_table.csv'
   rows={int(q['n']):q for q in csv.DictReader(evidence(p).open())}
   if n not in rows:self.issues.append(f'missing notebook n {ref} {n}');return
   q=rows[n];up=q['source_ref'];fn=Path(q['source_file']).name
   self.add(f'{ref} per_n_source_table.csv, donor n = {n}: {up} :: {fn}',n)
  if ref=='sigmaborov/squares-in-squares-certified-contact-polish':
   p=S/'harvest-2026-11-10/nb/sigmaborov__squares-in-squares-certified-contact-polish/baseline_source.json'
   q=json.loads(evidence(p).read_text());self.add(f"{ref} baseline_source.json, donor n = {n}: {q['kernel']} V{q['version']}",n)
   self.daily(n,old=True)
  if ref=='kmmmvs/squares-public-merge-daily' and 'V42' not in text:self.daily(n)
  if ref=='malyshevdanil/squares-in-squares-living-atlas-of-tight-packings':
   # Use the current output only for the current public pass; inherited rows name their historical output.
   p=PATHS[ref]/'submission_sources.csv'
   if not p.is_file():p=S/'harvest-2026-11-10/nb'/ref.replace('/','__')/'submission_sources.csv'
   rows={int(q['n']):q for q in csv.DictReader(evidence(p).open())}
   if n in rows:self.add(f"{ref} submission_sources.csv, donor n = {n}: {rows[n]['source']} (no earlier external file named by this per-n record)",n)
 def daily(self,n,old=False):
  key=('daily',n,old)
  if key in self.seen:return
  self.seen.add(key)
  p=S/'harvest-2026-11-10/nb/kmmmvs__squares-public-merge-daily/merge_report.json' if old else PATHS['kmmmvs/squares-public-merge-daily']/'merge_report.json'
  if not p.is_file():self.issues.append(f'missing daily report {p}');return
  q=json.loads(evidence(p).read_text());row=q['replaced_groups'].get(str(n))
  src=row['source'] if row else 'datasets/kmmmvs/squares-in-squares-private-packings/data.zip!local_bank.csv (unchanged)'
  m=re.search(r'(?:datasets|notebooks)/([^/]+/[^/]+)/(.+)',src)
  if m:
   ref,fn=m.groups();self.add(f'kmmmvs/squares-public-merge-daily'+(' V42' if old else '')+f' merge_report.json, donor n = {n}: {ref} :: {fn}',n)
   if ref in LIC:self.refs.add(ref);self.lic.append(ref+' :: '+fn+', '+LIC[ref])
   else:self.issues.append('unregistered public '+ref)
  elif src.startswith('squares-in-squares-starter-notebook/'):
   self.add(f'kmmmvs/squares-public-merge-daily merge_report.json, donor n = {n}: pablodiegoo/squares-in-squares-starter-notebook :: '+src.split('/',1)[1],n)
  else:self.issues.append('unparsed daily '+src)
