"""Preserve, validate, and stop round35 before its deadlines without an interactive agent."""
from pathlib import Path
import subprocess,json,os,time,datetime,shlex,shutil,csv,hashlib,traceback,signal
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;REPO=Path('$PRIVATE_REPO');L=REPO/'lanes/squares';PY=str(S/'venv/bin/python');os.environ['K123_FINALIZER_PID']=str(os.getpid());csv.field_size_limit(1<<28)
boxes=['boxD','boxE']
def note(s):
 line=time.strftime('%FT%TZ',time.gmtime())+' boxA FINAL36 '+s
 with (T/'STATE.txt').open('a') as f:f.write(line+'\n')
 print(line,flush=True)
def run(args,timeout=120,check=True,cwd=None):
 p=subprocess.Popen(args,cwd=cwd or W,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,start_new_session=True)
 try:out,_=p.communicate(timeout=timeout)
 except subprocess.TimeoutExpired:
  os.killpg(p.pid,signal.SIGKILL);out,_=p.communicate();print(out,flush=True);raise
 print(out[-16000:],flush=True)
 if check and p.returncode:raise RuntimeError(f'{shlex.join(args)} failed rc={p.returncode}')
 return subprocess.CompletedProcess(args,p.returncode,out,'')
def waitat(h,m):
 at=datetime.datetime(2026,11,17,h,m,tzinfo=datetime.timezone.utc).timestamp()
 while time.time()<at:time.sleep(min(30,max(0,at-time.time())))
def config(host):
 return json.load((W/'runtime33.json' if host=='boxE' else W/host/'runtime33.json').open())
def archive(host,final=False):
 D=W/({'boxE':'boxE-final','boxC':'boxC-final','boxD':'boxD-final'}[host]);D.mkdir(exist_ok=True)
 if final:run(['ssh',host,f'cd $SCRATCH/squares-k123 && {config(host)["python"]} -I manifest25.py'],timeout=180)
 run(['rsync','-acz','--partial',host+':scratch/squares-k123/',str(D)+'/'],timeout=300)
 if not final:return
 manifest=json.loads((D/'manifest25.json').read_text());bad=[]
 for name,r in manifest.items():
  p=D/name
  if not p.is_file() or p.stat().st_size!=r['bytes'] or hashlib.file_digest(p.open('rb'),'sha256').hexdigest()!=r['sha256']:bad.append(name)
 assert not bad,(host,bad[:10])
 assert not json.loads((D/'processes-stopped25.json').read_text())['remaining']
 r={'files':len(manifest),'bytes':sum(v['bytes'] for v in manifest.values()),'checksum_differences':bad};a=json.loads((W/'archives34.json').read_text()) if (W/'archives34.json').exists() else {};a[host]=r;(W/'archives34.json').write_text(json.dumps(a,indent=2))
 run(['ssh',host,'test -d $SCRATCH/squares-k123 && rm -rf -- $SCRATCH/squares-k123'])
 note('ARCHIVE '+host+' verified '+json.dumps(r)+'; owned scratch removed, shared runtime preserved.')
def stopremote(host):
 for name in ['stop_remote25.py','manifest25.py']:
  run(['scp','-q',str(W/name),host+':scratch/squares-k123/'])
 run(['ssh',host,f'cd $SCRATCH/squares-k123 && touch STOP34 && {config(host)["python"]} -I stop_remote25.py'])
def artifacts():
 run([PY,str(W/'report36.py'),'--artifacts'])
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round36-section.md')])
 p=L/'avenues/k123.md';s=p.read_text().split('\n## Round 36\n')[0];p.write_text(s.rstrip()+'\n\n'+(W/'round36-section.md').read_text())
 D=L/'tools/k123/r36';D.mkdir(exist_ok=True)
 for p in W.glob('*.py'):shutil.copy(p,D/p.name)
 (D/'lane').mkdir(exist_ok=True)
 for name in ['finesafe.py','methods_take.py','k123_join_diverse29.py']:shutil.copy(W/'lane'/name,D/'lane'/name)
def commit():
 paths=['lanes/squares/avenues/k123.md','lanes/squares/results/k123-r36-2026-11-17.tsv','lanes/squares/tools/k123/r36']
 command=shlex.join(['git','add','--',*paths])+' && '+shlex.join(['git','commit','--only','-m','Record round 36 k123 band joins','--',*paths])
 r=run(['/bin/zsh','-c',command],cwd=REPO,check=False)
 if r.returncode and 'index.lock' in r.stdout:time.sleep(3);r=run(['/bin/zsh','-c',command],cwd=REPO,check=False)
 if r.returncode:
  if 'nothing to commit' in r.stdout:return
  raise RuntimeError('exact-path commit failed')
 sha=run(['git','log','-1','--format=%H','--grep=^Record round 36 k123 band joins$'],cwd=REPO).stdout.strip()
 run(['git','show','--stat',sha],cwd=REPO)
 files=run(['git','show','--pretty=','--name-only',sha],cwd=REPO).stdout.splitlines();assert all(p in paths[:2] or p.startswith(paths[2]+'/') for p in files)
 commits=json.loads((W/'commits34.json').read_text()) if (W/'commits34.json').exists() else [];commits.append(sha);(W/'commits34.json').write_text(json.dumps(commits))
 pushed=False
 for attempt in range(2):
  pull=run(['git','pull','--rebase','--autostash','origin','main'],cwd=REPO,check=False)
  if pull.returncode and 'CONFLICT' in pull.stdout:break
  push=run(['git','push','origin','HEAD:main'],cwd=REPO,check=False)
  if push.returncode==0:pushed=True;break
  time.sleep(3)
 actual=run(['git','log','-1','--format=%H','--grep=^Record round 36 k123 band joins$'],cwd=REPO).stdout.strip()
 if actual:commits[-1]=actual;(W/'commits34.json').write_text(json.dumps(commits))
 if not pushed:(W/'blocked34.json').write_text(json.dumps('not pushed'))
 note('COMMIT '+(actual or sha)+(' pushed' if pushed else ' not pushed'))

def close_connections():
 paths=[('/tmp/squares-k123-r36-'+h,h) for h in boxes]+[('/tmp/squares-k123-r36-ssh','boxE')]
 for sock,host in paths:
  run(['ssh','-S',sock,'-O','exit',host],timeout=15,check=False)
 # A failed duplicate ControlMaster launch can leave an idle direct SSH connection.
 stopped=[]
 for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:
  parts=line.strip().split(None,1)
  if len(parts)!=2:continue
  pid,cmd=int(parts[0]),parts[1]
  if Path(cmd.split()[0]).name=='ssh' and '/tmp/squares-k123-r36-' in cmd:
   try:os.kill(pid,signal.SIGTERM);stopped.append(pid)
   except ProcessLookupError:pass
 (W/'connections-closed34.json').write_text(json.dumps({'stopped':stopped,'time':time.strftime('%FT%TZ',time.gmtime())}))
 note('Owned SSH connections closed after all remote copies and removals.')

