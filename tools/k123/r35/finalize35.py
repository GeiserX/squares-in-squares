"""Preserve, validate, and stop round35 before its deadlines without an interactive agent."""
from pathlib import Path
import subprocess,json,os,time,datetime,shlex,shutil,csv,hashlib,traceback,signal
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;REPO=Path('$PRIVATE_REPO');L=REPO/'lanes/squares';PY=str(S/'venv/bin/python');os.environ['K123_FINALIZER_PID']=str(os.getpid());csv.field_size_limit(1<<28)
boxes=['boxC','boxD','boxE']
def note(s):
 line=time.strftime('%FT%TZ',time.gmtime())+' boxA FINAL35 '+s
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
 run([PY,str(W/'report35.py'),'--artifacts'])
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(W/'round35-section.md')])
 p=L/'avenues/k123.md';s=p.read_text().split('\n## Round 35\n')[0];p.write_text(s.rstrip()+'\n\n'+(W/'round35-section.md').read_text())
 D=L/'tools/k123/r35';D.mkdir(exist_ok=True)
 for p in W.glob('*.py'):shutil.copy(p,D/p.name)
 (D/'lane').mkdir(exist_ok=True)
 for name in ['finesafe.py','methods_take.py','k123_join_diverse29.py']:shutil.copy(W/'lane'/name,D/'lane'/name)
def commit():
 paths=['lanes/squares/avenues/k123.md','lanes/squares/results/k123-r35-2026-11-17.tsv','lanes/squares/tools/k123/r35']
 command=shlex.join(['git','add','--',*paths])+' && '+shlex.join(['git','commit','--only','-m','Record round 35 k123 band joins','--',*paths])
 r=run(['/bin/zsh','-c',command],cwd=REPO,check=False)
 if r.returncode and 'index.lock' in r.stdout:time.sleep(3);r=run(['/bin/zsh','-c',command],cwd=REPO,check=False)
 if r.returncode:
  if 'nothing to commit' in r.stdout:return
  raise RuntimeError('exact-path commit failed')
 sha=run(['git','log','-1','--format=%H','--grep=^Record round 35 k123 band joins$'],cwd=REPO).stdout.strip()
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
 actual=run(['git','log','-1','--format=%H','--grep=^Record round 35 k123 band joins$'],cwd=REPO).stdout.strip()
 if actual:commits[-1]=actual;(W/'commits34.json').write_text(json.dumps(commits))
 if not pushed:(W/'blocked34.json').write_text(json.dumps('not pushed'))
 note('COMMIT '+(actual or sha)+(' pushed' if pushed else ' not pushed'))

def close_connections():
 paths=[('/tmp/squares-k123-r35-'+h,h) for h in boxes]+[('/tmp/squares-k123-r35-ssh','boxE')]
 for sock,host in paths:
  run(['ssh','-S',sock,'-O','exit',host],timeout=15,check=False)
 # A failed duplicate ControlMaster launch can leave an idle direct SSH connection.
 stopped=[]
 for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:
  parts=line.strip().split(None,1)
  if len(parts)!=2:continue
  pid,cmd=int(parts[0]),parts[1]
  if Path(cmd.split()[0]).name=='ssh' and '/tmp/squares-k123-r35-' in cmd:
   try:os.kill(pid,signal.SIGTERM);stopped.append(pid)
   except ProcessLookupError:pass
 (W/'connections-closed34.json').write_text(json.dumps({'stopped':stopped,'time':time.strftime('%FT%TZ',time.gmtime())}))
 note('Owned SSH connections closed after all remote copies and removals.')

def main():
 note('START durable finalizer pid'+str(os.getpid())+' precopy15:25, checkpoint15:40, drain15:55, finish16:15, freeze16:35Z.')
 waitat(15,25)
 for host in boxes:
  try:archive(host)
  except Exception as e:note('precopy retry later '+host+' '+repr(e))
 waitat(15,40);artifacts();commit()
 waitat(15,58)
 # Stop extra search and finish bridging its complete receipts before archiving.
 for host in ['boxC','boxD']:stopremote(host)
 (W/'bridge-stop34').touch()
 # Let the warm bridge release its lock, bounded to preserve the certification window.
 p=W/'bridge34.pid'
 if p.exists():
  pid=int(p.read_text())
  try:os.kill(pid,signal.SIGTERM)
  except ProcessLookupError:pass
 run([PY,str(W/'bridge34.py'),'--once','--no-export'],timeout=240)
 for host in ['boxC','boxD']:archive(host,True)
 note('Extra boxes archived. boxE certification queue remains active until16:15Z.')
 waitat(16,15)
 run([PY,str(W/'stop_local25.py')]);stopremote('boxE')
 for attempt in range(2):
  try:run([PY,str(W/'collect22.py')],timeout=80)
  except Exception as e:note('final collect '+repr(e))
 run([PY,str(W/'peer33.py')],timeout=90)
 run([PY,str(W/'validate25.py')],timeout=180)
 run([PY,str(W/'independent33.py')],timeout=120)
 run([PY,str(W/'history28.py')],timeout=120,check=False)
 archive('boxE',True)
 close_connections()
 (W/'cleanup34.json').write_text(json.dumps({'complete':True,'time':time.strftime('%FT%TZ',time.gmtime())}))
 artifacts();commit()
 note('Search stopped and source/float checks passed. Three box archives verified. Take stays under peer and withdrawal checks through16:35Z.')
 waitat(16,25)
 freeze=datetime.datetime(2026,11,17,16,34,30,tzinfo=datetime.timezone.utc).timestamp()
 while time.time()<freeze-10:
  try:
   run([PY,str(W/'retention32.py')],timeout=max(1,min(20,freeze-time.time()-8)))
   run([PY,str(W/'peer33.py')],timeout=max(1,min(5,freeze-time.time()-2)))
  except Exception as e:note('late retention '+repr(e))
  time.sleep(max(0,min(15,freeze-time.time()-10)))
 run([PY,str(W/'peer33.py')],timeout=10)
 run([PY,str(W/'report35.py')])
 (W/'finalize34.done').write_text(json.dumps({'time':time.strftime('%FT%TZ',time.gmtime())}))
 note('FINISH final take and report written. processes_left=0.')
if __name__=='__main__':
 try:main()
 except BaseException as e:
  note('ERROR '+repr(e));traceback.print_exc();(W/'finalize34.error').write_text(repr(e));(W/'blocked34.json').write_text(json.dumps('finalization incomplete: '+repr(e)))
  try:run([PY,str(W/'report35.py')])
  except BaseException:traceback.print_exc()
  raise
