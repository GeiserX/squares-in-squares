"""Round 34 twoshort collector on boxA (light python only). Override 8: deep kicks of class n mod 4 = 1.
Plan from sel34.json: list A (rows changed in round 33 a with only probed 900 s kicks since), then list B (fewer than
two unprobed 900 s kicks since the current geometry, board gap 1e-6 or more, largest first), then list C (the rest of
B, kept so no slot idles). Each row gets its missing seeds (two at most) as unprobed 900 s midm_scan lkick,kick jobs on
boxE (worker34.py, 2 workers). Before a row starts: one claim line naming its seeds, wait 5 s, re-read
handoff-r34.log and start only if no earlier claim or kick line of another lane names that n this round; skip a row
when a live r34 take of another lane holds n below the held bar (kick only the lowest live row). No new job while the
boxE 5-minute load is 13 or more. A running job stops (stopn/<n>) when another lane posts a row more than 1e-6
below the bar at n. Each loop checks both workers (pid file), restarts a dead one and frees its job. Finds: the
worker runs the full fq loop (zone_corner.py quench); here finesafe certifies, the take is written, and the find is
handed to backlog at once. No share gate: every start is a held row (override 2)."""
import csv, json, math, os, re, shutil, subprocess, sys, time, hashlib, glob, calendar
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r34';W=T/'work';LOG=B/'handoff-r34.log'
sys.path.insert(0,str(W))
import finesafe
HOST='boxE';RD='scratch/squares-twoshort';PYR='$SCRATCH/squares-base/venv/bin/python'
DL=int((W/'deadline').read_text());SDL=int((W/'search-deadline').read_text())
LAST_START=calendar.timegm(time.strptime('2026-11-17T06:42:00','%Y-%m-%dT%H:%M:%S'))
NWORK=2;SEEDS=(3441,7341);LOADMAX=13.0
HELD=B/'gather/round33-2026-11-17a.csv';DET=B/'gate/cand-round33-1117a/details.csv'
def now():return time.strftime('%FT%TZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(now()+' boxA '+s+'\n')
def handoff(s,to='all'):
 with open(LOG,'a') as f:f.write(now()+' twoshort -> %s: '%to+s+'\n')
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
def ssh(cmd,t=60):return subprocess.run(['ssh',HOST,cmd],capture_output=True,text=True,timeout=t)
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round34-briefs/bar34.tsv'),delimiter='\t')}
L0={int(r['n']):float(r['L']) for r in csv.DictReader(open(DET))}
RES=Path('results')
def held_src():
 src={}
 def k(f):return int(re.match(r'round(\d+)',Path(f).name)[1])
 for f in sorted(glob.glob(str(RES/'round*-best-*.tsv')),key=k):
  for r in csv.DictReader(open(f),delimiter='\t'):
   try:src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
   except (ValueError,TypeError):pass
 return src
SRC=held_src()
def takes():
 out={}
 for p in B.glob('take-*-r34/take.tsv'):
  if p.parent==T:continue
  lane=p.parent.name[5:-4]
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   out[(lane,n)]=dict(lane=lane,n=n,new=s)
 return out
def live():
 lv={}
 for (lane,n),r in takes().items():
  if r['new']<lv.get(n,(9,''))[0]:lv[n]=(r['new'],lane)
 return lv
def tsec(s):
 try:return calendar.timegm(time.strptime(s[:19],'%Y-%m-%dT%H:%M:%S'))
 except ValueError:return 0
def other_claims(n,before=None):
 """claim, kick or follow lines of other lanes in handoff-r34.log naming n (before a time if given)"""
 hits=[]
 if not LOG.exists():return hits
 for line in open(LOG,errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort' or not re.search(r'claim|kick|follow',line,re.I):continue
  if before and m[1][:19]>before[:19]:continue
  ns=set(int(x) for x in re.findall(r'\bn ?= ?(\d+)',line))|set(int(x) for x in re.findall(r'(?:held\w*|starts|take-[\w-]+-r3\d)/(\d+)[-.]',line))
  if n in ns:hits.append(line[:240].strip())
 return hits
def plan():
 d=json.load(open(W/'sel34.json'))
 A=d['A'];Bl=[o for o in d['B'] if o['gap']>=1e-6];C=[o for o in d['B'] if o['gap']<1e-6 and o['gap']>1e-9]
 return [('A',o) for o in A]+[('B',o) for o in Bl]+[('C',o) for o in C]
def pdb():
 p=W/'plan34.json'
 return json.load(open(p)) if p.exists() else {}
def save_pdb(d):(W/'plan34.json.tmp').write_text(json.dumps(d,indent=1));(W/'plan34.json.tmp').replace(W/'plan34.json')
def remote_status():
 r=ssh('cd %s && echo LOAD $(sysctl -n vm.loadavg); for f in jobs/*.json; do b=$(basename $f); if [ -d locks/$b ]; then [ -f done/$b ] || echo RUN $b; else echo PEND $b; fi; done; for w in w1 w2; do p=$(cat pid-$w 2>/dev/null); if [ -n "$p" ] && kill -0 $p 2>/dev/null; then echo ALIVE $w $p; else echo DEAD $w; fi; echo CUR $w $(cat cur-$w 2>/dev/null); done'%RD)
 st=dict(load=None,run=[],pend=[],alive={},cur={})
 for l in r.stdout.splitlines():
  q=l.split()
  if not q:continue
  if q[0]=='LOAD':
   try:st['load']=float(q[3])
   except (IndexError,ValueError):pass
  elif q[0]=='RUN':st['run'].append(q[1])
  elif q[0]=='PEND':st['pend'].append(q[1])
  elif q[0]=='ALIVE':st['alive'][q[1]]=q[2]
  elif q[0]=='DEAD':st['alive'][q[1]]=None
  elif q[0]=='CUR':st['cur'][q[1]]=q[2] if len(q)>2 else ''
 return st
def liveness(st):
 if time.time()+120>SDL:return
 for w,pid in st['alive'].items():
  if pid:continue
  job=st['cur'].get(w,'')
  fix=''
  if job:
   r=ssh('cd %s && [ -f done/%s ] || { rm -rf locks/%s; echo freed; }'%(RD,job,job));fix=' freed job %s (%s)'%(job,r.stdout.strip() or 'done')
  ssh('cd %s && echo "" > cur-%s && (nohup nice -n 5 %s -I worker34.py %s > out-%s.txt 2>&1 &)'%(RD,w,PYR,w,w))
  state('RESTART worker %s on boxE (pid file dead)%s'%(w,fix))
def supersede(st):
 lv=live()
 for w,job in st['cur'].items():
  m=re.match(r'\d+-(?:deep34|control)-(\d+)',job or '')
  if not m:continue
  n=int(m[1])
  if n in lv and lv[n][0]<bar[n]-1e-6:
   r=ssh('cd %s && [ -f stopn/%d ] || { touch stopn/%d; echo new; }'%(RD,n,n))
   if 'new' in r.stdout:state('STOPN n=%d: %s posted %.13f, more than 1e-6 below bar34 %.13f; job %s stopped (lesson 6e)'%(n,lv[n][1],lv[n][0],bar[n],job))
def make_start(n):
 rows=[r for r in csv.DictReader(open(HELD)) if r['n']==str(n)]
 f=W/'starts'/('%d-held33a.csv'%n)
 with open(f,'w',newline='') as g:
  cw=csv.writer(g);cw.writerow(['n','square_id','x','y','angle'])
  for r in rows:cw.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
 return f,sha(f)
def queue_next(st):
 if time.time()>LAST_START:return 0
 if st['load'] is not None and st['load']>=LOADMAX:state('WAIT boxE 5-minute load %.2f (no new kick at %.0f or more)'%(st['load'],LOADMAX));return 0
 db=pdb();lv=live();mine=set(int(r['n']) for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')) if (T/'take.tsv').exists() else set()
 for lst,o in plan():
  n=o['n'];e=db.get(str(n),dict(status='new',sent=[]))
  if e['status'] in ('skip','done'):continue
  seeds=list(SEEDS[:o['seeds_left']])
  left=[s for s in seeds if s not in e['sent']]
  if not left:e['status']='done';db[str(n)]=e;save_pdb(db);continue
  def skip(why):
   e['status']='skip';e['why']=why;db[str(n)]=e;save_pdb(db);state('SKIP deep n=%d (list %s): %s'%(n,lst,why[:300]))
  if n in lv and lv[n][0]<bar[n]-1e-12:skip('a live r34 row of %s holds n below the held bar (%.13f); kick only the lowest live row'%(lv[n][1],lv[n][0]));continue
  if n in mine:skip('our own r34 row holds n; its legs follow it');continue
  if e['status']=='new':
   cl=other_claims(n)
   if cl:skip('claimed in handoff-r34: '+cl[0]);continue
   f,h=make_start(n)
   if abs(L0[n]-o['side'])>1e-9:state('NOTE n=%d details L %.12f vs sel side %.12f'%(n,L0[n],o['side']))
   hs=SRC.get(n,('','',''))
   if re.search(r'prvsiyan/squares-verified-best-of-1105|joegun-boxed',hs[1]+hs[2]) and 'own' not in hs[1]:skip('source names an out file');continue
   t=now()
   handoff('claim: 900 s midm_scan lkick,kick (seeds %s, probe 0 s, boxE; legs on finds while a leg moves; full fq loop; finds go to backlog) of n=%d, start bytes sha256 %s, the held round 33 a row (deep-kick class n mod 4 = 1, list %s: board gap %.2e of score, %d unprobed and %d probed 900 s kicks since its current geometry (%s)), %s'%(' and '.join(map(str,seeds)),n,h,lst,o['gap'],o['unprobed'],o['probed'],o['since'],f))
   time.sleep(5)
   cl=other_claims(n,before=now())
   if cl:skip('an earlier or same-time claim in handoff-r34 after our claim at %s: %s'%(t,cl[0]));handoff('releases its claim of n=%d (another lane claimed it first)'%n);continue
   e.update(status='claimed',claim=t,start=str(f),sha=h,list=lst,gap=o['gap']);db[str(n)]=e;save_pdb(db)
   subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  seed=left[0];f=Path(e['start']);h=e['sha']
  tag='deep34-%d-%s'%(n,h[:8]);hs=SRC.get(n,('','',''))
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=seed,seconds=900,probe=0,leg_seconds=150,leg_probe=120,bar=bar[n],root_side=L0[n],legs=0,priority=10,chain=[str(f)],held=True,kind_text='900 s midm_scan lkick,kick (no probe)',
         follow=dict(lane='held round 33 a',csv=str(HELD),score=bar[n],source='results/%s row n=%d: %s'%(hs[0],n,hs[1][:1200]),licence=(hs[2] or 'ours')+'; the held round 33 a row (a row of a file we submitted)'))
  jf=W/'jobsent'/('030-%s-%d.json'%(tag,seed));jf.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  e['sent'].append(seed);e['status']='claimed' if len(e['sent'])<len(seeds) else 'done';db[str(n)]=e;save_pdb(db)
  state('QUEUE %s seed %d n=%d (list %s, seed %d of %d) held round 33 a side %.12f gap %.2e; boxE midm_scan lkick,kick 900 s no probe; log %s/runs/%s-s%d; search deadline 07:00Z, deadline 07:25Z'%(tag,seed,n,lst,len(e['sent']),len(seeds),L0[n],o['gap'],RD,tag,seed))
  return 1
 return 0
def mirror():
 subprocess.run(['rsync','-a','--exclude','tmp','--exclude','lane','--exclude','ext','%s:%s/'%(HOST,RD),str(W/'boxE34')+'/'],timeout=300)
def certify_all():
 seen=json.load(open(W/'cert-seen.json')) if (W/'cert-seen.json').exists() else {}
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')} if (T/'take.tsv').exists() else {}
 changed=False;lv=live()
 for p in sorted((W/'boxE34/done').glob('*.json')):
  j=json.load(open(p));q=j.get('quench')
  if p.name in seen:continue
  if j.get('control'):
   seen[p.name]=dict(control=True);json.dump(seen,open(W/'cert-seen.json','w'))
   state('CONTROL %s n=%d start %s best %s moved %s tries %s %s'%(j['tag'],j['n'],j.get('start_side'),j.get('best'),(j['start_side']-j['best']) if j.get('best') is not None and j.get('start_side') is not None else None,j.get('tries'),j.get('why')));continue
  if not q:
   seen[p.name]=dict(moved=(j.get('start_side') or 0)-(j.get('best') or 0));json.dump(seen,open(W/'cert-seen.json','w'))
   state('DONE %s seed %s n=%d moved %.3e of side in %s tries (%s, %s s), no find near the bar'%(j['tag'],j['seed'],j['n'],(j.get('start_side') or 0)-(j.get('best') or 0),j.get('tries'),j.get('why'),j.get('seconds_used')));continue
  if q.get('rc')!=0:
   seen[p.name]=dict(qrc=q.get('rc'));json.dump(seen,open(W/'cert-seen.json','w'));state('QUENCH FAIL %s rc %s'%(p.name,q.get('rc')));continue
  n=j['n'];qf=W/'boxE34/q'/('%s-s%d'%(j['tag'],j['seed']))/('%d-best.csv'%n)
  if not qf.exists():continue
  rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qf))]
  _,fr,s,e=finesafe.work((n,rows))
  seen[p.name]=dict(score=s,e=e,bar=bar[n]);json.dump(seen,open(W/'cert-seen.json','w'))
  lvn=min(lv.get(n,(9,''))[0],bar[n])
  state('CERTCHECK %s n=%d finesafe %.13f bar %.13f (%+.3e) live %.13f'%(p.name,n,s if fr else float('nan'),bar[n],(s-bar[n]) if fr else 0,lvn))
  if fr is None or len(rows)!=n:continue
  if s>=bar[n]-1e-10 or s>=lvn-1e-10:
   if s<bar[n]+5e-7:
    nf=T/'near'/('%d-twoshort34-%s-s%d.csv'%(n,j['tag'].split('-')[-1],j['seed']))
    with open(nf,'w',newline='') as g:
     cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
   continue
  if n in cur and s>=float(cur[n]['new']):continue
  dst=T/('%d.csv'%n);tmp=T/('%d.csv.tmp'%n)
  with open(tmp,'w',newline='') as g:
   cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
  tmp.replace(dst)
  loc=lambda x:str(W/'boxE34'/x.replace(str(Path.home())+'/'+RD+'/','')) if not x.startswith('/Volumes') else x
  chain=' -> '.join('%s (sha256 %s)'%(loc(c),sha(loc(c)) if os.path.exists(loc(c)) else '?') for c in j.get('chain',[j['start']]))
  bf=loc(j.get('best_file') or '');bfs=sha(bf) if os.path.exists(bf) else '?'
  fo=j.get('follow',{})
  tooltxt='midm_scan.py --modes lkick,kick (%d s, %s, seed %d, leg %d)'%(j['seconds'],'no probe' if not j.get('probe') else 'probe %s s'%j.get('probe'),j['seed'],j.get('legs',0))
  source=('twoshort round 34: '+tooltxt+' on boxE, the held round 33 a row of n=%d (gather/round33-2026-11-17a.csv; score %.13f, start snapshot sha256 %s): %s; raw best %s (sha256 %s); '
   'the full fq loop (zone_corner.py quench: default then polish flags, up to 3 passes) from its floatsafe-certified copy; finesafe (pinned sha256 e35eac45cc52); held-row descendant, override 2, no share gate. '
   'Start row source: %s')%(n,fo.get('score',0),j['start_sha256'],chain,bf,bfs,fo.get('source','')[:1200])
  lic=(fo.get('licence') or 'own layout (held row)')
  cur[n]=dict(n=n,held=bar[n],new=s,gain=bar[n]-s,source=source,licence=lic)
  changed=True;writetake(cur)
  handoff('certified n=%d gain=%.4e on bar34 (score %.13f, %.3e below the live r34 rows), %s of the held round 33 a row (seed %d, leg %d), full fq loop from the certified file, held-row descendant (no share gate), %s'%(n,bar[n]-s,s,lvn-s,j.get('kind_text'),j['seed'],j.get('legs',0),dst))
  handoff('hands off take-twoshort-r34/%d.csv (sha256 %s, score %.13f) for your 180 s follow at once (override 8); our worker queues legs from it only while a leg moves'%(n,sha(dst),s),to='backlog')
  state('CERT n=%d gain %.4g against bar34, %.4g below the live r34 rows, %s; handed to backlog'%(n,bar[n]-s,lvn-s,dst))
def writetake(cur):
 with open(T/'take.tsv.tmp','w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
 (T/'take.tsv.tmp').replace(T/'take.tsv')
def prune():
 if not (T/'take.tsv').exists():return
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')};lv=live();drop=[n for n in cur if lv.get(n,(9,''))[0]<=float(cur[n]['new'])]
 if not drop:return
 for n in drop:
  shutil.copy2(T/('%d.csv'%n),T/'near'/('%d-overtaken-twoshort34.csv'%n));state('PRUNE n=%d: live r34 row of %s %.13f at or below ours %.13f (csv kept in place)'%(n,lv[n][1],lv[n][0],float(cur[n]['new'])));cur.pop(n)
 writetake(cur)
def inbox():
 seen=set((W/'inbox-seen.txt').read_text().splitlines()) if (W/'inbox-seen.txt').exists() else set();new=[]
 if not LOG.exists():return
 for line in open(LOG,errors='replace'):
  if re.search(r'-> [\w, -]*twoshort|take-twoshort-r34|main -> all|WITHDRAW',line) and not re.match(r'\S+ twoshort ->',line) and line.strip() not in seen:new.append(line.strip())
 for l in new:state('INBOX '+l[:400])
 if new:
  with open(W/'inbox-seen.txt','a') as f:f.write(''.join(l+'\n' for l in new))
if __name__=='__main__':
 if sys.argv[1:]==['once']:
  mirror();certify_all();sys.exit()
 (W/'collector-pid').write_text(str(os.getpid()))
 state('COLLECTOR manage34 start PID %d'%os.getpid())
 while time.time()<DL+300 and not (W/'STOP-COLLECT').exists():
  try:
   st=remote_status()
   liveness(st);supersede(st)
   if time.time()<SDL-900:
    # keep one job pending so no worker idles
    free=NWORK-len([x for x in st['run'] if not x.startswith('000-')])
    want=max(0,free+1-len(st['pend']))
    for _ in range(min(want,2)):
     if not queue_next(st):break
   mirror();certify_all();prune();inbox()
  except Exception as ex:state('COLLECTOR ERROR '+repr(ex)[:300])
  time.sleep(60)
 state('COLLECTOR exit')
