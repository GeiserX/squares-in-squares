"""Build a known native recipe from real geometry without unused ranking tables."""
import hashlib,importlib.util,json,math,pickle,sys,types
from pathlib import Path
sys.path[:0]=['lane','.']
import modules as M
import expanded as E
import corner_paths as C
control=json.load(open('corner-paths-control.json'))
assert control['passed']and control['helper_sha256']==hashlib.sha256(Path('corner_paths.py').read_bytes()).hexdigest()
C.install()
spec=importlib.util.spec_from_file_location('native_direct_job','lane/stair-c_job.py');J=importlib.util.module_from_spec(spec);spec.loader.exec_module(J)
p=sys.argv[1];a,b=map(int,sys.argv[2:4]);meta=json.load(open(p+'.json'));n=meta['n'];digest=hashlib.sha256(Path(p).read_bytes()).hexdigest();assert digest==meta['queued_sha256']
if not meta.get('control_only'):assert json.load(open('native-direct-control.json'))['passed']
sq=M.np.asarray(M.read_layouts(p)[n],float);d,why=M.cut(sq,n);assert d is not None,why
d=E.expand(d,a,b);tag='r30direct'+digest[:12]+str(a)+str(b)
mods=M.modules_of(d,meta['source']+'; native corner with fixed-start preservation '+str((a,b)),meta['licence'],tag);twins,ids=M.slid(d,mods)
by={q['id']:q for q in mods+twins};mods=[by[k]for k in ids]
for q in mods:
 if q['kind']=='corner':q['turn']=True
pool=Path('native-pools')/tag;pool.mkdir(parents=True,exist_ok=True);pickle.dump(dict(mods=mods,layouts=[]),open(pool/'library.pkl','wb'))
# The known recipe needs geometry and ids. M.cmd_job uses no table values.
# Its assembler and full-layout legality checks still run for every probe.
original=M.Library;M.Library=lambda *args,**kwargs:types.SimpleNamespace(byid={q['id']:dict(id=q['id'],q=q)for q in mods})
raw=Path('native-control/raw'if meta.get('control_only')else'raw-a');name=f'{n}-native-direct-{digest[:12]}-{a}{b}'
try:J.run([str(pool),str(raw),'details.csv',name,str(n),ids[2],ids[0],ids[1],str(d['s1']),str(d['s2']),repr(float(d['f'])),'--fq','./fq','--squeeze','family'])
finally:M.Library=original
for suffix in['.json','-slp.json']:
 out=raw/(name+suffix)
 if out.exists():
  j=json.load(open(out));j.update(native_direct_geometry=True,corner_paths_preserve_fixed=True,control_only=bool(meta.get('control_only')));out.write_text(json.dumps(j))
if meta.get('control_only'):
 out=raw/(name+'.csv');rows=M.np.asarray(M.read_layouts(str(out))[n],float);side,gap=M.layout_state(rows)
 assert len(rows)==975 and gap>=-1e-7 and side<=d['s']+2e-6,(side,gap)
 Path('native-direct-control.json').write_text(json.dumps(dict(passed=True,n=n,side=side,gap=gap,input_sha256=digest,helper_sha256=control['helper_sha256'])))
 print('CONTROL native direct975 passed; no ranking table used; side',side,'gap',gap,flush=True)
