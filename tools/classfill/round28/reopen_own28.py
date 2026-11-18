from common28 import *
from ancestor_share28 import inspect
n=982;oldtag='x7128d96bb122';oldW=S/'take-classfill-r27/work';r=read(oldW/'accepted-candidates'/f'{n}-{oldtag}.json');parent=read(oldW/'audited'/f'{oldtag}.json');p=Path(r['output']);closure=Path(r['proof']);proof=read(closure)
assert parent.get('accepted') is False and 'share' in parent.get('reason',''),parent.get('reason')
assert not BAD.search(source_text(proof['source']+' '+proof['licence']))
anc=inspect(closure);assert not anc['errors']
manual=read(oldW/'manual-audit'/f'{oldtag}.json');assert not proof['expanded']['history']['excluded'];assert proof['expanded']['history']['issues']==[manual['resolved_issue']]
for q in manual['pins']:assert hashlib.sha256(Path(q['snapshot']).read_bytes()).hexdigest()==q['sha256']
assert manual['original_closure']==str(closure)
sha=hashlib.sha256(p.read_bytes()).hexdigest();tag='x'+sha[:12];dst=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(p,dst)
rec=dict(parent);rec.update(accepted=True,tag=tag,n=n,input=str(p),input_sha256=sha,certified_output_sha256=None,input_proof=str(closure),leg=1,parent_tag=oldtag,source='classfill r28 reopening own982 endpoint after RULE001903; prior complete source audit '+str(oldW/'audited'/f'{oldtag}.json')+'; ancestry '+str(closure)+'; before it: '+proof['source'],licence=proof['licence'],time_utc=now(),reopened_reason=parent['reason'],reason='own ancestor share gate lifted by RULE001903',queue_snapshot=blob(p),parent_audit_snapshot=blob(oldW/'audited'/f'{oldtag}.json'))
atomic(W/'audited'/f'{tag}.json',rec)
job=dict(tag=tag,kind='scan',input='data/'+dst.name,source=str(p)+'; leg 1 reopened own endpoint; ancestry '+str(closure),licence=proof['licence'],priority=-5,seed=int(sha[:6],16)+28000,seconds=180,wall=900,kicks='0.02,0.04')
publish_job(job,dst,'boxE','A');scanned=set(read(W/'scanned.json',[]));scanned.add(sha);atomic(W/'scanned.json',sorted(scanned));note('REOPEN own982 endpoint, below bar28 by7.8888e-7, source refusal was only ancestor share; fresh remote scan/certification/quench queued.')
