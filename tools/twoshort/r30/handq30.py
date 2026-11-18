"""Queue a reopened whole layout on boxE by hand (round 27), with an immutable snapshot and intake proof.
Usage: handq30.py LANE_LABEL WHY PATH [PATH ...]   (prints the tags; rsync starts/ and jobs/ after)."""
import sys,json,hashlib,shutil,csv
from pathlib import Path
W=Path(__file__).parent;R=W/'boxE30';sys.path.insert(0,str(W))
import nosamanyu30
sys.path.insert(0,'.');import forensics_sources as FS
label,why=sys.argv[1],sys.argv[2]
for a in [x for x in sys.argv[3:] if not x.startswith('--')]:
 src=Path(a);n=int(next(csv.DictReader(open(src)))['n'])
 rec,_=FS.record(src,n)
 if rec is None:
  for jp in (src.with_suffix('.json'),Path(str(src)+'.json')):
   if jp.exists():rec=json.load(open(jp));break
 if isinstance(rec,dict) and not rec.get('source') and isinstance(rec.get('parts'),dict):
  pl=sorted({str(v.get('licence')) for v in rec['parts'].values() if isinstance(v,dict) and v.get('licence')})
  rec=dict(rec,source='rectangle windows '+json.dumps(rec['parts']),licence='; '.join(pl))
 if not isinstance(rec,dict) or not rec.get('source') or not rec.get('licence'):print('NO RECORD',src);continue
 sha=hashlib.sha256(src.read_bytes()).hexdigest();tag='reopen-%s-%d-%s'%(label,n,sha[-8:])
 snap=W/'starts'/(tag+'.csv');shutil.copy2(src,snap);shutil.copy2(src,R/'starts'/(tag+'.csv'))
 source=why+'; origin '+str(src)+' (sha256 '+sha+'); its record: '+rec['source'];lic=rec['licence']
 ip=W/'intake'/(tag+'.json');ip.write_text(json.dumps(dict(origin=str(src),sha256=sha,source=source,licence=lic),indent=1))
 ap=W/'intake'/(tag+'-ancestry.json')
 ap.write_text(json.dumps(dict(admitted=True,snapshot=str(snap),sha256=hashlib.sha256(snap.read_bytes()).hexdigest(),origin=str(src),origin_sha256=sha,ancestry=dict(admitted=True,record=dict(source=source,licence=lic),note='round 27 hand intake; quench_walk r27 and the admit30 closure run again on every result before it counts')),indent=1))
 job=dict(tag=tag,n=n,start='starts/'+snap.name,seed=1125,remaining=2,seconds=180,miss=0,priority=0,source=source+'; immutable intake '+str(ip),licence=lic,force_quench=('--no-force' not in sys.argv),input_ancestry_proof=str(ap))
 jp=R/'jobs'/('000-01-%s-1125.json'%tag);jp.write_text(json.dumps(job,indent=2));shutil.copy2(jp,W/'jobs'/jp.name);print(tag)
