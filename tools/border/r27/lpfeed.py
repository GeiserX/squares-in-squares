"""boxA feeder for contact-LP jobs on boxC (border r27, light python; r26 next item 1).
Every 60 s: each fresh take or near csv of the other take-*-r27 dirs whose side is within LP_GAP above the live bar
(bars.json) and whose recorded ancestry passes provenance.audit is copied (pinned by sha256) to lp/nin/<id>_<n>.csv
with a job lp/jobs/<id>.json; the boxC worker runs methods_lp.py on it (90 s cap). Outputs are pulled, floatsafed,
and every one below the live bar by more than 1e-10 of score gets a certified-file fq job in final/ with an 'lp'
manifest, which the driver publishes through the same source policy and share test as every other row."""
import os,sys,time,json,csv,math,hashlib,shutil,subprocess,glob
from pathlib import Path
W=Path(__file__).parent;S=W.parent.parent;T=W.parent
src=(W/'driver.py').read_text()
src=src[:src.index("log('start round27 collector/scanner")]
src=src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_lpfeed','__file__':str(W/'driver.py')};exec(compile(src,str(W/'driver.py'),'exec'),ns)
bs=ns['bs'];floatsafe=ns['floatsafe'];audit=ns['audit'];metadata=ns['metadata'];csvout=ns['csvout']
REMOTE='boxC:scratch/squares-border-r27/'
END=float((W/'deadline').read_text());LP_GAP=float(os.environ.get('LP_GAP','5e-9'))
D=W/'lp';[ (D/x).mkdir(parents=True,exist_ok=True) for x in ('nin','jobs','nout')]
index_file=D/'index.json';index=json.load(open(index_file)) if index_file.exists() else {}
seen=set(v['key'] for v in index.values());done=set()
def log(msg):
 s=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+msg
 print(s,flush=True)
 with open(T/'STATE.txt','a') as f:f.write(s+'\n')
def side_of(p):
 xs=[]
 for r in csv.DictReader(open(p)):
  a=float(r['angle']);h=.5*(abs(math.cos(a))+abs(math.sin(a)));xs.append((float(r['x']),float(r['y']),h))
 return len(xs),max(max(x+h for x,y,h in xs)-min(x-h for x,y,h in xs),max(y+h for x,y,h in xs)-min(y-h for x,y,h in xs))
while time.time()<END-420:
 try:
  L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
  new=0
  for t in S.glob('take-*-r27'):
   if t==T:continue
   try:rows={r['n']:r for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t')}
   except (OSError,ValueError,KeyError):rows={}
   cands=[(p,rows.get(p.stem)) for p in t.glob('*.csv') if p.stem.isdigit()]+[(p,None) for p in t.glob('near/*.csv')]
   # r27: frozen raw and unconverged layouts within 5e-9 of side above bar27 (work/lp-extra.txt from below.tsv, raw
   # first) after the fresh files; r26 measured 1.5e-10 to 5.0e-10 of score from the LP on raw layouts.
   if t==sorted(x for x in S.glob('take-*-r27') if x!=T)[-1] and (W/'lp-extra.txt').exists():
    cands+=[(Path(x),None) for x in (W/'lp-extra.txt').read_text().split()]
   for p,row in cands:
    try:st=p.stat()
    except OSError:continue
    key=f'{p}|{st.st_mtime_ns}|{st.st_size}'
    if key in seen or st.st_size>1500000:continue
    seen.add(key)
    try:
     first=next(csv.DictReader(open(p)));N=int(first['n'])
     m,side=side_of(p)
    except Exception:continue
    if m!=N or N not in L or not(-3e-9<side-L[N]<LP_GAP):continue
    # r27: the walk runs when an LP result certifies below the bar (boxA at load 120), not at queue time.
    data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()
    ident=digest[:12]
    if ident in index:continue
    (D/'nin'/f'{ident}_{N}.csv').write_bytes(data)
    (D/'jobs'/f'{ident}.json').write_text(json.dumps(dict(input=f'nin/{ident}_{N}.csv',out=f'nout/{ident}_{N}',n=N,priority=(-160 if p.stem.isdigit() else -150) if '-r27/' in str(p) else -140)))
    index[ident]=dict(key=key,path=str(p),row=row,n=N,sha256=digest,side=side,gap=side-L[N]);new+=1
    if new>=40:break
    log(f'LP queue {N} from {p} (sha256 {digest[:16]}), side {side:.13f}, {side-L[N]:.3e} above the live bar; boxC worker, 90 s cap, deadline 23:45Z')
  if new:
   tmp=index_file.with_suffix('.tmp');tmp.write_text(json.dumps(index));tmp.replace(index_file)
   subprocess.run(['rsync','-a','--ignore-existing',str(D/'nin')+'/',REMOTE+'lp/nin/'],check=True)
   subprocess.run(['rsync','-a','--ignore-existing',str(D/'jobs')+'/',REMOTE+'lp/jobs/'],check=True)
  subprocess.run(['rsync','-a',REMOTE+'lp/nout/',str(D/'nout')+'/'],check=True)
  for ident,meta in index.items():
   if ident in done:continue
   N=meta['n'];outdir=D/'nout'/f'{ident}_{N}'
   if not (outdir/'DONE').exists():continue
   done.add(ident)
   raw=sorted(glob.glob(str(outdir/'raw/*.csv')))
   # r27 21:35Z: the LP of the backlog 866 gave 4.6e-9 of side and the certified-file fq after it 1.2e-6 more, so
   # every LP result within LP_GAP of the live bar gets the certified-file fq; with no LP output the start itself does.
   src_file=raw[-1] if raw else str(D/'nin'/f'{ident}_{N}.csv')
   if not raw:log(f'LP {N} {ident}: no LP gain; the start gets the certified-file fq')
   rr=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(src_file))]
   _,fr,sc,e=floatsafe.work((N,rr))
   if fr is None:log(f'LP {N} {ident}: output does not certify ({e})');continue
   side=(sc+1)*math.sqrt(N);gap=side-L[N]
   with open(D/'lp.tsv','a') as f:f.write(f"{time.time()}\t{N}\t{meta['side']!r}\t{side!r}\t{L[N]!r}\t{meta['path']}\n")
   if not gap<LP_GAP:
    log(f'LP {N} {ident}: certified side {side:.13f}, {gap:.3e} above the live bar (start {meta["gap"]:.3e}); no row');continue
   p=Path(meta['path'])
   if not audit(p,meta['row']):log(f'LP {N} {ident}: below the bar but the walk refuses {p}');continue
   copy=W/'donors'/f'{N}-{ident}.csv'
   if not copy.exists():(copy).write_bytes((D/'nin'/f'{ident}_{N}.csv').read_bytes())
   row=meta['row']
   dsrc=f'{p}'+(f', from {p.parent}/take.tsv: {row["source"]}' if row else ', '+bs.near_source(str(p),N,meta['side'],L[N]))
   lic=row.get('licence','ours') if row else bs.near_metadata(str(p)).get('licence') or 'ours (near layout of another lane)'
   md=metadata(p)
   if md:
    dsrc+='; recorded ancestry '+json.dumps(md,sort_keys=True);lic=md.get('licence') or lic
   uid=f'{N}-lp-{ident[:8]}-'+hashlib.sha256(repr(sc).encode()).hexdigest()[:8]
   ss,AA=bs.normalize([(float(q['x']),float(q['y']),float(q['angle'])) for q in fr])
   man=dict(id=uid,kind='lp',donor=str(N),n=str(N),corner='0',variant='0',dropped='0',near=str(copy),donor_source=dsrc,donor_licence=lic,built_L=repr(ss),start_sha256=meta['sha256'])
   csvout(W/'staged'/f'{uid}.csv',fr)
   bs.write_txt(str(W/'final'/f'{uid}.input.txt'),ss,AA)
   job=dict(input=f'{uid}.input.txt',output=f'{uid}.output.txt',n=N,manifest=man,certified_before=sc,
            chain={'mode':'contact LP reclose (methods_lp.py --iters 40 on boxC), certified directly','s_start':ss,'log':[]})
   (W/'final'/f'{uid}.job.json').write_text(json.dumps(job))
   log(f'LP {N} {ident}: certified score {sc:.16g} (side {side:.13f}, {gap:.3e} vs the live bar); queued certified-file fq {uid}')
 except Exception:
  import traceback;traceback.print_exc()
 time.sleep(60)
log('lpfeed finished by deadline')
