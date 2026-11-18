"""Round 31 twoshort collector on boxA (light python only): queue held-row kicks with claims, mirror boxE,
certify quenched finds with the pinned finesafe, write the take."""
import csv, json, math, os, re, shutil, subprocess, sys, time, hashlib, glob, calendar
from pathlib import Path
csv.field_size_limit(16000000)
B=Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r31';W=T/'work'
sys.path.insert(0,str(W));sys.path.insert(0,'.')
import finesafe
RES=Path('results')
HOST='boxE';RD='scratch/squares-twoshort'
DL=int((W/'deadline').read_text());SDL=int((W/'search-deadline').read_text())
def now():return time.strftime('%FT%TZ',time.gmtime())
def state(s):
 with open(T/'STATE.txt','a') as f:f.write(now()+' boxA '+s+'\n')
def handoff(s):
 with open(B/'handoff-r31.log','a') as f:f.write(now()+' twoshort -> all: '+s+'\n')
def sha(p):return hashlib.sha256(open(p,'rb').read()).hexdigest()
bar={int(r['n']):float(r['bar']) for r in csv.DictReader(open(B/'round31-briefs/bar31.tsv'),delimiter='\t')}
L={int(r['n']):float(r['L']) for r in csv.DictReader(open(B/'gate/cand-round30-1115c/details.csv'))}
src={}
def _tkey(f):
 # round 31 22:10: harvest-best tables too, ordered by date, then round number or letter
 b=Path(f).name;d=re.search(r'(\d{4}-\d\d-\d\d)([a-z]?)',b);r=re.search(r'round(\d+)-best',b)
 return (d[1],1 if r else 0,int(r[1]) if r else 0,d[2])
for f in sorted(glob.glob(str(RES/'round*-best-*.tsv'))+glob.glob(str(RES/'harvest-best-*.tsv')),key=_tkey):
 for r in csv.DictReader(open(f),delimiter='\t'):
  try:src[int(r['n'])]=(Path(f).name,r.get('source',''),r.get('licence',''))
  except (ValueError,TypeError):pass
HELD=None
def held_rows(n):
 global HELD
 if HELD is None:
  HELD={}
  with open(B/'gather/round30-2026-11-15c.csv') as f:
   for r in csv.DictReader(f):HELD.setdefault(int(r['n']),[]).append(r)
 return HELD[n]
def live():
 lv={}
 for p in B.glob('take-*-r31/take.tsv'):
  if p.parent==T:continue
  try:rows=list(csv.DictReader(open(p),delimiter='\t'))
  except (OSError,csv.Error):continue
  for r in rows:
   try:n=int(r['n']);s=float(r['new'])
   except (KeyError,ValueError,TypeError):continue
   lv[n]=min(lv.get(n,9),s)
 return lv
OUT={639,691,745,858,918}
BADSRC=('squares-verified-best-of-1105','986b3b6d','5a4c0cdb','take-harvest-r26/695')
def others_claimed():
 cl={}
 for line in open(B/'handoff-r31.log',errors='replace'):
  m=re.match(r'(\S+) (\S+) ->',line)
  if not m or m[2]=='twoshort':continue
  if not re.search(r'claim|kick',line,re.I):continue
  # round 31 21:40: a claim older than 60 minutes no longer blocks, unless it is an lkick (invent_rest) of the row
  try:age=time.time()-calendar.timegm(time.strptime(m[1][:19],'%Y-%m-%dT%H:%M:%S'))
  except ValueError:age=0
  if age>3600 and not ('invent_rest' in line or ('lkick' in line and 'midm' not in line)):continue
  for x in re.findall(r'\bn ?= ?(\d+)',line):cl.setdefault(int(x),line[:200])
  for x in re.findall(r'\b([0-9a-f]{16,64})\b',line):cl.setdefault(x[:16],line[:200])
 return cl
def queued_ns():
 s=set()
 for p in (W/'jobsent').glob('*.json'):s.add(json.load(open(p))['n'])
 return s
def pending_remote():
 r=subprocess.run(['ssh',HOST,'cd %s && for f in jobs/*.json; do b=$(basename $f); [ -d locks/$b ] || echo $b; done'%RD],capture_output=True,text=True,timeout=60)
 return [x for x in r.stdout.split() if x.endswith('.json')]
def queue_next(k):
 sel=json.load(open(W/'sel31.json'))['ok'];cl=others_claimed();lv=live();done=queued_ns();made=0
 for o in sel:
  if made>=k:break
  n=o['n']
  if n in done or n in OUT or n in cl or n in lv:continue
  s=src.get(n,('','',''))
  if any(b in s[1] for b in BADSRC):continue
  rows=held_rows(n);st=W/'starts';st.mkdir(exist_ok=True)
  f=st/('%d-held30c.csv'%n)
  with open(f,'w',newline='') as g:
   cw=csv.writer(g);cw.writerow(['n','square_id','x','y','angle'])
   for r in rows:cw.writerow([r['n'],r['square_id'],r['x'],r['y'],r['angle']])
  h=sha(f)
  if h[:16] in cl:state('SKIP n=%d bytes claimed by another lane: %s'%(n,cl[h[:16]]));continue
  tag='held31-%d-%s'%(n,h[:8])
  j=dict(tag=tag,n=n,start='starts/'+f.name,start_sha256=h,seed=3101,seconds=150,tool='lkick',leg_seconds=150,bar=bar[n],root_side=L[n],legs=0,priority=10,chain=[str(f)],held_src=s[0])
  handoff('claim: 150 s invent_rest lkick (seed 3101, boxE; legs while a step moves 1e-8 of side) of n=%d, start bytes sha256 %s, the held round 30 c row (%s; board score gap %.2e; side not a closed form a+b*sqrt2), %s'%(n,h,o.get('note','no kick line names it in rounds 28 to 31'),o['gap'],f))
  subprocess.run(['rsync','-a',str(f),'%s:%s/starts/'%(HOST,RD)],check=True,timeout=120)
  jf=W/'jobsent'/('010-%s-3101.json'%tag);jf.parent.mkdir(exist_ok=True);jf.write_text(json.dumps(j,indent=1))
  subprocess.run(['rsync','-a',str(jf),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120)
  state('QUEUE %s n=%d held round 30 c side %.12f gap %.2e; boxE lkick 150 s; log %s/runs/%s-s3101; deadline 23:55Z search, 00:15Z quench'%(tag,n,L[n],o['gap'],RD,tag))
  made+=1
def mirror():
 subprocess.run(['rsync','-a','--exclude','tmp','--exclude','lane','--exclude','ext','%s:%s/'%(HOST,RD),str(W/'boxE31')+'/'],timeout=300)
def certify_all():
 seen=json.load(open(W/'cert-seen.json')) if (W/'cert-seen.json').exists() else {}
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')} if (T/'take.tsv').exists() else {}
 changed=False;lv=live()
 for p in sorted((W/'boxE31/done').glob('*.json')):
  j=json.load(open(p));q=j.get('quench')
  if not q or p.name in seen or j.get('control') or q.get('rc')!=0:continue
  n=j['n'];qf=W/'boxE31/q'/('%s-s%d'%(j['tag'],j['seed']))/('%d-best.csv'%n)
  if not qf.exists():continue
  rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qf))]
  _,fr,s,e=finesafe.work((n,rows))
  seen[p.name]=dict(score=s,e=e,bar=bar[n]);json.dump(seen,open(W/'cert-seen.json','w'))
  lvn=min(lv.get(n,9),bar[n])
  msg='CERTCHECK %s n=%d finesafe %.13f bar %.13f (%+.3e) live %.13f'%(p.name,n,s if fr else float('nan'),bar[n],(s-bar[n]) if fr else 0,lvn);state(msg)
  if fr is None or len(rows)!=n:continue
  if s>=bar[n]-1e-10 or s>=lvn-1e-10:
   if s<bar[n]+5e-7:
    nd=T/'near';nf=nd/('%d-twoshort31-%s-s%d.csv'%(n,j['tag'].split('-')[-1],j['seed']))
    with open(nf,'w',newline='') as g:
     cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
   continue
  if n in cur and s>=float(cur[n]['new']):continue
  dst=T/('%d.csv'%n);tmp=T/('%d.csv.tmp'%n)
  with open(tmp,'w',newline='') as g:
   cw=csv.DictWriter(g,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)
  tmp.replace(dst)
  hs=src.get(n,('','',''))
  loc=lambda x:str(W/'boxE31'/x.replace(str(Path.home())+'/'+RD+'/','')) if not x.startswith('/Volumes') else x
  chain=' -> '.join('%s (sha256 %s)'%(loc(c),sha(loc(c)) if os.path.exists(loc(c)) else '?') for c in j.get('chain',[j['start']]))
  bf=loc(j.get('best_file') or '');bfs=sha(bf) if os.path.exists(bf) else '?'
  source=('twoshort round 31: midm_scan.py --modes lkick,kick (%d s, probe 120 s, seed %d, leg %d) on boxE, kick chain from the held round 30 c row of n=%d '
   '(gather/round30-2026-11-15c.csv, start snapshot sha256 %s): %s; raw best %s (sha256 %s); one fq quench (zone_corner.py quench) from its floatsafe-certified copy; finesafe (pinned sha256 e35eac45cc52). '
   'Held row source: results/%s row n=%d: %s')%(j['seconds'],j['seed'],j.get('legs',0),n,j['start_sha256'],chain,bf,bfs,hs[0],n,hs[1][:600])
  lic=(hs[2] or 'ours')+'; the held round 30 c row (a row of a file we submitted)'
  cur[n]=dict(n=n,held=bar[n],new=s,gain=bar[n]-s,source=source,licence=lic)
  changed=True
  handoff('certified n=%d gain=%.4e on bar31 (score %.13f, %.3e below the live r31 rows), from a 900 s midm kick chain of the held round 30 c row, quenched once with fq from the certified file, %s'%(n,bar[n]-s,s,lvn-s,dst))
  state('CERT n=%d gain %.4g against bar31, %.4g below the live r31 rows, %s'%(n,bar[n]-s,lvn-s,dst))
 if changed:
  with open(T/'take.tsv.tmp','w',newline='') as f:
   cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
  (T/'take.tsv.tmp').replace(T/'take.tsv')
def prune():
 # drop our rows another live r31 take beats; the csv stays in place (rows of other lanes name it: round 29 trap, round 31 811)
 if not (T/'take.tsv').exists():return
 cur={int(r['n']):r for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t')};lv=live();drop=[n for n in cur if lv.get(n,9)<=float(cur[n]['new'])]
 if not drop:return
 for n in drop:
  (T/'near').mkdir(exist_ok=True);shutil.copy2(T/('%d.csv'%n),T/'near'/('%d-overtaken-twoshort31.csv'%n));state('PRUNE n=%d: live r31 row %.13f at or below ours %.13f'%(n,lv[n],float(cur[n]['new'])));cur.pop(n)
 with open(T/'take.tsv.tmp','w',newline='') as f:
  cw=csv.DictWriter(f,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t');cw.writeheader();cw.writerows(cur[n] for n in sorted(cur))
 (T/'take.tsv.tmp').replace(T/'take.tsv')
def inbox():
 seen=set((W/'inbox-seen.txt').read_text().splitlines()) if (W/'inbox-seen.txt').exists() else set();new=[]
 for line in open(B/'handoff-r31.log',errors='replace'):
  if re.search(r'-> twoshort|take-twoshort-r31',line) and not re.match(r'\S+ twoshort ->',line) and line.strip() not in seen:new.append(line.strip())
 for l in new:state('INBOX '+l[:400])
 if new:
  with open(W/'inbox-seen.txt','a') as f:f.write(''.join(l+'\n' for l in new))
def queue_ab():
 # round 31 20:33: every held row our midm probe found dry also gets one 150 s invent_rest lkick (465 paid that way)
 cl=others_claimed();lv=live();made=[]
 have={json.load(open(p))['n'] for p in (W/'jobsent').glob('011-ab-*.json')}
 for p in sorted((W/'boxE31/done').glob('010-held31-*.json')):
  j=json.load(open(p));n=j['n']
  if j.get('why')!='probe-dry' or n in have or n in (37,54) or n in cl or n in lv:continue
  have.add(n)
  jj={k:v for k,v in j.items() if k not in ('start_side','best','tries','best_file','why','seconds_used','quench','error')}
  jj.update(tag='ab-'+j['tag'],tool='lkick',seed=3201,seconds=150,leg_seconds=150,legs=0,priority=11)
  f=W/'jobsent'/('011-ab-%s-3201.json'%j['tag']);f.write_text(json.dumps(jj,indent=1))
  handoff('claim: 150 s invent_rest lkick (seed 3201, boxE, after our dry midm probe of the same bytes) of n=%d, start bytes sha256 %s, the held round 30 c row, %s'%(n,j['start_sha256'],W/j['start']))
  subprocess.run(['rsync','-a',str(f),'%s:%s/jobs/'%(HOST,RD)],check=True,timeout=120);made.append(n)
 if made:state('QUEUE lkick after dry midm probe: '+' '.join(map(str,made)))
if __name__=='__main__':
 if sys.argv[1:]==['once']:
  mirror();certify_all();sys.exit()
 state('COLLECTOR manage31 start PID %d'%os.getpid())
 while time.time()<DL+300 and not (W/'STOP-COLLECT').exists():
  try:
   if time.time()<SDL-1200:
    pend=[x for x in pending_remote() if '-ab-' not in x]
    if len(pend)<2:queue_next(2-len(pend))
   mirror();certify_all();prune();inbox()
   if time.time()<SDL-900:queue_ab()
  except Exception as ex:state('COLLECTOR ERROR '+repr(ex)[:300])
  time.sleep(60)
 state('COLLECTOR exit')
