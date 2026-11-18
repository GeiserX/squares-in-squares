"""Admit current rectangle records with the producer and assembler source walks."""
import hashlib,json,pathlib,sys
LANE=pathlib.Path('.')
ROOT=pathlib.Path('$SCRATCH/bounties-squares')
WORK=ROOT/'take-stair-c-r27/work'
sys.path.insert(0,str(LANE))
import importlib.util
spec=importlib.util.spec_from_file_location('stair_c_provenance27',pathlib.Path(__file__).with_name('provenance.py'))
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
clean,pin=P.clean,P.pin
import forensics_sources27 as F
import quench_walk as Q

def audit(path,n,metadata):
    if not metadata.get('parts'):return None
    ok,evidence=F.check_parts(metadata['parts'],ROOT)
    if not ok:return None
    result=Q.check(str(path))
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
    digest=hashlib.sha256(raw).hexdigest();blob=folder/(digest+'.txt')
    if not blob.exists():blob.write_bytes(raw)
    proof=dict(n=n,path=str(path),snapshot_sha256=hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest(),source=source,licence=licence,assembler_walk=result,full_walk_snapshot=str(blob),full_walk_sha256=digest)
    raw=json.dumps(proof,sort_keys=True,separators=(',',':')).encode();dest=WORK/'proofs'/(hashlib.sha256(raw).hexdigest()+'.json')
    if not dest.exists():dest.write_bytes(raw)
    short,notice=pin(f'{path} immutable sha256 {proof["snapshot_sha256"]}; ancestry proof {dest}; '+source,licence)
    return dict(n=n,source=short,licence=notice,proof=str(dest))

if __name__=='__main__':
    path=pathlib.Path(sys.argv[1]);n=int(path.name.split('-')[0]);metadata=json.loads(pathlib.Path(str(path)+'.json').read_text())
    record=audit(path,n,metadata);print('rectangle',n,'admitted',record is not None,flush=True)
    if '--control' in sys.argv:
        assert record is not None,'positive rectangle control must trace'
        changed=json.loads(json.dumps(metadata));changed['parts']['A']['source']=['/missing/stair-c-control.csv',n];changed['parts']['A']['original_file']='/missing/stair-c-control.csv'
        assert audit(path,n,changed) is None
        print('CONTROL pinned rectangle accepted through two walks; missing part rejected',flush=True)
