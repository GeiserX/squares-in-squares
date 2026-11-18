"""Test the wider perturbation with the same certification path as production."""
import ast,csv,hashlib,json,os,pathlib,signal,subprocess,sys,time,traceback
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='1';os.environ['VECLIB_MAXIMUM_THREADS']='1'
D=pathlib.Path(__file__).resolve().parent;os.chdir(D);sys.path.insert(0,str(D/'lane'))
import floatsafe
import pandas as pd
PYTHON=os.path.expanduser('$SCRATCH/squares-base/venv/bin/python');FQ=os.path.expanduser('$SCRATCH/squares-base/fq');DEADLINE=float((D/'deadline').read_text())
module=ast.parse((D/'worker28.py').read_text());defs=[v for v in module.body if isinstance(v,ast.FunctionDef)and v.name in('post','run_bounded','writecsv')]
exec(compile(ast.Module(body=defs,type_ignores=[]),'worker28-functions','exec'),globals())
options=['--rmax','5.0','--sigs','0.01,0.02,0.04','--apart','0.08']
j=dict(id='wide907-control',n=907);run=D/j['id'];run.mkdir(exist_ok=True);result=dict(options=options,started=time.strftime('%FT%TZ',time.gmtime()),green=False)
try:
 cmd=[PYTHON,'-I','lane/invent_rest.py','907','starts/control907.csv',j['id'],'--seconds','300','--seed','2','--modes','lkick','--bar','30.6195806','--deadline','deadline']+options
 with (run/'run.log').open('a')as log:run_bounded(cmd,log,420)
 result.update(post(j));result['side']=(result['new']+1)*(907**.5)if'new'in result else None
 result['green']=bool(result.get('quench_from_certified'))and result['side']<30.6195806
except Exception as e:result['error']=repr(e);traceback.print_exc()
result['ended']=time.strftime('%FT%TZ',time.gmtime());(D/'wide-control-result.json').write_text(json.dumps(result))
if result['green']:(D/'WIDE_CONTROL_GREEN').write_text(json.dumps(result))
print(json.dumps(result),flush=True)
