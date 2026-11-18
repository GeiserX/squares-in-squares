from pathlib import Path
import csv,json,math,subprocess,sys,shutil,hashlib
W=Path(__file__).parent
csv.field_size_limit(16000000)
sys.path.insert(0,str(W))
import source_policy as sp
def source_bonus(policy,n):
 return -2 if policy['status']=='none' else 200  # r25/r26: seeds and unresolved never publish, so they never take a slot
def rank(donor,margin,untried_count,record=None,bar=None):
 bonus=8 if donor in (931,870,794) else 5 if donor in (847,860) else 0
 value=-90-bonus+100*max(0,margin)-(4 if untried_count else 0)
 if record and bar is not None:
  gap=record['s_final']-bar;den=record['s_start']-bar
  if (record.get('round')==1 and record.get('cut') and 0<gap<.003 and den>0 and record['s_start']-record['s_final']>.001 and (record['s_start']-record['s_final'])/den>.3):value=-124
  if 0<gap<.001 and den>0 and (record['s_start']-record['s_final'])/den>.75:value=-135
 return value
if '--control' in sys.argv:
 # The previous fresh policy tied these measured pairs. The revised order must prefer931.
 old=lambda donor:-90
 assert not old(931)<old(911)
 assert rank(931,.006,False)<rank(911,.006,False)<rank(873,.019,False)
 assert rank(931,.006,False,{'s_final':31.9005,'s_start':31.906},31.9)==-135
 assert rank(634,.00426,False,{'s_final':26.002584,'s_start':26.004260,'round':1,'cut':True},26.)==-124
 assert -110 >= rank(931,.006,True)-20
 assert rank(634,.00426,False,{'s_final':26.002584,'s_start':26.004260,'round':1,'cut':True},26.) < rank(931,.006,True)-20
 assert rank(931,.006,True)-20 < -100+.006*100-20 < rank(911,.006,False)-20
 assert source_bonus({'status':'none'},735)<source_bonus({'status':'seeds'},735)<=source_bonus({'status':'unknown'},735)
 print('priority control: old931/911 tie; new931 before911 before873; promising saved round=-135')
 raise SystemExit
import fcntl
lock=open(W/'priority.lock','w')
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
 print('priority update already running',flush=True);raise SystemExit
cachefile=W/'source-classification.json'
cache=json.load(open(cachefile)) if cachefile.exists() else {}
man={r['id']:r for r in csv.DictReader(open(W/'q/manifest.tsv'),delimiter='\t')}
bars={int(n):float(v) for n,v in json.load(open(W/'bars.json')).items()}
seen={int(p.name.split('-')[0]) for p in (W/'q').glob('*.k0.json')}
updates=W/'priority';updates.mkdir(exist_ok=True);count=0
for p in (W/'q').glob('*.job.json'):
 j=json.load(open(p))
 if j.get('k'):continue
 ident=p.name.removesuffix('.job.json');r=man[ident];n=int(r['n']);rec=W/'q'/(ident+'.k0.json');record=json.load(open(rec)) if rec.exists() else None
 margin=float(r['built_L'])-bars[n]
 backlog_first=False and bool(j.get('adopted_r23') and record is None and n not in seen and margin<.006)
 if not j.get('fresh23') and record is None and not backlog_first:continue
 value=rank(int(r['donor']),float(r['built_L'])-bars[n],n not in seen,record,bars[n])
 base=j.get('priority_base',j['priority'])
 if not j.get('fresh23') and value>=-100:value=base
 if backlog_first:value=-100+100*max(0,margin)
 digest=hashlib.sha256(('full-parent-v4'+r['donor_source']+r.get('donor_licence','')).encode()).hexdigest()
 entry=cache.get(ident)
 if entry is None or entry['digest']!=digest:
  entry=cache[ident]=dict(digest=digest,policy=sp.manifest_policy(r))
 value+=source_bonus(entry['policy'],n)
 j['priority_base']=base
 if abs(value-j['priority'])<1e-8:continue
 j['priority']=value;p.write_text(json.dumps(j));shutil.copyfile(p,updates/p.name);count+=1
if count:
 subprocess.run(['rsync','-a',str(updates)+'/', 'boxC:scratch/squares-border-r26/q/'],check=True)
 for p in updates.glob('*.json'):p.unlink()
tmp=cachefile.with_suffix('.tmp');tmp.write_text(json.dumps(cache));tmp.replace(cachefile)
print('priority updates',count,'source groups',dict(__import__('collections').Counter(v['policy']['status'] for v in cache.values())),flush=True)
