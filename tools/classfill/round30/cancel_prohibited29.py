"""Cancel only named jobs in this lane's own scratch."""
import json,os,signal,subprocess
from pathlib import Path
B=Path(__file__).resolve().parent
assert B.name=='squares-classfill-r29'
tags=json.loads((B/'prohibited-tags.json').read_text());cancelled=[]
for tag in tags:
 for p in (B/'queue').glob('*/'+tag+'.json'):
  p.rename(p.with_suffix('.cancelled'));cancelled.append(dict(tag=tag,queued=True))
 for line in subprocess.check_output(['ps','-axo','pid=,pgid=,command='],text=True).splitlines():
  a=line.split(None,2)
  if len(a)!=3 or 'lane/classfill_finish.py ' not in a[2] or '--tag '+tag+' ' not in a[2]:continue
  pid,group=map(int,a[:2])
  if group!=pid:continue
  try:os.killpg(group,signal.SIGTERM);cancelled.append(dict(tag=tag,group=group))
  except ProcessLookupError:pass
print(json.dumps(cancelled))
