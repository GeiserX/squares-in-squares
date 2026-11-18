import pathlib,sys,json,csv,hashlib,tempfile
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));S=W.parents[1]
import ancestry28 as A,source_gate28 as G,public_branch30 as B
from held32 import resolve,projection
p=W/'controls-held/971.csv';p.parent.mkdir(exist_ok=True)
base=S/'gather/round34-2026-11-17a.csv';root=resolve(dict(path=str(base),n=971));assert root
rows=[r for r in csv.DictReader(open(base))if int(r['n'])==971]
with p.open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows([{k:r[k]for k in w.fieldnames}for r in rows])
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
pathlib.Path(str(p)+'.json').write_text(json.dumps(dict(n=971,held_file=str(base),held_sha256=sha(base),row_sha256=sha(p))))
assert projection(p,971)
saveG=G.prv_share;saveB=B.P.share
G.prv_share=lambda *a:(_ for _ in()).throw(AssertionError('owned layout received share gate'))
B.P.share=lambda *a:(_ for _ in()).throw(AssertionError('held ancestry received share gate'))
a=A.audit(p,971);assert a['ok'],a
e=G.freeze(p,971,a['proof']);assert e['clean'],e
j=dict(id='source-control35',n=971,evidence=e['path'],evidence_sha256=e['sha256'],ancestry=a['proof'])
assert G.check(j,p)['clean'];assert not G.check(dict(j,evidence_sha256='0'*64),p)['clean']
assert G.Q.LIVE=='35';assert 'handoff-r35.log'in [v.name for v in G.handoff_logs()]
logs=G.handoff_logs
with tempfile.TemporaryDirectory(dir=W)as tmp:
 log=pathlib.Path(tmp)/'handoff-r35.log';log.write_text('');G.handoff_logs=lambda:[log]
 assert G.check(j,p)['clean']
 rel=str(p).removeprefix(str(S)+'/')
 log.write_text(f'2026-11-16T18:00:00Z test -> all: WITHDRAW n971 source missing proof {rel} sha256={sha(p)}\n')
 assert not G.check(j,p)['clean']
 log.write_text(f'2026-11-16T18:00:00Z test -> all: WITHDRAW n971 source missing proof {rel} sha256={"0"*64}\n')
 assert G.check(j,p)['clean']
G.handoff_logs=logs;G.prv_share=saveG;B.P.share=saveB
old=rows[0]['x'];rows[0]['x']=str(float(old)+.001)
with p.open('w',newline='')as f:
 w=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);w.writeheader();w.writerows([{k:r[k]for k in w.fieldnames}for r in rows])
assert projection(p,971)is None
result=dict(submitted_round35_owned_without_share=True,wrong_evidence_refused=True,current_round_withdrawal_selected=True,exact_bytes_withdrawal_refused=True,wrong_hash_notice_ignored=True,changed_projection_refused=True)
(W/'controls35.json').write_text(json.dumps(result));print(json.dumps(result))
