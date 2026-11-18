"""Keep complete producer proofs once by hash and refuse excluded roots."""
import csv, functools, hashlib, importlib.util, json, os, re, sys
from pathlib import Path
LANE=Path('.')
ROOT=Path('$SCRATCH/bounties-squares')
WORK=ROOT/'take-stair-c-r32/work'
sys.path.insert(0,str(LANE))
import readers_sources
# Round 27: the Samanyu rule is lifted (round 27 override 2). The producer trace is our
# copy of tools/softround/provenance.py with only the Samanyu markers and the Samanyu
# 735 tree ban taken out (trace27.py); every other check of it is unchanged.
spec=importlib.util.spec_from_file_location('producer_provenance27',Path(__file__).resolve().parent/'trace27.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
csv.field_size_limit(64*1024*1024)
# Kept: penguin069 joegun union, prvsiyan best-of-1105, CC BY-SA. A "no licence" note
# counts only outside the text that names the Samanyu-dev seed.
def atomic_text(path,value):
    path=Path(path);temp=path.with_name(path.name+'.tmp-'+str(os.getpid()))
    temp.write_text(value);temp.replace(path)
def atomic_bytes(path,value):
    path=Path(path);temp=path.with_name(path.name+'.tmp-'+str(os.getpid()))
    temp.write_bytes(value);temp.replace(path)
def policy_text(text):
    return re.sub(r'prvsiyan[\w /.-]{0,40}?\(CC BY-SA\)\s*(?:share\s*)?=?\s*\d+(?:\.\d+)?','comparison',text,flags=re.I)
BAD=re.compile(r'penguin069/squares-joegun-boxed-certified-union|squares-verified-best-of-1105|CC BY-SA',re.I)
NOLIC=re.compile(r'no licen[cs]e|unlicensed',re.I)
SAMANYU=re.compile(r'Samanyu(?:-dev)?(?:/squares_in_squares)?[^;|\n]{0,160}',re.I)
def nolicence(text):return bool(NOLIC.search(SAMANYU.sub(' ',text)))

def held_identity(source,licence):
    m=re.search(r'own submitted held n=(\d+) in ($DATA/[^;<> ]+\.csv); source record ($DATA/[^;<> ]+\.json)',source)
    if not m:return None
    from held_proof import HELD,held_rows,coords
    n=int(m[1]);record=Path(m[3]);snapshot=record.with_name(str(n)+'.csv')
    if m[2]!=str(HELD)or record.parent!=WORK/'held31'or record.name!=str(n)+'-source.json':return None
    try:
        value=json.loads(record.read_text())
        if value['n']!=n or value['licence']not in licence:return None
        if coords(list(csv.DictReader(snapshot.open())))!=coords(held_rows()[n]):return None
    except(OSError,ValueError,KeyError):return None
    return dict(n=n,record=value,path=str(record),snapshot=str(snapshot))

def clean(source,licence):
    text=source+' '+licence
    held=held_identity(source,licence)
    if held is not None:
        record=held['record']
        allowed_text=policy_text(text+' '+record.get('source','')+' '+record.get('licence',''))
        if held['n']==801:allowed_text=re.sub(r'prvsiyan/squares-verified-best-of-1105|CC BY-SA','',allowed_text,flags=re.I)
        return bool(source and licence)and not BAD.search(allowed_text)
    if not deep_references_clean(text):return False
    for path in re.findall(r'stair-c proof (/[^ ;<>]+/ancestry/[0-9a-f]{64}\.json)',source):
        if not pinned_clean(path):return False
    if BAD.search(policy_text(text)) or nolicence(text):return False
    if re.search(r'take-harvest-r22/(?:near/)?(?:639|691|745|858|918)(?:[.\-]|/)|take-forensics-r23/(?:near/)?980(?:[.\-]|/)',text):return False
    # RULE001903: held801 is an allowed own root.
    if 'sis-certified-union-micro-shrink' in text and 'per_n.csv' not in text:return False
    return bool(source and licence)

@functools.lru_cache(None)
def held_records():
    H={int(r['n']):float(r['L']) for r in csv.DictReader(open(ROOT/'gate/cand-round25-1114b/details.csv'))}
    records={}
    paths=sorted(LANE.glob('results/round*-best-*.tsv'),key=lambda p:int(re.search(r'round(\d+)',p.name)[1]))
    for p in paths:
        for r in csv.DictReader(open(p),delimiter='\t'):
            try:
                n=int(r['n'])
                if abs(float(r['L'])-H[n])<2e-7:records[n]=(p,r)
            except (KeyError,ValueError):pass
    return records

@functools.lru_cache(None)
def held_record(n):
    record=held_records().get(n)
    if not record:return None
    p,r=record
    if not clean(r.get('source',''),r.get('licence','')):return None
    return dict(n=n,source=str(p.relative_to(LANE))+': '+r['source'],licence=r['licence'],table=str(p),reason='source record matching clean held side')


@functools.lru_cache(None)
def original_matches_held(n):
    p=ROOT/'take-stair-c-r25/work/round23ab-geometry.json'
    if not p.exists():return False
    data=json.loads(p.read_text())
    return n in data['same']

def proof_ok(value):
    if isinstance(value,dict):
        path=str(value.get('path',''));n=value.get('n')
        if value.get('held31_origin'):
            from held_proof import HELD,check
            if path==str(HELD):
                try:
                    origin=value['held31_origin'];assert origin['n']==n
                    check(origin);record=json.loads(Path(origin['record']).read_text())
                    assert record['n']==n and record['licence']in value['licence']
                except(AssertionError,OSError,ValueError,KeyError):return False
                text=policy_text(record.get('source','')+' '+record.get('licence',''))
                if n==801:text=re.sub(r'prvsiyan/squares-verified-best-of-1105|CC BY-SA','',text,flags=re.I)
                return not BAD.search(text)
        if path.endswith('/gather/round23-2026-11-13a.csv'):
            return isinstance(n,int) and original_matches_held(n) and held_record(n) is not None
        src=value.get('source',value.get('src'))
        if isinstance(src,str) and src:
            lic=value.get('licence')
            if lic and not clean(src,str(lic)):return False
        items=[(k,v) for k,v in value.items() if not (k=='source_proof' and isinstance(v,str) and v in ACTIVE_PROOFS)]
        for k,v in items:
            if isinstance(v,str) and k in {'source_record','source_proof','ancestry_file','ancestry_proof','proof_file'} and not deep_references_clean(k+' '+v):return False
        return all(proof_ok(v) for k,v in items)
    if isinstance(value,list):return all(proof_ok(v) for v in value)
    if isinstance(value,str):
        if BAD.search(policy_text(value)) or not deep_references_clean(value):return False
    return True

def audit(path,n,source=None,licence=None):
    path=Path(path)
    from held_proof import audit as held_audit
    held=held_audit(path,n)
    if held is not None:return held
    if source is None:source,licence,_=P.metadata(path,n)
    if not clean(source,licence):return None
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    # A snapshot's own leading locator binds these bytes, independently of
    # the producer trace recovered from its sidecar.
    self_pin=re.match(re.escape(str(path))+r'\s+immutable sha256\s+([0-9a-f]{64})(?![0-9a-f])',source)
    if self_pin is not None and self_pin[1]!=digest:return None
    key=hashlib.sha256(('RULE001903'+str(path)+digest+source+licence).encode()).hexdigest()
    dest=WORK/'proofs'/f'{key}.json';dest.parent.mkdir(exist_ok=True)
    proof=json.loads(dest.read_text()) if dest.exists() else P.trace(path,n)
    if not proof.get('ok'):
        import forensics_sources28 as current
        ok,evidence=current.trace(path,n,ROOT)
        proof=dict(ok=bool(ok),path=str(path),n=n,evidence=evidence,reason='current producer source walk' if ok else 'current producer source walk unresolved')
    proof.update(snapshot_sha256=digest,source=source,licence=licence)
    encoded=json.dumps(proof,separators=(',',':'))
    if not dest.exists()or dest.read_text()!=encoded:atomic_text(dest,encoded)
    if not proof.get('ok') or not proof_ok(proof):return None
    from public_roots import audit as public_audit
    public_record=public_audit(proof)
    proof.update(public_record)
    encoded=json.dumps(proof,separators=(',',':'))
    if dest.read_text()!=encoded:atomic_text(dest,encoded)
    # Compact module metadata names the immutable full proof. Avoid recursive
    # source copies in queues while retaining the original credits once.
    try:short,notice=pin(source,licence)
    except ValueError:return None
    return dict(n=n,source=f'{path} immutable sha256 {digest}; ancestry proof {dest}; '+short,licence=notice,proof=str(dest),**public_record)

def control():
    assert clean('twoshort_corner.py: staircase corner (own construction)','our own')
    # Round 27: the Samanyu rule is lifted; these were refused in round 26 and pass now.
    assert clean('held: n = 504 of Samanyu-dev/squares_in_squares (no licence)','our own')
    assert clean('Samanyu seed ancestry: yes, seed n=365','our own')
    assert clean('module 921r25c921.F1 of held 921; parent take-stair-c-r17/near/921-29e12ff3.csv','our own')
    assert proof_ok(dict(ok=True,parent=dict(source='Samanyu-dev/squares_in_squares',licence='no licence'),seed_policy=dict(status='seeds',seeds=[365])))
    # Still out.
    assert not clean('penguin069/squares-joegun-boxed-certified-union','Apache 2.0')
    assert not clean('prvsiyan/squares-verified-best-of-1105','CC BY-SA 4.0')
    assert not clean('some/other-dataset','no licence')
    assert not clean('Samanyu-dev seed; parent some/other-dataset; terms: unknown','CC BY-SA 4.0')
    assert not clean('start take-harvest-r22/745.csv','Apache 2.0')
    assert clean('held packing of n=801','held')
    assert clean('own construction; prvsiyan 1105 (CC BY-SA) share 0.55','our own')
    assert not proof_ok(dict(ok=True,parent=dict(source='prvsiyan/squares-verified-best-of-1105',licence='CC BY-SA 4.0')))
    print('CONTROL r27 source gate: Samanyu seed, 921-29e12ff3 and 921r25c921 now accepted; penguin, prvsiyan, CC BY-SA, plain no-licence and harvest-r22 745 rejected; held801 allowed by RULE001903',flush=True)

@functools.lru_cache(None)
def pinned_clean(path):
    p=Path(path)
    if not p.is_file():return False
    raw=p.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=p.stem:return False
    value=json.loads(raw)
    return clean(value['source'],value['licence'])

def pin(source,licence):
    """Keep the full immutable record once, with bounded queue notices."""
    raw=json.dumps(dict(source=source,licence=licence),sort_keys=True,separators=(',',':')).encode()
    digest=hashlib.sha256(raw).hexdigest();folder=WORK/'ancestry';folder.mkdir(exist_ok=True)
    p=folder/(digest+'.json')
    if not p.exists():atomic_bytes(p,raw)
    # Exact notice clauses are deduplicated. Their complete order remains in p.
    notice='; '.join(sorted({v.strip() for v in licence.split(';') if v.strip()}))
    short=f'stair-c proof {p} immutable sha256 {digest}; results/round25-best-2026-11-14.tsv; results/round23-best-2026-11-13.tsv'
    upstream=upstream_notices(source,licence)
    if upstream:
        actual=' | '.join(upstream);short+='; Upstream per-n records: '+actual;notice+='; Upstream per-n records: '+actual
    return short,notice


# Other lanes also retain full source trees by reference. Inspect those files,
# rather than treating a short licensed wrapper as the complete source tree.
PROOF_PATH=re.compile(r'($DATA/[^\s,;<>"\\]+/(?:ancestry|provenance|proofs)/[^\s,;<>"\\]+\.json)')
PROOF_KEYWORD=re.compile(r'(?:pinned\s+ancestry|source_record|source_proof|ancestry_file|ancestry_proof|proof_file|ancestry proof)[\s:=]*'+r'($DATA/[^\s,;<>"\\]+\.json)',re.I)
ACTIVE_PROOFS=set()
@functools.lru_cache(maxsize=4096)
def foreign_proof_clean(path,mtime,size):
    if path in ACTIVE_PROOFS:return False
    ACTIVE_PROOFS.add(path)
    try:
        p=Path(path);value=json.loads(p.read_text())
        return proof_ok(value) and has_source_record(value)
    except (OSError,ValueError,RecursionError):return False
    finally:ACTIVE_PROOFS.remove(path)

def has_source_record(value):
    if isinstance(value,dict):
        if isinstance(value.get('source',value.get('src')),str) and value.get('source',value.get('src')) and value.get('licence'):return True
        return any(has_source_record(v) for v in value.values())
    if isinstance(value,list):return any(has_source_record(v) for v in value)
    return False

def deep_references_clean(text):
    paths=set(PROOF_PATH.findall(text))|set(PROOF_KEYWORD.findall(text))
    for path in paths:
        p=Path(path)
        try:st=p.stat()
        except OSError:return False
        if not foreign_proof_clean(path,st.st_mtime_ns,st.st_size):return False
    return True


UPSTREAM_NOTICE=re.compile(r'areebbb/sis-certified-union-micro-shrink-lb-22-17479\s*::\s*per_n\.csv,\s*donor n\s*=\s*(\d+),\s*src=([^;<>]+);\s*upstream ([^;<>]+);\s*both public notebooks Apache 2\.0')
@functools.lru_cache(None)
def upstream_rows():
    path=ROOT/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
    return {int(r['n']):r for r in csv.DictReader(open(path))}

@functools.lru_cache(maxsize=8192)
def upstream_notices(source,licence):
    pending=[source,licence];seen=set();notices=set();has_public=False
    while pending:
        text=pending.pop();has_public=has_public or 'areebbb/sis-certified-union-micro-shrink' in text
        for m in UPSTREAM_NOTICE.finditer(text):
            n=int(m[1]);row=upstream_rows().get(n)
            if not row or row['src']!=m[2].strip() or not row['src'].startswith('notebooks/'):raise ValueError('per-n upstream notice mismatch')
            notices.add(m[0])
        for path in set(PROOF_PATH.findall(text))|set(PROOF_KEYWORD.findall(text)):
            if path in seen:continue
            seen.add(path)
            try:value=json.loads(Path(path).read_text())
            except (OSError,ValueError):raise ValueError('missing full public source record')
            def visit(v):
                if isinstance(v,dict):
                    row=v.get('per_n_row')
                    if isinstance(row,dict) and v.get('licence'):
                        n=int(row['n']);actual=upstream_rows().get(n)
                        if not actual or actual['src']!=row.get('src'):raise ValueError('retained per-n row mismatch')
                        notices.add('areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n='+str(n)+', record='+json.dumps(actual,sort_keys=True)+'; upstream '+str(v.get('source',''))+'; terms '+str(v['licence']))
                    for k,x in v.items():
                        if isinstance(x,str) and k in {'source_record','source_proof','ancestry_file','ancestry_proof','proof_file'}:pending.append(k+' '+x)
                        visit(x)
                elif isinstance(v,list):
                    for x in v:visit(x)
                elif isinstance(v,str):pending.append(v)
            visit(value)
    if has_public and not notices:raise ValueError('areebbb source lacks verified per-n credit')
    return tuple(sorted(notices))

if __name__=='__main__':control()


# Round 26: a held record may name an areebbb row only as "n = 703 (fq quench check of
# areebbb ... :: submission.csv". The per_n.csv row of that n names its upstream notebook.
# Only the malyshevdanil atlas upstream is derived here; any other upstream stays refused.
ATLAS='notebooks/malyshevdanil/squares-in-squares-living-atlas-of-tight-packings|'
def derive_credit(text):
    out=[]
    for n in sorted({int(x) for x in re.findall(r'n\s*=\s*(\d+)\s*\(fq quench check of areebbb/sis-certified-union-micro-shrink-lb-22-17479',text)}):
        r=upstream_rows().get(n)
        if not r or not r['src'].startswith(ATLAS):raise ValueError('no derivable per-n credit for areebbb n='+str(n))
        out.append('areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n='+str(n)+', src='+r['src']+'; upstream malyshevdanil/squares-in-squares-living-atlas-of-tight-packings :: submission_merged.csv; both public notebooks Apache 2.0')
    return out
