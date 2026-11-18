"""Collect source ledgers and sidecars for a completed result without changing inputs."""
from pathlib import Path
import json,re,hashlib,csv,sys
csv.field_size_limit(16000000)
W=Path(__file__).parent;B=W.parent.parent;sys.path.insert(0,str(W));from source24 import BANNED
seen=set();records=[];banned=[]
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for k,v in x.items():
   if k in ['source','src','licence','modules','parts','parent','donor','inputs','source_metadata','source_record','raw','parent_path','admission','evidence','record','original_file','snapshot','A','B']:yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
def visit(p):
 p=Path(p)
 if str(p) in seen or not p.exists():return
 seen.add(str(p));record=dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
 if p.suffix=='.json':
  try:d=json.load(open(p))
  except ValueError:return
  ss=list(strings(d));record['metadata']=d if len(p.read_bytes())<50000 else ss
  for s in ss:
   if BANNED.search(s):banned.append(dict(path=str(p),match=BANNED.search(s)[0]))
   for path in re.findall(r'$DATA/[^\s,;<>"\)\\]+\.(?:csv|json)',s):visit(path)
 elif p.suffix=='.csv':
  for q in [p.with_suffix('.json'),Path(str(p)+'.json')]:visit(q)
  tp=p.parent/'take.tsv'
  if tp.exists() and p.stem.isdigit():
   for r in csv.DictReader(open(tp),delimiter='\t'):
    if r['n']==p.stem:
     record['ledger']=r
     for s in [r['source'],r.get('licence','')]:
      if BANNED.search(s):banned.append(dict(path=str(tp),match=BANNED.search(s)[0]))
      for path in re.findall(r'$DATA/[^\s,;<>"\)\\]+\.(?:csv|json)',s):visit(path)
 records.append(record)
if __name__=='__main__':
 p=Path(sys.argv[1]);visit(p);text=json.dumps(records)
 out=dict(start=str(p),records=records,excluded_roots=banned,own_staircase_root='staircase corner (our own design)' in text,own_taper_root='taper enumeration (our own design)' in text)
 target=Path(sys.argv[2]);target.parent.mkdir(exist_ok=True);target.write_text(json.dumps(out,indent=2));print(json.dumps(dict(records=len(records),excluded_roots=banned,own_staircase_root=out['own_staircase_root'],own_taper_root=out['own_taper_root'])))
