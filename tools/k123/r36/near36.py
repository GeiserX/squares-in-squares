"""Return certified non-winning joins in board-room order."""
from pathlib import Path
import sys,json,csv,hashlib,subprocess,re,time,shutil
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;sys.path[:0]=[str(W),str(W/'lane')]
from provenance24 import mlp
from compact_source28 import credits
from publication_source26 import check
SSH=['ssh','-S','/tmp/squares-k123-r36-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r36-ssh'];csv.field_size_limit(1<<28)
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round36-briefs/bar36.tsv'),delimiter='\t')};board={int(r['n']):float(r['board_L'])/int(r['n'])**.5-1 for r in csv.DictReader(open(W/'board.tsv'),delimiter='\t')}
def room(n,side):return bar[n]-board[n]-(side/n**.5-1-bar[n])
statefile=W/'near-state36.json';state=json.load(open(statefile)) if statefile.exists() else {}
# Durable hand-queued requests merge in this single writer, without racing near-state updates.
for request in (W/'near-inbox36').glob('*.json'):
 queued=json.load(open(request));state.setdefault(queued['request_key'],{k:v for k,v in queued.items() if k!='request_key'})
# Finish completed jobs before dispatching another donor.
for key,j in list(state.items()):
 if j['status']!='queued':continue
 done=W/'taskdone'/('verify-near36-'+key+'.json')
 if not done.exists():continue
 if json.load(open(done))['rc']!=0:j['status']='numeric-failed';continue
 D=W/'near-cert36'/key;D.mkdir(parents=True,exist_ok=True)
 subprocess.run(['rsync','-az','-e','ssh -S /tmp/squares-k123-r36-ssh','boxE:scratch/squares-k123/'+j['out']+'/',str(D)+'/'],check=True)
 result=json.load(open(D/'result36.json'));n=j['n'];p=D/f'{n}.csv';assert hashlib.sha256(p.read_bytes()).hexdigest()==result['csv_sha256'];gap=result['score']-bar[n];rroom=room(n,result['side'])
 if gap>=1e-4 or rroom<=0:j['status']='no-room';continue
 if abs(gap)<=1e-10:j['status']='at-bar-no-leg';continue
 A=mlp.load(str(p),{n})[n]
 duplicate=False
 for prior in state.values():
  if prior.get('status')!='published' or prior.get('n')!=n or not prior.get('path'):continue
  B=mlp.load(prior['path'],{n})[n]
  if A.shape==B.shape and __import__('numpy').max(__import__('numpy').abs(A-B))<1e-9:duplicate=True;break
 if duplicate:j['status']='duplicate-geometry';continue
 row={'n':str(n),'source':j['source'],'licence':j['licence'],'csv_sha256':result['csv_sha256'],'certified_clearance':result['clearance'],'full_fq_loop':result['fq'],'gap_to_bar':gap,'board_room':rroom}
 proof=check(p,row)
 if not proof['clean'] or proof.get('capped',False):j['status']='source-refused';continue
 if gap < -1e-10:
  import publish_certified36,importlib
  publisher=importlib.reload(publish_certified36)
  promoted=publisher.publish(n,p,row,result,proof,j.get('producer_job',key),bar[n]) if result['score']<publisher.best_live_score(n,bar[n])-1e-10 else None
  if promoted:
   j.update(status='promoted',path=promoted['path'],score=result['score'],gap=gap,board_room=rroom)
   print('PROMOTED fully certified near',n,result['score'],flush=True);continue
 dest=T/'near'/f'{n}-join36-{result["csv_sha256"][:16]}.csv';Path(str(dest)+'.json').write_text(json.dumps(row));shutil.copy(p,str(dest)+'.tmp');Path(str(dest)+'.tmp').replace(dest)
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: certified near donor n={n}, side={result["side"]:.14g}, score={result["score"]:.15g}, gap_to_bar={gap:.9g}, board_room={rroom:.9g}, sha256={result["csv_sha256"]}, finesafe2.2e-11 full_fq_loop, walk_files={proof["files"]}, capped={proof.get("capped",False)}, {dest}\n'
 for log in [S/'handoff-r36.log',T/'STATE.txt']:
  with log.open('a') as f:f.write(line)
 j.update(status='published',path=str(dest),score=result['score'],gap=gap,board_room=rroom);print(line,flush=True)
statefile.write_text(json.dumps(state))
if sum(j['status']=='queued' for j in state.values())>=2:raise SystemExit
records=[json.loads(l) for l in (W/'records.jsonl').read_text().splitlines()]
def key(r):return r['worker']+'-'+r['pool']+'-'+r['tag']
choices=[r for r in records if key(r) not in state and r.get('code')==0 and 'side' in r and not r.get('raw') and -1e-9<r['side']/r['n']**.5-1-bar[r['n']]<1e-4 and room(r['n'],r['side'])>0 and r['worker'].startswith('j22')]
choices.sort(key=lambda r:-room(r['n'],r['side']))
for r in choices[:1]:
 k=key(r);n=r['n'];pool=r['pool'];D=W/'near-cert36'/k;D.mkdir(parents=True,exist_ok=True)
 mp=W/pool/('sources-'+pool+'.json')
 if not mp.exists():continue
 m=re.fullmatch(r'(\d+)(r?)-(\d+)(r?)-j(\d+)-(\d+)-s(-?\d+)',r['tag'])
 if not m:continue
 from source25 import audit
 meta=json.load(open(mp));parents=[audit(meta[z]) for z in [m[1],m[3]]]
 if not all(parents):state[k]={'status':'source-refused','n':n};continue
 raw=f'out/{r["worker"]}/{pool}-{n}-{r["tag"]}/turn/{n}-self-+0.000-{r.get("loosen",1.001):.3f}.csv'
 source=f'own k123_join.py {r["tag"]}; k123_turn.py self loosen{r.get("loosen",1.001):.3f}; pinned donor ancestry: '+credits(parents)
 out='near-cert36/'+k;tag='verify-near36-'+k
 j=dict(kind='verify',near_donor36=True,tag=tag,n=n,raw=raw,out=out,source=source,licence='own band join; terms in the pinned donor ancestry')
 p=D/'job36.json';p.write_text(json.dumps(j));subprocess.run(SCP+[str(p),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True);subprocess.run(SSH+['mv $SCRATCH/squares-k123/tasks/'+tag+'.json.tmp $SCRATCH/squares-k123/tasks/'+tag+'.json'],check=True)
 state[k]={**j,'status':'queued'};print('near queued',n,room(n,r['side']),flush=True)
statefile.write_text(json.dumps(state))
