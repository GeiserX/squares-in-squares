"""Check actual pinned ancestor packings, keeping count-specific pool contexts."""
from common27 import *
from prvsim27 import check
CACHE=W/'ancestor-share';CACHE.mkdir(exist_ok=True)
def inspect(closure):
 data=Path(closure).read_bytes();cache=CACHE/(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:12]+'-'+hashlib.sha256(data).hexdigest()+'.json')
 if cache.exists():return read(cache)
 a=json.loads(data);text=a.get('source','')+'\n'+'\n'.join(a.get('expanded',{}).get('history',{}).get('parts',[]))
 wanted={}
 # Pool donor counts are explicitly recorded in each join description.
 for match in re.finditer(r'immutable input pool ([^;\s<>]+\.csv)',text):
  start=text.rfind('k123_join.py',0,match.start());piece=text[max(0,start):match.start()]
  ns={int(n) for n in re.findall(r'\bn\s*=\s*(\d+) from ',piece)}
  wanted.setdefault(match[1],set()).update(ns)
 checks=[];errors=[]
 for q in a.get('snapshots',[]):
  p=Path(q['path'])
  if p.suffix.lower()!='.csv':continue
  snap=Path(q['snapshot']);ns=set(wanted.get(str(p),set()))
  # A per-n CSV is unambiguous. A multi-n ledger is checked only at recorded donor counts.
  try:
   with snap.open() as f:
    rr=csv.DictReader(f)
    if not {'x','y'}<=set(rr.fieldnames or []) or not ({'n','id'}&set(rr.fieldnames or [])):continue
    found=set()
    for row in rr:
     n=int(row['n']) if 'n' in row else int(row['id'].split('_')[0]);found.add(n)
     if len(found)>1:break
   if len(found)==1:ns|=found
   elif not ns:
    name=re.match(r'(\d+)(?:[-.]|$)',p.name)
    if name:ns.add(int(name[1]))
   for n in sorted(ns):
    if n<100:continue
    r=check(str(snap),n);assert r['n']==n
    checks.append(dict(n=n,original=str(p),snapshot=str(snap),sha256=q['sha256'],share=r['share'],excluded=r['excluded']))
  except (OSError,ValueError,KeyError,AssertionError,csv.Error) as e:errors.append(dict(path=str(p),error=repr(e)))
 # Original seed rows have one stable, retained per-count source, selected by the assembler's seed resolver.
 sys.path.insert(0,str(S/'take-assemble-r21/bin'))
 from seedsrc import src as seed_source
 for ref,n in a.get('expanded',{}).get('history',{}).get('public',[]):
  if n<100 or ref not in ['Samanyu-dev/squares_in_squares','franciscouzo/square-packing'] or ref not in seed_source(n):continue
  p=S/'seeds/merged0.csv';pin=blob(p);r=check(pin['snapshot'],n)
  checks.append(dict(n=n,original=str(p),snapshot=pin['snapshot'],sha256=pin['sha256'],share=r['share'],excluded=r['excluded'],seed_ref=ref))
 result=dict(time=now(),closure=str(closure),checks=checks,excluded=[r for r in checks if r['excluded']],errors=errors)
 tmp=cache.with_name(cache.name+'.'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(result)+'\n');os.replace(tmp,cache);return result
if __name__=='__main__':
 for p in sys.argv[1:]:
  r=inspect(p);print(json.dumps(dict(closure=p,checks=len(r['checks']),excluded=r['excluded'],errors=r['errors'])))
