"""Bind legacy gathered packings to their exact accepted gate and source history."""
import csv,hashlib,json,pathlib,re
S=pathlib.Path('$SCRATCH/bounties-squares');_validated={}

def accepted(path,n,policy,expected=None):
 p=pathlib.Path(path);m=re.fullmatch(r'round(\d+)-2026-(\d\d)-(\d\d)([a-z])\.csv',p.name)
 if not m or p.parent!=S/'gather'or not p.is_file():return None
 rnd=int(m[1]);gate=S/f'gate/cand-round{rnd}-{m[2]}{m[3]}{m[4]}'
 try:
  manifest=json.load(open(gate/'gate.json'))if expected is None else expected
  if manifest.get('file')!=str(p)or manifest.get('verdict')!='GREEN':return None
  stamp=(str(p),p.stat().st_mtime_ns,p.stat().st_size,manifest['sha256'])
  if stamp not in _validated:_validated[stamp]=hashlib.sha256(p.read_bytes()).hexdigest()==manifest['sha256']
  if not _validated[stamp]:return None
  detail=next(r for r in csv.DictReader(open(gate/'details.csv'))if int(r['n'])==n)
  # A rollback can make a round's source table newer than the held row.
  for version in range(rnd,8,-1):
   row,record=policy.held_record(n,version)
   if not row:continue
   score=row.get('score',row.get('new'))
   if score is None or abs(float(score)-float(detail['score']))>1e-10:continue
   if not row.get('source')or not row.get('licence'):continue
   return dict(row,source=row['source']+'; accepted gather gate '+str(gate/'gate.json')+' sha256 '+manifest['sha256']),record
 except (OSError,ValueError,KeyError,StopIteration):pass
 return None
