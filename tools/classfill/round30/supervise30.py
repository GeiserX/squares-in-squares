"""Supervise disk-backed lane drivers without occupying a numerical slot."""
from common29 import *
last='';tick=0
while not (T/'report.json').exists():
 t=time.time();tick+=1
 # Activate changed bar-input geometry only after its real remote positive control returns.
 if not (W/'bar-control-result.json').exists():
  job=W/'boxE/out/xbarcontrol30-status.json'
  status=read(job,{})
  if status:
   paths=list((W/'boxE/out').glob('near-xbarcontrol30/2.json'))+list((W/'boxE/out').glob('final-xbarcontrol30/2.json'))
   logs=list((W/'boxE/out/finish-xbarcontrol30').glob('kick.log'))
   result=read(paths[0],{}) if paths else {};log=logs[0].read_text() if logs else ''
   ok=status.get('returncode')==0 and result.get('finish_score',1)<2.000001/math.sqrt(2)-1 and 'fq_input_side 2.00000000005' in log
   # Check the numeric input rather than a display-string rounding.
   m=re.search(r'fq_input_side ([0-9.e+-]+) bar ([0-9.e+-]+)',log)
   ok=status.get('returncode')==0 and result.get('finish_score',1)<2.000001/math.sqrt(2)-1 and bool(m) and float(m[1])==float(m[2])
   atomic(W/'bar-control-result.json',dict(passed=ok,status=status,finish=result,bar_input_line=next((q for q in log.splitlines() if 'BAR_INPUT_CONTROL' in q),None)))
   note('CONTROL bar-input '+('PASS' if ok else 'FAIL')+'; '+str(result.get('finish_score')))
 # Verify detached local controllers remain alive until their assigned cutoff.
 if time.time()<SEARCH_END:
  owned=read(W/'local-owned.json',{})
  for script,pid in list(owned.items()):
   try:os.kill(pid,0)
   except ProcessLookupError:
    p=subprocess.Popen([sys.executable,'-u',str(W/script)],stdout=open(W/(script[:-3]+'.log'),'a'),stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,start_new_session=True);owned[script]=p.pid;note(f'ADOPT restarted {script} pid{p.pid}')
  atomic(W/'local-owned.json',owned)
 state=(T/'STATE.txt').read_text().splitlines();take=rows(T/'take.tsv');starts=sum('START_QUEUE ' in q for q in state);done=sum('WORKER_EVENT ' in q and ' DONE ' in q for q in state)
 latest=next((q for q in reversed(state) if any(k in q for k in ['CERTIFIED','PUBLIC_PREFLIGHT','WORKER_EVENT','CONTROL bar','FINAL','ERROR'])),state[-1] if state else '')
 print(now()+' jobs '+str(done)+'/'+str(starts)+' take '+','.join(r['n'] for r in take)+((' | '+latest[:240]) if latest!=last else ''),flush=True);last=latest
 if tick%10==0:
  try:subprocess.run([sys.executable,str(W/'stats29.py')],stdout=open(W/'stats-latest.txt','w'),stderr=subprocess.STDOUT,timeout=20)
  except Exception as e:note('STATS_ERROR '+repr(e))
 time.sleep(max(1,60-(time.time()-t)))
print('REPORT_READY '+str(T/'report.json'),flush=True)
