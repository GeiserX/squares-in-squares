from pathlib import Path
import sys,json,csv,hashlib,shutil,subprocess,datetime
W=Path(__file__).parent;T=W.parent;S=T.parent;old=S/'take-border-r23/work'
sys.path.insert(0,str(W));sys.path.insert(0,'.')
from provenance import audit_manifest
import border_sweep as b
csv.field_size_limit(16000000)
manifest={r['id']:r for r in csv.DictReader(open(old/'q/manifest.tsv'),delimiter='\t')}
known={hashlib.md5(p.read_bytes()).hexdigest() for p in (W/'q').glob('*.start.txt') if p.with_name(p.name.removesuffix('.start.txt')+'.job.json').exists()}
new=[]
for row in csv.DictReader(open(old/'unstarted.tsv'),delimiter='\t'):
 ident=row['id'];r=manifest[ident];start=old/'q'/(ident+'.start.txt');job=W/'q'/(ident+'.job.json')
 if job.exists() or (W/'q'/(ident+'.k0.json')).exists() or not start.exists() or not audit_manifest(r):continue
 b.check_start(str(old/'q'),r)
 digest=hashlib.md5(start.read_bytes()).hexdigest()
 if digest in known:continue
 dst=W/'q'/start.name
 if dst.exists():assert dst.read_bytes()==start.read_bytes()
 else:shutil.copyfile(start,dst)
 if r.get('donor_copy'):shutil.copyfile(old/'q'/r['donor_copy'],W/'q'/r['donor_copy'])
 job.write_text(json.dumps(dict(start=start.name,priority=10+float(row['margin']),adopted_r23=True,recovered_source=True)))
 known.add(digest);new.append(r)
if new:
 with (W/'q/manifest.tsv').open('a') as f:
  wr=csv.DictWriter(f,fieldnames=list(new[0]),delimiter='\t');wr.writerows(new)
 # Send starts before the jobs can be claimed.
 subprocess.run(['rsync','-a','--ignore-existing','--include','*.start.txt','--exclude','*',str(W/'q')+'/', 'boxC:scratch/squares-border-r24/q/'],check=True)
 jobs=W/'recovered-jobs';jobs.mkdir(exist_ok=True)
 for r in new:shutil.copyfile(W/'q'/(r['id']+'.job.json'),jobs/(r['id']+'.job.json'))
 subprocess.run(['rsync','-a',str(jobs)+'/', 'boxC:scratch/squares-border-r24/q/'],check=True)
with (T/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+f' boxA ADOPT {len(new)} extra unstarted r23 starts after reader-source recovery. Every start passed its retained SHA-256 recipe check. Sources were rechecked with the current resolver. Command recover_unstarted.py, log recover-unstarted.log, deadline22:15Z.\n')
print('recovered clean exact unstarted jobs',len(new),flush=True)
