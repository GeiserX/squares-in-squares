"""Stage fresh and deferred joins with immutable input and ancestry records."""
import pathlib,sys,json,csv,re,collections,hashlib,subprocess,os,time,tarfile
from provenance24 import W,S,R,mlp,credit,key,banned
from eligible24 import SPECIAL,BARS
sys.path.insert(0,str(W/'lane'));import k123_join as kj
os.chdir(W)
remote_bytes=1024*int(subprocess.check_output(['ssh','-S','/tmp/squares-k123-r24-ssh','boxE','du -sk $SCRATCH/squares-k123'],text=True).split()[0])
if remote_bytes>2800000000:raise RuntimeError('boxE scratch budget: staging paused above 2.8GB')
from thin23 import select as thin_select
def journal(msg):
 with open(W.parent/'STATE.txt','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA '+msg+'\n')
def stage(tag,P,origins,pairs,kind,source):
 D=W/tag;D.mkdir(exist_ok=True);manifest={}
 for n,A in P.items():
  c=credit(n,A,origins.get(n))
  if c:manifest[str(n)]=c
 pairs=[(a,b) for a,b in pairs if str(a) in manifest and str(b) in manifest]
 if not pairs:return False
 need={n for pair in pairs for n in pair}
 with open(D/(tag+'.csv'),'w') as f:
  w=csv.writer(f);w.writerow(['n','square_id','x','y','angle'])
  for n in sorted(need):w.writerows((n,i,*r) for i,r in enumerate(P[n]))
 (D/('sources-'+tag+'.json')).write_text(json.dumps(manifest))
 (D/('bars-'+tag+'.tsv')).write_text((W/'bars.tsv').read_text())
 remote_csv=D/(tag+'.csv');remote_manifest=D/('sources-'+tag+'.json')
 if remote_bytes>1700000000 and len(need)>16:
  common=collections.Counter(nn for a,b in pairs for nn in (a,b)).most_common(1)[0][0]
  others=sorted(need-{common});levels={nn:int(mlp.side(P[nn])) for nn in need};frac={nn:float(mlp.side(P[nn]))-levels[nn] for nn in need}
  keep=set(thin_select(others,frac,levels,frac[common],levels[common],limit=15))|{common}
  plan=dict(tag=tag,source=source,full_input=str(D/(tag+'.csv')),planned_pairs=pairs,selected=sorted(keep),reason='1.7GB watermark; productive ends retained, including928')
  (D/'cap-deferred24.json').write_text(json.dumps(plan))
  with open(W/'cap-deferred24.jsonl','a') as h:h.write(json.dumps(plan)+'\n')
  pairs=[(a,b) for a,b in pairs if a in keep and b in keep]
  remote_csv=D/('remote-'+tag+'.csv');remote_manifest=D/('remote-sources-'+tag+'.json')
  with open(remote_csv,'w') as f:
   wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
   for nn in sorted(keep):wr.writerows((nn,i,*r) for i,r in enumerate(P[nn]))
  remote_manifest.write_text(json.dumps({nn:c for nn,c in manifest.items() if int(nn) in keep}))
 (D/('pairs-'+tag+'.txt')).write_text(' '.join(f'{min(a,b)},{max(a,b)}' for a,b in pairs))
 task=dict(kind='scan',tag=tag,source=source,origin_kind=kind,pairs=len(pairs));(D/(tag+'.json')).write_text(json.dumps(task))
 with tarfile.open(D/'send.tgz','w:gz',compresslevel=1) as t:
  t.add(remote_csv,arcname=tag+'.csv');t.add(remote_manifest,arcname='sources-'+tag+'.json')
  for name in ['bars-'+tag+'.tsv','pairs-'+tag+'.txt']:t.add(D/name,arcname=name)
  t.add(D/(tag+'.json'),arcname='incoming/'+tag+'.json')
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r24-ssh','-o','ControlMaster=auto','-o','ControlPersist=600','-q',str(D/'send.tgz'),'boxE:scratch/squares-k123/send.tgz'],check=True)
 subprocess.run(['ssh','-S','/tmp/squares-k123-r24-ssh','boxE','cd $SCRATCH/squares-k123 && tar xzf send.tgz && mv incoming/*.json tasks/ && rm send.tgz'],check=True)
 journal(f'START boxE {kind} scan {tag}, pairs={len(pairs)}, source={source}, log out/scan{tag}.log, deadline22:15Z')
 print('staged',tag,kind,len(pairs),source,flush=True);return True

def current():
 P=mlp.load(str(S/'gather/round23-2026-11-13a.csv'));origins={n:'held' for n in P};scores={int(r['n']):float(r['score']) for r in csv.DictReader(open(S/'gate/cand-round23-1113a/details.csv'))}
 for p in sorted(S.glob('take-*-r24/take.tsv')):
  for row in csv.DictReader(open(p),delimiter='\t'):
   try:
    n=int(row['n']);s=float(row['new']);f=p.parent/f'{n}.csv'
    if s<scores[n] and f.exists():
     A=mlp.load(str(f),{n})[n]
     if credit(n,A,str(f)):P[n]=A;origins[n]=str(f);scores[n]=s
   except (ValueError,KeyError):pass
 (W/'bars.tsv.tmp').write_text(''.join(f'{n}\t{(BARS[n] if n in SPECIAL else (scores[n]+1)*n**.5):.12f}\t{scores[n]!r}\t{origins[n]}\n' for n in sorted(P)));(W/'bars.tsv.tmp').replace(W/'bars.tsv')
 subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r24-ssh','-o','ControlMaster=auto','-o','ControlPersist=600','-q',str(W/'bars.tsv'),'boxE:scratch/squares-k123/bars.tmp'],check=True);subprocess.run(['ssh','-S','/tmp/squares-k123-r24-ssh','boxE','cd $SCRATCH/squares-k123 && mv bars.tmp bars.tsv'],check=True)
 return P,origins

def fresh():
 P,origins=current();seenfile=W/'fresh-seen.json';seen=json.load(open(seenfile)) if seenfile.exists() else {};classes={}
 for n,A in P.items():
  if n<100:continue
  try:
   X=kj.Lay(n,*kj.norm(A),str(n))
   if len(X.G)<10:continue
   pairs={(int(X.size[i-1]),int(X.size[i])) for i in range(4,len(X.G)-4)};pairs|={(b,a) for a,b in list(pairs)};classes[n]=pairs
  except Exception:pass
 candidates=[]
 for t in S.glob('take-*-r24'):
  candidates+=list(t.glob('*.csv'))+list((t/'near').glob('*.csv'))
 log=S/'handoff-r24.log'
 if log.exists():
  candidates.extend(pathlib.Path(p) for p in re.findall(r'($DATA/[^\s,;]+\.csv)',log.read_text()) if '-r24/' in p and pathlib.Path(p).exists())
 candidates=list(dict.fromkeys(candidates))
 candidates.sort(key=lambda p:('/near/' in str(p),-p.stat().st_mtime))
 seq=int((W/'seq').read_text()) if (W/'seq').exists() else 10000;staged=0;refused=[]
 for p in candidates:
  sig=hashlib.sha256(p.read_bytes()).hexdigest()
  if seen.get(str(p))==sig:continue
  try:
   d=mlp.load(str(p))
   if len(d)!=1:seen[str(p)]=sig;continue
   n,A=next(iter(d.items()));c=credit(n,A,str(p))
   if not c:refused.append(str(p));continue
   X=kj.Lay(n,*kj.norm(A),str(n))
   if len(X.G)<10:seen[str(p)]=sig;continue
   types={(int(X.size[i-1]),int(X.size[i])) for i in range(4,len(X.G)-4)};types|={(b,a) for a,b in list(types)}
   partners=[nn for nn in classes if types&classes[nn]];ns=set(partners)|{n};donors={nn:A if nn==n else P[nn] for nn in ns};oo={**origins,n:str(p)}
   seq+=1;(W/'seq').write_text(str(seq));tag=f'fresh{seq}';npairs=[(n,nn) for nn in partners]+([(n,n)] if n not in partners else [])
   if stage(tag,donors,oo,npairs,'fresh',str(p)):
    staged+=1;seen[str(p)]=sig;seenfile.write_text(json.dumps(seen));(W/'seq').write_text(str(seq))
   if staged>=6:break
  except Exception as e:
   if isinstance(e,KeyError):seen[str(p)]=sig
   print('stage error',str(p),type(e).__name__,str(e),flush=True)
 (W/'seq').write_text(str(seq));seenfile.write_text(json.dumps(seen));(W/'fresh-refused.json').write_text(json.dumps(refused,indent=2));print('fresh staged',staged,'refused',len(refused),flush=True)

def deferred(limit=6):
 if (W/'deferred-batch-size').exists():limit=int((W/'deferred-batch-size').read_text())
 if not (W/'bars.tsv').exists():current()
 O=S/'take-k123-r23/work';seenfile=W/'deferred-seen.json';seen=set(json.load(open(seenfile))) if seenfile.exists() else set();seq=int((W/'deferred-seq').read_text()) if (W/'deferred-seq').exists() else 0;catalogs={};count=0
 for line in (O/'cap-deferred.jsonl').read_text().splitlines():
  j=json.loads(line)
  if j['tag'] in seen:continue
  seen.add(j['tag']);catalog=j['full_catalog'];n=j['donor'];source=j['source'];target=pathlib.Path(j['donor_geometry'])
  if not target.exists():continue
  donor=mlp.load(str(target),{n});A=donor[n]
  if not credit(n,A,source):continue
  if catalog not in catalogs:catalogs[catalog]=mlp.load(catalog)
  C=catalogs[catalog];bp=pathlib.Path(catalog).with_name(pathlib.Path(catalog).stem+'-bars.tsv');orig={int(w[0]):w[3] for l in bp.read_text().splitlines() if len(w:=l.split('\t'))>=4}
  partners=set(j['planned_partners'])-set(j['selected_partners']);P={nn:C[nn] for nn in partners if nn in C};P[n]=A;orig[n]=source
  seq+=1;(W/'deferred-seq').write_text(str(seq));tag=f'defer{seq:05d}'
  if stage(tag,P,orig,[(n,nn) for nn in P if nn!=n],'deferred',source):
   count+=1;seenfile.write_text(json.dumps(sorted(seen)))
  if count>=limit:break
 seenfile.write_text(json.dumps(sorted(seen)));(W/'deferred-seq').write_text(str(seq));print('deferred staged',count,'visited',len(seen),flush=True)
if __name__=='__main__':
 if len(sys.argv)>1 and sys.argv[1]=='deferred':deferred(int(sys.argv[2]) if len(sys.argv)>2 else 6)
 else:fresh()
