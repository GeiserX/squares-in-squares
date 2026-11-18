"""Audit fetched public roots while leaving owned geometry outside share tests."""
import hashlib,json,re,sys
from pathlib import Path
LANE=Path('.')
sys.path.insert(0,str(LANE))
import forensics_public29 as F
import forensics_watch as W
ROOT=Path('$SCRATCH/bounties-squares/take-stair-c-r30/work')
REF=re.compile(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.(?:json|txt))')

def warm():
    return F.reader()

def closure(proof):
    texts=[];seen=set();pending=[proof]
    def file(path):
        p=Path(path)
        if str(p)in seen or not p.is_file():return
        if len(seen)>=2048:raise ValueError('public-root reference closure reached its cap')
        seen.add(str(p));raw=p.read_text()
        try:value=json.loads(raw)
        except ValueError:return
        texts.append(raw);pending.append(value)
    while pending:
        v=pending.pop()
        if isinstance(v,dict):
            for k,x in v.items():
                if k in {'full_walk_snapshot','source_record','source_proof','proof','ancestry_file','ancestry_proof','proof_file'}and isinstance(x,str):file(x)
                pending.append(x)
        elif isinstance(v,list):pending.extend(v)
        elif isinstance(v,str):
            for path in REF.findall(v):file(path)
    return texts

def gather(parts):
    # The held 801 is an authoritative owned root under the round30 override.
    root=parts.get('root',{}).get('source',[])
    if len(root)==2 and root[1]==801:return []
    return W.gather_notices(parts)

def audit(proof,folder=ROOT):
    folder=Path(folder);folder.mkdir(exist_ok=True)
    references=closure(proof)
    rows=F.audit(proof,references,folder,[],gather=gather)
    refused=[r for r in rows if not r['allowed']]
    if refused:raise ValueError('excluded public-first root: '+json.dumps(refused[:2],sort_keys=True))
    raw=json.dumps(rows,sort_keys=True,separators=(',',':')).encode()
    out=folder/'public-root-proofs';out.mkdir(exist_ok=True)
    path=out/(hashlib.sha256(raw).hexdigest()+'.json')
    if not path.exists():path.write_bytes(raw)
    return dict(public_roots=rows,public_root_proof=str(path),public_root_sha256=path.stem)

def control():
    import tempfile,numpy as np
    public=F.reader()
    assert not public.public_node('/owned/975.csv',975,{'/owned/975.csv':'own construction: staircase'}, {})
    assert not public.public_node('/seeds/503.csv',503,{'/seeds/503.csv':'Samanyu-dev/squares_in_squares'}, {})
    with tempfile.TemporaryDirectory(dir=ROOT)as d:
        folder=Path(d);p=folder/'4.csv'
        from policy import prvsiyan
        xy=prvsiyan()[4]
        import csv
        with p.open('w')as h:
            w=csv.writer(h);w.writerow(['n','x','y']);w.writerows((4,*q)for q in xy)
        # An explicit rejected source fixture, never a packing search input.
        proof=dict(path=str(p),n=4,record=dict(public_first=True,source='prvsiyan/squares-verified-best-of-1105 :: control',licence='CC BY-SA 4.0'))
        measured=F.audit(proof,[],folder,[])
        assert len(measured)==1 and measured[0]['share1e3']==1 and not measured[0]['allowed']
        try:audit(proof,folder)
        except ValueError:pass
        else:raise AssertionError('public source control admitted')
        own=dict(path='/owned/975.csv',n=975,record=dict(source='own construction: staircase',licence='our own'))
        assert audit(own,folder)['public_roots']==[]
    print('CONTROL public roots: owned staircase and original seed produce no share tests; real reference fixture measures share1 and is rejected with its licence',flush=True)

if __name__=='__main__':control()
