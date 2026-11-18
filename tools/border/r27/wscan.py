"""boxC window scanner (border r26): every square sub-window of each fresh layout in wq/in (literature_window.scan_one),
newest first; per count c the smallest window side within 1e-4 above the live bar (bars.json), into wq/out/<name>.json.
Runs until the deadline file; one process."""
import sys,os,json,time,csv,glob
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import literature_window as lw,signal
# r27: one layout held the scanner for over 37 min at 21:00Z; each scan now stops after 90 s.
def _alarm(*a):raise TimeoutError('scan over 90 s')
signal.signal(signal.SIGALRM,_alarm)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
END=float(open('deadline').read())
os.makedirs('wq/in',exist_ok=True);os.makedirs('wq/out',exist_ok=True)
while time.time()<END:
 try:L={int(k):v for k,v in json.load(open('bars.json')).items()}
 except (OSError,ValueError):time.sleep(5);continue
 todo=[p for p in glob.glob('wq/in/*.csv') if not os.path.exists('wq/out/'+os.path.basename(p)[:-4]+'.json')]
 if not todo:time.sleep(10);continue
 p=min(todo,key=lambda q:(os.path.basename(q).startswith('z'),-os.path.getmtime(q)))  # fresh first, then backlog (z*)
 try:
  rows=list(csv.DictReader(open(p)))
  t0=time.time();signal.alarm(90)
  try:best=lw.scan_one(rows,L,-1e-4,1)
  finally:signal.alarm(0)
  out=dict(file=os.path.basename(p),n=len(rows),secs=round(time.time()-t0,1),hits={str(c):v for c,v in best.items()})
 except Exception as e:
  out=dict(file=os.path.basename(p),error=repr(e),hits={})
 tmp='wq/out/'+os.path.basename(p)[:-4]+'.tmp';json.dump(out,open(tmp,'w'));os.replace(tmp,tmp[:-4]+'.json')
 print(time.strftime('%H:%M:%S',time.gmtime()),'scanned',p,out.get('secs'),len(out['hits']),flush=True)
print('deadline',flush=True)
