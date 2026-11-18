from common29 import *
# Repeat only with a measured method change: larger perturbations after small kicks stalled.
control=(len(sys.argv)>1 and sys.argv[1]=='control')
if control:
 source=W/'widekick-control.csv'
 with source.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(CSV);w.writerow([2,0,0.5,0.5,0]);w.writerow([2,1,1.5004,0.5,0])
 tag='xwidecontrol28c';copy=W/'inputs'/('2-'+tag+'.csv');shutil.copy2(source,copy)
 job=dict(tag=tag,kind='scan',input='data/'+copy.name,source='own loose n2 positive control for larger kicks',licence='own control',priority=-10,seed=280811,seconds=5,wall=120,kicks='0.08,0.12')
 publish_job(job,copy,'boxE','A');note('START larger-kick positive control n2, known side2.0004 inside worker side allowance; strengths0.08,0.12 instead of0.02,0.04');raise SystemExit()
proof=read(W/'widekick-control.json',{})
assert proof.get('passed') and proof.get('kicks')=='0.08,0.12','larger-kick control must pass first'
marker=W/'widekick-scheduled.json';done=read(marker,[])
for n,host,slot in [(264,'boxE','A'),(793,'boxE','B'),(798,'boxD','C')]:
 p=T/f'{n}.csv'
 if not p.exists() or n in done:continue
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 claims=[l for l in (S/'handoff-r30.log').read_text().splitlines() if re.search(r'backlog ->[^:]*: claims ',l)]
 if any(sha[:12] in l for l in claims):
  note(f'CHANGED_METHOD_SKIP n{n} exact input already claimed by backlog');done.append(n);atomic(marker,done);continue
 parent=next((read(q,{}) for q in (W/'audited').glob('*.json') if read(q,{}).get('accepted') and read(q,{}).get('certified_output_sha256')==sha),None)
 assert parent and parent.get('input_proof'),n
 tag='x'+hashlib.sha256((sha+':wide0.08,0.12-r28').encode()).hexdigest()[:12]
 copy=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(p,copy)
 record=dict(parent);record.update(tag=tag,parent_tag=parent['tag'],input=str(p),input_sha256=sha,certified_output_sha256=None,quench_receipt='pending '+tag,leg=3,source=f'larger kicks 0.08,0.12 on own certified n{n}; small-kick follow stalled; parent '+parent['source'],time_utc=now())
 atomic(W/'audited'/f'{tag}.json',record)
 job=dict(tag=tag,kind='scan',input='data/'+copy.name,source=str(p)+'; changed-method larger kicks0.08,0.12; immutable accepted parent '+str(W/'audited'/(parent['tag']+'.json')),licence='Own larger-kick scan; notices '+str(W/'audited'/(parent['tag']+'.json')),priority=-7,seed=int(tag[1:7],16),seconds=420,wall=900,kicks='0.08,0.12')
 publish_job(job,copy,host,slot);done.append(n);atomic(marker,done)
 note(f'CHANGED_METHOD n{n} stronger kicks0.08,0.12 replace0.02,0.04 after small-kick endpoint stalled; one420s scan, complete certified-file quench if it wins, common deadline17:45Z')
