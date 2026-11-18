import csv,fcntl,hashlib,importlib.util,math,os,pickle,sys
sys.path.insert(0,'lane');import modules as M
sys.path.insert(0,'.');from cache23 import load,save
spec=importlib.util.spec_from_file_location('rank','lane/stair-c_rank.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
seed=pickle.load(open('patches/legacy52-newfar.pkl','rb'));ids={q['id'] for q in seed['mods']}
with open('cache23/LOCK','a') as h:
 fcntl.flock(h,fcntl.LOCK_SH);L,E=load('cache23')
L['mods']=[q for q in L['mods'] if q['id'] in ids or q['kind']=='far' and q['c']==9];L['layouts']=[]
for q in seed['mods']:q['ours']=True
L['mods']=[q for q in L['mods'] if q['id'] not in ids]+seed['mods'];E.update(seed['lens']);have={q['id'] for q in L['mods']};E={k:v for k,v in E.items() if k in have}
pool='lib-legacy52-nofloor';save(pool,L,E);open(pool+'/need.txt','w').write('\n'.join(sorted(ids)))
oldL,oldE=load('libbase');oldL['mods']=[q for q in oldL['mods'] if q['kind']=='far' and q['c']==9]+seed['mods'];oldE.update(seed['lens']);oldpool=pool+'-baseline';save(oldpool,oldL,oldE)
a=R.FreshLibrary(pool,only=M.usable);b=R.FreshLibrary(oldpool,only=M.usable)
H={int(r['n']):float(r['L']) for r in csv.DictReader(open('details.csv'))};rows=[];candidates=[]
for n in map(int,open('ns-all.txt').read().split()):
 m=math.isqrt(n-1)
 got=a.best(n,top=1,below=H[n]-m+.014,need=ids,distinct=True,depth=.06)
 if not got:continue
 row=got[0];f,stop,C,F1,F2,s1,s2=row;side=m+f;rows.append(dict(n=n,side=side,bar=H[n],margin=side-H[n],corner=C['id'],far1=F1['id'],far2=F2['id']))
 if side>H[n]+.008:continue
 baseline=b.best(n,top=1,below=H[n]-m+.04,need=ids,distinct=True,depth=.1);old=m+baseline[0][0] if baseline else float('inf')
 if side>=old-1e-6:continue
 for up in [.0002,.0006,.0015,.003]:
  P,why=M.assemble(a,n,C,F1,F2,s1,s2,f+up)
  if P is not None:
   actual,gap=M.layout_state(P)
   if gap>=-1e-7 and actual<=m+f+up+1e-6:
    candidates.append((row,n,old,actual));print('VALID NEW FAR START',n,'predicted',side,'baseline',old,'actual',actual,'gap',gap,flush=True);break
rows.sort(key=lambda x:x['margin'])
print('AUDIT52 no prediction floor, fresh9-arm farzones',len(a.far[9]),'closest',rows[:10],flush=True)
for row,n,old,actual in sorted(candidates,key=lambda x:x[0][0]+math.isqrt(x[1]-1)-H[x[1]])[:4]:
 f,stop,C,F1,F2,s1,s2=row;key=repr((n,C['id'],F1['id'],F2['id'],s1,s2,f));name=f'{n}-52nf'+hashlib.sha256(key.encode()).hexdigest()[:8]
 with open('q.txt','a') as h:h.write(f'{name} ./py -I lane/modules.py job {pool} raw-a details-r21.csv {name} {n} {C["id"]} {F1["id"]} {F2["id"]} {s1} {s2} {f!r} --fq ./fq --squeeze family\n')
print('AUDIT52 qualifying new-far exact starts',len(candidates),'full probes queued',min(4,len(candidates)),flush=True)
