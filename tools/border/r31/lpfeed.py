"""boxA feeder for contact-LP jobs on boxC (border r27, light python; r26 next item 1).
Every 60 s: each fresh take or near csv of the other take-*-r31 dirs whose side is within LP_GAP above the live bar
(bars.json) and whose recorded ancestry passes provenance.audit is copied (pinned by sha256) to lp/nin/<id>_<n>.csv
with a job lp/jobs/<id>.json; the boxC worker runs methods_lp.py on it (90 s cap). Outputs are pulled, floatsafed,
and every one below the live bar by more than 1e-10 of score gets a certified-file fq job in final/ with an 'lp'
manifest, which the driver publishes through the same source policy and share test as every other row."""
import os,sys,time,json,csv,math,hashlib,shutil,subprocess,glob
from pathlib import Path
W=Path(__file__).parent;S=W.parent.parent;T=W.parent
src=(W/'driver.py').read_text()
src=src[:src.index("log('start round31 collector/scanner")]
src=src.replace("LOCK=open(W/'collector.lock','w');fcntl.flock(LOCK,fcntl.LOCK_EX|fcntl.LOCK_NB)","")
ns={'__name__':'border_lpfeed','__file__':str(W/'driver.py')};exec(compile(src,str(W/'driver.py'),'exec'),ns)
bs=ns['bs'];floatsafe=ns['floatsafe'];audit=ns['audit'];metadata=ns['metadata'];csvout=ns['csvout']
REMOTE='boxC:scratch/squares-border-r31/'
END=float((W/'deadline').read_text());LP_GAP=float(os.environ.get('LP_GAP','5e-9'))
# r28: a near file of another lane up to LP_GAP_NEAR above the live bar also gets the LP and, idle slots only, the
# certified-file fq (r27: fq gained 1.2e-6 on one unconverged input; on converged inputs it gave back up to 6e-3).
LP_GAP_NEAR=float(os.environ.get('LP_GAP_NEAR','1e-6'))
D=W/'lp';[ (D/x).mkdir(parents=True,exist_ok=True) for x in ('nin','jobs','nout')]
index_file=D/'index.json';index=json.load(open(index_file)) if index_file.exists() else {}
seen=set(v['key'] for v in index.values());done=set()
# r28 02:45Z: the processed LP outputs persist (lp/done.json), so a restart does not certify every output again; at the
# switch to finesafe only outputs whose raw side is below the rule are certified again (side_of on the raw csv).
def side_of(p):
 xs=[]
 for r in csv.DictReader(open(p)):
  a=float(r['angle']);h=.5*(abs(math.cos(a))+abs(math.sin(a)));xs.append((float(r['x']),float(r['y']),h))
 return len(xs),max(max(x+h for x,y,h in xs)-min(x-h for x,y,h in xs),max(y+h for x,y,h in xs)-min(y-h for x,y,h in xs))
DONE_FILE=D/'done.json'
if DONE_FILE.exists():done=set(json.load(open(DONE_FILE)))
else:
 _L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
 for _i,_m in index.items():
  _o=D/'nout'/f"{_i}_{_m['n']}"
  if not (_o/'DONE').exists():continue
  _r=sorted(glob.glob(str(_o/'raw/*.csv')));_f=_r[-1] if _r else str(D/'nin'/f"{_i}_{_m['n']}.csv")
  try:_n,_s=side_of(_f)
  except Exception:continue
  if _s>=_L.get(_m['n'],0)-math.sqrt(_m['n'])*1e-10:done.add(_i)
# r29 06:55Z: rank by the measured source of crossings. In r28 every crossing came from a take csv (gap 0) or from a near
# file above the bar (the forensics 916-rect at +6.2e-7 and +8.7e-8); no near file within 5e-9 of the bar crossed (its
# certify gain is about 28% of the rule). r28 ranked those bar-side near files (-150) before the near files above the bar
# (-130); now the order is take csv, near above the bar, bar-side near, frozen extras.
def lp_priority(p,gap):
 fresh='-r31/' in str(p)
 if p.stem.isdigit():return -160 if fresh else -135
 if gap>=LP_GAP:return -138 if fresh else -132   # r30 17:15Z: after the worker-1 kicks (-140); near-file LP gave no lasting row this round, held-row kicks gave 2
 return -125 if fresh else -120
def final_priority(path,gap0,cert_gap,N):
 # the certified-file fq after an LP: a certified input below the rule keeps the worker default (-200); otherwise
 # take inputs -175, near inputs above the bar -165, bar-side near inputs -122 (after every fresh LP job).
 if cert_gap < -math.sqrt(N)*1e-10:return None
 p=Path(path)
 if p.stem.isdigit():return -175
 return -165 if gap0>=LP_GAP else -122
def log(msg):
 s=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())+' '+msg
 print(s,flush=True)
 with open(T/'STATE.txt','a') as f:f.write(s+'\n')
while time.time()<END-420:
 try:
  L={int(k):v for k,v in json.load(open(W/'bars.json')).items()}
  new=0
  for t in S.glob('take-*-r31'):
   if t==T:continue
   try:rows={r['n']:r for r in csv.DictReader(open(t/'take.tsv'),delimiter='\t')}
   except (OSError,ValueError,KeyError):rows={}
   cands=[(p,rows.get(p.stem)) for p in t.glob('*.csv') if p.stem.isdigit()]  # r31 (r30 next item 4): take csv only; 406 near-file LP inputs gave no row in r30
   # r27: frozen raw and unconverged layouts within 5e-9 of side above bar27 (work/lp-extra.txt from below.tsv, raw
   # first) after the fresh files; r26 measured 1.5e-10 to 5.0e-10 of score from the LP on raw layouts.
   if False:
    cands+=[(Path(x),None) for x in (W/'lp-extra.txt').read_text().split()]
   for p,row in cands:
    try:st=p.stat()
    except OSError:continue
    key=f'{p}|{st.st_mtime_ns}|{st.st_size}'
    if key in seen or st.st_size>1500000:continue
    try:
     first=next(csv.DictReader(open(p)));N=int(first['n'])
     m,side=side_of(p)
    except Exception:continue
    gapmax=LP_GAP if p.stem.isdigit() else LP_GAP_NEAR
    # r29 06:37Z: a file more than 3e-9 below bars.json is read again next pass (the backlog 421 take was read before
    # the driver's refresh put it into bars.json, marked seen, and never queued); others are marked seen as before.
    if m==N and N in L and side-L[N]<=-3e-9:continue
    seen.add(key)
    if m!=N or N not in L or not(-3e-9<side-L[N]<gapmax):continue
    # r27: the walk runs when an LP result certifies below the bar (boxA at load 120), not at queue time.
    data=p.read_bytes();digest=hashlib.sha256(data).hexdigest()
    ident=digest[:12]
    if ident in index:continue
    (D/'nin'/f'{ident}_{N}.csv').write_bytes(data)
    (D/'jobs'/f'{ident}.json').write_text(json.dumps(dict(input=f'nin/{ident}_{N}.csv',out=f'nout/{ident}_{N}',n=N,priority=lp_priority(p,side-L[N]))))
    index[ident]=dict(key=key,path=str(p),row=row,n=N,sha256=digest,side=side,gap=side-L[N]);new+=1
    if new>=40:break
    log(f'LP queue {N} from {p} (sha256 {digest[:16]}), side {side:.13f}, {side-L[N]:.3e} above the live bar; boxC worker, 90 s cap, deadline 00:15Z')
  if new:
   tmp=index_file.with_suffix('.tmp');tmp.write_text(json.dumps(index));tmp.replace(index_file)
   subprocess.run(['rsync','-a','--ignore-existing',str(D/'nin')+'/',REMOTE+'lp/nin/'],check=True)
   subprocess.run(['rsync','-a','--ignore-existing',str(D/'jobs')+'/',REMOTE+'lp/jobs/'],check=True)
  subprocess.run(['rsync','-a',REMOTE+'lp/nout/',str(D/'nout')+'/'],check=True)
  for ident,meta in index.items():
   if ident in done:continue
   N=meta['n'];outdir=D/'nout'/f'{ident}_{N}'
   if not (outdir/'DONE').exists():continue
   done.add(ident);tmpd=DONE_FILE.with_suffix('.tmp');tmpd.write_text(json.dumps(sorted(done)));tmpd.replace(DONE_FILE)
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
   if not gap<(LP_GAP if Path(meta['path']).stem.isdigit() else LP_GAP_NEAR):
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
   # r28: the certified-file fq runs with the POLISH flags (no loosen, no ALM) on every LP result; a near input more
   # than LP_GAP above the bar (not converged) also gets the default-flag fq. r27: the default fq ended higher than its
   # input on 140 of 146 LP finals (median 9.2e-5 of side worse).
   pol=W/'final'/f'{uid}-p.input.txt';pol.write_bytes((W/'final'/f'{uid}.input.txt').read_bytes())
   (W/'staged'/f'{uid}-p.csv').write_bytes((W/'staged'/f'{uid}.csv').read_bytes())
   fp=final_priority(meta['path'],meta['gap'],gap,N)
   if fp is not None:job['priority']=fp
   jp=dict(job,input=f'{uid}-p.input.txt',output=f'{uid}-p.output.txt',flags=list(bs.POLISH),manifest=dict(man,id=uid+'-p'))
   (W/'final'/f'{uid}-p.job.json').write_text(json.dumps(jp))
   default=False  # r31: the polish fq only (two worker slots; r27: the default fq ended higher than its input on 140 of 146 LP finals)
   if default:
    (W/'final'/f'{uid}.job.json').write_text(json.dumps(job))
   log(f'LP {N} {ident}: certified score {sc:.16g} (side {side:.13f}, {gap:.3e} vs the live bar); queued certified-file fq {uid}-p (polish flags)'+(f' and {uid} (default flags)' if default else ''))
 except Exception:
  import traceback;traceback.print_exc()
 time.sleep(60)
log('lpfeed finished by deadline')
