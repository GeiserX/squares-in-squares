"""A lowered peer bar must not crash a fresh worker with no prior build counts."""
import ast,json,os,sys,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
src=(H/'worker.py').read_text();ns=dict(os=os,json=json,glob=__import__('glob'),sys=sys,time=__import__('time'),hashlib=__import__('hashlib'),CAP=8,CLOSE=.002,DEAD=10**12)
for node in ast.parse(src).body:
 if isinstance(node,ast.FunctionDef)and node.name=='build':exec(compile(ast.Module([node],[]),str(H/'worker.py'),'exec'),ns)
with tempfile.TemporaryDirectory()as d:
 old=os.getcwd();os.chdir(d)
 try:
  Path('raw-a').mkdir();Path('bar.json').write_text('{"813":29.0}')
  calls=[];ns.update(S=dict(built=0,build=[dict(n=813,ids=['a','b','c'],stacks=[1,1],f=.9,name='813-fresh',predicted=28.999,bar=29.01,patch='fresh')],fresh=set()),H={813:dict(L=29.01)},L=dict(mods=[]),BOARD={813:28.9},fingerprint=lambda q:q,checkpoint=lambda:None,run=lambda cmd,name,limit:calls.append(name),log=lambda *a:None)
  ns['build']();assert calls==['813-fresh'];assert 'nogain'in ns['S']
 finally:os.chdir(old)
print('CONTROL fresh worker with lowered peer bar built once and initialized counts; empty loss history accepted',flush=True)
