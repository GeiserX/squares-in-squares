import pathlib,subprocess,re,sys,time
R=pathlib.Path.home()/'scratch/squares-k123';ps=subprocess.check_output(['ps','-axo','pid,command'],text=True);active=[line for line in ps.splitlines() if re.search(r'/python -I qrun22.py j22[abd](?:\s|$)',line)]
assert not active,active
(R/'search-deadline.saved27').replace(R/'search-deadline')
for name in ['j22a','j22b','j22d']:
 with open(R/f'out/{name}.log','a') as f:p=subprocess.Popen(['/usr/bin/nice','-n','5',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'),'-I','qrun22.py',name],cwd=R,stdin=subprocess.DEVNULL,stdout=f,stderr=f,start_new_session=True)
 (R/(name+'.pid')).write_text(str(p.pid));print(name,p.pid,flush=True)
