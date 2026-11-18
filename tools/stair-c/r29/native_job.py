"""Build a changed corner with the far zones and stack counts of its exact input."""
import hashlib,importlib.util,json,os,pickle,sys
from pathlib import Path
sys.path[:0]=['lane','.']
import expanded as E
import modules as M
spec=importlib.util.spec_from_file_location('native_stair_job','lane/stair-c_job.py');J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
path=sys.argv[1];a,b=map(int,sys.argv[2:4]);meta=json.load(open(path+'.json'));n=meta['n'];payload=Path(path).read_bytes();digest=hashlib.sha256(payload).hexdigest()
assert digest==meta['queued_sha256'],'changed queued bytes'
sq=M.np.asarray(M.read_layouts(path)[n],float);d,why=M.cut(sq,n);assert d is not None,why
d=E.expand(d,a,b);tag='r29native'+digest[:12]+str(a)+str(b)
mods=M.modules_of(d,meta['source']+'; native whole-stack corner transfer '+str((a,b)),meta['licence'],tag);twins,ids=M.slid(d,mods);mods+=twins
for q in mods:
 if q['kind']=='corner':q['turn']=True
pool=Path('native-pools')/tag;pool.mkdir(parents=True,exist_ok=True)
pickle.dump(dict(mods=mods,layouts=[]),open(pool/'library.pkl','wb'))
pickle.dump({q['id']:M.tabulate(q)for q in mods},open(pool/'lens.pkl','wb'))
by={q['id']:q for q in mods};C,F1,F2=[dict(q=by[k])for k in[ids[2],ids[0],ids[1]]]
print('NATIVE RECIPE',n,a,b,'side',d['s'],'source',digest,'standard four-probe ladder',flush=True)
name=f'{n}-native-{digest[:12]}-{a}{b}'
J.run([str(pool),'raw-a','details.csv',name,str(n),ids[2],ids[0],ids[1],str(d['s1']),str(d['s2']),repr(float(d['f'])),'--fq','./fq','--squeeze','family'])
