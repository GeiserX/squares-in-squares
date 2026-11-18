"""Collect raw finds, certify locally and queue the certified-file fq in slot three."""
import pathlib,os,sys,subprocess,json,csv,re,shutil,math,time
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;os.chdir(W)
if (W/'restart-collect25').exists():
 (W/'restart-collect25').unlink()
 os.execv(sys.executable,[sys.executable,str(W/'resident25.py'),'collect'])
from provenance24 import banned
from source25 import audit
assert 'r27-full-tree-v6:' in audit.__code__.co_consts,'stale source admission module'
(W/'source-runtime26.json').write_text(json.dumps({'version':'r27-full-tree-v1','pid':os.getpid(),'time':time.strftime('%FT%TZ',time.gmtime())}))
def expand(c):
 return audit(c) or {**c,"clean":False}
from seed_notice24 import notice
from eligible24 import SPECIAL,A,E
import fcntl
lock=open(W/'collect.lock','w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:sys.exit(0)
csv.field_size_limit(20000000)
PY=str(S/'venv/bin/python');LANE='.'
# Record each task completion in the append-only lane journal.
subprocess.run(['rsync','-e','ssh -S /tmp/squares-k123-r27-ssh','-az','boxE:scratch/squares-k123/taskdone/',str(W/'taskdone')+'/'],check=True)
finishedfile=W/'finished-tasks.json'
finished=set(json.load(open(finishedfile))) if finishedfile.exists() else set()
for p in sorted((W/'taskdone').glob('*.json')):
 if p.name in finished:continue
 j=json.load(open(p));tag=j['tag'];kind=j['kind'];rc=j['rc']
 log='out/scan'+tag+'.log' if kind=='scan' else 'out/'+tag+('-q.log' if kind=='stepq' else '.log')
 with open(T/'STATE.txt','a') as f:f.write(j['ended']+f' boxE FINISH third22.py task {p.name}, kind={kind}, rc={rc}; log {log}; deadline23:45Z.\n')
 finished.add(p.name)
finishedfile.write_text(json.dumps(sorted(finished)))
statefile=W/'collect-state.json';state=json.load(open(statefile)) if statefile.exists() else {}
# Copy compact result manifests first, then only raw CSVs from new finds.
o=subprocess.run(['ssh','-S','/tmp/squares-k123-r27-ssh','boxE','cd $SCRATCH/squares-k123 && cat out/j22*/done.jsonl out/steps/done.jsonl 2>/dev/null'],capture_output=True,text=True)
(W/'records.jsonl').write_text(o.stdout)
records=[]
for l in o.stdout.splitlines():
 try:records.append(json.loads(l))
 except Exception:pass
pass_started=time.time()
for r in records:
 if time.time()-pass_started>30:break
 key=r['worker']+'-'+r['pool']+'-'+r['tag'];n=r['n']
 if key in state or not r.get('raw'):continue
 D=W/'certs'/key; (D/'raw').mkdir(parents=True,exist_ok=True)
 remote='out/'+r['worker']+'/'+(r['pool']+'-'+str(n)+'-'+r['tag'] if r['worker']!='steps' else r['tag'])+'/raw/'
 subprocess.run(['rsync','-e','ssh -S /tmp/squares-k123-r27-ssh','-az','boxE:scratch/squares-k123/'+remote,str(D/'raw')+'/'],check=True)
 # Keep interrupted CSV writes as evidence, outside the certification input set.
 for rawfile in (D/'raw').glob('*.csv'):
  try:
   rawrows=list(csv.DictReader(open(rawfile)))
   valid=len(rawrows)==n and all(int(q['n'])==n and all(q.get(k) is not None for k in ['n','square_id','x','y','angle']) and all(math.isfinite(float(q[k])) for k in ['x','y','angle']) for q in rawrows)
  except Exception:valid=False
  if not valid:
   (D/'partial').mkdir(exist_ok=True);shutil.move(str(rawfile),str(D/'partial'/rawfile.name))
 if r.get('source',{}).get('recipe_text'):
  donors=r['source']['donors'];source=r['source']['recipe_text']
 elif r['worker']=='steps':
  j=r['source'];donors=[j['n']];source='k123_step.py: n=%s cut %s rows and %s chains, target %s, start %s, then fq' % (j['n'],j['rows'],j['chains'],n,r['tag'])
 else:
  m=re.fullmatch(r'(\d+)(r?)-(\d+)(r?)-j(\d+)-(\d+)-s(-?\d+)',r['tag']);x,xr,y,yr,j1,j2,s=m.groups();donors=[int(x),int(y)]
  source='k123_join.py %s: first band up to chain %s joined with second band from chain %s, shift %s rows; k123_turn.py and fq loop' % (r['tag'],j1,j2,s)
 if r.get('source',{}).get('kick'):source='midm_scan.py 450s seed22, kick and local kick on n=%d from the frozen round21 pool, then certified-file fq' % n
 bp=W/('bars-'+r['pool']+'.tsv')
 if not bp.exists():bp=W/r['pool']/('bars-'+r['pool']+'.tsv')
 manifest=json.load(open(W/('sources-'+r['pool']+'.json'))) if (W/('sources-'+r['pool']+'.json')).exists() else json.load(open(W/r['pool']/('sources-'+r['pool']+'.json')))
 src={int(w[0]):w[3] for l in bp.read_text().splitlines() if (w:=l.split('\t'))}
 for nn in donors:
  c=manifest[str(nn)];source+='; n=%d from %s, source table %s' % (nn,c['origin'],c.get('table',c.get('ledger',c.get('evidence','pinned manifest'))))
 if r.get('source',{}).get('build_up'):source=source.replace('cut %s rows and %s chains' % (r['source']['rows'],r['source']['chains']),'insert %s rows and %s chains' % (r['source']['rows'],r['source']['chains']))
 if r.get('source',{}).get('repair'):source+='; family_step.squeeze repairs the overlapping cut before fq'
 if r.get('source',{}).get('kick'):source=source.replace('k123_step.py:', 'midm_scan.py 450s kick/ local kick seed22, no cut:')
 source+='; immutable input pool '+str((W/r['pool']/(r['pool']+'.csv')) if (W/r['pool']/(r['pool']+'.csv')).exists() else W/(r['pool']+'.csv'))+'; donor paths above name the source at staging time'
 credits=[expand(manifest[str(nn)]) for nn in donors]
 if not all(c.get('clean') and not banned(c.get('origin','')) and not banned(json.dumps(c)) for c in credits):
  state[key]={'status':'source-refused','n':n};continue
 source+='; pinned donor ancestry: '+json.dumps(credits,separators=(',',':'))
 lic='ours, on: '+' | '.join(c['licence'] for c in credits)
 seed_label,seed_flag,seed_ns=notice(source,lic)
 if seed_flag is not False:
  state[key]={'status':'unresolved-seed-ancestry','n':n};continue
 from terms26 import unique
 lic=unique(lic+' | '+seed_label)
 baseline=str(E)
 args=[PY,'-I',LANE+'/methods_take.py',baseline,str(D/'out'),source,str(D/'raw')]
 from remoteverify26 import verify
 o=verify(key,'initial',source,[D/'raw'])
 if o is None:continue
 (D/'cert.log').write_text(o.stdout+o.stderr)
 take=D/'out/take.tsv'
 rows=list(csv.DictReader(open(take),delimiter='\t')) if take.exists() else []
 if not rows:state[key]={'status':'not-certified','n':n};continue
 row=rows[0];score=float(row['new']);other=[]
 existing=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
 if any(int(q['n'])==n and float(q['new'])<=score+1e-10 for q in existing):
  state[key]={'status':'own-lower-before-quench','n':n,'score':score};continue
 row['licence']=lic
 import publication_source26,importlib
 full_initial_source_check=importlib.reload(publication_source26).check
 source_check=full_initial_source_check(D/'out'/f'{n}.csv',row)
 if not source_check['clean']:
  state[key]={'status':'source-refused','n':n,'source_check_file':str(D/'out/source-walk26.json')}
  continue
 for t in list(S.glob('take-*-r27/take.tsv')):
  if t.parent==T:continue
  for q in csv.DictReader(open(t),delimiter='\t'):
   try:
    if int(q['n'])==n and not (n in SPECIAL and seed_flag is False and notice(q.get('source',''),q.get('licence',''))[1] is not False):other.append(float(q['new']))
   except (ValueError,KeyError):pass
 if other and score>=min(other)-1e-10:
  shutil.copy(D/'out'/f'{n}.csv',T/'near'/f'{n}-{key}.csv')
  pathlib.Path(str(T/'near'/f'{n}-{key}.csv')+'.json').write_text(json.dumps(dict(n=n,source=source,licence=lic,score=score)))
  with open(S/'handoff-r27.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: near n={n}, certified against round25b bar but another take is lower; source in work/certs/{key}/out/take.tsv, {T}/near/{n}-{key}.csv\n')
  state[key]={'status':'not-below-takes','n':n,'score':score,'other':min(other)};continue
 # Certified-file quench must run before publishing. A cert task uses the third slot.
 near_stage=T/'near'/f'{n}-pending-{key}.csv'
 if not near_stage.exists():
  shutil.copy(D/'out'/f'{n}.csv',str(near_stage)+'.tmp');os.replace(str(near_stage)+'.tmp',near_stage)
  pathlib.Path(str(near_stage)+'.json').write_text(json.dumps(dict(n=n,source=source,licence=lic,score=score)))
  with open(S/'handoff-r27.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: uncounted initial-certified near n={n}, score={score:.15g}; awaiting required certified-file boxE quench; source {D}/out/take.tsv, {near_stage}\n')
 tag='cert-'+key
 job=dict(kind='cert',tag=tag,**{'in':f'certs/{key}/in','out':f'certs/{key}/fq','take':f'certs/{key}/take.tsv'})
 subprocess.run(['ssh','-S','/tmp/squares-k123-r27-ssh','boxE',f'mkdir -p scratch/squares-k123/certs/{key}/in'],check=True)
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r27-ssh','-o','ControlMaster=auto','-o','ControlPersist=600','-q',str(D/'out'/f'{n}.csv'),'boxE:scratch/squares-k123/'+job['in']+'/'],check=True)
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r27-ssh','-o','ControlMaster=auto','-o','ControlPersist=600','-q',str(take),'boxE:scratch/squares-k123/'+job['take']],check=True)
 (D/(tag+'.json')).write_text(json.dumps(job))
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r27-ssh','-o','ControlMaster=auto','-o','ControlPersist=600','-q',str(D/(tag+'.json')),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r27-ssh','boxE',f'mv scratch/squares-k123/tasks/{tag}.json.tmp scratch/squares-k123/tasks/{tag}.json'],check=True)
 state[key]=dict(status='quench-pending',n=n,source=source,licence=lic,tag=tag,pool=r['pool'],donors=donors,ancestry_expanded=True,samanyu_seed_n=seed_ns,samanyu=seed_flag,baseline=baseline)
 statefile.with_suffix('.tmp').write_text(json.dumps(state,indent=2));statefile.with_suffix('.tmp').replace(statefile)
 with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' CERT initial {n}, score {score:.15g}; queued certified-file fq in third boxE slot ({tag}), log work/certs/{key}/cert.log.\n')
# Finish pending certification tasks.
for key,r in list(state.items()):
 if r['status']!='quench-pending':continue
 tag=r['tag'];n=r['n'];D=W/'certs'/key
 if r.get('pool'):
  pp=r['pool'];mp=W/pp/('sources-'+pp+'.json');manifest=json.load(open(mp))
  credits=[expand(manifest[str(nn)]) for nn in r['donors']]
  if not all(c.get('clean') and not banned(c.get('origin','')) and not banned(json.dumps(c)) for c in credits):
   r['status']='withdrawn-before-publish';continue
  if not r.get('ancestry_expanded'):
   r['source']+='; expanded recorded donor ancestry: '+json.dumps(credits,separators=(',',':'));r['licence']='ours, on: '+' | '.join(c['licence'] for c in credits);r['ancestry_expanded']=True
 chk=subprocess.run(['ssh','-S','/tmp/squares-k123-r27-ssh','boxE',f'cat scratch/squares-k123/taskdone/{tag}.json 2>/dev/null'],capture_output=True,text=True)
 if not chk.stdout:continue
 j=json.loads(chk.stdout)
 if j['rc']!=0:r['status']='quench-error';continue
 (D/'fq').mkdir(exist_ok=True);subprocess.run(['rsync','-e','ssh -S /tmp/squares-k123-r27-ssh','-az','--include=*.csv','--exclude=*','boxE:scratch/squares-k123/certs/'+key+'/fq/',str(D/'fq')+'/'],check=True)
 out=D/'final'
 from remoteverify26 import verify
 o=verify(key,'final',r['source'],[D/'out',D/'fq'])
 if o is None:continue
 (D/'final.log').write_text(o.stdout+o.stderr)
 rows=list(csv.DictReader(open(out/'take.tsv'),delimiter='\t'))
 if not rows:r['status']='final-dropped';continue
 row=rows[0];score=float(row['new']);others=[]
 for t in list(S.glob('take-*-r27/take.tsv')):
  if t.parent==T:continue
  for q in csv.DictReader(open(t),delimiter='\t'):
   try:
    if int(q['n'])==n and not (n in SPECIAL and r.get('samanyu') is False and notice(q.get('source',''),q.get('licence',''))[1] is not False):others.append(float(q['new']))
   except (ValueError,KeyError):pass
 if others and score>=min(others)-1e-10:r['status']='overtaken-before-publish';continue
 old=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'))
 own=next((q for q in old if int(q['n'])==n),None)
 if n in SPECIAL and own:
  old_flag=notice(own.get('source',''),own.get('licence',''))[1]
  if r.get('samanyu') is False and old_flag is not False:
   saved=T/'near'/f'{n}-samanyu-prior-{key}.csv';shutil.copy(T/f'{n}.csv',saved);pathlib.Path(str(saved)+'.json').write_text(json.dumps(own));old=[q for q in old if int(q['n'])!=n]
  elif r.get('samanyu') is not False and old_flag is False:
   saved=T/'near'/f'{n}-provisional-{key}.csv';shutil.copy(out/f'{n}.csv',saved);pathlib.Path(str(saved)+'.json').write_text(json.dumps(dict(n=n,source=r['source'],licence=r['licence'])));r['status']='provisional-below-clean-take';continue
 if any(int(q['n'])==n and float(q['new'])<=score+1e-10 for q in old):r['status']='own-lower';continue
 seed_label,seed_flag,seed_ns=notice(r['source'],r['licence'])
 if seed_flag is not False:r['status']='unresolved-seed-ancestry';continue
 if 'Samanyu-dev seed ancestry:' not in r['licence']:r['licence']+=' | '+seed_label
 from terms26 import unique
 r['licence']=unique(r['licence'])
 row['licence']=r['licence'];row['gain']=repr(float(row['held'])-score)
 import publication_source26,importlib
 full_source_check=importlib.reload(publication_source26).check
 source_check=full_source_check(out/f'{n}.csv',row)
 if not source_check['clean']:
  r['status']='source-refused';r['source_check_file']=str(out/'source-walk26.json')
  with open(T/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' DROP source-refused raw n={n}; complete source walk failed; record {out}/source-walk26.json; deadline23:45Z.\n')
  continue
 old=[q for q in old if int(q['n'])!=n]+[row];old.sort(key=lambda q:int(q['n']))
 shutil.copy(out/f'{n}.csv',T/f'{n}.csv.tmp');os.replace(T/f'{n}.csv.tmp',T/f'{n}.csv')
 with open(T/'take.tsv.tmp','w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');w.writeheader();w.writerows(old)
 os.replace(T/'take.tsv.tmp',T/'take.tsv')
 from replacements25 import register
 register(T/f'{n}.csv',row)
 r['status']='published';r['score']=score;r['gain_over_other_at_publish']=(min(others) if others else float(row['held']))-score
 msg=f'{time.strftime("%FT%TZ",time.gmtime())} k123 -> all: certified n={n}, score={score:.15g}, gain={row["gain"]}, recipe {key}, source record {T}/take.tsv, certified-file quench receipt {D}/fq, {T}/{n}.csv\n'
 with open(S/'handoff-r27.log','a') as f:f.write(msg.replace('k123 -> all:', 'k123 -> forensics,readers,family,border,soft,all:'))
 with open(T/'STATE.txt','a') as f:f.write(msg)
 print('PUBLISHED',n,score,flush=True)
statefile.with_suffix('.tmp').write_text(json.dumps(state,indent=2));statefile.with_suffix('.tmp').replace(statefile)

lock.close()
