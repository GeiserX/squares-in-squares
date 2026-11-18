"""Inspect only this lane's boxE jobs, then require a verified transfer before removal."""
import hashlib,json,os,pathlib,signal,subprocess,sys,time
D=pathlib.Path(__file__).resolve().parent
assert D==pathlib.Path.home()/'scratch/squares-invent-r29','unexpected lane scratch path'
def processes():
 rows={}
 for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
  a=line.split(None,2)
  if len(a)==3:
   try:rows[int(a[0])]=dict(ppid=int(a[1]),command=a[2])
   except ValueError:pass
 roots={p for p,r in rows.items()if any(str(D/name)in r['command']for name in ('worker28.py','verify28.py'))}
 owned=set(roots)
 while True:
  more={p for p,r in rows.items()if r['ppid']in owned}
  if more<=owned:break
  owned|=more
 candidates=[p for p,r in rows.items()if p not in owned and p!=os.getpid()and any(t in r['command']for t in ('invent_rest.py','invent_domain29.py','globalfit29.py','midm_fqonce.py','/fq quench'))]
 if candidates:
  proc=subprocess.run(['lsof','-a','-p',','.join(map(str,candidates)),'-d','cwd','-Fn'],capture_output=True,text=True)
  pid=None
  for line in proc.stdout.splitlines():
   if line.startswith('p'):pid=int(line[1:])
   if line.startswith('n')and pid in rows:
    cwd=line[1:]
    if cwd==str(D)or cwd.startswith(str(D)+'/'):owned.add(pid)
 return dict(roots=sorted(roots),owned={str(p):rows[p]for p in sorted(owned)})
def save(name,value):(D/name).write_text(json.dumps(value,indent=2))
def acknowledged():
 path=D/'TRANSFER_OK.json';manifest=D/'csv-manifest.json'
 if not path.exists()or not manifest.exists():return False
 ack=json.load(open(path));return ack.get('manifest_sha256')==hashlib.sha256(manifest.read_bytes()).hexdigest()and ack.get('files')==len(json.load(open(manifest)))
mode=sys.argv[1]
if mode=='inventory':
 result=processes();save('processes26.json',result);print(json.dumps(result))
elif mode=='stop':
 before=processes()
 for pid in before['owned']:
  try:os.kill(int(pid),signal.SIGTERM)
  except ProcessLookupError:pass
 time.sleep(2)
 for pid in processes()['owned']:
  try:os.kill(int(pid),signal.SIGKILL)
  except ProcessLookupError:pass
 time.sleep(.2)
 after=processes();result=dict(before=before,after=after);save('cleanup-processes.json',result);print(json.dumps(result));assert not after['owned']
elif mode=='cancel':
 ids=sys.argv[2:];before=processes();targets=[]
 for raw,row in before['owned'].items():
  if any(ident in row['command'].split()or '/'+ident+'/'in row['command']for ident in ids):targets.append(int(raw))
 for pid in targets:
  try:
   if os.getpgid(pid)==pid:os.killpg(pid,signal.SIGTERM)
   else:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
 print(json.dumps(dict(cancelled_jobs=ids,pids=targets)))
elif mode=='manifest':
 assert not processes()['owned'],'own jobs still run'
 manifest={str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(D.rglob('*.csv'))}
 save('csv-manifest.json',manifest);print(json.dumps(dict(files=len(manifest),manifest_sha256=hashlib.sha256((D/'csv-manifest.json').read_bytes()).hexdigest())))
elif mode=='preflight':
 result=dict(path=str(D),transfer_acknowledged=acknowledged(),processes=processes());print(json.dumps(result));assert not result['transfer_acknowledged'],'preflight expects no transfer acknowledgment yet'
elif mode=='remove':
 assert acknowledged(),'verified local CSV transfer acknowledgment is missing or changed'
 assert not processes()['owned'],'own jobs still run'
 import shutil
 count=len(json.load(open(D/'csv-manifest.json')));shutil.rmtree(D);print(json.dumps(dict(removed=str(D),copied_csv=count)))
else:raise SystemExit('expected inventory, stop, manifest, preflight or remove')
