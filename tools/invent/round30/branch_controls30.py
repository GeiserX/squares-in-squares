"""Exercise held-only and direct-public branches on frozen packing bytes."""
import hashlib,json,pathlib,sys,csv
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import public_branch30 as B
D=W/'branch-controls';D.mkdir(exist_ok=True)
S=pathlib.Path('$SCRATCH/bounties-squares')
root=D/'owned2.csv';root.write_text('n,x,y,angle\n2,.5,.5,0\n2,1.5001,.5,0\n')
pub=D/'public416.csv';pub.write_bytes((S/'take-harvest-r28/work/ancestry-inputs/harvest-416-6bb3721a-2d91e8a6f7f45e33.csv').read_bytes())
meta=pathlib.Path(str(pub)+'.json');meta.write_text(json.dumps(dict(n=416,source='example/public-file :: submission.csv',licence='Apache 2.0')))
def fixture(direct):
 nodes={'r':dict(source='own construction: branch control',licence='our own construction',record=str(root),parents=['h','p']if direct else['h']),
 'h':dict(source='held row control',licence='our own construction',record='/repo/results/round28-best-2026-11-15.tsv n=416',parents=['p']),
 'p':dict(source='example/public-file :: submission.csv',licence='Apache 2.0',record=str(pub)+' n=416',parents=[])}
 g=D/('direct.json'if direct else'held.json');g.write_text(json.dumps(dict(policy='strict28v1',ok=True,root='r',nodes=nodes,path=str(root),n=2)))
 pins=[dict(original=str(p),path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in(root,pub,meta,g)]
 e=D/('direct-evidence.json'if direct else'held-evidence.json');e.write_text(json.dumps(dict(n=2,input_sha256=hashlib.sha256(root.read_bytes()).hexdigest(),snapshots=pins,texts=[[str(root),'own construction'],[str(pub),''],[str(meta),meta.read_text()],[str(g),g.read_text()]])))
 return e,g
saved=B.P.share;B.P.share=lambda *a:(_ for _ in ()).throw(AssertionError('held-only path was share-gated'))
e,g=fixture(False);a=B.audit(e,g);assert a['clean']and not a['public_roots'];B.P.share=saved
e,g=fixture(True)
bad=B.audit(e,g)
assert not bad['clean']and any(r['share1e3']>=.4 for r in bad['public_roots']),bad
negative=str([(r['n'],r['share1e3'])for r in bad['public_roots']if not r['allowed']])
# The real held641 proof must also pass without invoking the share function.
B.P.share=lambda *a:(_ for _ in ()).throw(AssertionError('actual held641 was share-gated'))
a=B.audit(W/'evidence/recovered641.json',W/'ancestry/recovered641.json');assert a['clean']and not a['public_roots'];B.P.share=saved
old=S/'take-invent-r29/work';j=next(j for j in json.load(open(old/'jobs.json'))if j['id']=='f073954x907x77')
a=B.audit(j['evidence'],j['ancestry']);assert a['clean']and a['public_roots']and all(r['share1e3']<.4 for r in a['public_roots']),a
# Removing the public byte pin must fail even while the live file still exists.
e,g=fixture(True);missing=json.load(open(e));missing['snapshots']=[p for p in missing['snapshots']if p['original']!=str(pub)];e.write_text(json.dumps(missing))
try:B.audit(e,g)
except (ValueError,AssertionError):pass
else:raise AssertionError('direct public reference without captured bytes passed')

def named_fixture(n,logical,direct):
 from policy import prvsiyan
 packing=D/('named'+str(n)+'.csv')
 with packing.open('w')as f:
  out=csv.DictWriter(f,fieldnames=['n','x','y']);out.writeheader();out.writerows(dict(n=n,x=x,y=y)for x,y in prvsiyan()[n])
 metadata=D/('named'+str(n)+'-meta.json');metadata.write_text(json.dumps(dict(n=n,source='own construction stale label',licence='our own construction')))
 nodes={'r':dict(source='own construction: named transport control',licence='our own construction',record=str(root),parents=['h','p']if direct else['h']),
 'h':dict(source='held n = '+str(n)+' of round 22',licence='our own construction',record='/repo/results/round22-best-2026-11-13.tsv n='+str(n),parents=['p']),
 'p':dict(source='own construction stale label',licence='our own construction',record=logical+' n='+str(n),parents=[])}
 graph=D/('named'+str(n)+('-direct'if direct else'-held')+'.json');graph.write_text(json.dumps(dict(root='r',nodes=nodes,path=str(root),n=2)))
 pins=[dict(original=original,path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())for original,path in [(str(root),root),(logical,packing),(logical+'.json',metadata),(str(graph),graph)]]
 evidence=D/('named'+str(n)+('-direct'if direct else'-held')+'-evidence.json');evidence.write_text(json.dumps(dict(n=2,input_sha256=hashlib.sha256(root.read_bytes()).hexdigest(),snapshots=pins,texts=[[str(root),'own construction'],[logical,''],[logical+'.json',metadata.read_text()],[str(graph),graph.read_text()]])))
 return evidence,graph
for n,logical in [(695,str(S/'take-harvest-r26/695.csv')),(799,str(S/'take-forensics-r22/work/donors/799-986b3b6daebce05b9257.csv'))]:
 e,g=named_fixture(n,logical,False);B.P.share=lambda *a:(_ for _ in ()).throw(AssertionError('named held-only path was share-gated'));ok=B.audit(e,g);assert ok['clean'];B.P.share=saved
 e,g=named_fixture(n,logical,True);bad=B.audit(e,g);assert not bad['clean']and any(r['n']==n and r['share1e3']>=.4 for r in bad['public_roots']),bad

result=dict(held_only_without_share=True,direct_bad_parent_beside_held_rejected=True,named695_and799_direct_rejected=True,named695_and799_held_only_exempt=True,missing_direct_byte_pin_refused=True,actual641_without_share=True,actual_public907_allowed=True,actual_public907_roots=a['public_roots'],direct_failure=negative)
(W/'branch-controls30.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='actual_public907_roots'}),flush=True)
