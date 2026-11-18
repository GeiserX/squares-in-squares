from common28 import *
# Repeat only with a measured method change: smaller perturbations after small kicks stalled.
control=(len(sys.argv)>1 and sys.argv[1]=='control')
if control:
 source=W/'finekick-control.csv'
 with source.open('w',newline='') as f:
  w=csv.writer(f);w.writerow(CSV);w.writerow([2,0,0.5,0.5,0]);w.writerow([2,1,1.5004,0.5,0])
 tag='xfinecontrol28c';copy=W/'inputs'/('2-'+tag+'.csv');shutil.copy2(source,copy)
 job=dict(tag=tag,kind='scan',input='data/'+copy.name,source='own loose n2 positive control for smaller kicks',licence='own control',priority=-10,seed=280811,seconds=5,wall=120,kicks='0.004,0.008')
 publish_job(job,copy,'boxE','A');note('START smaller-kick positive control n2, known side2.0004 inside worker side allowance; strengths0.004,0.008 instead of0.02,0.04');raise SystemExit()
proof=read(W/'finekick-control.json',{})
assert proof.get('passed') and proof.get('kicks')=='0.004,0.008','smaller-kick control must pass first'
marker=W/'finekick-scheduled.json';done=read(marker,[])
for n,host,slot in [(264,'boxE','A'),(793,'boxE','B'),(798,'boxD','C')]:
 p=T/f'{n}.csv'
 if not p.exists() or n in done:continue
 sha=hashlib.sha256(p.read_bytes()).hexdigest()
 claims=[l for l in (S/'handoff-r28.log').read_text().splitlines() if re.search(r'backlog ->[^:]*: claims ',l)]
 if any(sha[:12] in l for l in claims):
  note(f'CHANGED_METHOD_SKIP n{n} exact input already claimed by backlog');done.append(n);atomic(marker,done);continue
 parent=next((read(q,{}) for q in (W/'audited').glob('*.json') if read(q,{}).get('accepted') and read(q,{}).get('certified_output_sha256')==sha),None)
 assert parent and parent.get('input_proof'),n
 tag='x'+hashlib.sha256((sha+':fine0.004,0.008-r28').encode()).hexdigest()[:12]
 copy=W/'inputs'/f'{n}-{tag}.csv';shutil.copy2(p,copy)
 record=dict(parent);record.update(tag=tag,parent_tag=parent['tag'],input=str(p),input_sha256=sha,certified_output_sha256=None,quench_receipt='pending '+tag,leg=3,source=f'smaller kicks 0.004,0.008 on own certified n{n}; larger-kick follow moved at most 1.4e-9 of side; parent '+parent['source'],time_utc=now())
 atomic(W/'audited'/f'{tag}.json',record)
 job=dict(tag=tag,kind='scan',input='data/'+copy.name,source=str(p)+'; changed-method smaller kicks0.004,0.008; immutable accepted parent '+str(W/'audited'/(parent['tag']+'.json')),licence='Own smaller-kick scan; notices '+str(W/'audited'/(parent['tag']+'.json')),priority=-7,seed=int(tag[1:7],16),seconds=420,wall=900,kicks='0.004,0.008')
 publish_job(job,copy,host,slot);done.append(n);atomic(marker,done)
 note(f'CHANGED_METHOD n{n} smaller kicks0.004,0.008 replace0.02,0.04 after larger-kick endpoint moved at most 1.4e-9 of side; one420s scan, complete certified-file quench if it wins, common deadline05:45Z')
