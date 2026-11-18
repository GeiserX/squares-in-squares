"""Dispatch repaired native builds only after the certified805 control exists."""
import datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;W=Path('$SCRATCH/bounties-squares/take-stair-c-r33/work')
END=float((W/'box/search-deadline').read_text())-900

def main():
 receipt=W/'slide-envelope-control.json'
 while time.time()<END:
  r=subprocess.run(['rsync','-a','boxC:scratch/squares-stair-c/slide-envelope-control.json',str(receipt)],capture_output=True,timeout=35)
  if r.returncode==0:
   j=json.loads(receipt.read_text())
   if j.get('passed')and j.get('certified805_witnesses',0)==4:break
  time.sleep(20)
 else:return
 assert j['helper_sha256']==hashlib.sha256((H/'slide_envelope.py').read_bytes()).hexdigest()
 jobs=[]
 for order,(a,b)in enumerate([(4,4),(5,5),(4,0),(0,4)]):
  p=W/'native-wide'/f'020-envelope805-{order}-{a}{b}.json'
  p.write_text(json.dumps(dict(name=f'envelope805-{a}{b}',command=['venv/bin/python','-I','envelope_job.py','donors/805-native-held.csv',str(a),str(b)],limit=600)))
  subprocess.run(['rsync','-a',str(p),'boxC:scratch/squares-stair-c/requests/'],capture_output=True,timeout=40,check=True);jobs.append(str(p))
 (W/'envelope-queued.json').write_text(json.dumps(dict(control=j,requests=jobs,owner='boxC'),indent=2))
 with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA START4 envelope-repaired native805 constructions on boxC after four actual805 finesafe2.2e-11 controls and rejected duplicate-square copies. Changed the measured2.0601e-6 overlap by propagating core-edge slides, rather than deleting the guard. Logs envelope805-*.log; cap600s each, numeric deadline00:15UTC. Final outputs still require finesafe, full fq loop and live-bar checks.\n')
 print('ENVELOPE CONSTRUCTIONS QUEUED',jobs,flush=True)
if __name__=='__main__':main()
