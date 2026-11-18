import csv,glob,importlib.util,math,os,sys,time
sys.path.insert(0,'lane');import modules as M
spec=importlib.util.spec_from_file_location('stair_rank','lane/stair-c_rank.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
pool=sys.argv[1];need=set(open(pool+'/need.txt').read().split());data=M.Library(pool,only=M.usable)
new=[q for q in data.byid.values() if q['id'] in need];arms={q['q'].get('c',q['q'].get('c1')) for q in new}
old=[q['id'] for q in data.corners if q['c1'] in arms or q['c2'] in arms][:32];ids=set(old)|need
only=lambda q:M.usable(q) and (q['kind']=='far' or q['id'] in ids)
a=M.Library(pool,only=only);b=R.FreshLibrary(pool,only=only)
source=next(q['q']['n'] for q in new if q['q']['n']>0);m=math.isqrt(source-1)
ns=sorted({source,source-(2*m-1),source+(2*m+1)}&set(range(300,1001)))
key=lambda rows:[(r[0],r[1],r[2]['id'],r[3]['id'],r[4]['id'],r[5],r[6]) for r in rows]
positive=0
for n in ns:
 t=time.time();x=a.best(n,top=3,below=1.,need=need,distinct=True,depth=.15);ta=time.time()-t
 t=time.time();y=b.best(n,top=3,below=1.,need=need,distinct=True,depth=.15);tb=time.time()-t
 assert key(x)==key(y),(n,key(x),key(y));positive+=bool(x)
 print('CONTROL fresh join',n,'rows',len(x),'same exact f/ids/stacks',key(x)==key(y),'legacy_seconds',ta,'new_seconds',tb,flush=True)
assert positive
assert a.best(source,need={'missing-state'},below=1.,depth=.15)==b.best(source,need={'missing-state'},below=1.,depth=.15)==[]
open('FRESH_JOIN_READY','w').write(pool)
print('CONTROL fresh join PASS positive targets',positive,'missing-state rejects all; optimized join enabled',flush=True)
