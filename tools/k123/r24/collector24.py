import pathlib,subprocess,time,os,signal
W=pathlib.Path(__file__).resolve().parent;PY=str(W.parent.parent/'venv/bin/python');end=float((W/'deadline').read_text());env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
while time.time()<end:
 with open(W/'collector24.log','a') as h:
  p=subprocess.Popen([PY,str(W/'collect22.py')],stdout=h,stderr=h,env=env,start_new_session=True)
  try:p.wait(timeout=min(110,max(1,end-time.time())))
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
 if time.time()<end:time.sleep(min(20,end-time.time()))
