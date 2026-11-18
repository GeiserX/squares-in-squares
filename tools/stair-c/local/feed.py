import datetime,glob,hashlib,json,math,os,pickle,re,subprocess,sys,time
S='$SCRATCH/bounties-squares';T=S+'/take-stair-c-r23';W=T+'/work';L='.';sys.path.insert(0,L)
import modules as M
import numpy as np
_base=pickle.load(open(W+'/box/libbase/library.pkl','rb'))
baseprints={q['id']:hashlib.sha256(np.round(q['P'],9).tobytes()+repr((q.get('f0'),q['count'],q.get('y0'),q.get('x0'),q.get('lam0'),q.get('g'),q.get('g1'),q.get('g2'))).encode()).hexdigest() for q in _base['mods']}
def modprint(q):return hashlib.sha256(np.round(q['P'],9).tobytes()+repr((q.get('f0'),q['count'],q.get('y0'),q.get('x0'),q.get('lam0'),q.get('g'),q.get('g1'),q.get('g2'))).encode()).hexdigest()
def fingerprint(b):
 f=b.get('f',b.get('f0'));return 'geom:'+hashlib.sha256(repr((b['c1'],b['c2'],round(f,8),b['count'],round(b['y0'],7),round(b['x0'],7))).encode()+np.round(b['P'],7).tobytes()).hexdigest()
stop=datetime.datetime(2026,11,13,18,15,tzinfo=datetime.timezone.utc).timestamp()
state=W+'/feed-state.json';seen=set(json.load(open(state))) if os.path.exists(state) else set()
for _tag in (json.load(open(W+'/donor-delivery-proof.json')) if os.path.exists(W+'/donor-delivery-proof.json') else []):seen.add('delivered:'+_tag)
os.makedirs(W+'/donors',exist_ok=True)
def checkpoint():
 json.dump(sorted(seen),open(state+'.tmp','w'));os.replace(state+'.tmp',state)
def mtime(p):
 try:return os.stat(p).st_mtime_ns
 except OSError:return 0
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def shell(cmd):return subprocess.run(cmd,timeout=55,capture_output=True,text=True)
def queuepatch(tag,x):
 p=W+'/patches/'+tag+'.pkl';pickle.dump(x,open(p,'wb'))
 r=shell(['rsync','-az',p,'boxE:scratch/squares-stair-c/patches/'])
 if r.returncode:raise RuntimeError('rsync '+r.stderr)
 r=shell(['ssh','-n','boxE',f'cd $SCRATCH/squares-stair-c && echo "follow-{tag} ./patch22.sh {tag}" >> q.txt'])
 if r.returncode:raise RuntimeError('ssh '+r.stderr)
 print(stamp(),'QUEUED',tag,len(x['mods']),flush=True)
 with open(T+'/STATE.txt','a') as h:h.write(stamp()+' FOLLOW '+tag+' '+str(len(x['mods']))+' modules queued boxE patch22.sh; deadline18:30Z; log logs/q-'+tag+'.log\n')
def cycle():
 # New corner-library handoffs are copied as data and tabulated in our existing slots.
 txt=open(S+'/handoff-r23.log').read() if os.path.exists(S+'/handoff-r23.log') else ''
 paths=set(re.findall(r'$SCRATCH/bounties-squares/take-[^\s,;]+/work/zones-[^\s,;]+',txt))
 for p in sorted(paths):
  if '/take-stair-c-' in p or not os.path.exists(p+'/corners.pkl'):continue
  digest=hashlib.sha256(open(p+'/corners.pkl','rb').read()).hexdigest()
  versionkey=p+':corners:'+digest
  if versionkey in seen:continue
  oldtag='ext-'+hashlib.sha256(p.encode()).hexdigest()[:9]
  oldcopy=W+'/external/'+oldtag+'/corners.pkl'
  if p in seen and os.path.exists(oldcopy) and hashlib.sha256(open(oldcopy,'rb').read()).hexdigest()==digest:
   seen.add(versionkey);continue
  tag='ext-'+hashlib.sha256((p+digest).encode()).hexdigest()[:9]
  d=W+'/external/'+tag;os.makedirs(d,exist_ok=True)
  for f in glob.glob(p+'/*.pkl'):
   __import__('shutil').copy2(f,d+'/'+os.path.basename(f))
  r=shell(['rsync','-az',d,'boxC:scratch/squares-stair-c/external/'])
  if r.returncode:continue
  r=shell(['ssh','-n','boxC',f'cd $SCRATCH/squares-stair-c && echo "follow-{tag} ./external.sh {tag}" >> q.txt'])
  if r.returncode:continue
  seen.add(versionkey);checkpoint();print(stamp(),'CORNER',p,tag,flush=True)
  with open(T+'/STATE.txt','a') as h:h.write(stamp()+' FOLLOW new corner '+p+' queued boxC external.sh '+tag+'; deadline18:30Z\n')
 # New staircase base files handed over by another design lane also get a table run.
 known=set(seen)
 for own in glob.glob(W+'/boxcopy/*/corners/*.pkl'):
  try:
   for b in pickle.load(open(own,'rb')):known.add(fingerprint(b))
  except Exception:pass
 bases=set(re.findall(r'$SCRATCH/bounties-squares/take-[^\s,;]+/work/[^\s,;]+\.pkl',txt))
 for p in sorted(bases):
  if '/take-stair-c-' in p or not os.path.isfile(p):continue
  try:
   data=pickle.load(open(p,'rb'))
   if not isinstance(data,list) or not data or not all(k in data[0] for k in ('f','P','c1','c2','count')):continue
  except Exception:continue
  digest=hashlib.sha256(open(p,'rb').read()).hexdigest()[:9];key=p+digest
  if key in seen:continue
  tag='base-'+digest
  fresh=[b for b in data if fingerprint(b) not in known]
  if not fresh:seen.add(key);print(stamp(),'SKIP identical base',p,flush=True);continue
  filtered=W+'/external/'+tag+'.pkl';pickle.dump(fresh,open(filtered,'wb'))
  r=shell(['rsync','-az',filtered,'boxC:scratch/squares-stair-c/external/'+tag+'.pkl'])
  if r.returncode:continue
  r=shell(['ssh','-n','boxC',f'cd $SCRATCH/squares-stair-c && echo "follow-{tag} ./base22.sh {tag}" >> q.txt'])
  if r.returncode:continue
  known.update(fingerprint(b) for b in fresh);seen.update(fingerprint(b) for b in fresh)
  seen.add(key);checkpoint();print(stamp(),'BASE',p,len(data),tag,flush=True)
 # Import only the new modules named by each new modules-lane handoff.
 for p in sorted(glob.glob(S+'/take-modules-r23/work/need-j*.txt')):
  base=os.path.dirname(p)+'/lib23'
  try:version=p+':lens:'+str(os.stat(base+'/lens.pkl').st_mtime_ns)
  except OSError:continue
  if version in seen:continue
  ids=set(open(p).read().split())
  a=pickle.load(open(base+'/library.pkl','rb'));b=pickle.load(open(base+'/lens.pkl','rb'))
  missing=ids-set(b)
  if missing:print(stamp(),"SKIP untabulated states",p,sorted(missing),flush=True)
  ids&=set(b)
  if not ids:seen.add(version);continue
  fresh=[q for q in a['mods'] if q['id'] in ids and modprint(q)!=baseprints.get(q['id']) and 'module:'+modprint(q) not in seen]
  ids={q['id'] for q in fresh}
  if not ids:seen.add(version);print(stamp(),'SKIP base-identical module patch',p,flush=True);continue
  x={'mods':fresh,'lens':{k:v for k,v in b.items() if k in ids}}
  tag='mod-'+os.path.basename(p)[5:-4]+'-'+hashlib.sha256((' '.join(sorted(ids))+version).encode()).hexdigest()[:6]
  queuepatch(tag,x);seen.update('module:'+modprint(q) for q in fresh);seen.add(version);checkpoint()
 # Read fresh full layouts in our slice immediately. Their module tables are made on the box.
 for p in sorted(glob.glob(S+'/take-*-r23/*.csv')+glob.glob(S+'/take-*-r23/near/*.csv'),key=mtime,reverse=True):
  if '/take-stair-c-r23/' in p:continue
  try:n=int(os.path.basename(p).split('-')[0].split('.')[0])
  except ValueError:continue
  m=math.isqrt(n-1);k=n-m*m
  if n<100:continue
  try:
   donorbytes=open(p,'rb').read();fullhash=hashlib.sha256(donorbytes).hexdigest();taghash=fullhash[:12]
  except OSError:continue
  key=str(n)+':'+taghash
  tag='don-'+taghash[:9];legacy=key in seen
  if 'complete:'+key in seen:continue
  if 'delivered:'+tag in seen:
   seen.add('complete:'+key);continue
  snapshot=W+'/donors/'+str(n)+'-'+fullhash+'.csv'
  if not os.path.exists(snapshot):open(snapshot,'wb').write(donorbytes)
  try:
   packing=np.asarray(M.read_layouts(snapshot)[n],float);d,e=M.cut(packing,n)
  except Exception as e:
   print(stamp(),'READ FAILED',p,str(e),flush=True);seen.add('complete:'+key);checkpoint();continue
  print(stamp(),'READ',p,'arms',None if d is None else (d['c1'],d['c2']),'reason',e,flush=True)
  # The full-layout follow lanes already walk unreadable layouts. A new readable layout
  # contributes its corner and both far zones to our target combinations.
  if d is None:seen.add('complete:'+key);checkpoint();continue
  shape='packing:'+str(n)+':'+hashlib.sha256(np.round(packing[np.lexsort((packing[:,2],packing[:,1],packing[:,0]))],9).tobytes()).hexdigest()
  if shape in seen and not legacy:seen.add('complete:'+key);checkpoint();continue
  tag='don-'+taghash[:9];folder=W+'/external/'+tag;os.makedirs(folder,exist_ok=True)
  parent=os.path.dirname(p)
  if os.path.basename(parent)=='near':parent=os.path.dirname(parent)
  source='round23 layout '+p+'; immutable '+snapshot+' sha256 '+fullhash+'; source in '+parent+'/take.tsv'
  licence='source in '+parent+'/take.tsv'
  if os.path.exists(parent+'/take.tsv'):
   import csv
   row=next((r for r in csv.DictReader(open(parent+'/take.tsv'),delimiter='\t') if r['n']==str(n)),None)
   if row:source+=': '+row.get('source','');licence=row.get('licence',licence)
  for sidecar in (p+'.json',p[:-4]+'.json'):
   if not os.path.exists(sidecar):continue
   try:
    sj=json.load(open(sidecar));source+='; '+str(sj.get('source','manifest '+sidecar));licence=str(sj.get('licence',licence));break
   except Exception:pass
  source+='; donor manifests '+parent+'/work/sources-all.tsv and '+parent+'/take.tsv'
  mods=M.modules_of(d,source,licence,tag)
  pickle.dump(mods,open(folder+'/mods.pkl','wb'))
  r=shell(['rsync','-az',folder,'boxE:scratch/squares-stair-c/external/'])
  if r.returncode:continue
  r=shell(['ssh','-n','boxE',f'cd $SCRATCH/squares-stair-c && echo "follow-{tag} ./donor23.sh {tag}" >> q.txt'])
  if r.returncode:continue
  seen.update((key,'complete:'+key,shape,'delivered:'+tag));checkpoint()
 # Queue preparation starts before older builds, so fresh handoffs get tested promptly.
 priority='cd $SCRATCH/squares-stair-c && ./py -I priority23.py > logs/priority.log'
 result=shell(['ssh','-n','boxE','cd $SCRATCH/squares-stair-c && ./py -I dedupe23.py > logs/dedupe.log 2>&1'])
 result=shell(['ssh','-n','boxE',priority])
 shell(['ssh','-n','boxC','cd $SCRATCH/squares-stair-c && ./py -I dedupe23.py > logs/dedupe.log 2>&1 && ./py -I priority23.py > logs/priority.log'])
 if result.returncode:print(stamp(),'PRIORITY ERROR',result.stderr,flush=True)
 json.dump(sorted(seen),open(state+'.tmp','w'));os.replace(state+'.tmp',state)
while time.time()<stop:
 try:cycle()
 except Exception as e:
  import traceback
  print(stamp(),'ERROR',repr(e),flush=True);traceback.print_exc()
 if '--once' in sys.argv:break
 time.sleep(120)
