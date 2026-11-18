"""Collect, verify and remove owned workers within the round's recorded deadlines."""
import csv,json,os,pathlib,shutil,signal,subprocess,sys,time
W=pathlib.Path(__file__).resolve().parent;T=W.parent
sys.path.insert(0,str(W));import controller28 as C
PY='$SCRATCH/bounties-squares/venv/bin/python';REMOTE='boxE:scratch/squares-invent-r29/'
ROOT='$SCRATCH/squares-invent-r29';RP='$SCRATCH/squares-base/venv/bin/python'
END=float((W/'deadline').read_text());START=float((W/'search-deadline').read_text())
def state(message):
 with (T/'STATE.txt').open('a')as stream:stream.write(time.strftime('%FT%TZ',time.gmtime())+' FINALIZER '+message+'\n')
def run(cmd,limit=120):
 result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=limit)
 if result.returncode:raise RuntimeError(str(cmd)+' '+result.stdout[-1800:])
 return result.stdout

def once():
 sys.path.insert(0,str(W));import controller28 as C
 C.COLLECT_ONLY=True;C.turn()

def finalize():
 import contextlib,io,runpy
 output=io.StringIO()
 with contextlib.redirect_stdout(output):runpy.run_path(str(W/'finalize28.py'),run_name='__main__')
 return output.getvalue()

def finish():
 progress=W/'finish-progress.json'
 def load():return json.load(open(progress))if progress.exists()else{}
 def mark(key,value=True):
  obj=load();obj[key]=value;temp=progress.with_suffix('.tmp');temp.write_text(json.dumps(obj));temp.replace(progress)
 if not load().get('controller_stopped'):
  pid=int((W/'controller.pid').read_text())
  try:
   group=os.getpgid(pid)
   if group==pid:os.killpg(group,signal.SIGTERM)
   else:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
  once();(W/'STOP').touch()
  (W/'local-controller-stopped.json').write_text(json.dumps(dict(pid=pid,time=time.strftime('%FT%TZ',time.gmtime()))))
  mark('controller_stopped');state('stopped own collector and completed one final collection')
 if not load().get('remote_workers_done'):
  while time.time()<END-120:
   info=json.loads(run(['ssh','boxE',RP,'-I',ROOT+'/cleanup28.py','inventory']))
   if not info['owned']:break
   time.sleep(20)
  else:raise TimeoutError('workers left less than two minutes for verification')
  mark('remote_workers_done');state('all three boxE slots finished before independent verification')
 if not load().get('verified'):
  # The collector no longer writes, so this immutable snapshot covers all worker ends.
  once()
  run([PY,'-I',str(W/'verify_specs28.py'),'--competitive'])
  run(['rsync','-a',str(W/'verify-specs.json'),str(W/'verify28.py'),REMOTE])
  state('start uncached boxE verification, common hard deadline11:45Z')
  output=run(['ssh','boxE','nice','-n','5',RP,'-I',ROOT+'/verify28.py'],max(1,END-time.time()))
  (W/'verification-log.txt').write_text(output);once()
  verification=json.load(open(W/'boxE-raw/verification26.json'))
  assert not verification['errors'] and all(verification['controls'].values())
  mark('verified');state('uncached boxE verification complete: '+str(len(verification['verified']))+' files')
 if not load().get('copied'):
  stop=run(['ssh','boxE',RP,'-I',ROOT+'/cleanup28.py','stop'])
  (W/'stop-log.json').write_text(stop)
  run(['ssh','boxE',RP,'-I',ROOT+'/cleanup28.py','manifest'])
  run(['rsync','-a','--exclude=lane/','--exclude=starts/','--exclude=locks/','--exclude=*.py','--exclude=tmp/','--exclude=*.tmp',REMOTE,str(W/'boxE-raw')+'/'])
  # Starts can include remote byte-identical inputs. Preserve any that local publication has not copied.
  run(['rsync','-a',REMOTE+'starts/',str(W/'starts')+'/'])
  print(run([PY,'-I',str(W/'transfer_check28.py')]),flush=True)
  run(['rsync','-a',str(W/'TRANSFER_OK.json'),REMOTE]);mark('copied')
  state('copied every boxE CSV and verified the full manifest')
 if not load().get('removed'):
  result=json.loads(run(['ssh','boxE',RP,'-I',ROOT+'/cleanup28.py','remove']))
  (W/'remote-removal.json').write_text(json.dumps(result));mark('removed')
  state('removed only owned boxE scratch after checked transfer')
 print(finalize(),flush=True)
 run([PY,'-I',str(W/'measure28.py')]);state('final verified comparison refreshed; waiting for last live-peer refresh')

if __name__=='__main__':
 if '--now' not in sys.argv:
  while time.time()<START+10:time.sleep(min(30,START+10-time.time()))
 try:
  finish()
  if '--now'not in sys.argv:
   import datetime,runpy
   freeze_at=datetime.datetime(2026,11,15,11,54,35,tzinfo=datetime.timezone.utc).timestamp()
   report_at=datetime.datetime(2026,11,15,11,55,5,tzinfo=datetime.timezone.utc).timestamp()
   while time.time()<freeze_at:time.sleep(min(30,freeze_at-time.time()))
   print(finalize(),flush=True);run([PY,'-I',str(W/'measure28.py')]);state('take frozen after final peer/source comparison')
   while time.time()<report_at:time.sleep(min(30,report_at-time.time()))
   runpy.run_path(str(W/'report28.py'),run_name='__main__')
   state('report written after11:55Z; finalizer ends')
 except Exception as error:
  state('ERROR '+repr(error));raise
