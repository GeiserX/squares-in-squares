"""boxA feeder for the boxC window scanner (border r26, light python).
Every 60 s: copy each new fresh layout of the other take-*-r26 dirs (take csv and near csv) whose recorded ancestry
passes provenance.audit to boxC wq/in, pull wq/out, and for each count c whose best sub-window is below the live bar
(bars.json) by more than 1e-10*sqrt(c)+1e-9: cut the window from the local copy, floatsafe it, and when it certifies
below the bar stage a certified-file fq job in final/ with a 'win' manifest. The driver's collect() publishes it after
the source policy and the fq receipt, exactly as for a direct corner window. Measurements go to wscan.tsv."""
import os,sys,time,json,csv,math,hashlib,shutil,subprocess,re
from pathlib import Path
W=Path(__file__).parent;S=W.parent.parent;T=W.parent
src=(W/'driver.py').read_text()
src=src[:src.index("log('start round26 collector/scanner")]
src=src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_wfeed','__file__':str(W/'driver.py')};exec(compile(src,str(W/'driver.py'),'exec'),ns)
bs=ns['bs'];floatsafe=ns['floatsafe'];audit=ns['audit'];metadata=ns['metadata'];csvout=ns['csvout']
REMOTE='boxC:scratch/squares-border-r26/'
END=float((W/'deadline').read_text())
WQ=W/'wq';(WQ/'in').mkdir(parents=True,exist_ok=True);(WQ/'out').mkdir(exist_ok=True)
index_file=WQ/'index.json';index=json.load(open(index_file)) if index_file.exists() else {}
seen=set(v['key'] for v in index.values());done_out=set()
def log(msg):
 s=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+msg
 print(s,flush=True)
 with open(T/'STATE.txt','a') as f:f.write(s+'\n')
def files():
 out=[]
 for t in S.glob('take-*-r26'):
  if t==T or not t.is_dir():continue
  rows={}
  try:rows={r['n']:r for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t')}
  except (OSError,ValueError,KeyError):pass
  for p in t.glob('*.csv'):
   if p.stem.isdigit():out.append((p,rows.get(p.stem)))
  for p in t.rglob('near/*.csv'):
   if not any(q.startswith(('control','ctl-','broken')) for q in p.relative_to(t).parts):out.append((p,None))
 return out
BACKLOG=None
def backlog():
 # Frozen r25 then r24 take and near layouts (read only), scanned after every fresh r26 file (names zb-*).
 global BACKLOG
 if BACKLOG is None:
  BACKLOG=[]
  for rnd in ('r25','r24'):
   for t in sorted(S.glob('take-*-'+rnd)):
    rows={}
    try:rows={r['n']:r for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t')}
    except (OSError,ValueError,KeyError):pass
    for q in sorted(t.glob('*.csv')):
     if q.stem.isdigit():BACKLOG.append((q,rows.get(q.stem),'zb-'))
    for q in sorted(t.rglob('near/*.csv')):
     if not any(z.startswith(('control','ctl-','broken')) for z in q.relative_to(t).parts):BACKLOG.append((q,None,'zb-'))
 return BACKLOG
sys.path.insert(0,str(W))
from wfeed_rows import window_rows
while time.time()<END:
 try:
  L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
  new=[]
  budget=[0]
  for p,row,pre in [(a,b,'') for a,b in files()]+backlog():
   if pre and budget[0]>=150:break
   try:st=p.stat()
   except OSError:continue
   key=f'{p}|{st.st_mtime_ns}|{st.st_size}'
   if key in seen or st.st_size>1500000:continue
   seen.add(key)
   if not audit(p,row):continue
   data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()[:16]
   try:N=int(next(csv.DictReader(open(p)))['n'])
   except (StopIteration,ValueError,KeyError):continue
   if N<30:continue
   name=f'{pre}{digest}-{N}'
   if pre:budget[0]+=1
   if name in index:continue
   (WQ/'in'/f'{name}.csv').write_bytes(data)
   index[name]=dict(key=key,path=str(p),row=row,n=N);new.append(name)
  if new:
   tmp=index_file.with_suffix('.tmp');tmp.write_text(json.dumps(index));tmp.replace(index_file)
   subprocess.run(['rsync','-a','--ignore-existing',str(WQ/'in')+'/',REMOTE+'wq/in/'],check=True)
  subprocess.run(['rsync','-a',REMOTE+'wq/out/',str(WQ/'out')+'/'],check=True)
  for o in sorted((WQ/'out').glob('*.json')):
   if o.name in done_out:continue
   try:res=json.load(open(o))
   except ValueError:continue
   done_out.add(o.name);name=o.name[:-5];meta=index.get(name)
   if not meta:continue
   p=Path(meta['path']);N=meta['n'];hits=res.get('hits',{})
   best=min(((float(v[0])-L[int(c)],int(c),v) for c,v in hits.items()),default=None)
   with open(W/'wscan.tsv','a') as f:
    f.write(f"{time.time()}\t{N}\t{res.get('secs')}\t{len(hits)}\t{'' if best is None else best[1]}\t{'' if best is None else repr(best[0])}\t{p}\t{res.get('error','')}\n")
   local=WQ/'in'/f'{name}.csv'
   for c,(s,a,b) in sorted(((int(c),v) for c,v in hits.items())):
    if not s<L[c]-math.sqrt(c)*1e-10-1e-9:continue
    rows=window_rows(local,a,b,s,c)
    if rows is None:log(f'window {N}->{c} from {p}: window does not hold {c} squares, dropped');continue
    _,fr,sc,e=floatsafe.work((c,rows))
    if fr is None or not (sc+1)*math.sqrt(c)<L[c]-math.sqrt(c)*1e-10:
     log(f'window {N}->{c} from {p}: certified {None if fr is None else (sc+1)*math.sqrt(c)} not below the bar {L[c]}');continue
    copy=W/'donors'/f'{N}-{name[:16]}.csv'
    if not copy.exists():shutil.copyfile(local,copy)
    row=meta['row']
    _,sN,_=bs.read_near(str(local))
    dsrc=f'{p}'+(f', from {p.parent}/take.tsv: {row["source"]}' if row else ', '+bs.near_source(str(p),N,sN,L[N]))
    lic=row.get('licence','ours') if row else bs.near_metadata(str(p)).get('licence') or 'ours (near layout of another lane)'
    md=metadata(p)
    if md:
     dsrc+='; recorded ancestry '+json.dumps(md,sort_keys=True);lic=md.get('licence') or lic
    uid=f'{c}-win-{N}-{name[:8]}-'+hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
    ss,AA=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr])
    man=dict(id=uid,kind='win',donor=str(N),n=str(c),corner='0',variant='0',dropped='0',window=dict(a=a,b=b,s=s),
             near=str(copy),donor_source=dsrc,donor_licence=lic,built_L=repr(ss))
    csvout(W/'staged'/f'{uid}.csv',fr)
    bs.write_txt(str(W/'final'/f'{uid}.input.txt'),ss,AA)
    job=dict(input=f'{uid}.input.txt',output=f'{uid}.output.txt',n=c,manifest=man,certified_before=sc,
             chain={'mode':'sub-window, certified directly (literature_window.scan_one on boxC)','s_start':ss,'log':[]})
    (W/'final'/f'{uid}.job.json').write_text(json.dumps(job))
    log(f'direct sub-window {N}->{c} score {sc:.16g} (side {ss:.12f}, bar {L[c]:.12f}) from {p}; queued certified-file fq {uid}')
 except Exception:
  import traceback;traceback.print_exc()
 time.sleep(60)
log('wfeed finished by deadline')
