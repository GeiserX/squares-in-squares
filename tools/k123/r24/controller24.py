import pathlib,subprocess,time,os,json,sys,signal
W=pathlib.Path(__file__).resolve().parent;S=W.parent.parent;PY=str(S/'venv/bin/python');env=os.environ.copy();env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1');end=float((W/'deadline').read_text());lastfresh=0;lastdefer=0
while time.time()<end:
 for script,args,limit in [('collect22.py',[],100),('stage24.py',[],150),('stage24.py',['deferred','4'],150)]:
  if script=='stage24.py' and not args and time.time()-lastfresh<60:continue
  if script=='stage24.py' and args and time.time()-lastdefer<180:continue
  if script=='stage24.py' and not args:lastfresh=time.time()
  if args:lastdefer=time.time()
  log=W/('collect24.log' if script=='collect22.py' else 'stage24.log')
  with open(log,'a') as h:
   p=subprocess.Popen([PY,str(W/script),*args],stdout=h,stderr=h,env=env,start_new_session=True)
   try:rc=p.wait(timeout=min(limit,max(1,end-time.time())))
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait();rc=-2
  with open(W/'controller24.log','a') as h:h.write(time.strftime('%FT%TZ',time.gmtime())+f' {script} {args} rc={rc}\n')
 if time.time()<end:time.sleep(min(20,end-time.time()))
