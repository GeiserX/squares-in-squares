from common28 import *
result={}
for host in ['boxE','boxD']:
 root=W/f'remote-final-{host}'
 manifest=read(root/'archive-manifest.json');assert isinstance(manifest,dict) and manifest
 total=0
 for rel,expected in manifest.items():
  p=root/rel;assert p.is_file(),p
  data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==expected,p
  total+=len(data)
 stop=read(root/'stop-result.json');assert stop['left']==[],stop
 result[host]=dict(files=len(manifest),bytes=total,remaining_processes=stop['left'],time_utc=stop['time_utc'],scipy=stop['scipy'])
 assert stop['scipy']=='1.18.1'
 for name in ['out','logs']:
  cmd(['rsync','-a',str(root/name)+'/',str(W/host/name)+'/'])
atomic(W/'archive-verification.json',dict(time=now(),hosts=result))
note('FINISH remote archive verification '+json.dumps(result)+'. Every manifest hash matches the local copy. Safe to remove only each owned squares-classfill-r27 remote root.')
print(json.dumps(result,indent=1))
