import pathlib,subprocess,os,json
D=pathlib.Path.home()/'scratch/squares-invent-r33';os.chdir(D)
rows=subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines();active=[r for r in rows if 'worker33.py' in r and 'python -' not in r]
assert not active,active
pids={}
for slot in ('1','2','3','4'):
 with (D/f'worker{slot}.log').open('a')as h:
  p=subprocess.Popen(['nohup','nice','-n','5',str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python'),'-u',str(D/'worker33.py'),slot],stdout=h,stderr=subprocess.STDOUT,start_new_session=True,cwd=D)
 (D/f'worker{slot}.pid').write_text(str(p.pid));pids[slot]=p.pid
print(json.dumps(pids))
