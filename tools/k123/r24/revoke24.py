import pathlib,json,csv,re,subprocess,time,tarfile,os
from provenance24 import W,S,banned
bad={};updates=[]
for p in list(W.glob('fresh*/sources-*.json'))+list(W.glob('defer*/sources-*.json')):
 try:m=json.load(open(p))
 except ValueError:continue
 ns=[];changed=False
 for nn,c in m.items():
  # A candidate geometry remains admissible unless the origin itself was withdrawn.
  txt=json.dumps(c)
  if banned(c.get('origin','')) or banned(txt):
   ns.append(int(nn));c['clean']=False;c['refused_reason']='withdrawn or forbidden ancestry'
  elif c.get('refused_reason')=='withdrawn or forbidden ancestry':
   c['clean']=True;c.pop('refused_reason',None);changed=True
 if ns:bad[p.parent.name]=ns
 if ns or changed:p.write_text(json.dumps(m));updates.append(p)
(W/'revoked24.json').write_text(json.dumps(bad,indent=2))
with tarfile.open(W/'revoke24.tgz','w:gz') as t:
 for p in updates:t.add(p,arcname=p.name)
 t.add(W/'revoked24.json',arcname='revoked24.json')
print('revoked pools',len(bad),'donor instances',sum(map(len,bad.values())),flush=True)
subprocess.run(['scp','-q',str(W/'revoke24.tgz'),'boxE:scratch/squares-k123/'],check=True)
subprocess.run(['ssh','boxE','cd $SCRATCH/squares-k123 && tar xzf revoke24.tgz && rm revoke24.tgz'],check=True)
