"""Keep outputs reviewable and stop the lane before the round36 deadlines."""
from pathlib import Path
import sys,os,time,signal,json,subprocess,traceback,datetime
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W))
from finalutil36 import note,run,waitat,archive,stopremote,artifacts,commit,close_connections,PY,T,S
os.environ['K123_FINALIZER_PID']=str(os.getpid())
def stoplocal(names):
 for name in names:
  (W/('stop-'+name+'36')).touch()
  p=W/(name+'.pid')
  if not p.exists():continue
  pid=int(p.read_text())
  command=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout.strip()
  if str(W)+'/' not in command or not command or not Path(command.split()[0]).name.lower().startswith('python'):
   note('SKIP completed or reused pid for '+name+' pid'+str(pid));continue
  try:os.killpg(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  note('STOP local '+name+' pid'+str(pid))
def final_checks():
 for name,timeout in [('peer33.py',30),('independent33.py',120),('history28.py',60)]:
  try:run([PY,str(W/name)],timeout=timeout)
  except Exception as e:note('CHECK '+name+' '+repr(e))
def main():
 note('START durable finalizer. Precopy22:30, checkpoint22:45, final walk23:05, drain23:15, all search/quench stopped23:25, freeze23:54:30Z.')
 waitat(22,30)
 for host in ['boxD','boxE']:
  try:archive(host)
  except Exception as e:note('PRECOPY retry later '+host+' '+repr(e))
 waitat(22,45)
 try:artifacts();commit()
 except Exception as e:note('CHECKPOINT '+repr(e))
 waitat(23,5)
 with open(W/'finalwalk36.log','a') as f:p=subprocess.Popen([PY,str(W/'finalwalk36.py')],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
 (W/'finalwalk36.pid').write_text(str(p.pid));note('START final walk pid'+str(p.pid)+' log work/finalwalk36.log')
 waitat(23,15);stoplocal(['stage','seed36','third','storage'])
 stopremote('boxD');stoplocal(['bridge34']);(W/'bridge-stop34').touch()
 try:run([PY,str(W/'bridge34.py'),'--once','--no-export'],timeout=240)
 except Exception as e:note('BRIDGE final '+repr(e))
 archive('boxD',True)
 note('boxD stopped and archived. boxE finishes certification only until23:25Z.')
 waitat(23,25);stoplocal(['collect']);stopremote('boxE')
 for _ in range(2):
  try:run([PY,str(W/'collect22.py')],timeout=60)
  except Exception as e:note('COLLECT final '+repr(e))
 final_checks();archive('boxE',True);close_connections()
 # The final pass must include any output published after the early walk.
 try:run([PY,str(W/'finalwalk36.py')],timeout=300)
 except Exception as e:
  note('FINAL WALK '+repr(e));(W/'blocked34.json').write_text(json.dumps('final walk incomplete: '+repr(e)))
 (W/'cleanup34.json').write_text(json.dumps({'complete':True,'time':time.strftime('%FT%TZ',time.gmtime())}))
 try:artifacts();commit()
 except Exception as e:note('FINAL ARTIFACTS '+repr(e));(W/'blocked34.json').write_text(json.dumps('artifact or push failure: '+repr(e)))
 freeze=datetime.datetime(2026,11,17,23,54,30,tzinfo=datetime.timezone.utc).timestamp()
 late=None
 from policy27 import lines as withdrawal_lines
 import hashlib,csv
 def withdrawal_stamp():return hashlib.sha256(json.dumps(withdrawal_lines(),sort_keys=True).encode()).hexdigest()
 marker=W/'retention-withdraw-stamp32';late_error=False
 while time.time()<freeze-15:
  if late is not None and late.poll() is not None:
   if late.returncode:late_error=True;note('LATE source refresh failed rc'+str(late.returncode))
   late=None
  if late is None and not late_error and (not marker.exists() or marker.read_text()!=withdrawal_stamp()):
   with open(W/'late-retention36.log','a') as f:late=subprocess.Popen([PY,str(W/'retention32.py')],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
   note('START late withdrawal refresh pid'+str(late.pid)+'; it keeps running between peer checks.')
  try:run([PY,str(W/'peer33.py')],timeout=10)
  except Exception as e:note('LATE PEER '+repr(e))
  time.sleep(min(30,max(0,freeze-time.time()-15)))
 if late is not None and late.poll() is None:
  os.killpg(late.pid,signal.SIGTERM);late.wait(timeout=5);late_error=True
 if late_error or not marker.exists() or marker.read_text()!=withdrawal_stamp():
  # No unfinished ancestry check can be used as proof at the freeze.
  before=(T/'take.tsv').read_text();(W/'late-unverified-take36.tsv').write_text(before)
  tmp=T/'take.tsv.tmp';tmp.write_text('n\theld\tnew\tgain\tsource\tlicence\n');tmp.replace(T/'take.tsv')
  (W/'blocked34.json').write_text(json.dumps('late withdrawal walk incomplete at freeze; unverified rows left out'))
  note('FREEZE left out rows whose latest withdrawal refresh was unfinished.')
 run([PY,str(W/'peer33.py')],timeout=10);run([PY,str(W/'report36.py')],timeout=15)
 (W/'finalize36.done').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime())}));note('FINISH take.tsv and report.json final; processes_left=0.')
if __name__=='__main__':
 try:main()
 except BaseException as e:
  note('ERROR '+repr(e));traceback.print_exc();(W/'finalize36.error').write_text(repr(e));(W/'blocked34.json').write_text(json.dumps('finalization incomplete: '+repr(e)))
  try:run([PY,str(W/'report36.py')])
  except Exception:traceback.print_exc()
  raise
