import pathlib,subprocess,os,json
D=pathlib.Path.home()/'scratch/squares-invent-r35';os.chdir(D)
rows=subprocess.check_output(['ps','-axo','pid=,command='],text=True).splitlines();active=[r for r in rows if 'worker35.py' in r and 'python -' not in r]
assert not active,active
pids={}
PY=str(D/'venv/bin/python')if(D/'venv/bin/python').exists()else str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python')
for slot in (tuple((D/'slots').read_text().split())if(D/'slots').exists()else('1','2','3')):
 with (D/f'worker{slot}.log').open('a')as h:
  p=subprocess.Popen(['nohup','nice','-n','5',PY,'-u',str(D/'worker35.py'),slot],stdout=h,stderr=subprocess.STDOUT,start_new_session=True,cwd=D)
 (D/f'worker{slot}.pid').write_text(str(p.pid));pids[slot]=p.pid
print(json.dumps(pids))
