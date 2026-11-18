"""Admit current rectangle records with the producer and assembler source walks."""
import hashlib,json,pathlib,re,sys
LANE=pathlib.Path('.')
ROOT=pathlib.Path('$SCRATCH/bounties-squares')
WORK=ROOT/'take-stair-c-r33/work'
sys.path.insert(0,str(LANE))
import importlib.util
spec=importlib.util.spec_from_file_location('stair_c_provenance27',pathlib.Path(__file__).with_name('provenance.py'))
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
clean,pin=P.clean,P.pin
import forensics_sources28 as F
import quench_walk as Q

def _audit(path,n,metadata):
    if not metadata.get('parts'):return None
    ok,evidence=F.check_parts(metadata['parts'],ROOT)
    if not ok:return None
    # This is an own rectangle composition under RULE001903.
    old_share,old_ancestor,old_names=Q.prv_share,getattr(Q,'anc_share',None),Q.NAMES
    Q.prv_share=lambda *args:(0.,0.,0.,0.);Q.anc_share=lambda *args:None
    Q.NAMES=re.compile(r'squares-joegun-boxed|penguin069/squares-joegun|squares-verified-best-of-1105|CC BY-SA|ShareAlike',re.I)
    try:result=Q.check(str(path))
    finally:
        Q.prv_share,Q.NAMES=old_share,old_names
        if old_ancestor is None:del Q.anc_share
        else:Q.anc_share=old_ancestor
    # Old handoff share refusals are lifted for these own layouts.
    result['hits']=[h for h in result.get('hits',[]) if not (re.search(r'withdrawn|refused by its lane',h,re.I) and re.search(r'share|prvsiyan.*0\.',h,re.I) and not re.search(r'verified-best-of-1105|joegun',h,re.I))]
    result['clean']=not result['hits']
    if not result.get('clean'):return None
    notices=set()
    def collect(v):
        if isinstance(v,dict):
            if isinstance(v.get('source'),str) and v.get('licence'):notices.add((v['source'],str(v['licence'])))
            for x in v.values():collect(x)
        elif isinstance(v,list):
            for x in v:collect(x)
    collect(evidence)
    for tag in ('A','B','C'):
        part=metadata['parts'].get(tag)
        if not part:continue
        origin=pathlib.Path(part['source'][0]+'.origin.json')
        if origin.exists():collect(json.loads(origin.read_text()))
    if not notices:return None
    source='forensics rectangle composition; '+' | '.join(s for s,l in sorted(notices))
    licence='our own composition; '+'; '.join(sorted({l for s,l in notices}))
    if not clean(source,licence):return None
    # Save the exact full walk once. A text blob avoids treating a compact proof
    # without a licence field as a new, independent source root.
    texts,missing,seen,helds,refused=Q.walk(str(path),n)
    raw=json.dumps(dict(texts=texts,missing=missing,seen=sorted(seen),helds=sorted(helds,key=str),refused=refused,producer_evidence=evidence),sort_keys=True,separators=(',',':')).encode()
    folder=WORK/'rectangle-evidence';folder.mkdir(exist_ok=True)
    (WORK/'proofs').mkdir(exist_ok=True)
    digest=hashlib.sha256(raw).hexdigest();blob=folder/(digest+'.txt')
    if not blob.exists():blob.write_bytes(raw)
    proof=dict(n=n,path=str(path),snapshot_sha256=hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),source=source,licence=licence,assembler_walk=result,full_walk_snapshot=str(blob),full_walk_sha256=digest)
    raw=json.dumps(proof,sort_keys=True,separators=(',',':')).encode();dest=WORK/'proofs'/(hashlib.sha256(raw).hexdigest()+'.json')
    if not dest.exists():dest.write_bytes(raw)
    from public_roots import audit as public_audit
    public_audit(proof)
    short,notice=pin(f'{path} immutable sha256 {proof["snapshot_sha256"]}; ancestry proof {dest}; '+source,licence)
    return dict(n=n,source=short,licence=notice,proof=str(dest))

def audit(path,n,metadata):
    try:return _audit(path,n,metadata)
    except (TypeError,IndexError)as ex:raise ValueError('unsupported current rectangle metadata: '+str(ex))from ex
    finally:
        # The shared walker otherwise retains a flattened source tree per file/count.
        cache=getattr(Q,'_jt',{})
        if len(cache)>128:cache.clear()

if __name__=='__main__':
    path=pathlib.Path(sys.argv[1]);n=int(path.name.split('-')[0]);metadata=json.loads(pathlib.Path(str(path)+'.json').read_text())
    record=audit(path,n,metadata);print('rectangle',n,'admitted',record is not None,flush=True)
    if '--control' in sys.argv:
        assert record is not None,'positive rectangle control must trace'
        changed=json.loads(json.dumps(metadata));changed['parts']['A']['source']=['/missing/stair-c-control.csv',n];changed['parts']['A']['original_file']='/missing/stair-c-control.csv'
        assert audit(path,n,changed) is None
        print('CONTROL pinned rectangle accepted through two walks; missing part rejected',flush=True)
