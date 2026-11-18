import datetime,hashlib,json,os,pathlib,shlex,subprocess,tarfile
W=pathlib.Path(__file__).parent;T=W.parent

def run(a,**kw):return subprocess.run(a,capture_output=True,text=True,timeout=55,check=True,**kw)
probe="""import os,json,shlex
q=open('q.txt').readlines();pending=[s for s in q if s.strip() and not os.path.exists('blog/'+s.split()[0]+'.lock')]
print(json.dumps({'pending':len(pending)}))
"""
q=json.loads(run(['ssh','-n','boxC','cd $SCRATCH/squares-stair-c && ./py -I -c '+shlex.quote(probe)]).stdout)
if q['pending']>2:print('BALANCE boxC pending',q['pending']);raise SystemExit()
alloc="""import os,json,shlex
q=open('q.txt').readlines();pick=[];pool=None
for s in q:
 a=shlex.split(s)
 if 'job' not in a or not any(x.endswith('/modules.py') for x in a):continue
 if os.path.exists('blog/'+a[0]+'.lock'):continue
 k=a.index('job');p=a[k+1]
 if not os.path.exists(p+'/library.pkl'):continue
 if pool is not None and pool!=p:continue
 try:
  fd=os.open('blog/'+a[0]+'.lock',os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.write(fd,b'assigned to boxC by atomic transfer\\n');os.close(fd)
 except FileExistsError:continue
 pool=p;pick.append(s)
 if len(pick)==4:break
print(json.dumps({'pool':pool,'jobs':pick}))
"""
pending=sorted(x for x in (W/'transfers').glob('*/request.json') if not (x.parent/'enqueued.json').exists()) if (W/'transfers').exists() else []
d=json.load(open(pending[0])) if pending else json.loads(run(['ssh','-n','boxE','cd $SCRATCH/squares-stair-c && ./py -I -c '+shlex.quote(alloc)]).stdout)
if not d['jobs']:print('BALANCE no pending build');raise SystemExit()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ');tag=hashlib.sha256(''.join(d['jobs']).encode()).hexdigest()[:10];out=W/'transfers'/tag;out.mkdir(parents=True,exist_ok=True);json.dump(d,open(out/'request.json','w'),indent=2)
with open(T/'STATE.txt','a') as h:h.write(stamp+' START transfer '+tag+' boxE->boxC, '+str(len(d['jobs']))+' atomically claimed recipes, saved work/transfers/'+tag+'/request.json; deadline18:30Z.\n')
pool=d['pool'];local=W/'transfers'/pool
try:
 run(['rsync','-az','boxE:scratch/squares-stair-c/'+pool+'/',str(local)+'/'])
except subprocess.CalledProcessError:
 archive=W/'transfers'/(pool+'.tar.gz')
 run(['rsync','-az','boxE:scratch/squares-stair-c/pool-archive/'+pool+'.tar.gz',str(archive)])
 run(['rsync','-az','boxE:scratch/squares-stair-c/pool-archive/'+pool+'.tar.gz.sha256.json',str(archive)+'.sha256.json'])
 manifest=json.load(open(str(archive)+'.sha256.json'))
 with tarfile.open(archive) as tf:
  for member in tf.getmembers():
   if not member.name.startswith(pool+'/') or '..' in pathlib.Path(member.name).parts:raise ValueError('unsafe library member')
   if member.isfile():assert hashlib.sha256(tf.extractfile(member).read()).hexdigest()==manifest[member.name]
  tf.extractall(W/'transfers',filter='data')
 print('BALANCE archive fallback verified',pool,flush=True)
run(['rsync','-az',str(local)+'/','boxC:scratch/squares-stair-c/'+pool+'/'])
expected={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in local.iterdir() if p.is_file()}
verify='import pathlib,hashlib,json; p=pathlib.Path('+repr(pool)+'); print(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in p.iterdir() if x.is_file()}))'
received=json.loads(run(['ssh','-n','boxC','cd $SCRATCH/squares-stair-c && ./py -I -c '+shlex.quote(verify)]).stdout)
assert expected==received,(expected,received)
proof=dict(d,sha256=expected,verified=True,stamp=stamp);json.dump(proof,open(out/'receipt.json','w'),indent=2)
(out/'jobs.txt').write_text(''.join(d['jobs']))
run(['rsync','-az',str(out/'jobs.txt'),'boxC:scratch/squares-stair-c/transfer-'+tag+'.txt'])
run(['ssh','-n','boxC','cd $SCRATCH/squares-stair-c && cat transfer-'+tag+'.txt >> q.txt && ./py -I priority23.py > logs/priority.log'])
json.dump(dict(enqueued=True,stamp=stamp),open(out/'enqueued.json','w'))
with open(T/'STATE.txt','a') as h:h.write(stamp+' ADOPT boxC '+str(len(d['jobs']))+' boxE build recipes from '+pool+'; atomic boxE locks precede transfer; SHA256 verified '+str(len(expected))+' library files before enqueue. Receipt work/transfers/'+tag+'/receipt.json; existingoneworker, deadline18:30Z.\n')
print('BALANCE',len(d['jobs']),pool,'verified',len(expected),'files',tag,flush=True)
