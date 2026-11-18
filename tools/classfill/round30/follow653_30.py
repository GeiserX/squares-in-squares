from common29 import *
from light29 import load,key
n=653;raw=T/f'{n}.csv'
if not raw.exists():raise SystemExit('row already retired')
sha=hashlib.sha256(raw.read_bytes()).hexdigest();tag='x'+sha[:12]
if (W/'jobs'/f'{tag}.json').exists():raise SystemExit('already queued')
parent=next((read(p,{}) for p in (W/'audited').glob('*.json') if read(p,{}).get('accepted') and read(p,{}).get('certified_output_sha256')==sha),None);assert parent
copy=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(raw,copy);assert hashlib.sha256(copy.read_bytes()).hexdigest()==sha
rec=dict(parent);rec.update(tag=tag,leg=2,parent_tag=parent['tag'],input=str(raw),input_sha256=sha,certified_output_sha256=None,queue_snapshot=blob(copy),source='classfill round30 follow of certified own653 '+parent['tag']+'; before it: '+parent['source'],time_utc=now())
atomic(W/'audited'/f'{tag}.json',rec)
loads=[]
for host,slots in [('boxE',['A','B']),('boxD',['C'])]:
 for slot in slots:
  lines=cmd(['ssh',host,'find '+REMOTE+'/queue/'+slot+' -type f \\( -name "*.json" -o -name "*.active" \\)']).splitlines();loads.append((len(lines),host,slot))
count,host,slot=min(loads)
job=dict(tag=tag,kind='scan',input='data/'+copy.name,source=str(raw)+'; leg2 changed certified geometry from '+parent['tag']+'; immutable proof '+parent['input_proof'],licence=rec['licence'],priority=-10,seed=int(sha[:6],16),seconds=900,wall=1200,kicks='0.02,0.04',bar_input=True)
publish_job(job,copy,host,slot);scanned=set(read(W/'scanned.json',[]));scanned.add(sha);atomic(W/'scanned.json',sorted(scanned));geometries=read(W/'geometry-scanned.json',{});geometries[key(load(copy,{n})[n])]=str(copy);atomic(W/'geometry-scanned.json',geometries)
note('FOLLOW653 accepted gain1.107545635203877e-7; last side move2.829224641232031e-6. One high-priority900s follow from exact certified current row, source only owned Samanyu root. No extra compute slot.')
