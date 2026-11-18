from common28 import *
from prvsim28 import check
from ancestor_share28 import inspect
for n,oldtag,host,slot,reason in [(793,'x20b8671141d0','boxE','A','last round leg3 shortened side0.0007198; this endpoint has not had its next scan'),(693,'x223aa1460592','boxE','B','last round leg2 shortened side2.404e-6; new random seed and600s budget follow changed endpoint')]:
 p=S/'take-classfill-r27'/f'{n}.csv';parent=read(S/'take-classfill-r27/work/audited'/f'{oldtag}.json');sha=hashlib.sha256(p.read_bytes()).hexdigest()
 assert parent['accepted'] and parent['certified_output_sha256']==sha
 assert not check(str(p),n)['excluded'];anc=inspect(parent['input_proof']);assert not anc['excluded'] and not anc['errors']
 for q in read(parent['input_proof'])['snapshots']:assert hashlib.sha256(Path(q['snapshot']).read_bytes()).hexdigest()==q['sha256']
 tag='x'+sha[:12];dst=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(p,dst)
 rec=dict(parent);rec.update(tag=tag,n=n,input=str(p),input_sha256=sha,certified_output_sha256=None,leg=1,parent_tag=oldtag,source=f'classfill r28 continuation of certified r27 {n}; parent audit {S}/take-classfill-r27/work/audited/{oldtag}.json; before it: '+parent['source'],time_utc=now(),queue_reason=reason,queue_snapshot=blob(p),parent_audit_snapshot=blob(S/'take-classfill-r27/work/audited'/f'{oldtag}.json'))
 atomic(W/'audited'/f'{tag}.json',rec)
 job=dict(tag=tag,kind='scan',input='data/'+dst.name,source=str(p)+'; leg 1 continuation from '+oldtag+'; ancestry '+parent['input_proof'],licence=parent['licence'],priority=-6,seed=int(sha[:6],16)+28000,seconds=600,wall=1200,kicks='0.02,0.04')
 publish_job(job,dst,host,slot);scanned=set(read(W/'scanned.json',[]));scanned.add(sha);atomic(W/'scanned.json',sorted(scanned));note(f'START priority own endpoint n{n}: '+reason)
