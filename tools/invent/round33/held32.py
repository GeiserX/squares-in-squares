"""Resolve a submitted held root against its accepted gate and pinned bytes."""
import pathlib,json,hashlib,csv,re
S=pathlib.Path('$SCRATCH/bounties-squares');R=pathlib.Path('.');_cache={}
# These files are explicitly recorded as submitted in the brief or main handoff.
SUBMITTED={'round32-2026-11-16a.csv','round22-2026-11-13b.csv','round23-2026-11-13b.csv','round25-2026-11-14b.csv','round30-2026-11-15c.csv','round31-2026-11-16b.csv'}
_witness_cache={}
def held_witness(p,n):
 if p.name in SUBMITTED:return str(p)
 # The round23 a candidate was never submitted. Only identical rows of b are held.
 if p.name!='round23-2026-11-13a.csv':return None
 witness=p.with_name('round23-2026-11-13b.csv');key=(str(p),n)
 if key not in _witness_cache:
  def values(path):return sorted(tuple(float(str(r[k]).removeprefix('s'))for k in ('x','y','angle'))for r in csv.DictReader(open(path))if int(r['n'])==n)
  _witness_cache[key]=values(p)==values(witness)
 return str(witness)if _witness_cache[key]else None

def resolve(root):
 p=pathlib.Path(root.get('path',''));n=int(root.get('n',0));m=re.fullmatch(r'round(\d+)-2026-(\d\d)-(\d\d)([a-z])\.csv',p.name)
 if not m or p.parent!=S/'gather'or not n:return None
 gate=S/f'gate/cand-round{m[1]}-{m[2]}{m[3]}{m[4]}'
 try:
  d=json.load(open(gate/'gate.json'));stamp=(str(p),p.stat().st_mtime_ns,p.stat().st_size,d['sha256'])
  if stamp not in _cache:_cache[stamp]=hashlib.sha256(p.read_bytes()).hexdigest()==d['sha256']and d.get('verdict')=='GREEN'and d.get('file')==str(p)
  if not _cache[stamp]:return None
  witness=held_witness(p,n)
  if not witness:return None
  if witness!=str(p):
   match=re.fullmatch(r'round(\d+)-2026-(\d\d)-(\d\d)([a-z])\.csv',pathlib.Path(witness).name)
   wg=S/f'gate/cand-round{match[1]}-{match[2]}{match[3]}{match[4]}/gate.json'
   wm=json.load(open(wg))
   if wm.get('verdict')!='GREEN'or wm.get('file')!=witness or hashlib.sha256(pathlib.Path(witness).read_bytes()).hexdigest()!=wm['sha256']:return None
  if root.get('sha256')and root['sha256']!=d['sha256']:return None
  row=next(x for x in csv.DictReader(open(gate/'details.csv'))if int(x['n'])==n)
  if row.get('reason','ok')!='ok':return None
  ledger=R/f'results/round{m[1]}-best-2026-{m[2]}-{m[3]}.tsv'
  if not ledger.is_file():return None
  return dict(root,held_witness_file=witness,source=f'our own construction: submitted held row n={n}, accepted {p} sha256 {d["sha256"]}; historical source and licence in {ledger} n={n}',licence='our own held packing; upstream terms in '+str(ledger),ledger=str(ledger))
 except (OSError,ValueError,KeyError,StopIteration):return None

_groups={}
def projection(p,n):
 p=pathlib.Path(p)
 for side in (pathlib.Path(str(p)+'.json'),p.with_suffix('.json')):
  try:d=json.load(open(side))
  except (OSError,ValueError):continue
  base=d.get('held_file',d.get('path',''));digest=d.get('held_sha256',d.get('sha256',''))
  root=resolve(dict(path=base,n=n,sha256=digest))
  if not root:continue
  if int(d.get('n',n))!=n:continue
  actual=hashlib.sha256(p.read_bytes()).hexdigest()
  expected=d.get('row_sha256',d.get('sha256')if d.get('held_file')else None)
  if expected and expected!=actual:continue
  if base not in _groups:
   groups={}
   for row in csv.DictReader(open(base)):groups.setdefault(int(row['n']),[]).append(row)
   _groups[base]=groups
  def values(rows):return sorted(tuple(float(str(r[k]).removeprefix('s'))for k in ('x','y','angle'))for r in rows)
  if values(csv.DictReader(open(p)))!=values(_groups[base][n]):continue
  return root['source'],root['licence'],root['ledger']
 return None
