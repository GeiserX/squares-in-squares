"""Round 33 twoshort collector (from manage32) on boxA (light python only). Override 8 fallback: the held pool of
n 1 to 399 is empty (sel33.py), so it follows fresh certified rows of other lanes in n 1 to 399.
A row is a take.tsv row of another live take-*-r33 dir. It is queued 10 minutes after we first saw its bytes when
no other lane wrote a claim or kick line naming that n since then (backlog is the follow lane), it is the lowest live
row of its n, its bytes are not named by a WITHDRAW line, and its source names no banned file. Job: 150 s invent_rest
lkick on boxE (worker33.py), legs while a step moves 1e-8 of side, one fq loop, finesafe certify here,
share31 gate (both tolerances) on every output, kept only when the followed row is our own or held ancestry or passes."""
import csv, json, math, os, re, shutil, subprocess, sys, time, hashlib, glob, calendar
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r33';W=T/'work';LOG=B/'handoff-r33.log'
sys.path.insert(0,str(W));sys.path.insert(0,'.')
import finesafe
HOST='boxE';RD='scratch/squares-twoshort'
DL=int((W/'deadline').read_text());SDL=int((W/'search-deadline').read_text())
NMAX=1000;WAIT=600   # 19:05: follows in any n (main 18:58Z answer)
def now():return time.strftime('%FT%TZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(now()+' boxA '+s+'\n')
def handoff(s):
 with open(LOG,'a') as f:f.write(now()+' twoshort -> all: '+s+'\n')
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round33-briefs/bar33.tsv'),delimiter='\t')}
OUT={639,691,745,858,918}
BADSRC=('squares-verified-best-of-1105','986b3b6d','5a4c0cdb','take-harvest-r26/695','joegun-boxed-certified-union')
def takes():
 """{(lane,n): row} of every other live r33 take; row has new score, csv path, source, licence"""
 out={}
 for p in B.glob('take-*-r33/take.tsv'):
  if p.parent==T:continue
  lane=p.parent.name[5:-4]
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   out[(lane,n)]=dict(lane=lane,n=n,new=s,csv=str(p.parent/('%d.csv'%n)),source=r.get('source',''),licence=r.get('licence',''))
 return out
def live():
 lv={}
 for (lane,n),r in takes().items():lv[n]=min(lv.get(n,9),r['new'])
 return lv
def tsec(s):
 try:return calendar.timegm(time.strptime(s[:19],'%Y-%m-%dT%H:%M:%S'))
 except ValueError:return 0
def claims_since(n,t0):
 """claim or kick lines of other lanes naming n written at or after t0"""
 hits=[]
 if not LOG.exists():return hits
 for line in open(LOG,errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort' or tsec(m[1])<t0-1800:continue   # 18:56: backlog claims within seconds of a cert line, before we see the take row (292 at 18:44:46)
  if not re.search(r'claim|kick|follow',line,re.I):continue
  ns=set(int(x) for x in re.findall(r'\bn ?= ?(\d+)',line))|set(int(x) for x in re.findall(r'take-[\w-]+-r33/(\d+)\.csv',line))|set(int(x) for x in re.findall(r'take-[\w-]+-r33-(\d+)-',line))
  if n in ns:hits.append(line[:220].strip())
 return hits
def withdrawn():
 w=set()
 for lg in ('handoff-r31.log','handoff-r32.log','handoff-r33.log'):
  if not (B/lg).exists():continue
  for line in open(B/lg,errors='replace'):
   if 'WITHDRAW' in line:
    for x in re.findall(r'\b([0-9a-f]{12,64})\b',line):w.add(x[:12])
 return w
def seen_db():
 p=W/'seen33.json'
 return json.load(open(p)) if p.exists() else {}
def save_seen(d):
 (W/'seen33.json.tmp').write_text(json.dumps(d,indent=1));(W/'seen33.json.tmp').replace(W/'seen33.json')
def pending_remote():
 r=subprocess.run(['ssh',HOST,'cd %s && for f in jobs/*.json; do b=$(basename $f); [ -d locks/$b ] || echo $b; done'%RD],capture_output=True,text=True,timeout=60)
 return [x for x in r.stdout.split() if x.endswith('.json')]
def scan_and_queue(k):
 db=seen_db();tk=takes();lv=live();wd=withdrawn();made=0;t=time.time()
 for (lane,n),r in sorted(tk.items(),key=lambda x:x[1]['new']-bar.get(x[1]['n'],0)):
  if n>NMAX or n in OUT:continue
  p=Path(r['csv'])
  if not p.exists():continue
  h=sha(p);key='%s-%d-%s'%(lane,n,h[:12])
  if key not in db:db[key]=dict(lane=lane,n=n,sha=h,first=t,status='wait',new=r['new']);state('SEE %s n=%d score %.13f (%.3e below bar33) %s sha256 %s; follow it at %s when unclaimed'%(lane,n,r['new'],bar[n]-r['new'],p,h[:16],time.strftime('%TZ',time.gmtime(t+WAIT))))
  e=db[key]
  if e['status']!='wait' or made>=k or t<e['first']+WAIT:continue
  why=None
  if r['new']>lv.get(n,9)+1e-15:why='not the lowest live row of n (live %.13f)'%lv[n]
  elif h[:12] in wd:why='bytes named by a WITHDRAW line'
  elif any(b in r['source'] for b in BADSRC) and 'own Samanyu' not in r['source']:why='source names a banned file'
  else:
   cl=claims_since(n,e['first'])
   if cl:why='claimed by another lane: '+cl[0]
  if why:e['status']='skip';state('SKIP %s n=%d: %s'%(key,n,why[:300]));continue
  st=W/'starts';st.mkdir(exist_ok=True);f=st/('%d-%s-%s.csv'%(n,lane,h[:12]));shutil.copy2(p,f)
  if sha(f)!=h:state('SKIP %s: bytes changed while copying'%key);continue
  tag='f33-%d-%s-%s'%(n,lane,h[:8]);seed=3301
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=seed,seconds=150,tool='lkick',leg_seconds=150,bar=min(bar[n],lv.get(n,9)),root_side=(r['new']+1)*math.sqrt(n),legs=0,priority=10,chain=[str(f)],
        follow=dict(lane=lane,csv=str(p),score=r['new'],source=r['source'][:1500],licence=r['licence'][:300]))
  handoff('claims the follow of take-%s-r33/%d.csv (sha256 %s), n=%d, unclaimed 10 minutes after it appeared: invent_rest.py lkick (150 s, seed %d, boxE; legs while a step moves 1e-8 of side; one fq loop of the certified find), start %s'%(lane,n,h,n,seed,f))
  subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  jf=W/'jobsent'/('010-%s-%d.json'%(tag,seed));jf.parent.mkdir(exist_ok=True);jf.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  e['status']='queued';e['tag']=tag;made+=1
  state('QUEUE %s n=%d follow of take-%s-r33/%d.csv score %.13f; boxE lkick 150 s seed %d; log %s/runs/%s-s%d; deadline 00:00Z search, 00:15Z quench'%(tag,n,lane,n,r['new'],seed,RD,tag,seed))
 save_seen(db)

RES=Path('results')
def held_src():
 src={}
 def _tkey(f):
  b=Path(f).name;d=re.search(r'(\d{4}-\d\d-\d\d)([a-z]?)',b);r=re.search(r'round(\d+)-best',b)
  return (d[1],1 if r else 0,int(r[1]) if r else 0,d[2])
 for f in sorted(glob.glob(str(RES/'round*-best-*.tsv'))+glob.glob(str(RES/'harvest-best-*.tsv')),key=_tkey):
  for r in csv.DictReader(open(f),delimiter='\t'):
   try:src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
   except (ValueError,TypeError):pass
 return src
def claims_r33(n):
 hits=[]
 for line in open(LOG,errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort' or not re.search(r'claim|kick',line,re.I):continue
  ns=set(int(x) for x in re.findall(r'\bn ?= ?(\d+)',line))|set(int(x) for x in re.findall(r'(?:held\w*|starts|take-[\w-]+-r33)/(\d+)[-.]',line))
  if n in ns:hits.append(line[:220].strip())
 return hits
def queue_held():
 """main 18:58Z: first 150 s lkicks of held rows n 400 to 1000 no lane lkicked or claimed (sel33b.json), one at a time"""
 sent={json.load(open(p))['n'] for p in (W/'jobsent').glob('*.json')}
 lv=live();wd=withdrawn();src=held_src()
 for o in json.load(open(W/'sel33b.json'))['ok']:
  n=o['n']
  if n in sent or n in OUT:continue
  if n in lv:state('SKIP held n=%d: a live r33 take row exists (%.13f), so the held row is not the lowest live row'%(n,lv[n]));sent.add(n);(W/'jobsent'/('skip-%d.json'%n)).write_text(json.dumps(dict(n=n)));continue
  cl=claims_r33(n)
  if cl:state('SKIP held n=%d: claimed in handoff-r33: %s'%(n,cl[0][:250]));(W/'jobsent'/('skip-%d.json'%n)).write_text(json.dumps(dict(n=n)));continue
  hs=src.get(n,('','',''))
  if any(b in hs[1] for b in BADSRC) and 'own Samanyu' not in hs[1]:state('SKIP held n=%d: source names a banned file'%n);(W/'jobsent'/('skip-%d.json'%n)).write_text(json.dumps(dict(n=n)));continue
  rows=[r for r in csv.DictReader(open(B/'gather/round32-2026-11-16a.csv')) if r['n']==str(n)]
  st=W/'starts';st.mkdir(exist_ok=True);f=st/('%d-held32a.csv'%n)
  with open(f,'w',newline='') as g:
   cw=csv.writer(g);cw.writerow(['n','square_id','x','y','angle'])
   for r in rows:cw.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
  h=sha(f)
  if h[:12] in wd:state('SKIP held n=%d: start bytes named by a WITHDRAW line'%n);continue
  tag='held33-%d-%s'%(n,h[:8]);seed=3301
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=seed,seconds=150,tool='lkick',leg_seconds=150,bar=bar[n],root_side=o['L'],legs=0,priority=10,chain=[str(f)],held=True,
         follow=dict(lane='held round 32 a',csv='gather/round32-2026-11-16a.csv',score=bar[n],source='results/%s row n=%d: %s'%(hs[0],n,hs[1][:1200]),licence=(hs[2] or 'ours')+'; the held round 32 a row (a row of a file we submitted)'))
  handoff('claim: 150 s invent_rest lkick (seed %d, boxE; legs while a step moves 1e-8 of side; one fq loop) of n=%d, start bytes sha256 %s, the held round 32 a row (first lkick of its current geometry: no lkick or claim line since it last changed; board score gap %.2e; main 18:58Z answer), %s'%(seed,n,h,o['gap'],f))
  subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  jf=W/'jobsent'/('020-%s-%d.json'%(tag,seed));jf.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  state('QUEUE %s n=%d held round 32 a side %.12f gap %.2e; boxE lkick 150 s seed %d; log %s/runs/%s-s%d; deadline 00:00Z search, 00:15Z quench'%(tag,n,o['L'],o['gap'],seed,RD,tag,seed))
  return 1
 return 0

NWORK=8;DEEP_T0=calendar.timegm(time.strptime('2026-11-16T21:46:39','%Y-%m-%dT%H:%M:%S'))
LAST_START=calendar.timegm(time.strptime('2026-11-16T23:15:00','%Y-%m-%dT%H:%M:%S'))
def running_remote():
 r=subprocess.run(['ssh',HOST,'cd %s && for f in locks/*.json; do b=$(basename $f); [ -f done/$b ] || echo $b; done'%RD],capture_output=True,text=True,timeout=60)
 return [x for x in r.stdout.split() if x.endswith('.json')]
def deep_claims(n):
 hits=[]
 for line in open(LOG,errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort' or not re.search(r'claim|kick',line,re.I):continue
  pm=re.search(r'probe\s*(\d+)|(\d+)\s*s probe|probe (\d+) s',line);prb=bool(pm) and int(next(x for x in pm.groups() if x))>0
  if not (tsec(m[1])>=DEEP_T0-5 or (re.search(r'\b900\s*s|900s',line) and not prb)):continue   # 22:20: a probed 900 s line before 21:46 does not close the row
  ns=set(int(x) for x in re.findall(r'\bn ?= ?(\d+)',line))|set(int(x) for x in re.findall(r'(?:held\w*|starts|take-[\w-]+-r33)/(\d+)[-.]',line))
  if n in ns:hits.append(line[:220].strip())
 return hits
def queue_deep():
 """main 21:46Z SHARED DEEP-KICK QUEUE: one unprobed 900 s midm_scan lkick,kick seed per held row (sel33c.json), largest gap first"""
 if time.time()>LAST_START:return 0
 sent={json.load(open(p))['n'] for p in (W/'jobsent').glob('0[23]*.json')}|{json.load(open(p))['n'] for p in (W/'jobsent').glob('skipd-*.json')}
 lv=live();wd=withdrawn();src=held_src()
 for o in json.load(open(W/'sel33c.json'))['ok']+(json.load(open(W/'sel33d.json'))['ok'] if (W/'sel33d.json').exists() else []):
  n=o['n']
  if n in sent or n in OUT:continue
  ld=subprocess.run(['ssh',HOST,'sysctl -n vm.loadavg'],capture_output=True,text=True,timeout=60).stdout.split()
  if ld and float(ld[1])>=13:state('WAIT deep: boxE load %s (keep under 16)'%ld[1]);return 0
  def skip(why):state('SKIP deep n=%d: %s'%(n,why[:280]));(W/'jobsent'/('skipd-%d.json'%n)).write_text(json.dumps(dict(n=n)))
  if n in lv:skip('a live r33 take row exists (%.13f)'%lv[n]);continue
  cl=deep_claims(n)
  if cl:skip('claimed in handoff-r33: '+cl[0]);continue
  hs=src.get(n,('','',''))
  if any(b in hs[1] for b in BADSRC) and 'own Samanyu' not in hs[1]:skip('source names a banned file');continue
  rows=[r for r in csv.DictReader(open(B/'gather/round32-2026-11-16a.csv')) if r['n']==str(n)]
  st=W/'starts';f=st/('%d-held32a.csv'%n)
  with open(f,'w',newline='') as g:
   cw=csv.writer(g);cw.writerow(['n','square_id','x','y','angle'])
   for r in rows:cw.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
  h=sha(f)
  if h[:12] in wd:skip('start bytes named by a WITHDRAW line');continue
  L0=float(next(r['L'] for r in csv.DictReader(open(B/'gate/cand-round32-1116a/details.csv')) if r['n']==str(n)))
  tag='deep33-%d-%s'%(n,h[:8]);seed=3341
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=seed,seconds=900,probe=0,leg_seconds=150,leg_probe=120,bar=bar[n],root_side=L0,legs=0,priority=10,chain=[str(f)],held=True,kind_text='900 s midm_scan lkick,kick (no probe)',
         follow=dict(lane='held round 32 a',csv='gather/round32-2026-11-16a.csv',score=bar[n],source='results/%s row n=%d: %s'%(hs[0],n,hs[1][:1200]),licence=(hs[2] or 'ours')+'; the held round 32 a row (a row of a file we submitted)'))
  handoff('claim: 900 s midm_scan lkick,kick (seed %d, probe 0 s, boxE; one seed, no second seed; legs on finds; full fq loop) of n=%d, start bytes sha256 %s, the held round 32 a row (main 21:46Z SHARED DEEP-KICK QUEUE: above the 2026-11-09 board side by %.2e of score, no unprobed 900 s kick line since its current geometry, not on border\'s remaining deep order), %s'%(seed,n,h,o['gap'],f))
  subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  jf=W/'jobsent'/('030-%s-%d.json'%(tag,seed));jf.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  state('QUEUE %s n=%d held round 32 a side %.12f gap %.2e; boxE midm_scan lkick,kick 900 s no probe seed %d; log %s/runs/%s-s%d; deadline 00:00Z search, 00:15Z quench'%(tag,n,L0,o['gap'],seed,RD,tag,seed))
  return 1
 return 0
def mirror():
 subprocess.run(['rsync','-a','--exclude','tmp','--exclude','lane','--exclude','ext','%s:%s/'%(HOST,RD),str(W/'boxE33')+'/'],timeout=300)
def share_gate(n,path):
 items=W/'share-items.json';out=W/'share-out.json'
 items.write_text(json.dumps([dict(label='twoshort33-%d'%n,path=str(path),n=n)]))
 r=subprocess.run([str(B/'venv/bin/python'),'-I',str(B/'take-assemble-r31/scripts/share31.py'),str(items),str(out)],capture_output=True,text=True,timeout=900)
 try:return json.load(open(out)),r.returncode
 except Exception:return None,r.returncode
def certify_all():
 seen=json.load(open(W/'cert-seen.json')) if (W/'cert-seen.json').exists() else {}
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')} if (T/'take.tsv').exists() else {}
 changed=False;lv=live()
 for p in sorted((W/'boxE33/done').glob('*.json')):
  j=json.load(open(p));q=j.get('quench')
  if not q or p.name in seen or j.get('control') or q.get('rc')!=0:continue
  n=j['n'];qf=W/'boxE33/q'/('%s-s%d'%(j['tag'],j['seed']))/('%d-best.csv'%n)
  if not qf.exists():continue
  rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qf))]
  _,fr,s,e=finesafe.work((n,rows))
  seen[p.name]=dict(score=s,e=e,bar=bar[n]);json.dump(seen,open(W/'cert-seen.json','w'))
  lvn=min(lv.get(n,9),bar[n])
  state('CERTCHECK %s n=%d finesafe %.13f bar %.13f (%+.3e) live %.13f'%(p.name,n,s if fr else float('nan'),bar[n],(s-bar[n]) if fr else 0,lvn))
  if fr is None or len(rows)!=n:continue
  if s>=bar[n]-1e-10 or s>=lvn-1e-10:
   if s<bar[n]+5e-7:
    nd=T/'near';nf=nd/('%d-twoshort33-%s-s%d.csv'%(n,j['tag'].split('-')[-1],j['seed']))
    with open(nf,'w',newline='') as g:
     cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
   continue
  if n in cur and s>=float(cur[n]['new']):continue
  tmp=T/('%d.csv.tmp'%n)
  with open(tmp,'w',newline='') as g:
   cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
  sh,rc=share_gate(n,tmp);fo=j.get('follow',{})
  smax=None
  try:it=sh['items'][0];smax=max(float(it['max_nonown']['0.001']),float(it['max_nonown']['0.01']))
  except Exception:it=None;smax=None
  state('SHARE31 n=%d rc %s max_nonown %s (all_own %s)'%(n,rc,smax,it.get('all_own') if it else None))
  if (smax is None or smax>=0.4) and not j.get('held'):   # 22:45: a held row's descendant is ours (rule 2); the r32 assembler logged held 540 at 0.419 as no reason
   (W/'hold').mkdir(exist_ok=True);shutil.copy2(tmp,W/'hold'/('%d-%s.csv'%(n,j['tag'])));tmp.unlink()
   state('HOLD n=%d: share31 %s on the output (or unreadable); review by hand whether take-%s-r33/%d.csv is public-first before it counts'%(n,smax,fo.get('lane'),n));continue
  dst=T/('%d.csv'%n);tmp.replace(dst)
  loc=lambda x:str(W/'boxE33'/x.replace(str(Path.home())+'/'+RD+'/','')) if not x.startswith('/Volumes') else x
  chain=' -> '.join('%s (sha256 %s)'%(loc(c),sha(loc(c)) if os.path.exists(loc(c)) else '?') for c in j.get('chain',[j['start']]))
  bf=loc(j.get('best_file') or '');bfs=sha(bf) if os.path.exists(bf) else '?'
  what=('the held round 32 a row of n=%d (gather/round32-2026-11-16a.csv)'%n) if j.get('held') else ('a follow of take-%s-r33/%d.csv'%(fo.get('lane'),n))
  tooltxt=('midm_scan.py --modes lkick,kick (%d s, no probe, seed %d, leg %d)' if j.get('tool')!='lkick' else 'invent_rest.py lkick (%d s, seed %d, leg %d)')
  heldnote=(' (held-row descendant: rule 2, no share gate; the round 32 assembler table logs the held row of n=%d with its own share as no reason for a held root)'%n) if j.get('held') and smax is not None and smax>=0.4 else ''
  source=('twoshort round 33: '+tooltxt+' on boxE, '+what+' (score %.13f, start snapshot sha256 %s): %s; raw best %s (sha256 %s); '
   'one fq loop (zone_corner.py quench: default then polish flags, up to 3 passes) from its floatsafe-certified copy; finesafe (pinned sha256 e35eac45cc52); share31 max %s%s. '
   'Start row source: %s')%(j['seconds'],j['seed'],j.get('legs',0),fo.get('score',0),j['start_sha256'],chain,bf,bfs,smax,heldnote,fo.get('source','')[:1200])
  lic=(fo.get('licence') or '?')+' (licence of the followed row)'
  cur[n]=dict(n=n,held=bar[n],new=s,gain=bar[n]-s,source=source,licence=lic)
  changed=True
  handoff('certified n=%d gain=%.4e on bar33 (score %.13f, %.3e below the live r33 rows), %s of %s, quenched once with the fq loop from the certified file, share31 max %s, %s'%(n,bar[n]-s,s,lvn-s,j.get('kind_text','a 150 s invent_rest lkick'),what,smax,dst))
  state('CERT n=%d gain %.4g against bar33, %.4g below the live r33 rows, %s'%(n,bar[n]-s,lvn-s,dst))
 if changed:writetake(cur)
def writetake(cur):
 with open(T/'take.tsv.tmp','w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
 (T/'take.tsv.tmp').replace(T/'take.tsv')
def prune():
 if not (T/'take.tsv').exists():return
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')};lv=live();drop=[n for n in cur if lv.get(n,9)<=float(cur[n]['new'])]
 if not drop:return
 for n in drop:
  shutil.copy2(T/('%d.csv'%n),T/'near'/('%d-overtaken-twoshort33.csv'%n));state('PRUNE n=%d: live r33 row %.13f at or below ours %.13f'%(n,lv[n],float(cur[n]['new'])));cur.pop(n)
 writetake(cur)
def inbox():
 seen=set((W/'inbox-seen.txt').read_text().splitlines()) if (W/'inbox-seen.txt').exists() else set();new=[]
 if not LOG.exists():return
 for line in open(LOG,errors='replace'):
  if re.search(r'-> [\w,-]*twoshort|take-twoshort-r33|main -> all: BASE|WITHDRAW',line) and not re.match(r'\S+ twoshort ->',line) and line.strip() not in seen:new.append(line.strip())
 for l in new:state('INBOX '+l[:400])
 if new:
  with open(W/'inbox-seen.txt','a') as f:f.write(''.join(l+'\n' for l in new))
if __name__=='__main__':
 if sys.argv[1:]==['once']:
  mirror();certify_all();sys.exit()
 state('COLLECTOR manage33 start PID %d'%os.getpid())
 while time.time()<DL+300 and not (W/'STOP-COLLECT').exists():
  try:
   if time.time()<SDL-900:
    pend=[x for x in pending_remote() if not x.startswith('000-')]
    if len(pend)<2:scan_and_queue(2-len(pend))
    else:scan_and_queue(0)
    pend=[x for x in pending_remote() if not x.startswith('000-')]
    if not pend:queue_held()
    pend=pending_remote()
    if not pend and len(running_remote())<NWORK:queue_deep()
   mirror();certify_all();prune();inbox()
  except Exception as ex:state('COLLECTOR ERROR '+repr(ex)[:300])
  time.sleep(60)
 state('COLLECTOR exit')
