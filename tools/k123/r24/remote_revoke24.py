import pathlib,json,os,signal,re,subprocess,time
R=pathlib.Path.home()/'scratch/squares-k123';bad=json.load(open(R/'revoked24.json'));producer=int((R/'worker.pids').read_text().splitlines()[3]);os.kill(producer,signal.SIGSTOP)
try:
 removed=[];kept=[]
 for l in (R/'queue.tsv').read_text().splitlines():
  w=l.split('\t')
  if len(w)<8:continue
  pool=w[7];m=re.match(r'(\d+)r?-(\d+)r?-j',w[1]);ns=set(map(int,m.groups()))
  if ns&set(bad.get(pool,[])):removed.append(l)
  else:kept.append(l)
 (R/'queue-revoked.tsv').write_text('\n'.join(removed)+'\n');(R/'queue-revoke.tmp').write_text('\n'.join(kept)+'\n');(R/'queue-revoke.tmp').replace(R/'queue.tsv')
 for p in (R/'tasks').glob('*.json'):
  j=json.load(open(p))
  if j.get('tag') in bad and j.get('kind')=='scan':
   j['rc']=-3;j['ended']=time.strftime('%FT%TZ',time.gmtime());j['refused']=True;(R/'taskdone'/('refused-'+p.name)).write_text(json.dumps(j));p.unlink()
 killed=[]
 for l in subprocess.check_output(['ps','-axo','pid,pgid,command'],text=True).splitlines()[1:]:
  a=l.strip().split(None,2)
  if len(a)!=3:continue
  pid,pgid,cmd=int(a[0]),int(a[1]),a[2]
  if '-I lane/k123_turn.py' not in cmd and '-I fq2.py' not in cmd and '-I lane/k123_join.py scan' not in cmd:continue
  if not any(pool+'.csv' in cmd or '/'+pool+'-' in cmd for pool in bad):continue
  if pid==pgid:
   try:os.killpg(pgid,signal.SIGKILL);killed.append(pid)
   except ProcessLookupError:pass
 result=dict(time=time.strftime('%FT%TZ',time.gmtime()),removed=len(removed),killed=killed,affected_pools=bad);(R/'revoke-result24.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
finally:os.kill(producer,signal.SIGCONT)
