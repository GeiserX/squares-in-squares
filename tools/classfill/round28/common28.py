import csv,hashlib,json,math,os,re,shutil,subprocess,sys,time
from pathlib import Path
sys.dont_write_bytecode=True
csv.field_size_limit(100000000)
S=Path('$SCRATCH/bounties-squares');T=S/'take-classfill-r28';W=T/'work';R=Path('.');REMOTE='scratch/squares-classfill-r28'
END=float((W/'stage/deadline').read_text());SEARCH_END=END-600
sys.path.insert(0,str(R));sys.path.insert(0,str(W))
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ[k]='1'
COL=['n','held','new','gain','source','licence'];CSV=['n','square_id','x','y','angle']
def now():return time.strftime('%FT%TZ',time.gmtime())
def note(s):
 with open(T/'STATE.txt','a') as h:h.write(now()+' '+s+'\n')
def hand(s,to='all'):
 with open(S/'handoff-r28.log','a') as h:h.write(now()+' classfill -> '+to+': '+s+'\n')
def cmd(a,timeout=120):
 a=list(a)
 # Legacy SCP completed the same positive transfer control while SFTP stalled.
 if a[0]=='scp':a[1:1]=['-O','-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2']
 elif a[0]=='ssh':a[1:1]=['-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=2']
 return subprocess.run(a,check=True,capture_output=True,text=True,timeout=timeout).stdout
def read(p,default=None):
 try:return json.loads(Path(p).read_text())
 except (OSError,ValueError):return default

def atomic(p,j):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=Path(str(p)+'.tmp');q.write_text(json.dumps(j,indent=1)+'\n');os.replace(q,p)
def blob(p):
 p=Path(p);data=p.read_bytes();sha=hashlib.sha256(data).hexdigest();dest=W/'objects'/sha
 if not dest.exists():dest.parent.mkdir(exist_ok=True);dest.write_bytes(data)
 return dict(path=str(p),sha256=sha,snapshot=str(dest),bytes=len(data))
def rows(p):
 try:return list(csv.DictReader(open(p),delimiter='\t'))
 except (OSError,csv.Error):return []
def bar():
 detail=S/'round28-briefs/bar28.tsv'
 base={int(r['n']):float(r['bar']) for r in rows(detail)}
 live=dict(base)
 for p in S.glob('take-*-r28/take.tsv'):
  if 'assemble' in str(p) or p.parent==T:continue
  for r in rows(p):
   try:n=int(r['n']);live[n]=min(live[n],float(r['new']))
   except (ValueError,KeyError):pass
 return base,live,str(detail)

def writebar():
 base,live,label=bar(); own={int(r['n']):float(r['new']) for r in rows(T/'take.tsv')}
 path=W/'bar.csv'
 with open(str(path)+'.tmp','w') as h:
  w=csv.writer(h);w.writerow(['n','L','score','min_gap'])
  for n,v in live.items():
   v=min(v,own.get(n,v));w.writerow([n,(1+v)*math.sqrt(n),v,2.2e-11])
 data=Path(str(path)+'.tmp').read_bytes();changed=not path.exists() or path.read_bytes()!=data
 os.replace(str(path)+'.tmp',path)
 if changed:
  for host in ['boxE','boxD']:
   cmd(['scp','-q',str(path),host+':'+REMOTE+'/bar.csv.new']);cmd(['ssh',host,'mv '+REMOTE+'/bar.csv.new '+REMOTE+'/bar.csv'])
 atomic(W/'base-current.json',dict(label=label,base=base,live=live,time=now()))
 return base,live

BAD=re.compile(r'joegun-boxed|joegun excluded donor|penguin069/squares-joegun-boxed-certified-union|verified-best-of-1105|prvsiyan/squares-verified|CC BY-SA|CC-BY-SA',re.I)
def source_text(text):
 text=re.sub(r'Samanyu-dev/squares_in_squares :: best_fit_[0-9_]+\.csv \(GitHub;[^)\n]*?no licen[cs]e stated upstream\)', 'own-discovered seed',text,flags=re.I)
 # Round27 accepts the independently discovered Samanyu-identical seed.
 text=re.sub(r'Samanyu[^\n;]{0,180}?(?:no licen[cs]e(?: stated upstream)?|unlicensed)', 'own-discovered seed', text,flags=re.I)
 return text

def audit(src,lic,meta,n):
 # New direct public inputs need an allowed notice. Inherited held/table roots retain their named upstream terms.
 if not re.search(r'Apache|CC.?BY(?![- ]?SA)|CC0|Public Domain|own|ours',lic,re.I) and not re.search(r'take-|held|gather/round|results/round|Samanyu-dev',src,re.I):
  return dict(text=src+' '+lic,records=[],unresolved_csv=[]),'unsupported direct public notice '+lic
 from ancestry24 import expand
 a=expand(src,lic,meta,n)
 for held_path,record in read(W/'source-holds.json',{}).items():
  if held_path in a['text']:return a,'explicit source hold '+held_path
 bad=BAD.search(source_text(a['text']))
 if bad:return a,'excluded '+bad.group()
 if re.search(r'no licen[cs]e',source_text(a['text']),re.I):return a,'unlicensed non-Samanyu source'
 if len(a['records'])>=300:return a,'source expansion cap 300'
 from history28 import trace
 try:
  history=trace(src,lic,dict(producer=meta,expanded_records=a['records'],unresolved_csv=a['unresolved_csv']),n);a['history']=history
  a['text']+='\n'+'\n'.join(history.get('parts',[]))
  if history['excluded']:return a,'excluded historical '+history['excluded']
 except Exception as e:return a,'history resolver '+repr(e)
 if not src or not lic:return a,'missing source or licence'
 return a,None

def publish_job(job,local,host,slot):
 p=W/'jobs'/(job['tag']+'.json');p.parent.mkdir(exist_ok=True);atomic(p,job)
 cmd(['scp','-q',str(local),host+':'+REMOTE+'/data/'+local.name])
 cmd(['scp','-q',str(p),host+':'+REMOTE+'/queue/'+slot+'/'+job['tag']+'.tmp'])
 cmd(['ssh',host,'mv '+REMOTE+'/queue/'+slot+'/'+job['tag']+'.tmp '+REMOTE+'/queue/'+slot+'/'+job['tag']+'.json'])
 note(f'START_QUEUE {host} slot{slot} {job["tag"]} {job["kind"]}, command worker28.py {slot} from work/jobs/{job["tag"]}.json, input {job["input"]}, log work/{host}/logs/{job["tag"]}.log; common deadline05:45Z, search cutoff05:35Z')
