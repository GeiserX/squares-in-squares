import sys,re,json,csv,pathlib,hashlib
sys.path.insert(0,'.')
import forensics_policy as fp
RELAXED=fp.RELAXED
S=pathlib.Path('$SCRATCH/bounties-squares')

CACHE=pathlib.Path('$SCRATCH/bounties-squares/take-invent-r24/work/policy-cache.json')
try:_cache=json.load(open(CACHE))
except (OSError,ValueError):_cache={}
def save_cache():
 CACHE.with_suffix('.tmp').write_text(json.dumps(_cache));CACHE.with_suffix('.tmp').replace(CACHE)

def classify(src,lic):
 key=hashlib.sha256(('v3:'+src+'\0'+lic).encode()).hexdigest()
 if key in _cache:return _cache[key]
 text=src+' '+lic
 text=re.sub(r'Samanyu(?:-dev)?(?: seed)? ancestry:\s*(?:no|none)\b(?:\s*\([^)]*\))?', '',text,flags=re.I)
 p=fp.classify_text(text);seeds=set(p['seeds'])
 for m in re.finditer(r'(?i)Samanyu[^;\n]{0,130}?seed\s+n\s*=\s*([\d, ]+)',text):seeds.update(map(int,re.findall(r'\d+',m[1])))
 # The named module aliases retain their seed count even when the old notice says merged0.
 for m in re.finditer(r'(\d{2,4})[a-z0-9_.~-]*\s*<held:\s*seed merged0',text,re.I):
  n=int(m[1])
  if n in {365,503,504,755,804,811,861,934,983}:seeds.add(n)
 if seeds:p={'status':'seeds','seeds':sorted(seeds)}
 elif 'seed merged0' in text:p={'status':'unknown','seeds':[]}
 if not src.strip() or lic.strip() in ('','see source','ours, on: see source'):
  # A full source appendix with named roots still permits a known seeded group.
  if p['status']=='none':p={'status':'unknown','seeds':[]}
 _cache[key]=p
 return p

def annotate(src,lic):
 p=classify(src,lic);tag='; invent source group: '+fp.label(p)
 return src,lic if lic.endswith(tag) else lic+tag

def bars(take_dir):
 from ancestry24 import clean
 a={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round23-1113a/details.csv'))}
 b={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round22-1113b/details.csv'))}
 allbar=dict(a);freebar=dict(b);owners={};freeowners={}
 for file in sorted(S.glob('take-*-r24/take.tsv')):
  if file.parent==pathlib.Path(take_dir):continue
  for r in csv.DictReader(open(file),delimiter='\t'):
   try:n=int(r['n']);score=float(r['new']);p=classify(r['source'],r['licence'])
   except (ValueError,KeyError):continue
   if score<allbar[n]:allbar[n]=score;owners[n]=file.parent.name
   if p['status']=='none' and score<freebar[n]:freebar[n]=score;freeowners[n]=file.parent.name
 return a,b,allbar,freebar,owners,freeowners
