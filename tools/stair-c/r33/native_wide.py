"""Use exact native far zones when a deeper corner leaves a ranked donor no slide."""
import hashlib,json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
W=Path(C.WORK);END=float((W/'box/search-deadline').read_text())-1200

def send(paths,dest):
 subprocess.run(['rsync','-a',*[str(p)for p in paths],'boxC:scratch/squares-stair-c/'+dest],capture_output=True,timeout=40,check=True)
def main():
 out=W/'native-wide';out.mkdir(exist_ok=True)
 send([H/'control_paths.py',H/'native_direct.py'],'')
 p=out/'975-native-control.csv';p.write_bytes((W/'box/control975.csv').read_bytes());sha=hashlib.sha256(p.read_bytes()).hexdigest()
 side=Path(str(p)+'.json');side.write_text(json.dumps(dict(n=975,control_only=True,queued_sha256=sha,source='own construction: exact975 native direct control',licence='our own')))
 send([p,side],'donors/')
 for order,name,cmd,limit in [(0,'native-paths-control',['venv/bin/python','-I','control_paths.py'],180),(1,'native975-control',['venv/bin/python','-I','native_direct.py','donors/'+p.name,'0','0'],600)]:
  request=out/f'000-native-{order}-control.json';request.write_text(json.dumps(dict(name=name,command=cmd,limit=limit)));send([request],'requests/')
 receipt=out/'native-direct-control.json'
 while time.time()<END:
  r=subprocess.run(['rsync','-a','boxC:scratch/squares-stair-c/native-direct-control.json',str(receipt)],capture_output=True,timeout=35)
  if r.returncode==0:break
  time.sleep(30)
 else:return
 control=json.loads(receipt.read_text());assert control['passed']and control['n']==975
 p=out/'805-native-held.csv';p.write_bytes((W/'held31/805.csv').read_bytes());sha=hashlib.sha256(p.read_bytes()).hexdigest()
 meta=json.loads((W/'held31/805.csv.json').read_text());meta['source']=str(W/'held31/805.csv')+' immutable sha256 '+sha+'; '+meta['source'];meta['queued_sha256']=sha
 assert C.full_admission(str(W/'held31/805.csv'),805,meta)is not None
 side=Path(str(p)+'.json');side.write_text(json.dumps(meta));send([p,side],'donors/')
 jobs=[]
 for order,(a,b)in enumerate([(4,4),(5,5),(4,0),(0,4)]):
  request=out/f'010-native805-{order}-{a}{b}-{sha[:12]}.json'
  request.write_text(json.dumps(dict(name=f'native805-{a}{b}-{sha[:12]}',command=['venv/bin/python','-I','native_direct.py','donors/'+p.name,str(a),str(b)],limit=600)))
  send([request],'requests/');jobs.append(str(request))
 (W/'native-wide-queued.json').write_text(json.dumps(dict(control=control,source_sha256=sha,owner='boxC',requests=jobs),indent=2))
 C.state(f'START4 native805 builds after actual full975 reconstruction control. Source{sha}; transfers44,55,40,04 use exact matching far zones and fixed-start preservation. This changes the measured no-slide failure of ranked far donors. One805 recipe owner boxC; cap600s per build and common numeric deadline00:15UTC.')
 print('NATIVE WIDE QUEUED',sha,jobs,flush=True)
if __name__=='__main__':main()
