"""Admit the bounded trial that never ran in round 30, preserving its byte pin."""
import pathlib,sys,json,subprocess,os,signal,time,hashlib
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import campaign31 as C
review=C.load(W/'saved539-review.json',{});old=review['job'];assert review['gate']['clean']and review['branch']['clean']and not review['branch'].get('public_roots')
P=W.parent.parent/'take-invent-r30/work'/old['start'];assert C.sha(P)==old['input_sha256']
assert C.G.check(old,P)['clean']
lines=(C.S/'handoff-r31.log').read_text().splitlines();assert not C.claimed(old['input_sha256'],lines),'peer owns exact bytes'
proofgraph=json.load(open(old['ancestry']));root=proofgraph['nodes'][proofgraph['root']]
proof=dict(ok=True,ancestry=old['ancestry'],evidence=old['evidence'],evidence_sha256=old['evidence_sha256'],source='own round30 endpoint; unrun bounded retention trial; complete frozen graph '+old['ancestry']+'; root '+root['source'],licence=root['licence']+'; upstream notices in complete frozen graph '+old['ancestry'])
j,why=C.produce_input(P,539,'saved',123,C.peers(),proof);assert j is not None,why
j.update(seconds=420,priority=-3.5,probe=120,order=0,saved_round30_job=old['id'])
pid=int((W/'campaign.pid').read_text());line=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True);assert str(W/'campaign31-v2.py')in line
os.kill(pid,signal.SIGTERM)
for _ in range(50):
 try:os.kill(pid,0)
 except ProcessLookupError:break
 time.sleep(.1)
else:raise RuntimeError('old controller did not exit')
try:
 jobs=C.load(W/'jobs.json',[]);assert not any(x['id']==j['id']for x in jobs)
 C.hand('CLAIM saved n=539 sha256='+j['input_sha256']+', bounded420s probe120 seed123; '+str(W/j['start'])+'; unrun round30 recipe '+old['id'])
 C.atomic(W/'jobs.json',jobs+[j]);tried=set(C.load(W/'tried-inputs.json',[]));tried.add(j['input_sha256']);C.atomic(W/'tried-inputs.json',sorted(tried))
 C.cmd(['rsync','-a',str(W/j['start']),C.REMOTE+'starts/'])
 locks={p.name for p in(W/'boxE-raw/locks').glob('*')};pending=[x for x in jobs+[j]if not(W/'boxE-raw'/x['id']/'done.json').exists()and x['id']not in locks and not x.get('retired_profile')]
 pending.sort(key=C.dispatch_key);C.atomic(W/'queue.json',pending);C.cmd(['rsync','-a',str(W/'queue.json'),C.REMOTE])
 C.state('ADMIT saved539 original pin526125a96f19, unrun420s bounded recipe from round30. Current source and public-branch checks clean, no direct public roots. Start side remains0.000944758668748 above bar, so only a measured crossing will count. Existing controls cover this numerical profile and revised finisher. Three boxE slots unchanged.')
finally:
 with(W/'campaign-v2.log').open('a')as f:p=subprocess.Popen(['nice','-n','5',C.sys.executable,'-u',str(W/'campaign31-v2.py')],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,cwd=W)
 (W/'campaign.pid').write_text(str(p.pid));C.state('ADOPT controller'+str(p.pid)+' after single saved539 admission; previous controller'+str(pid)+' stopped first.')
print('ADMITTED',j['id'],'controller',p.pid,flush=True)
