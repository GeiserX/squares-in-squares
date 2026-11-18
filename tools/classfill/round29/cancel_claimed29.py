import json,os,re,signal,subprocess,sys
from pathlib import Path
B=Path(__file__).resolve().parent
assert B.name=='squares-classfill-r29'
tags=sys.argv[1:];assert all(re.fullmatch(r'x[0-9a-f]{12}',t) for t in tags)
removed=[]
for t in tags:
 for p in (B/'queue').glob('*/'+t+'.json'):p.unlink();removed.append(str(p.relative_to(B)))
info={}
for l in subprocess.check_output(['ps','-axo','pid=,ppid=,pgid=,command='],text=True).splitlines():
 a=l.split(None,3)
 if len(a)==4:
  try:pid,ppid,pgid=map(int,a[:3]);info[pid]=(ppid,pgid,a[3])
  except ValueError:pass
owned={pid for pid,q in info.items() if 'lane/classfill_finish.py' in q[2] and any('--tag '+t+' ' in q[2] for t in tags)}
for pid in list(owned):
 try:
  cwd=subprocess.check_output(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],text=True,stderr=subprocess.DEVNULL,timeout=10)
  assert any(l.startswith('n') and (Path(l[1:])==B or B in Path(l[1:]).parents) for l in cwd.splitlines())
 except Exception:owned.remove(pid)
for _ in range(20):
 extra={p for p,q in info.items() if q[0] in owned}
 if extra<=owned:break
 owned|=extra
for group in {info[p][1] for p in owned if info[p][1]!=os.getpgrp()}:
 try:os.killpg(group,signal.SIGTERM)
 except ProcessLookupError:pass
print(json.dumps(dict(tags=tags,removed=removed,stopped=sorted(owned))))
