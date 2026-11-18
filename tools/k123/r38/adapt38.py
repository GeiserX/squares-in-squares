"""Retarget the frozen k123 scripts that the round 38 runtime reuses."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = Path('$SCRATCH/bounties-squares/take-k123-r38/work')


def change(name, old, new):
    path = WORK / name
    body = path.read_text()
    if new in body:
        return
    if old not in body:
        raise ValueError(f'{name} lacks expected source {old!r}')
    body = body.replace(old, new)
    compile(body, str(path), 'exec')
    path.write_text(body)


def apply():
    change('box_guard34.py', 'import os,subprocess,signal,time,json\n',
           'import os,subprocess,signal,time,json,sys\n')
    change('box_guard34.py', 'def rows():\n out=[]',
           'sys.path.insert(0,str(R))\nfrom idle38 import queue_identity, should_start\n\ndef rows():\n out=[]')
    change('box_guard34.py', "  if not paused:\n   ps=rows();",
           """  if requeued:
   for marker in R.glob('idle-*38'):marker.unlink(missing_ok=True)
  if not paused:
   queue=queue_identity(R);searching=time.time()<float((R/'search-deadline').read_text())
   following=time.time()<float((R/'own-follow-deadline').read_text())
   ps=rows();""")
    change('box_guard34.py',
           "    if slot!='third' and time.time()>=float((R/'search-deadline').read_text()):continue",
           "    if not should_start(R,slot,queue,searching,following):continue")
    change('qrun22.py', 'from live_guard37 import should_stop\ndef live_lower37',
           'from live_guard37 import should_stop\nfrom idle38 import mark_idle\ndef live_lower37')
    change('qrun22.py', " queue=(R/'queue.tsv').read_text().splitlines()",
           " queue_bytes=(R/'queue.tsv').read_bytes();queue=queue_bytes.decode().splitlines()")
    change('qrun22.py', " if '--once' in sys.argv:break\n if not found:time.sleep(10)",
           """ if not found:mark_idle(R,slot,hashlib.sha256(queue_bytes).hexdigest())
 if '--once' in sys.argv or not found:break""")
    change('third22.py', "running=R/'running34/worker'","sys.path.insert(0,str(R))\nfrom idle38 import accepts_task, exhausted, queue_identity\nrunning=R/'running34/worker'")
    change('third22.py',
           " if time.time()>=float((R/'search-deadline').read_text()):jobs=[p for p in jobs if json.load(open(p)).get('kind') in ('cert','verify')]",
           """ searching=time.time()<float((R/'search-deadline').read_text())
 following=time.time()<float((R/'own-follow-deadline').read_text())
 jobs=[p for p in jobs if accepts_task(p,searching,following)]""")
    change('third22.py', '  time.sleep(1);continue\n p=jobs[0]',
           "  if not searching or exhausted(R,runtime.get('spare_join','j22c'),queue_identity(R)): break\n  time.sleep(1);continue\n p=jobs[0]")
    change('follow_runner37.py', "float((ROOT / 'search-deadline').read_text())",
           "float((ROOT / 'own-follow-deadline').read_text())")
    change('third22.py', "p.name.startswith('fresh-follow37-')", "p.name.startswith('own-follow38-')")
    change('third22.py',
           " rank=0 if native else 1 if follow else 2 if near else 3 if fresh else 4\n return (rank,p.stat().st_mtime if rank<2 else -p.stat().st_mtime)",
           """ try:
  mtime=p.stat().st_mtime
  task=json.loads(p.read_text()) if fresh else {}
 except (OSError,ValueError):
  return (5,0)
 primary=task.get('origin_kind')=='fresh-certificate' and '/near/' not in task.get('source','')
 rank=0 if native else 1 if follow else 2 if primary else 3 if near else 4
 return (rank,mtime if rank<3 else -mtime)""")
    change('collect22.py',
           " with open(T/'STATE.txt','a') as f:f.write(j['ended']+f' boxE FINISH third22.py task",
           """ box=j.get('worker_box','boxE')
 if box=='boxD':log=W/'routed-boxCD38'/tag/('scan'+tag+'.log')
 with open(T/'STATE.txt','a') as f:f.write(j['ended']+f' {box} FINISH worker task""")
    if "geometry=queue(path,row,result,source_check,key)" not in (WORK / 'collect22.py').read_text():
        change('collect22.py',
           " # The source walk can be long. Read live peers again immediately before the atomic write.",
           """ # Preserve an immutable native certificate for the producer's follow.
 from own_follow38 import queue
 import hashlib
 import floatsafe
 prepared=D/'own38';certified=prepared/'certified';certified.mkdir(parents=True,exist_ok=True)
 path=prepared/f'{n}.csv';shutil.copyfile(out/f'{n}.csv',path)
 shutil.copyfile(D/'out'/f'{n}.csv',certified/f'{n}.csv')
 shutil.copytree(D/'fq',prepared/'fq',dirs_exist_ok=True)
 receipt=json.load((prepared/'fq'/f'{n}-quench.json').open())
 clearance=floatsafe.clearance(list(csv.DictReader(path.open())))
 result=dict(n=n,score=score,side=(score+1)*n**.5,clearance=clearance,csv_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),full_fq_loop=True,fq=receipt)
 assert receipt['completed'] and receipt['full_fq_loop'] and clearance>=2.2e-11
 r.update(status='own-follow-pending',geometry=queue(path,row,result,source_check,key),score=score)
 continue
 # The source walk can be long. Read live peers again immediately before the atomic write.""")
    # The older direct publication path is replaced by the durable own follow packet.
    path = WORK / 'collect22.py'
    body = path.read_text()
    if ' # The source walk can be long.' in body:
        start = body.index(' # The source walk can be long.')
        end = body.index('statefile.with_suffix', start)
        path.write_text(body[:start] + body[end:])
    change('near36.py',
           "if gap>=1e-4 or rroom<=0:j['status']='no-room';continue",
           "if gap>1e-6 or (gap>=-1e-10 and rroom<=0):j['status']='outside-near-window';continue")
    change('near36.py', " if abs(gap)<=1e-10:j['status']='at-bar-no-leg';continue",
           """ if abs(gap)<=1e-10:j['status']='at-bar-no-leg';continue
 if gap>0:
  retired=W/'retired-donor-endpoints38.json'
  endpoints=json.loads(retired.read_text()) if retired.is_file() else {}
  if n in {367,372,591,634,642} or str(n) in endpoints.get('closed_counts',[]) or seed_fell_back(n):
   j.update(status='closed-donor-count',score=result['score'],gap=gap);continue
  if any(abs(result['score']-end)<=5e-11 for end in endpoints.get(str(n),[])):
   j.update(status='repeated-donor-endpoint',score=result['score'],gap=gap);continue""")
    change('near36.py', 'def room(n,side):',
           """def seed_fell_back(n):
 source=S/'take-classfill-r38/STATE.txt'
 if not source.is_file():return False
 with source.open('rb') as stream:
  stream.seek(max(0,source.stat().st_size-262144))
  return bool(re.search(rb' BASIN n'+str(n).encode()+rb': .*every further donor at n skipped',stream.read()))
def room(n,side):""")
    change('near36.py', """ held_matches=held_share(p,n)
 row=""", """ held_matches=held_share(p,n) if gap>=-1e-10 else (None,None)
 if gap>=-1e-10 and held_matches[0]>=.5:j.update(status='held-share-high',held_share=held_matches[0],gap=gap);continue
 row=""")
    change('near36.py',
           " promoted=publisher.publish(n,p,row,result,proof,j.get('producer_job',key),bar[n]) if result['score']<publisher.best_live_score(n,bar[n])-1e-10 else None\n  if promoted:\n   j.update(status='promoted',path=promoted['path'],score=result['score'],gap=gap,board_room=rroom)\n   print('PROMOTED fully certified near',n,result['score'],flush=True);continue",
           " from own_follow38 import queue\n  if result['score']<publisher.best_live_score(n,bar[n])-1e-10:\n   j.update(status='own-follow-pending',geometry=queue(p,row,result,proof,j.get('producer_job',key)),score=result['score'],gap=gap,board_room=rroom)\n  else:j.update(status='peer-lower',score=result['score'],gap=gap)\n  continue")
    if ' from bind_row30 import bind' not in (WORK / 'near36.py').read_text():
        change('near36.py', """ proof=check(p,row)
""", """ from bind_row30 import bind
 pool=j.get('pool')
 if pool:
  manifest=json.loads((W/pool/('sources-'+pool+'.json')).read_text())
  row=bind(row,manifest,j['donors'],pool,key+'-near38-v2')
 proof=check(p,row)
""")
    change('near36.py', """ and -1e-9<r['side']/r['n']**.5-1-bar[r['n']]<1e-4 and room(r['n'],r['side'])>0 and """,
           """ and (gap_for(r)<-1e-10 or gap_for(r)<1e-6 and room(r['n'],r['side'])>0) and """)
    change('near36.py', "def key(r):return r['worker']+'-'+r['pool']+'-'+r['tag']\nchoices=",
           """def key(r):return r['worker']+'-'+r['pool']+'-'+r['tag']
def gap_for(r):return r['side']/r['n']**.5-1-bar[r['n']]
choices=""")
    change('near36.py', "choices.sort(key=lambda r:-room(r['n'],r['side']))",
           "choices.sort(key=lambda r:(0 if gap_for(r)<-1e-10 else 1 if gap_for(r)<=1e-7 else 2,-room(r['n'],r['side'])))")
    change('near36.py', "j=dict(kind='verify',near_donor36=True,tag=tag,n=n,raw=raw,out=out,source=source,licence=",
           "j=dict(kind='verify',near_donor36=True,tag=tag,n=n,raw=raw,out=out,source=source,pool=pool,donors=[int(m[1]),int(m[3])],licence=")
    change('prejoin31.py', ' meta=json.load(mp.open());ns=[match[1],match[3]]\n from source25 import audit',
           """ meta=json.load(mp.open());ns=[match[1],match[3]]
 # The third seam is the last seam in this experiment.
 if any('/private-near36/' in meta[z].get('origin','') for z in ns):continue
 from source25 import audit""")
    change('publish_certified36.py', 'promoted certified near from {producer_job}', 'own 180 s follow completed for {producer_job}')
    change('publish_certified36.py', "  for name in ['certified','fq']:",
           """  archive=D/'final'/f'{n}.csv'
  Path(str(archive)+'.json').write_text(json.dumps(row))
  for name in ['certified','fq']:""")
    change('publish_certified36.py', 'capped=False, {T}/{n}.csv',
           'capped=False, immutable certificate {archive} (sha256 {digest}), {T}/{n}.csv')
    change('bind_row30.py', 'import json,csv,hashlib,re,os\n',
           'import json,csv,hashlib,re,os\nfrom pinned_path38 import replace_path\n')
    change('bind_row30.py', "for a,b in M.items():job['source']=job['source'].replace(a,b)",
           "for a,b in M.items():job['source']=replace_path(job['source'],a,b)")
    change('bind_row30.py', 'key=lambda z:-len(z[0])):text=text.replace(a,b)',
           'key=lambda z:-len(z[0])):text=replace_path(text,a,b)')
    change('collect22.py', "key+'-initial');source=row['source']",
           "key+'-initial-pin38');source=row['source']")
    change('peer33.py',
           """  if not Path(str(p)+'.json').exists():Path(str(p)+'.json').write_text(json.dumps(r))
  D=W/'superseded33';D.mkdir(exist_ok=True);(D/f'{n}-{hashlib.sha256(p.read_bytes()).hexdigest()}.json').write_text(json.dumps(r))""",
           """  D=W/'superseded33';D.mkdir(exist_ok=True)
  payload=p.read_bytes();digest=hashlib.sha256(payload).hexdigest()
  copy=D/f'{n}-{digest}.csv'
  if not copy.exists():copy.write_bytes(payload)
  record=Path(str(copy)+'.json')
  if not record.exists():record.write_text(json.dumps(r))""")
    for name in ['feed38.py', 'own_follow38.py', 'idle38.py', 'pinned_path38.py']:
        (WORK / name).write_bytes((HERE / 'runtime' / name).read_bytes())


if __name__ == '__main__':
    apply()
