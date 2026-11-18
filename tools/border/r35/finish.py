from pathlib import Path
import subprocess,sys,json,csv,hashlib,os,time,datetime,math,collections,shutil,re
csv.field_size_limit(16*1024*1024)
W=Path(__file__).parent;T=W.parent;S=T.parent;R=Path('$PRIVATE_REPO');L=R/'lanes/squares';P=str(S/'venv/bin/python');REMOTE='boxC:scratch/squares-border-r35/'
def log(msg):
 line=datetime.datetime.now(datetime.timezone.utc).isoformat()+' boxA '+msg
 print(line,flush=True)
 with open(T/'STATE.txt','a') as f:f.write(line+'\n')
def run(args,**kw):
 for attempt in range(2):
  r=subprocess.run(args,capture_output=True,text=True,**kw)
  if r.returncode and 'index.lock' in r.stderr and not attempt:time.sleep(3);continue
  if r.stdout:print(r.stdout,flush=True)
  if r.returncode:print(r.stderr,flush=True);r.check_returncode()
  return r.stdout
end=float((W/'deadline').read_text())
if '--now' not in sys.argv:
 while time.time()<end:time.sleep(min(30,end-time.time()))
log('FINISH search and certified-file quenches share 16:15Z. Stop owned collector and workers, then drain completed proofs.')
pid=int((W/'driver.pid').read_text())
cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
if 'driver.py' in cmd:
 time.sleep(0)
 try:os.kill(pid,15)
 except ProcessLookupError:pass
for name in ('wfeed.pid','lpfeed.pid','direct.pid','sfeed.pid','kfeed35.pid','deepfeed35.pid','sfeed35.pid'):  # r29: the self follow and the kick feed stop too
 try:
  q=int((W/name).read_text());c=subprocess.run(['ps','-p',str(q),'-o','command='],capture_output=True,text=True).stdout
  if re.search(r'[a-z]feed\d*\.py',c) or 'direct.py' in c:os.kill(q,15)
 except (OSError,ValueError,ProcessLookupError):pass
stop='''/usr/bin/python3 - <<'STOP'
from pathlib import Path
import subprocess,os,signal
r=Path.home()/'scratch/squares-border-r35'
pids=[]
for name in ['worker1.pid','worker2.pid','control.pid','wscan.pid','bfscan.pid']:
 try:pid=int((r/name).read_text())
 except (OSError,ValueError):continue
 cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
 cwd=subprocess.run(['/usr/sbin/lsof','-a','-p',str(pid),'-d','cwd','-Fn'],capture_output=True,text=True).stdout
 if (('n'+str(r)) in cwd.splitlines() or ('n'+str(r)+'/design') in cwd.splitlines()) and ('worker.py' in cmd or 'fast_control.py' in cmd or 'wscan.py' in cmd or 'bfmix' in cmd or 'bfbis' in cmd or 'mixfq' in cmd or 'bfscan' in cmd):pids.append(pid)
for line in subprocess.check_output(['ps','-axo','pid,ppid,command'],text=True).splitlines()[1:]:
 parts=line.strip().split(None,2)
 if len(parts)<3:continue
 pid,ppid,cmd=parts
 if int(ppid) in pids or str(r)+'/fq ' in cmd:
  try:os.kill(int(pid),signal.SIGTERM)
  except ProcessLookupError:pass
for pid in pids:
 try:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
print('stopped owned workers',pids)
STOP'''
run(['ssh','boxC',stop])
# The wscan venv holds symlinks to the box's own Python; it is no result, so it goes before the SHA-256 archive.
run(['ssh','boxC','rm -rf $SCRATCH/squares-border-r35/venv'])
log('removed the boxC venv (numpy and scipy, no results) before the archive')
# Read functions without running the scanner loop or reinitializing queues.
s=(W/'driver.py').read_text();s=s[:s.index("log('start round35 collector/scanner")]
s=s.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_drain','__file__':str(W/'driver.py')};exec(compile(s,str(W/'driver.py'),'exec'),ns)
ns['refresh']();ns['sync']();ns['collect']();ns['refresh']()
archive=W/'remote-final';archive.mkdir(exist_ok=True)
run(['rsync','-a',REMOTE,str(archive)+'/'])
proof=json.loads(run(['ssh','boxC',"cd $SCRATCH/squares-border-r35; /usr/bin/python3 - <<'PY'\nfrom pathlib import Path\nimport hashlib,json\nprint(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('.').rglob('*') if p.is_file() and '__pycache__' not in str(p)}))\nPY"]))
assert all((archive/p).exists() and hashlib.sha256((archive/p).read_bytes()).hexdigest()==h for p,h in proof.items())
(W/'remote-sha256.json').write_text(json.dumps(proof,indent=2));log(f'copied {len(proof)} remote files and verified SHA-256')
log('workers stopped and archive verified. Final competing-take refresh follows, before the 16:35Z take deadline.')
if '--now' not in sys.argv:
 while time.time()<end+360:time.sleep(min(30,end+360-time.time()))
ns['refresh']()  # r27: refresh() moves any row another live take has overtaken to near/ and rewrites take.tsv
validation=[]
for row in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(row['n']);pol=ns['sp'].classify(row['source'],row['licence'])
 if not ns['qualifies'](n,float(row['new']),pol):log(f'final check: {n} no longer qualifies');continue
 ref=ns['held'][n]
 validation.append(dict(n=n,score=ref))
with open(W/'validation-details.csv','w') as f:
 wr=csv.DictWriter(f,fieldnames=['n','score']);wr.writeheader();wr.writerows(validation)
for cmd in ([P,'-I',str(L/'literature_check.py'),str(W/'validation-details.csv'),str(T)],[P,'-I',str(W/'verify_proofs.py')]):
 try:run(cmd)
 except Exception as e:log('finish step failed (kept going): '+' '.join(cmd[2:])+' '+repr(e)[:200])
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
bars={n:float(r['new']) for n,r in ns['current'].items()}
manifest={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')} if (W/'q/manifest.tsv').exists() else {};pending=[]
for p in (W/'q').glob('*.job.json'):
 ident=p.name.removesuffix('.job.json');r=manifest.get(ident)
 if r and not p.with_name(ident+'.k0.json').exists():
  j=json.load(open(p));n=int(r['n']);pending.append(dict(id=ident,donor=r['donor'],n=n,kind=r['kind'],margin=float(r['built_L'])-(bars[n]+1)*math.sqrt(n),priority=j['priority'],source=r['donor_source'][:300],job=str(p)))
pending.sort(key=lambda x:(x['priority'],x['margin']))
with open(W/'unstarted.tsv','w') as f:
 wr=csv.DictWriter(f,fieldnames=['id','donor','n','kind','margin','priority','source','job'],delimiter='\t');wr.writeheader();wr.writerows(pending)
log(f'finish data: take {len(rows)} n, unstarted {len(pending)}, measure.tsv written')
run(['ssh','boxC','rm -rf $SCRATCH/squares-border-r35'])
log('removed boxC:$SCRATCH/squares-border-r35 after SHA-256-verified archive')
