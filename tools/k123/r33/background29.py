import pathlib,sys,time,runpy,traceback,os,signal
W=pathlib.Path(__file__).resolve().parent;os.chdir(W);sys.path[:0]=[str(W),str(W/'lane')]
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
class AdmissionDeadline(BaseException):pass
def expire(*args):raise AdmissionDeadline()
signal.signal(signal.SIGALRM,expire)
mode=sys.argv[1];script='intermediate28.py' if mode=='third' else 'storage26.py'
while time.time()<float((W/'search-deadline').read_text()):
 t=time.time()
 if mode=='third':signal.alarm(90)
 try:
  for entry in ([script,'prejoin31.py'] if mode=='third' else [script]):
   try:runpy.run_path(str(W/entry),run_name='__main__')
   except SystemExit:pass
 except AdmissionDeadline:
  f0=W/'intermediate-attempts29.jsonl'
  lines=f0.read_text().splitlines() if f0.exists() else []
  if lines:
   with (W/'deferred-intermediate29.jsonl').open('a') as h:h.write(lines[-1]+'\n')
  with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA DEFER intermediate source admission at90s budget; preserve uncounted inputs and continue fresh scans. Common cutoff00:15Z.\n')
 except SystemExit:pass
 except Exception:traceback.print_exc()
 finally:signal.alarm(0)
 print(time.strftime('%FT%TZ',time.gmtime()),mode,'seconds',time.time()-t,flush=True)
 time.sleep(30)
