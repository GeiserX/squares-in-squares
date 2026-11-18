import csv,datetime,glob,hashlib,json,math,os,shutil,subprocess,sys,time
S='$SCRATCH/bounties-squares';T=S+'/take-stair-c-r23';W=T+'/work'; L='.'
sys.path.insert(0,L)
import floatsafe
stop=datetime.datetime(2026,11,13,18,39,tzinfo=datetime.timezone.utc).timestamp()
H={int(r['n']):float(r['score']) for r in csv.DictReader(open(S+'/gate/cand-round21-1113a/details.csv'))}
seen=set(); published=set(); handed=set(); queued=set()
state=W+'/collect-state.json'
if os.path.exists(state):
 d=json.load(open(state));seen=set(d['seen']);published=set(d['published']);handed=set(d['handed']);queued=set(d['queued'])
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def hand(text):
 with open(S+'/handoff-r23.log','a') as h:h.write(stamp()+' stair-c -> all: '+text+'\n')
def shell(args,**kw):return subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=55,**kw)
def save():
 json.dump(dict(seen=list(seen),published=list(published),handed=list(handed),queued=list(queued)),open(state+'.tmp','w'));os.replace(state+'.tmp',state)
def rows(p):return [{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(p))]
def write(p,rs):
 with open(p+'.tmp','w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows(rs)
 os.replace(p+'.tmp',p)
def cycle():
 bar0=dict(H)
 for p in glob.glob(S+'/take-*-r2[23]/take.tsv'):
  if p==T+'/take.tsv':continue
  for r in csv.DictReader(open(p),delimiter='\t'):
   n=int(r['n']);bar0[n]=min(bar0[n],float(r['new']))
 for host,key in [('boxC','n'),('boxE','s')]:
  for folder in ['raw-a','final','corners']:
   out=f'{W}/boxcopy/{key}/{folder}';os.makedirs(out,exist_ok=True)
   try:shell(['rsync','-az',f'{host}:scratch/squares-stair-c/{folder}/',out+'/'])
   except subprocess.TimeoutExpired:print('copy timeout',host,folder,flush=True)
  try:shell(['rsync','-az','--include=*.log','--include=*.tsv','--include=*.txt','--exclude=*',f'{host}:scratch/squares-stair-c/',f'{W}/boxcopy/{key}/'])
  except subprocess.TimeoutExpired:pass
  for p in glob.glob(f'{W}/boxcopy/{key}/corners/*.pkl'):
   tag=key+os.path.basename(p)+hashlib.sha256(open(p,'rb').read()).hexdigest()[:10]
   if tag not in handed:
    hand('new design corners, fan or interleaved strips, '+p);handed.add(tag)
  prep=f'{W}/boxcopy/{key}/prep.log'
  if os.path.exists(prep):
   text=open(prep).read()
   for p in glob.glob(f'{W}/boxcopy/{key}/corners/*.pkl'):
    name=os.path.basename(p)[:-4];tag='library:'+key+name
    if tag in handed or not any(('ready '+name) in line for line in text.splitlines()):continue
    out=f'{W}/libs/{name}';os.makedirs(out,exist_ok=True)
    try:
     r=shell(['rsync','-az',f'{host}:scratch/squares-stair-c/lib-{name}/',out+'/'])
     if r.returncode==0:hand('new design library, '+out);handed.add(tag)
    except subprocess.TimeoutExpired:pass
  for p in glob.glob(f'{W}/boxcopy/{key}/raw-a/*.json'):
   tag=key+os.path.basename(p)
   if tag in seen:continue
   try:
    j=json.load(open(p));c=p[:-5]+'.csv';n=j['n'];b=j.get('built')
    if b is None or not os.path.exists(c):continue
    if len(rows(c))!=n:continue
   except Exception:continue
   seen.add(tag);name=os.path.basename(c);near=f'{T}/near/{name[:-4]}-{key}.csv';shutil.copyfile(c,near)
   manifest=dict(j,source='stair-c round23: '+', '.join(q['id']+' <'+q['source']+'>' for q in j['modules']),licence='; '.join(sorted(set(q['licence'] for q in j['modules']))))
   json.dump(manifest,open(near+'.json','w'),indent=2)
   hand(f'new build n={n}, side {b:.12f}, held delta {b-(1+H[n])*math.sqrt(n):+.6g}; kick and border start, {near}')
   if b>(1+bar0[n])*math.sqrt(n)-1e-9:continue
   _,fr,sc,e=floatsafe.work((n,rows(c)))
   if fr is None or sc>=H[n]-1e-10 or sc>=bar0[n]-1e-10:continue
   os.makedirs(W+'/cert-in',exist_ok=True);cp=W+'/cert-in/'+name
   write(cp,fr);shutil.copyfile(p,cp[:-4]+'.json')
   if tag not in queued:
    try:
     shell(['rsync','-az',cp,cp[:-4]+'.json',f'{host}:scratch/squares-stair-c/cert-in/'])
     cmd=f'cd $SCRATCH/squares-stair-c && mkdir -p final && echo "quench-{name[:-4]} ./py -I quench22.py cert-in/{name} final/{name}" >> q.txt'
     shell(['ssh','-n',host,cmd]);queued.add(tag)
    except subprocess.TimeoutExpired:pass
 bar=dict(H)
 for p in glob.glob(S+'/take-*-r2[23]/take.tsv'):
  if p==T+'/take.tsv':continue
  for r in csv.DictReader(open(p),delimiter='\t'):
   n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
 best={}
 for p in glob.glob(W+'/boxcopy/*/final/*.csv'):
  try:
   n=int(os.path.basename(p).split('-')[0]);_,fr,sc,e=floatsafe.work((n,rows(p)))
   if fr is None or sc>=H[n]-1e-10 or sc>=bar[n]-1e-10:continue
   if n not in best or sc<best[n][0]:best[n]=(sc,fr,p)
  except Exception as e:print('final error',p,str(e),flush=True)
 lines=['n\theld\tnew\tgain\tsource\tlicence\n']
 for n,(sc,fr,p) in sorted(best.items()):
  write(f'{T}/{n}.csv',fr);j=json.load(open(p[:-4]+'.json'));mods=j['modules']
  src='stair-c round23: '+', '.join(q['id']+' <'+q['source']+'>' for q in mods)+'; family squeeze then fq of certified file'
  lic='; '.join(sorted(set(q['licence'] for q in mods)))
  lines.append(f'{n}\t{H[n]!r}\t{sc!r}\t{H[n]-sc:.12g}\t{src}\t{lic}\n')
  mark=f'{n}:{sc:.17g}'
  if mark not in published:hand(f'certified n={n} gain={H[n]-sc:.9g}, {T}/{n}.csv');published.add(mark)
 with open(T+'/take.tsv.tmp','w') as h:h.writelines(lines)
 os.replace(T+'/take.tsv.tmp',T+'/take.tsv')
 for p in glob.glob(T+'/*.csv'):
  if int(os.path.basename(p)[:-4]) not in best:os.remove(p)
 save();print(stamp(),'seen',len(seen),'quench queued',len(queued),'take',len(best),'gain',sum(H[n]-b[0] for n,b in best.items()),flush=True)
while time.time()<stop:
 try:cycle()
 except Exception as e:print(stamp(),'ERROR',repr(e),flush=True)
 if '--once' in sys.argv:break
 time.sleep(60)
