"""Extend the original complete frozen source walk to its verified own endpoint."""
import hashlib,json,pathlib,shutil,sys,time
W=pathlib.Path(__file__).resolve().parent;S=W.parents[1]
sys.path.insert(0,str(W));import controller28 as C
G=C.G
old=S/'take-invent-r29/work';prior=next(j for j in json.load(open(old/'jobs.json'))if j['id']=='u080116x641x84')
ep=pathlib.Path(prior['evidence']);assert G.sha(ep)==prior['evidence_sha256'];ev=json.load(open(ep))
assert ev['clean']and not ev['hits']
for pin in ev['snapshots']:assert G.sha(pin['path'])==pin['sha256']
a=json.load(open(prior['ancestry']));assert a['ok']and G.sha(prior['ancestry'])==ev['ancestry_sha256']and G.held_boundary(a)
assert not G.banned(json.dumps(a))
assert all(C.A.rejected(v['source'],v['licence'],terminal=not v.get('parents'))is None for v in a['nodes'].values())
# The duplicate transport's missing notice is resolved by its captured origin.
origin=next(p for p in ev['snapshots']if p['original'].endswith('498-7126a036b6e2f51a2cbb46b6.csv.origin.json'))
meta=json.load(open(origin['path']));notice=meta['ancestry']['notices'][0]
assert notice['source']=='jazivxt/boxed-in-sub :: submission.csv'and 'Apache 2.0'in notice['licence']
assert meta['snapshot_sha256']=='7126a036b6e2f51a2cbb46b65553f77f954f05927a0fd3282c1a5c168b5f10b1'
assert meta['ancestry']['full_ancestry']['sha256']==G.sha(meta['ancestry']['full_ancestry']['path'])
parent=next(p for p in ev['snapshots']if p['original']==str(S/'take-forensics-r29/near/591-rect.csv'))
assert parent['sha256']=='c2821611f493c961875160285468eea2839b8878dee9fbdaf721ea9b608e409f'
p=old/'boxE-raw'/prior['id']/'final/641.csv';receipt_path=p.parents[1]/'done.json';receipt=json.load(open(receipt_path))
assert receipt['sha256']==G.sha(p)and receipt['quench_from_certified']and receipt['clearance']>=2.2e-11
assert G.sha(p.parents[1]/'certin/641.csv')==receipt['quench_input_sha256']==(p.parents[1]/'quench/641.done').read_text().strip()
proof=W/'recovery641-proof.json'
proof.write_text(json.dumps(dict(old_evidence=str(ep),old_evidence_sha256=G.sha(ep),old_graph=prior['ancestry'],old_graph_sha256=G.sha(prior['ancestry']),held_boundary=G.held_boundary(a),withdrawn_parent=parent,transport_origin=origin,transport_notice=notice,old_worker_receipt=str(receipt_path),old_worker_receipt_sha256=G.sha(receipt_path),policy='main12:40:55Z owns held descendants; numeric held-ancestor exclusion void'),indent=2))
# Reopen only the exact ancestor bytes implicated by the superseded numeric gate.
marker='REINSTATE exact held-ancestor parent591 '+parent['sha256']
log=S/'handoff-r30.log'
if marker not in log.read_text():
 with log.open('a')as f:f.write(C.now()+' invent -> all: '+marker+', '+parent['original']+'; main12:40:55Z voids its held-ancestor share reason. Captured duplicate498 origin resolves jazivxt/boxed-in-sub, Apache2.0. Full byte-bound proof '+str(proof)+'. Literal-source checks remain.\n')
check=G.check(prior,p);assert check['clean'],check
bad=G.check(dict(prior,input_sha256='0'*64),p);assert not bad['clean']
# A source walk already sealed at production time avoids unrelated later plan expansion.
graph=W/'ancestry/recovered641.json';assert graph.exists()
graph_value=json.load(open(graph));assert graph_value['path']==str(p)and graph_value['nodes'][graph_value['root']]['parents']==[a['root']]
new=dict(ev);new['snapshots']=list(ev['snapshots']);pins=W/'pins';pins.mkdir(exist_ok=True)
for original in [p,graph,receipt_path,proof]:
 digest=G.sha(original);dest=pins/(digest+original.suffix)
 if not dest.exists():shutil.copyfile(original,dest)
 assert G.sha(dest)==digest
 new['snapshots'].append(dict(original=str(original),path=str(dest),sha256=digest,original_mtime_ns=original.stat().st_mtime_ns))
new.update(policy='round30 sealed-walk extension',time=C.now(),input_sha256=G.sha(p),ancestry=str(graph),ancestry_sha256=G.sha(graph),public_first=False,share=0.,clean=True,hits=[],sealed_parent_evidence=str(ep),sealed_parent_sha256=G.sha(ep),extension_proof=str(proof),extension_sha256=G.sha(proof))
new['texts']=list(ev['texts'])+[(str(p),graph_value['nodes'][graph_value['root']]['source'])]
evidence=W/'evidence/recovered641.json';evidence.write_text(json.dumps(new,separators=(',',':')))
ident='recover641';start='starts/'+ident+'.csv';shutil.copyfile(p,W/start);bar,peer=C.bars()
job=dict(id=ident,n=641,start=start,seconds=0,seed=0,kind='recovered',program='lane/invent_rest.py',previous_program=receipt['program'],fq=False,bar=(peer[641]+1)*641**.5,side=(receipt['new']+1)*641**.5,order=-1.,priority=-5.5,ancestry=str(graph),input_sha256=G.sha(p),evidence=str(evidence),evidence_sha256=G.sha(evidence),options=[])
assert G.check(job,W/start)['clean']
extra=C.load(W/'extra-ready.json',[])
if not any(j['id']==ident for j in extra):extra.append(job);C.atomic(W/'extra-ready.json',extra)
C.state('QUEUE recover641, zero search then fq from certified input. Original192-pin source walk and endpoint receipt verified; altered input hash refused. Exact held-ancestor591 reinstated under main ruling with captured Apache notice. Raw score '+str(receipt['new'])+' versus bar '+str(bar[641])+'; no gain counted before new quench.')
print(json.dumps(dict(queued=ident,old_pins=len(ev['snapshots']),new_score=receipt['new'],bar=bar[641],peer=peer[641],source_clean=True,changed_input_refused=True)),flush=True)
