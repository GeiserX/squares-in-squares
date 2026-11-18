import hashlib,json,pathlib,sys
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W));import public_roots29 as A
folder=W/'public-root-controls';folder.mkdir(exist_ok=True)
def fixture(name,path,n,source,licence,public):
 b=pathlib.Path(path).read_bytes();p=folder/(name+'.csv');p.write_bytes(b);h=hashlib.sha256(b).hexdigest()
 proof=dict(root='root',nodes={'root':dict(source=source,licence=licence)})
 q=folder/(name+'-graph.json');q.write_text(json.dumps(proof))
 ev=dict(snapshots=[dict(path=str(p),original=str(p),sha256=h)],input_sha256=h,n=n,public_first=public)
 e=folder/(name+'-evidence.json');e.write_text(json.dumps(ev));return e,q
own=folder/'tiny.csv';own.write_text('n,x,y,a\n2,0,0,0\n2,1,0,0\n')
e,q=fixture('own',own,2,'own construction: contact domain control','our own construction',False)
public=A.P.reader();share=public.share
public.share=lambda *a,**k:(_ for _ in ()).throw(AssertionError('owned layout was share-gated'))
r=A.audit(e,q);assert r['clean']and not r['public_roots'];public.share=share
out={'owned_without_share':r}
path=W.parents[1]/'take-harvest-r28/work/ancestry-inputs/harvest-416-6bb3721a-2d91e8a6f7f45e33.csv'
e,q=fixture('public416',path,416,'public licensed/control :: captured public fixture','Apache 2.0',True)
r=A.audit(e,q);assert not r['clean']and r['public_roots'][0]['share1e3']>=.4;out['public416']=r
jobs=json.load(open(W/'jobs.json'))
for name,expect in [('n070325x641x54',False),('f073954x907x77',True)]:
 j=next(j for j in jobs if j['id']==name);r=A.audit(j['evidence'],j['ancestry']);assert r['clean']==expect,(name,r);out[name]=r
(W/'public-root-controls.json').write_text(json.dumps(out,indent=2))
print(json.dumps({k:dict(clean=v['clean'],roots=len(v['public_roots']),bad=[dict(n=r['n'],share=r['share1e3'])for r in v['public_roots']if not r['allowed']])for k,v in out.items()}))
# An ancestor's later same-path rewrite cannot replace its captured public bytes.
first=folder/'later-build.csv';first.write_bytes(path.read_bytes());pin=folder/'captured-public.csv';pin.write_bytes(path.read_bytes());digest=hashlib.sha256(pin.read_bytes()).hexdigest()
record=dict(parent=dict(path=str(first),n=416,record=dict(source='public licensed/control :: captured public fixture',licence='Apache 2.0',public_first=True)))
meta=folder/'captured-meta.json';meta.write_text(json.dumps(record))
e,q=fixture('descendant',own,2,'own construction: composite control','our own construction',False)
ev=json.load(open(e));ev['snapshots'] += [dict(original=str(first),path=str(pin),sha256=digest),dict(original=str(folder/'original-meta.json'),path=str(meta),sha256=hashlib.sha256(meta.read_bytes()).hexdigest())];e.write_text(json.dumps(ev));first.write_text('n,x,y\n2,0,0\n2,1,0\n')
r=A.audit(e,q);assert not r['clean']and r['public_roots'][0]['share1e3']>=.4;out['rewritten_ancestor_uses_pin']=r
pin.write_text('n,x,y\n2,0,0\n2,1,0\n')
try:A.audit(e,q)
except ValueError:out['changed_pin_refused']=True
else:raise AssertionError('altered frozen ancestor accepted')
(W/'public-root-controls.json').write_text(json.dumps(out,indent=2));print('rewritten ancestor used the captured public bytes; changed immutable pin refused')
ready=W/'original808-intake.json'
if ready.exists()and json.load(open(ready)).get('job'):
 j=json.load(open(ready))['job'];saved=public.share;public.share=lambda *a,**k:(_ for _ in ()).throw(AssertionError('actual owned808 was share-gated'))
 r=A.audit(j['evidence'],j['ancestry']);public.share=saved;assert r['clean']and not r['public_roots'];out['actual_owned808_without_share']=r
j=next(j for j in json.load(open(W/'jobs.json'))if j['id']=='o092822x377x1');r=A.audit(j['evidence'],j['ancestry']);assert r['clean']and any('/harvest/nb/prvsiyan__a-square-deal-research-to-verified-packings/'in a['original']and a['share1e3']<.4 for a in r['public_roots']);out['corrected377_original_public_archive']=r
(W/'public-root-controls.json').write_text(json.dumps(out,indent=2));print('actual owned808 passed with share forced to fail; corrected377 audits only its fetched public archive')
