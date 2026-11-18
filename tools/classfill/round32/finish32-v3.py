"""Stop, verify archives, preserve receipts, and publish the lane's final record."""
import sys,os,signal,time,subprocess,json,csv,math,hashlib,shutil,tarfile,shlex,datetime
from pathlib import Path
W=Path(__file__).parent;sys.dont_write_bytecode=True;sys.path.insert(0,str(W));import run32 as C
T=C.T;S=C.S;REPO=C.R.parent.parent;errors=[]
def safe(fn,label):
 try:return fn()
 except Exception as e:
  errors.append(label+': '+repr(e));C.note('FINISH_ERROR '+label+' '+repr(e));return None

def until(t):
 while time.time()<t and not (W/'FINISH_NOW').exists():time.sleep(min(20,t-time.time()))

def stop():
 (W/'STOP').touch();(W/'STOP_PREPARED').touch()
 for name,script in [('controller-pid','run32.py'),('freshguard-pid','freshguard32.py')]:
  p=W/name
  if not p.exists():continue
  pid=int(p.read_text());cmd=subprocess.run(['ps','-p',str(pid),'-o','command='],capture_output=True,text=True).stdout
  if str(W/script) in cmd:
   os.kill(pid,signal.SIGTERM)
 # The remote stopper verifies ownership from our recorded serial-worker PIDs.
 for host in dict(C.HOSTS):
  for p in W.glob('owned-'+host+'-*.json'):C.cmd(['scp','-q',str(p),host+':'+C.ROOT+'/'+p.name])
  C.cmd(['scp','-q',str(W/'stop32.py'),host+':'+C.ROOT+'/stop32.py'])
  py='$SCRATCH/squares-base/venv/bin/python' if host=='boxE' else '$SCRATCH/squares-readers/venv/bin/python'
  C.note('STOP_REMOTE '+host+' '+C.cmd(['ssh',host,py+' '+C.ROOT+'/stop32.py'],timeout=70).strip())
 C.atom(W/'local-stop-receipt.json',dict(time=C.now(),stopped=True))

def archive():
 verified={}
 for host in dict(C.HOSTS):
  target=W/('complete-'+host+'.tar.gz')
  with target.open('wb') as f:
   subprocess.run(['ssh','-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2',host,'cd '+C.ROOT+' && tar czf - .'],stdout=f,stderr=subprocess.PIPE,timeout=120,check=True)
  hashes={};sizes={};manifest=None
  with tarfile.open(target,'r|gz') as tf:
   for member in tf:
    if not member.isfile():continue
    name=member.name.removeprefix('./');data=tf.extractfile(member).read();hashes[name]=hashlib.sha256(data).hexdigest();sizes[name]=len(data)
    if name=='archive-manifest.json':manifest=json.loads(data)
  assert manifest and not manifest['remaining'],(host,manifest)
  for name,record in manifest['files'].items():
   assert hashes.get(name)==record['sha256'] and sizes[name]==record['bytes'],(host,name)
  verified[host]=dict(files=len(manifest['files']),bytes=sum(v['bytes'] for v in manifest['files'].values()),remaining=[],archive=str(target),archive_sha256=C.sha(target))
  C.atom(W/'archive-verification.json',verified)
  C.cmd(['ssh',host,'test -f '+C.ROOT+'/archive-manifest.json && rm -rf '+C.ROOT])
  C.note('ARCHIVE_VERIFIED_REMOVED '+host+' '+json.dumps(verified[host]))
 return verified

def compare():
 base,live=C.bars();take={}
 for r in C.rows(T/'take.tsv'):
  n=int(r['n']);p=T/f'{n}.csv';score=float(r['new'])
  if p.exists() and score<live[n]-1e-10:take[n]=r
  else:C.note(f'FINAL_SUPERSEDED n{n}; CSV retained for descendants')
 C.table(take);return take

def verify_retained():
 from retained32 import audit
 take={int(r['n']):r for r in C.rows(T/'take.tsv')};verified={}
 for n in list(take):
  try:
   p=T/f'{n}.csv';a=audit(p,C.read(p.with_suffix('.source.json'))['receipt']);verified[str(n)]={k:a[k] for k in ('sha256','score','source_clean','primary_binding','receipt')}
  except Exception as e:
   C.note('FINAL_AUDIT_REFUSED n'+str(n)+' '+repr(e));errors.append('retained n'+str(n)+': '+repr(e));del take[n]
 C.table(take);C.atom(W/'retained-verification.json',dict(time=C.now(),records=verified))
 C.note('RETAINED_AUDIT_PASS '+str(len(verified))+' rows; exact bytes, two metric reads, completed certified-file fq and independent primary source tree')
 return verified

def measurements():
 records=[C.read(p,{}) for p in (W/'candidates').glob('*.json')];production=[r for r in records if r.get('job',{}).get('n',0)>40]
 stats={};tries=0;finds=0;probes=0
 for host in dict(C.HOSTS):
  root=W/host/'out'
  for p in root.glob('finish-*/kick/*.tsv'):
   tag=p.parent.parent.name.removeprefix('finish-');j=C.read(W/'jobs'/f'{tag}.json',{})
   if j.get('n',0)<=40:continue
   for line in p.read_text().splitlines():
    tries+=bool(line[:1].isdigit());finds+=line.startswith('# FIND') or ('BEST' in line and line[:1].isdigit())
  for p in root.glob('finish-*/kick/probe.json'):probes+=bool(C.read(p,{}).get('stopped_no_find'))
 for r in production:
  j=r['job'];delta=r['finish']['finish_start_side']-(1+r['score'])*math.sqrt(j['n']);st=stats.setdefault(j['kind'],dict(scans=0,changed=0,max_side_move=0));st['scans']+=1;st['changed']+=delta>1e-8;st['max_side_move']=max(st['max_side_move'],delta)
 failures=[]
 for host in dict(C.HOSTS):
  for p in (W/host/'out').glob('*-status.json'):
   j=C.read(p,{})
   if j.get('n',0)>40 and j.get('returncode'):failures.append(dict(tag=j.get('tag'),n=j.get('n'),returncode=j.get('returncode')))
 result=dict(failed_searches=failures,completed_scans=len(production),tries=tries,raw_finds=finds,stopped_probes=probes,kinds=stats,control_returns=len(records)-len(production));C.atom(W/'measurements.json',result);return result

def git(args):return subprocess.run(['git',*args],cwd=REPO,capture_output=True,text=True,check=True,timeout=120).stdout

def documentation():
 assert len(C.read(W/'archive-verification.json',{}))==2,'both archives must be verified before documentation'
 take=compare();m=measurements();base,live=C.bars();gain=sum(base[n]-float(r['new']) for n,r in take.items())
 rel='lanes/squares/results/classfill-r32-2026-11-16.tsv';shutil.copy2(T/'take.tsv',REPO/rel)
 text='\n\n## Round 32\n\nThe [results table](../results/classfill-r32-2026-11-16.tsv) retains '+str(len(take))+' counts.\nThe gain against bar32 is '+format(gain,'.14g')+'.\n'
 text+='The workers completed '+str(m['completed_scans'])+' scans and '+str(m['tries'])+' perturbation tries.\nShort local kicks used 150 seconds on held counts absent from round 29 to 31 claims.\nChanged rectangles kept priority, with a 120-second probe before a 900-second kick.\nNew searches after 16:45 UTC were capped at 180 seconds. Intake closed at 16:55 UTC.\n'
 text+='Each retained row passed border finesafe at 2.2e-11 and completed a quench from its certified file.\nOriginal-byte audits checked the direct and pandas reads.\nExact input snapshots preserve the held container and inherited source records.\nTyped primary trees bind each output to its numerical inputs.\nThe independent source audit checks retained bytes through those trees.\n'
 text+='Withdrawals apply to pinned bytes. External claims reserve exact starts for 60 minutes.\nOwned layouts have no share gate. Public outputs use the frozen round 31 measure at both required tolerances.\n'
 text+='Both remote archives passed every manifest hash before scratch removal.\nDetailed measurements and immutable receipts remain under `take-classfill-r32/work/` on boxA.\n'
 draft=W/'doc-r32.md';draft.write_text(text)
 checker=Path('$STYLE_CHECK/check.py');subprocess.run(['/opt/homebrew/bin/python3',str(checker),'--level','default',str(draft)],check=True,capture_output=True,text=True)
 doc=REPO/'lanes/squares/avenues/classfill.md';old=doc.read_text();old=old.split('\n\n## Round 32')[0];old=old.replace('at 11:23 UTC','at 11:18 UTC');doc.write_text(old+text)
 tools=REPO/'lanes/squares/tools/classfill/round32';tools.mkdir(exist_ok=True)
 names=['run32.py','fresh32.py','freshguard32.py','sourcecontrol32.py','source32.py','stop32.py','finish32.py','public32.py','pose32.py','ancestry32.py','lineage32.py','retained32.py','finish32-v2.py','finish32-v3.py','deadline32.py','claims32.py','controls32.py','light29.py','physical30.py']
 for name in names:shutil.copy2(W/name,tools/name)
 shutil.copy2(W/'stage/lane/watchdog32.py',tools/'watchdog32.py');shutil.copy2(W/'stage/worker32.py',tools/'worker32.py');shutil.copy2(W/'stage/lane/classfill_finish.py',tools/'classfill_finish.py')
 paths=['lanes/squares/avenues/classfill.md',rel,'lanes/squares/tools/classfill/round32']
 command='git add -- '+' '.join(shlex.quote(p) for p in paths)+' && git commit --only -m '+shlex.quote('squares: record classfill round 32 search and certified results')+' -- '+' '.join(shlex.quote(p) for p in paths)
 for attempt in range(2):
  r=subprocess.run(['sh','-c',command],cwd=REPO,capture_output=True,text=True,timeout=120)
  if r.returncode==0:break
  if 'nothing to commit' in r.stdout:return C.read(W/'git-receipt.json',{})
  if attempt==0 and 'index.lock' in r.stderr:time.sleep(3);continue
  raise RuntimeError(r.stderr or r.stdout)
 sha=git(['log','-1','--format=%H','--',rel]).strip();changed=git(['show','--pretty=format:','--name-only',sha]).splitlines();assert all(p in paths[:2] or p.startswith(paths[2]+'/') for p in changed if p)
 (W/'git-show-stat.txt').write_text(git(['show','--stat','--oneline',sha]));C.atom(W/'git-receipt.json',dict(commits=[sha],pushed=False,files=changed))
 for attempt in range(2):
  try:
   git(['pull','--rebase','--autostash']);sha=git(['log','-1','--format=%H','--',rel]).strip();git(['push','origin','HEAD:main']);break
  except Exception:
   if attempt:raise
   time.sleep(3)
 receipt=dict(commits=[sha],pushed=True,files=changed);C.atom(W/'git-receipt.json',receipt);return receipt

def report():
 take=compare();m=measurements();base,live=C.bars();receipt=C.read(W/'git-receipt.json',{});archive=C.read(W/'archive-verification.json',{})
 next=[]
 for kind,st in sorted(m['kinds'].items(),key=lambda kv:(-kv[1]['changed']/max(1,kv[1]['scans']),-kv[1]['max_side_move'])):
  if st['changed']:next.append(f"Prioritize {kind}: {st['changed']} of {st['scans']} completed starts moved more than 1e-8 of side, maximum {st['max_side_move']:.12g}. Reuse only changed geometry or a justified new seed.")
 if not take:next.insert(0,'Prefer changed rectangle geometry to more held kicks. Round31 measured five meaningful rectangle moves in 37 starts and five short family moves in seven follows. Keep exact claims and changed-byte evidence.')
 next+=['Keep unchanged prepared-only and block/melt repeats closed. Round31 measured zero entries in 15 prepared-only and three block/melt scans.']
 r=dict(lane='classfill',improved_n=len(take),gain=dict(against_base_bar=sum(base[n]-float(v['new']) for n,v in take.items()),beyond_other_live_r32=sum(live[n]-float(v['new']) for n,v in take.items())),take_dir=str(T),summary=f"Retained {len(take)} counts below bar32 and all live takes. Numerical and source receipts are pinned under work/.",what_was_measured=[f"{m['completed_scans']} completed production scans, {m['tries']} perturbation tries, {m['raw_finds']} raw finds.",json.dumps(m['kinds'],sort_keys=True),'Failed production returns: '+json.dumps(m['failed_searches'],sort_keys=True),'The bounded-search control completed both certified-file fq attempts. The overlap control failed both original-byte metric reads.','Every retained CSV has border finesafe certification, a completed certified-file fq receipt and direct/pandas original-byte checks. Independent source checks bind its typed primary input tree. Tampered input and output pins fail the controls.','Owned starts had no share gate. Fresh rectangle roots used a complete imported source walk. Public outputs use frozen share31 at 1e-3 and 1e-2.','Round31 debt closed: 3287 boxE files and 1866 boxD files matched their manifests. Its existing result commit7637fda was on remote main. Recovery record e45617c was pushed.', 'Round32 archives: '+json.dumps(archive,sort_keys=True)],next=next,commits=C.read(W/'code-commits.json',{}).get('commits',['e45617c','72fd339'])+receipt.get('commits',[]),processes_left=[] if len(archive)==2 else ['remote cleanup not verified'],blocked=errors+([] if receipt.get('pushed') else ['not pushed']),repo=str(REPO),branch='main',worktree=str(REPO),pr='none (direct main workflow)')
 C.atom(T/'report.json',r);C.note('REPORT '+C.now()+' rows'+str(len(take))+' gain'+str(r['gain']));return r

def main():
 # Close queue admission, then let active jobs preserve and finish their finds.
 until(C.ADMIT_UNTIL)
 import importlib
 importlib.reload(C)
 (W/'STOP').touch();(W/'STOP_PREPARED').touch()
 for host in dict(C.HOSTS):safe(lambda host=host:C.cmd(['ssh',host,'touch '+C.ROOT+'/STOP']),'close remote admission '+host)
 C.note('DRAIN active jobs finish their search and certified-file fq; no new remote jobs after16:55Z. Archive stop17:08Z, common hard deadline17:15Z.')
 while time.time()<C.END-420 and not (W/'FINISH_NOW').exists():
  safe(C.collect,'drain collect');time.sleep(min(30,max(0,C.END-420-time.time())))
 safe(stop,'stop');safe(C.collect,'collect');safe(verify_retained,'retained verification');safe(archive,'archive');safe(documentation,'documentation');safe(report,'report')
 C.note('FINISH lane work complete; final comparison follows before take deadline17:25Z')
 until(C.END+540)
 before=(T/'take.tsv').read_bytes();safe(compare,'deadline comparison');safe(verify_retained,'deadline retained verification')
 if (T/'take.tsv').read_bytes()!=before:safe(documentation,'deadline table sync')
 safe(report,'final report');C.note('FINAL take and report frozen; owned remote scratch removed after archive verification')
 (W/'FINISHED').touch()
if __name__=='__main__':main()
