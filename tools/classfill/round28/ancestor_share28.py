"""Check pinned bytes. Own ancestor layouts no longer have a share gate."""
from common28 import *
from share_policy28 import POLICY
def inspect(closure):
 a=read(closure,{});errors=[]
 for q in a.get('snapshots',[])+a.get('expanded',{}).get('history',{}).get('snapshots',[]):
  p=Path(q['snapshot'])
  if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=q['sha256']:errors.append(dict(path=q['path'],error='snapshot hash differs or file missing'))
 return dict(time=now(),closure=str(closure),policy=POLICY,checks=[],excluded=[],errors=errors)
