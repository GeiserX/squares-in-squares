"""Publish a fully certified near result only after a fresh live-peer check under the take lock."""
from pathlib import Path
import csv,json,hashlib,shutil,fcntl,time,os
DEFAULT_W=Path(__file__).resolve().parent
FIELDS=['n','held','new','gain','source','licence']

def best_live_score(n,bar,work=None,include_own=True):
 W=Path(work) if work else DEFAULT_W;T=W.parent;S=T.parent;best=float(bar)
 csv.field_size_limit(1<<28)
 for table in S.glob('take-*-r36/take.tsv'):
  if not include_own and table.parent==T:continue
  for row in csv.DictReader(open(table),delimiter='\t'):
   try:
    if int(row['n'])==int(n):best=min(best,float(row['new']))
   except (ValueError,KeyError):pass
 return best

def publish(n,path,meta,result,proof,producer_job,bar,work=None,do_register=True):
 W=Path(work) if work else DEFAULT_W;T=W.parent;S=T.parent;W.mkdir(parents=True,exist_ok=True);path=Path(path);n=int(n);score=float(result['score']);digest=hashlib.sha256(path.read_bytes()).hexdigest()
 assert int(result['n'])==n and int(meta['n'])==n
 assert digest==result['csv_sha256'] and digest==proof['csv_sha256']
 assert proof['clean'] and not proof.get('capped',False) and result['clearance']>=2.2e-11
 fq=result['fq'];assert result['full_fq_loop'] and fq['full_fq_loop'] and fq['completed']
 source_dir=path.parent;certified=source_dir/'certified'/f'{n}.csv';assert hashlib.sha256(certified.read_bytes()).hexdigest()==fq['input_sha256']
 csv.field_size_limit(1<<28)
 with open(W/'collect.lock','a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);best=best_live_score(n,bar,work=W);other_best=best_live_score(n,bar,work=W,include_own=False)
  if score>=best-1e-10:return None
  row={'n':str(n),'held':repr(float(bar)),'new':repr(score),'gain':repr(float(bar)-score),'source':meta['source'],'licence':meta['licence']}
  key='near36-'+digest[:16]+'-'+producer_job;D=W/'certs'/key;(D/'final').mkdir(parents=True,exist_ok=True);shutil.copy(path,D/'final'/f'{n}.csv')
  for name in ['certified','fq']:
   if (source_dir/name).exists():shutil.copytree(source_dir/name,D/name,dirs_exist_ok=True)
  (D/'result36.json').write_text(json.dumps(result));(D/'source-check36.json').write_text(json.dumps(proof))
  with open(D/'final/take.tsv','w') as f:
   writer=csv.DictWriter(f,FIELDS,delimiter='\t');writer.writeheader();writer.writerow(row)
  old=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t')) if (T/'take.tsv').exists() else []
  old=[r for r in old if int(r['n'])!=n]+[row];old.sort(key=lambda r:int(r['n']))
  shutil.copy(path,T/f'{n}.csv.tmp');(T/f'{n}.csv.tmp').replace(T/f'{n}.csv')
  with open(T/'take.tsv.tmp','w') as f:
   writer=csv.DictWriter(f,FIELDS,delimiter='\t');writer.writeheader();writer.writerows(old)
  (T/'take.tsv.tmp').replace(T/'take.tsv')
  if do_register:
   from replacements25 import register
   register(T/f'{n}.csv',row)
  statepath=W/'collect-state.json';state=json.load(open(statepath)) if statepath.exists() else {}
  state[key]={'status':'published','n':n,'score':score,'source':row['source'],'licence':row['licence'],'producer_job':producer_job,'gain_over_other_at_publish':other_best-score,'full_fq_loop':True,'csv_sha256':digest}
  tmp=statepath.with_suffix('.tmp');tmp.write_text(json.dumps(state));tmp.replace(statepath)
  line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: certified n={n}, score={score:.15g}, gain={row["gain"]}, promoted certified near from {producer_job}, full_fq_loop, walk_files={proof["files"]}, capped=False, {T}/{n}.csv\n'
  for log in [T/'STATE.txt',S/'handoff-r36.log']:
   with open(log,'a') as f:f.write(line)
  return {'key':key,'path':str(T/f'{n}.csv'),'score':score,'gain':float(bar)-score}
