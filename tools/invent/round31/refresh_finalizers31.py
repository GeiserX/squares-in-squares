"""Refresh idle finalizers before draining, without moving any deadline."""
import pathlib,time,subprocess,os,signal,json
W=pathlib.Path(__file__).resolve().parent;when=float((W/'deadline').read_text())-300
while time.time()<when:time.sleep(min(30,when-time.time()))
def stop(pidfile,expected):
 pid=int(pidfile.read_text())
 try:line=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True)
 except subprocess.CalledProcessError:return
 assert str(W/expected)in line,(pid,line)
 os.kill(pid,signal.SIGTERM)
 for _ in range(50):
  try:os.kill(pid,0)
  except ProcessLookupError:return
  time.sleep(.1)
 raise RuntimeError('old finalizer did not exit')
for key,old,new in [('finish','finish31.py','finish31v2.py'),('report','report31.py','report31v2.py')]:
 stop(W/(key+'.pid'),old)
 with(W/(key+'-v2.log')).open('a')as log:
  p=subprocess.Popen(['nice','-n','5','$SCRATCH/bounties-squares/venv/bin/python','-u',str(W/new)],stdout=log,stderr=subprocess.STDOUT,start_new_session=True,cwd=W)
 (W/(key+'.pid')).write_text(str(p.pid))
 with(W.parent/'STATE.txt').open('a')as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA REFRESH {key} {p.pid} uses {new}. Original idle finalizer stopped first. Deadlines unchanged.\n')
pid=int((W/'light-monitor.pid').read_text())
try:
 line=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True).strip()
 if line.endswith('Python -u -'):os.kill(pid,signal.SIGTERM)
except (subprocess.CalledProcessError,ProcessLookupError):pass
(W/'finalizers-refreshed.json').write_text(json.dumps(dict(time=time.strftime('%FT%TZ',time.gmtime()),finish_pid=int((W/'finish.pid').read_text()),report_pid=int((W/'report.pid').read_text()),observer_stopped=True)))
