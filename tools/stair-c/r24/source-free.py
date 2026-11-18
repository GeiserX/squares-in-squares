"""Screen independent constructions at the held-20 source-free threshold."""
import csv,hashlib,importlib.util,json,math,os,pickle,sys,time
sys.path[:0]=['lane','.']
import modules as M
from prepare import fingerprint
spec=importlib.util.spec_from_file_location('rank','lane/stair-c_rank.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
PART=int(sys.argv[1]);H={int(r['n']):float(r['L']) for r in csv.DictReader(open('details-r22.csv'))}
def pure(q):
    s=q['src']
    return M.usable(q) and q['licence']=='our own' and ('twoshort_corner.py: staircase corner' in s or 'zone_search.py: taper enumeration' in s) and not any(x in s for x in ['held:','seed merged0','stair-c_design.py','sc22zip','one upright wall column','areebbb','Samanyu','prvsiyan','jazivxt','malyshevdanil','alexchilton'])
lib=R.FreshLibrary('libbase',only=pure)
assert lib.best(975,top=1,below=.78,depth=.10)
assert lib.best(975,top=1,below=.78,depth=.10,need={'missing-state'})==[]
print('CONTROL source-free library reconstructs975; missing-state refused; modules',len(lib.byid),flush=True)
state=pickle.load(open('state.pkl','rb'));seen=set(state['recipes']);old=pickle.load(open('prior-recipes.pkl','rb'));seen.update(old)
held=[809,866,868,927,935,990];records=[];start=time.time()
for n in [x for x in held if x%2==PART]:
    m=math.isqrt(n-1);rs=lib.best(n,top=12,below=H[n]-m+.003,depth=.045,distinct=True)
    fresh=[]
    for f,stop,C,F1,F2,s1,s2 in rs:
        qs=[C['q'],F1['q'],F2['q']];recipe=(n,*[fingerprint(q) for q in qs],s1,s2)
        if recipe in seen:continue
        fresh.append(dict(n=n,f=f,ids=[q['id'] for q in qs],stacks=[s1,s2],predicted=m+f,held_r22=H[n],sources=[q['src'] for q in qs]))
    records.append(dict(n=n,rows=len(rs),fresh=fresh[:2]))
    print('SOURCE-FREE',n,'rows',len(rs),'untried',len(fresh),'best_delta',fresh[0]['predicted']-H[n] if fresh else None,flush=True)
json.dump(records,open('source-free-'+str(PART)+'.json','w'),indent=2)
print('SOURCE-FREE SCREEN DONE seconds',time.time()-start,flush=True)
