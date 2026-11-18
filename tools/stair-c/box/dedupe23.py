import csv,glob,json,os,shlex
import sys
sys.path.insert(0,'.')
import fresh23
sys.path.insert(0,'lane')
from modules_round22 import CLOSED_CORNERS
old=fresh23.old; seen=set(); out=[];drops=0
p='q.txt';st=os.stat(p)
for s in open(p):
 try:
  a=shlex.split(s)
  if 'job' in a and any(x.endswith('/modules.py') for x in a):
   k=a.index('job');key=(int(a[k+5]),a[k+6],a[k+7],a[k+8],int(a[k+9]),int(a[k+10]))
   pool=a[k+1];identity=(pool,)+key
   if key[1] in CLOSED_CORNERS or (pool=='libbase' and key in old) or identity in seen:drops+=1;continue
   seen.add(identity)
 except (ValueError,IndexError):pass
 out.append(s)
now=os.stat(p)
if (st.st_size,st.st_mtime_ns)==(now.st_size,now.st_mtime_ns):
 open(p+'.dedupe','w').writelines(out);os.replace(p+'.dedupe',p)
print('DEDUPE removed',drops,'kept',len(out),flush=True)
