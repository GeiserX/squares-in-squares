"""Round 34 changed-window admission with pinned held boundaries."""
from pathlib import Path
import csv,hashlib,json,time,re,math
import forensics_round33 as old
from forensics_round31 import *
from forensics_round31 import _numeric_digest as numeric_digest, _held_projection as held_projection
prior=old.prior
public=old.public
WORK=SCRATCH/'take-forensics-r34/work'
LOADED_SHA34=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
prior.WORK=WORK
prior.MAC='$SCRATCH/squares-forensics-r34'
public.WORK=WORK

def base(scratch,work):
    return {int(r['n']):float(r['bar']) for r in csv.DictReader(open(Path(scratch)/'round34-briefs/bar34.tsv'),delimiter='\t')}
prior.base=base

def admission_priority(path):
    fresh='-r34/' in str(path)
    rank=(0 if path.parent.name.startswith('take-') else 1 if path.parent.name=='near' and path.parent.parent.name=='take-k123-r34' else 3 if '/work/interior/' in str(path) else 4 if '/work/held-inputs/' in str(path) else 2) if fresh else 5
    order=[488,292,530,585,866,970,909,971,973,864,577,485,999]
    n=int(path.stem) if path.stem.isdigit() else 0
    held_order=order.index(n) if rank==3 and n in order else len(order)
    if str(path) in priority_inputs34():rank=-1
    return rank,held_order,-path.stat().st_mtime
prior.admission_priority=admission_priority

_old_trace=prior.fs._trace

def trace34(path,n,scratch,active=None,recorded=None):
    path=Path(path)
    if public.held(path):
        return True,dict(path=str(path),n=n,reason='submitted own held root under round34 rule2',snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    sidecar=Path(str(path)+'.json')
    if path.parent==WORK/'held-inputs' and sidecar.exists():
        from forensics_adapters30 import numeric_rows
        rec=json.loads(sidecar.read_text());donor=Path(rec['held_file'])
        if rec.get('kind')!='round34-exact-held-export' or rec['n']!=n or not public.held(donor) or hashlib.sha256(donor.read_bytes()).hexdigest()!=rec['held_sha256'] or hashlib.sha256(path.read_bytes()).hexdigest()!=rec['sha256']:
            return False,dict(path=str(path),n=n,reason='changed round34 held binding')
        st=donor.stat()
        if numeric_digest(numeric_rows(list(csv.DictReader(path.open()))))!=held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
            return False,dict(path=str(path),n=n,reason='held coordinates differ')
        return True,dict(path=str(path),n=n,record=rec,parent=dict(path=str(donor),n=n,reason='submitted own held root'),snapshot_sha256=rec['sha256'],reason='exact round34 own held export')
    transported=public_transport34(path,n,scratch,active,recorded)
    if transported is not None:return transported
    transported=public_cert_copy34(path,n,scratch,active,recorded)
    if transported is not None:return transported
    chain=twoshort_held_chain34(path,n,scratch,active,recorded)
    if chain is not None:return chain
    modules=stair_modules34(path,n,scratch,active,recorded)
    if modules is not None:return modules
    primary=primary_quench34(path,n,scratch,active,recorded)
    if primary is not None:return primary
    followed=backlog_primary34(path,n,scratch,active,recorded)
    if followed is not None:return followed
    fetched=public_queue34(path,n,scratch,active,recorded)
    if fetched is not None:return fetched
    peer=peer_held34(path,n,scratch)
    if peer is not None:return peer
    return _old_trace(path,n,scratch,active,recorded)
prior.fs._trace=trace34

_original_withdrawn=prior.fs.withdrawn

@old.prior.lru_cache(maxsize=4)
def _withdrawal_lines(tokens):
    return tuple(l for path,size,mtime in tokens for l in Path(path).read_text().splitlines() if 'WITHDRAW' in l)

def withdrawal_lines():
    paths=[SCRATCH/f'handoff-r{rnd}.log' for rnd in (31,32,33,34)]
    return _withdrawal_lines(tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths))

def withdrawn34(path,n,scratch):
    path=Path(path)
    if _original_withdrawn(path,n,scratch):return True
    if path==SCRATCH/'take-harvest-r26/695.csv':return True
    if 'take-forensics-r22' in path.parts and path.name.startswith('799-986b3b6d'):return True
    matches=[line for line in withdrawal_lines() if str(path) in line]
    if not matches and not ('take-harvest-r26' in path.parts and n==814):return False
    if not path.is_file():return False
    st=path.stat();digest=public.file_sha(str(path),st.st_size,st.st_mtime_ns)
    if 'take-harvest-r26' in path.parts and n==814 and digest.startswith('5a4c0cdb'):return True
    return any(any(digest.startswith(h) for h in re.findall(r'\b[a-f0-9]{12,64}\b',line)) for line in matches)

prior.fs.withdrawn=withdrawn34
_source_hash=prior.source_policy_hash

def source_policy_hash():
    return hashlib.sha256((_source_hash()+LOADED_SHA34+'\n'.join(withdrawal_lines())).encode()).hexdigest()
prior.source_policy_hash=source_policy_hash

def admit34(files, scratch, work):
    """Pin each changed, traceable input once by its packing hash."""
    allowed, audit, mapping = [], [], {}
    feed = work / 'feed'
    feed.mkdir(exist_ok=True)
    indexfile = work / 'feed-map.json'
    if indexfile.exists():
        mapping = json.loads(indexfile.read_text())
    refusals_file = work / 'refused-inputs.json'
    refusals = json.loads(refusals_file.read_text()) if refusals_file.exists() else {}
    success_file = work / 'admitted-inputs.json'
    successes = json.loads(success_file.read_text()) if success_file.exists() else {}
    inspected = 0
    held_inspected = 0
    fresh_inspected = 0
    interior_inspected = 0
    interior_started = None
    policy_token = source_policy_hash()
    for path in sorted(files, key=admission_priority):
        if path.parent.name in ('held','held34','held-inputs') and path.parent != WORK/'held-inputs':
            continue
        # A full walk budget must not hide cleared files later in the list.
        is_interior = '/take-forensics-r34/work/interior/' in str(path)
        extra_interior = is_interior and interior_inspected < 16 and (interior_started is None or time.time()-interior_started < 10)
        if inspected >= 4 and str(path) not in successes and not extra_interior:
            continue
        if not path.is_file():
            continue
        match = re.match(r'(\d+)', path.stem)
        if not match:
            continue
        n = int(match[1])
        dependencies = [path, Path(str(path)+'.json'), path.with_suffix('.json')]
        if path.stem.isdigit():
            dependencies.append(path.parent/'take.tsv')
        if not any(p.exists() for p in dependencies[1:]):
            record_root = path.parent.parent if path.parent.name == 'near' else path.parent
            dependencies.append(record_root/'work/sources-all.tsv')
        token = admission_token(path, n, dependencies, policy_token)
        saved = successes.get(str(path))
        if saved and saved['token'] == token and Path(saved['dest']).exists():
            dest = Path(saved['dest'])
            allowed.append(dest)
            mapping[str(dest)] = str(dest.relative_to(feed))
            continue
        prior = refusals.get(str(path))
        if reusable_refusal(prior, token, time.time()):
            continue
        is_held = '/work/held-inputs/' in str(path)
        is_fresh = '-r34/' in str(path) and not is_held
        if fresh_inspected and not is_fresh:
            continue
        if inspected >= 4 and not extra_interior:
            continue
        if is_fresh and fresh_inspected >= 4 and not extra_interior:
            continue
        if is_held and held_inspected >= 4:
            continue
        inspected += 1
        held_inspected += int(is_held)
        fresh_inspected += int(is_fresh and not is_interior)
        if is_interior and interior_started is None:
            interior_started = time.time()
        interior_inspected += int(is_interior)
        (work/'active-admission.json').write_text(json.dumps(dict(path=str(path),n=n,at=time.time())))
        try:
            ok, proof = queue_source_check(path, n, scratch, seconds=3 if is_interior else 30)
        except AdmissionDeferred:
            ok, proof = False, dict(reason='deferred source walk')
        audit.append(dict(path=str(path), n=n, admitted=ok, reason=proof['reason']))
        if not ok:
            refusals[str(path)] = dict(token=token,at=time.time(),reason=proof['reason'])
            continue
        refusals.pop(str(path),None)
        payload = path.read_bytes()
        after = admission_token(path, n, dependencies, policy_token)
        if after != token:
            audit[-1].update(admitted=False, reason='source changed during admission; retry')
            continue
        digest = hashlib.sha256(payload).hexdigest()
        group = path.parent.parent.name if path.parent.name == 'near' else path.parent.name
        dest = feed / group / ('%d-%s.csv' % (n, digest[:24]))
        dest.parent.mkdir(exist_ok=True)
        origin = Path(str(dest) + '.origin.json')
        if not origin.exists():
            dest.write_bytes(payload)
            # The derivation is stored once at this immutable hash.
            proof_file = work / 'proofs' / (hashlib.sha256(json.dumps(proof, sort_keys=True).encode()).hexdigest() + '.json')
            proof_file.parent.mkdir(exist_ok=True)
            proof_file.write_text(json.dumps(proof, indent=2))
            origin.write_text(json.dumps(dict(path=str(path), n=n, verified_ancestry=True,
                snapshot_sha256=digest, ancestry=proof, source_proof=str(proof_file),
                full_ancestry=proof['full_ancestry'])))
        allowed.append(dest)
        successes[str(path)] = dict(token=token,dest=str(dest))
        mapping[str(dest)] = str(dest.relative_to(feed))
    for path, value in ((success_file, successes), (refusals_file, refusals), (indexfile, mapping), (work/'source-admission.json', audit)):
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value))
        temporary.replace(path)
    return allowed

prior.admit=admit34
admit=admit34

# Use the assembler's frozen round31 measurement for every public descendant.
import importlib.util
_spec34=importlib.util.spec_from_file_location('forensics_assembler34',SCRATCH/'take-assemble-r31/scripts/share31.py')
_assembler34=importlib.util.module_from_spec(_spec34)
_spec34.loader.exec_module(_assembler34)
_assembler34.TOLS=(1e-6,1e-3,1e-2)
public_policy31._assembler=_assembler34


def peer_held34(path,n,scratch):
    """Verify peer held exports without reading inherited public history."""
    held_start=path.parent.name=='starts' and path.name==str(n)+'-held33a.csv'
    if '-r34/work/' not in str(path) or (path.parent.name not in ('held','held34','held-inputs') and not held_start) or not path.is_file():return None
    record,ledger=prior.fs.record(path,n)
    if not isinstance(record,dict):
        log=Path(scratch)/'handoff-r34.log'
        declarations=[line for line in log.read_text().splitlines() if str(path) in line and 'held' in line.lower()]
        if not declarations:return None
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if not any(any(digest.startswith(h) for h in re.findall(r'\b[a-f0-9]{12,64}\b',line)) for line in declarations):return None
        donor=Path(scratch)/'gather/round33-2026-11-17a.csv'
    else:
        donor=Path(record.get('held_file',record.get('path','')))
        if not public.held(donor):return None
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if record.get('row_sha256') and record['row_sha256']!=digest:return False,dict(reason='peer held byte hash differs',path=str(path),n=n)
        expected=record.get('held_sha256',record.get('sha256'))
        if expected and expected!=hashlib.sha256(donor.read_bytes()).hexdigest():return False,dict(reason='peer submitted hash differs',path=str(path),n=n)
    if not public.held(donor):return None
    from forensics_adapters30 import numeric_rows
    rows=list(csv.DictReader(path.open()));st=donor.stat()
    if len(rows)!=n or numeric_digest(numeric_rows(rows))!=held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
        return False,dict(reason='peer held coordinates differ',path=str(path),n=n)
    return True,dict(path=str(path),n=n,snapshot_sha256=digest,reason='exact round34 peer held projection',parent=dict(path=str(donor),n=n,reason='submitted own held root'),producer_ledger=ledger)


_check_parts34=old._check_parts33

def check_parts(parts,scratch=SCRATCH,fresh=False):
    result=_check_parts34(parts,scratch,fresh=fresh)
    if not result[0]:
        blob=json.dumps(dict(parts=parts,evidence=result[1]),sort_keys=True).encode()
        directory=WORK/'source-refusals34';directory.mkdir(exist_ok=True)
        path=directory/(hashlib.sha256(blob).hexdigest()+'.json')
        if not path.exists():path.write_bytes(blob)
    return result
prior.check_parts=check_parts


def output_share_needed(proofs):
    """Own inputs and held ancestry exempt their descendants under rule 2."""
    if not proofs or any(not row.get('public_roots') for row in proofs):return False
    graph,boundaries=public.direct_graph(proofs)
    return not boundaries


@old.prior.lru_cache(maxsize=16)
def _public_projection34(path,size,mtime,n):
    from forensics_adapters30 import numeric_rows
    rows=[]
    with open(path) as stream:
        for row in csv.DictReader(stream):
            count=int(str(row.get('n',row.get('id','').split('_')[0])).lstrip('s'))
            if count==n:rows.append(row)
    if len(rows)!=n:raise ValueError('public raw count differs')
    return numeric_digest(numeric_rows(rows))


def verify_public_metadata34(path,n,record):
    """Bind metadata parents to their exact raw CSV and queued projection."""
    from forensics_adapters30 import numeric_rows
    digest=hashlib.sha256(Path(path).read_bytes()).hexdigest()
    if record.get('n')!=n or record.get('queued_sha256')!=digest:raise ValueError('public queue hash or count differs')
    ref=re.match(r'^public ([^ ]+) ::',record.get('source',''))
    raw=re.search(r'raw file ([^ ;]+\.csv)',record.get('source',''))
    if not ref or not raw:raise ValueError('missing direct public identity')
    raw=Path(raw[1]);bindings=[]
    parents=record.get('parents')
    if not isinstance(parents,list) or not parents or not all(isinstance(v,dict) for v in parents):raise ValueError('unsupported metadata parent records')
    captured=[]
    for entry in parents:
        snapshot=Path(entry['snapshot']);payload=snapshot.read_bytes()
        if hashlib.sha256(payload).hexdigest()!=entry['sha256']:raise ValueError('changed public parent snapshot')
        captured.append((entry,snapshot,payload))
    roots=[v for v in captured if Path(v[0]['original']).name=='meta.json']
    if len(roots)!=1:raise ValueError('missing unique public metadata root')
    entry,snapshot,payload=roots[0];metadata=json.loads(payload);directory=Path(entry['original']).parent
    if metadata.get('ref')!=ref[1] or metadata.get('license')!=record.get('licence'):raise ValueError('metadata source or licence differs')
    if not any(metadata['license'].startswith(term) for term in ('Apache 2.0','CC BY 4.0','CC0')):raise ValueError('public licence not allowed')
    matches=[v for v in metadata.get('files',[]) if directory/v['file']==raw]
    if len(matches)!=1:raise ValueError('raw CSV absent from metadata')
    st=raw.stat();item=matches[0]
    if st.st_size!=item['bytes'] or public.file_sha(str(raw),st.st_size,st.st_mtime_ns)!=item['sha256']:raise ValueError('changed raw public file')
    if numeric_digest(numeric_rows(list(csv.DictReader(open(path)))))!=_public_projection34(str(raw),st.st_size,st.st_mtime_ns,n):raise ValueError('queued public coordinates differ from raw')
    bindings.append(dict(source_proof=str(snapshot),sha256=entry['sha256'],raw=str(raw),raw_sha256=item['sha256']))
    for auxiliary,snapshot,payload in captured:
        if auxiliary is entry:continue
        original=Path(auxiliary['original'])
        listed=[v for v in metadata.get('files',[]) if directory/v['file']==original]
        if len(listed)!=1 or listed[0]['bytes']!=len(payload) or listed[0]['sha256']!=auxiliary['sha256']:
            raise ValueError('public auxiliary file differs from metadata manifest')
        if original.name=='submission_sources.csv' and '; per-n origin ' in record.get('source',''):
            text=record['source'].split('; per-n origin ',1)[1];notice=json.JSONDecoder().raw_decode(text)[0]
            rows=[v for v in csv.DictReader(payload.decode().splitlines()) if int(v['n'])==n]
            if len(rows)!=1 or any(str(rows[0].get(k))!=str(v) for k,v in notice.items()):raise ValueError('public per-n origin differs from source table')
        bindings.append(dict(auxiliary_snapshot=str(snapshot),sha256=auxiliary['sha256'],original=str(original)))
    sanitized=dict(record);sanitized.pop('parents');sanitized.pop('original',None);sanitized['metadata_parents34']=parents
    return sanitized,bindings


def public_queue34(path,n,scratch,active,recorded):
    if recorded is not None or path.parent!=Path(scratch)/'take-harvest-r34/work/inputs':return None
    sidecar=Path(str(path)+'.json')
    if not sidecar.exists():return None
    record=json.loads(sidecar.read_text())
    if record.get('kind') not in ('fresh-public','reopened-public') or not record.get('parents') or not all(isinstance(v,dict) for v in record['parents']):return None
    try:
        sanitized,bindings=verify_public_metadata34(path,n,record)
        ok,parent=prior._trace_before26(path,n,scratch,active,recorded=sanitized)
        return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=record['queued_sha256'],metadata_bindings=bindings,reason='hash-bound public metadata parents and exact raw projection')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid public metadata or raw binding',error=repr(error))


def primary_quench34(path,n,scratch,active,recorded=None):
    """Read the one declared quench input before inherited notice history."""
    if '-r34/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'explicit retained record') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith(('quench lane: one fq quench ','quench lane kick: ')):return None
    match=re.match(r'^quench lane(?:: one fq quench | kick: ).*? of (take-quench-r34/work/starts/[^ ()]+\.csv) \(a byte copy, sha256 ([a-f0-9]{16,64})',source)
    if not match:return False,dict(path=str(path),n=n,reason='unreadable primary quench input')
    parent=Path(scratch)/match[1]
    if parent==path:return False,dict(path=str(path),n=n,reason='primary quench input cycle')
    count=re.match(r'(\d+)',parent.name)
    if not count or int(count[1])!=n or not parent.is_file() or not hashlib.sha256(parent.read_bytes()).hexdigest().startswith(match[2]):
        return False,dict(path=str(path),n=n,reason='missing or changed primary quench input')
    if prior.fs.withdrawn(parent,n,scratch):return False,dict(path=str(path),n=n,reason='withdrawn primary quench input')
    if len(list(csv.DictReader(path.open())))!=n:return False,dict(path=str(path),n=n,reason='quench result count differs')
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='quench ancestry cycle')
    try:
        producer=None
        if source.startswith('quench lane kick: '):
            producer=verify_quench_kick34(path,n,parent,source)
        parent_record,_=prior.fs.record(parent,n)
        if isinstance(parent_record,dict) and parent_record.get('source','').startswith(f'held n = {n} of round 33 '):
            proof=verify_held_payload34(parent.read_bytes(),n,hashlib.sha256(parent.read_bytes()).hexdigest());ok=True
        else:
            ok,proof=prior.fs.trace(parent,n,scratch,active|{(str(path),n)})
        return ok,dict(path=str(path),n=n,parent=proof,producer=producer,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),record=dict(record,source=source.split(' | recorded source of the start:',1)[0]),ledger=ledger,reason='hash-bound primary input of one fq quench or kick')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid primary quench producer',error=repr(error))


def public_cert_copy34(path,n,scratch,active,recorded=None):
    if '-r34/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict) or record.get('kind') not in ('fresh-public','reopened-public') or not record.get('certified_from'):return None
    parent=Path(record['certified_from'])
    if parent.parent!=Path(scratch)/'take-harvest-r34/work/inputs':return None
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    input_sha=record.get('certified_input_sha256')
    if int(record.get('n',0))!=n or not parent.is_file() or hashlib.sha256(parent.read_bytes()).hexdigest()!=input_sha:
        return False,dict(path=str(path),n=n,reason='public certified-copy input bytes differ')
    producer=None
    if digest!=input_sha:
        original=Path(record.get('path',''))
        if original.parent!=Path(scratch)/'take-harvest-r34/near' or not original.name.startswith(str(n)+'-') or not original.is_file():
            return False,dict(path=str(path),n=n,reason='missing transformed public producer')
        produced,producer_ledger=prior.fs.record(original,n)
        fields=('kind','source','licence','certified_from','certified_input_sha256')
        if (record.get('sha256')!=digest or hashlib.sha256(original.read_bytes()).hexdigest()!=digest or
            not isinstance(produced,dict) or produced.get('sha256')!=digest or
            any(record.get(key)!=produced.get(key) for key in fields) or not input_sha or input_sha[:16] not in original.name):
            return False,dict(path=str(path),n=n,reason='changed transformed public output or producer record')
        producer=dict(path=str(original),n=n,snapshot_sha256=digest,producer_ledger=producer_ledger,reason='exact transformed certificate producer bytes')
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='public certified-copy cycle')
    ok,proof=prior.fs.trace(parent,n,scratch,active|{(str(path),n)})
    return ok,dict(path=str(path),n=n,parent=proof,producer=producer,record=record,ledger=ledger,snapshot_sha256=digest,reason='exact public certificate copy bound to its queued source')


def stair_modules34(path,n,scratch,active,recorded=None):
    if '-r34/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict) or not isinstance(record.get('modules'),list) or not record['modules']:return None
    if Path(str(path)+'.origin.json').is_file():return None
    if not any('immutable sha256 ' in v.get('source','') for v in record['modules']):return None
    parents=[];active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='module ancestry cycle')
    for module in record['modules']:
        match=re.match(r'($SCRATCH/bounties-squares/[^ ;<>]+\.csv) immutable sha256 ([a-f0-9]{64})\b',module.get('source',''))
        if not match:return False,dict(path=str(path),n=n,reason='unsupported primary module binding')
        parent=Path(match[1])
        if not parent.is_file() or hashlib.sha256(parent.read_bytes()).hexdigest()!=match[2]:return False,dict(path=str(path),n=n,reason='missing or changed primary module bytes')
        count=len(list(csv.DictReader(parent.open())))
        if not 1<=count<=1000:return False,dict(path=str(path),n=n,reason='module count outside packing range')
        ok,proof=prior.fs.trace(parent,count,scratch,active|{(str(path),n)});parents.append(proof)
        if not ok:return False,dict(path=str(path),n=n,parents=parents,reason='refused primary module')
    if len(list(csv.DictReader(path.open())))!=n:return False,dict(path=str(path),n=n,reason='module result count differs')
    return True,dict(path=str(path),n=n,parents=parents,record=dict(record,modules=[dict(id=v.get('id'),source=v['source'].split(';',1)[0]) for v in record['modules']]),ledger=ledger,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reason='complete hash-bound primary module inputs')


@old.prior.lru_cache(maxsize=4)
def _priority_inputs34(size,mtime):
    return frozenset(json.loads((WORK/'priority-inputs34.json').read_text()))

def priority_inputs34():
    path=WORK/'priority-inputs34.json'
    if not path.exists():return frozenset()
    st=path.stat();return _priority_inputs34(st.st_size,st.st_mtime_ns)


_declared_before34=prior.fs.declared_withdrawal

def declared_withdrawal34(value,scratch):
    """Keep a withdrawn ancestor pinned even after its live path changes."""
    if _declared_before34(value,scratch):return True
    if not isinstance(value,dict):return False
    pairs=[]
    if value.get('path'):
        pairs.extend((value['path'],value[key]) for key in ('snapshot_sha256','packing_sha256') if value.get(key))
    if value.get('input_file_snapshot') and value.get('input_file_sha256'):
        pairs.append((value['input_file_snapshot'],value['input_file_sha256']))
    for name,digest in pairs:
        path=Path(name)
        if not path.is_absolute() and str(path).startswith(('take-','gather/')):path=Path(scratch)/path
        if path.suffix!='.csv' or not isinstance(digest,str):continue
        for line in withdrawal_lines():
            if str(path) not in line:continue
            pins=re.findall(r'\bsha256[ =:]+([a-f0-9]{12,64})\b',line)
            if any(digest.startswith(pin) or pin.startswith(digest) for pin in pins):return True
    return False
prior.fs.declared_withdrawal=declared_withdrawal34


def twoshort_held_chain34(path,n,scratch,active,recorded=None):
    """Verify every declared member of an own held lkick chain."""
    if '-r34/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('twoshort round 34:'):return None
    primary=source.split('Held row source:',1)[0]
    if 'invent_rest.py lkick' not in primary or ('from the held round 33 a row of n='+str(n)) not in primary:return None
    owned=Path(scratch)/'take-twoshort-r34/work'
    members=re.findall(r'($SCRATCH/bounties-squares/take-twoshort-r34/work/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\)',primary)
    baseline=owned/'starts'/(str(n)+'-held33a.csv')
    if not members or not any(Path(name)==baseline for name,want in members):return False,dict(path=str(path),n=n,reason='missing held-chain baseline binding')
    chain=[]
    for name,want in members:
        member=Path(name)
        if not member.is_relative_to(owned) or not member.is_file() or hashlib.sha256(member.read_bytes()).hexdigest()!=want:
            return False,dict(path=str(path),n=n,reason='missing or changed held-chain member',member=name)
        rows=list(csv.DictReader(member.open()))
        if len(rows)!=n or any(int(row.get('n',n))!=n for row in rows):return False,dict(path=str(path),n=n,reason='held-chain member count differs',member=name)
        chain.append(dict(path=name,n=n,snapshot_sha256=want))
    if len(list(csv.DictReader(path.open())))!=n:return False,dict(path=str(path),n=n,reason='held-chain result count differs')
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='held-chain cycle')
    ok,parent=prior.fs.trace(baseline,n,scratch,active|{(str(path),n)})
    return ok,dict(path=str(path),n=n,parent=parent,chain=chain,record=dict(source=primary,licence=record.get('licence','')),ledger=ledger,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reason='complete exact own held lkick chain')


def backlog_primary34(path,n,scratch,active,recorded=None):
    """Bind a Backlog start to the source row retained by its producer."""
    if '-r34/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('backlog lane:'):return None
    match=re.match(r'^backlog lane: .*?from the byte copy ($SCRATCH/bounties-squares/take-backlog-r34/work/starts/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\), taken at queue time from the certified round 34 take ([^;]+); its take\.tsv row: (.+)$',source,re.S)
    if not match:return None
    parent=Path(match[1]);origin=Path(scratch)/match[3]
    if parent==path or origin.name!=str(n)+'.csv' or not origin.parent.name.startswith('take-'):
        return False,dict(path=str(path),n=n,reason='invalid primary backlog origin')
    if not parent.is_file() or hashlib.sha256(parent.read_bytes()).hexdigest()!=match[2]:
        return False,dict(path=str(path),n=n,reason='missing or changed primary backlog input')
    if any(len(list(csv.DictReader(p.open())))!=n for p in (path,parent)):
        return False,dict(path=str(path),n=n,reason='backlog result or input count differs')
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='backlog ancestry cycle')
    licence=record.get('licence','').split(' [deep25 walk (',1)[0]
    inherited=dict(source=match[4],licence=licence)
    legs=[]
    try:
        for member in re.findall(r'final file ($SCRATCH/bounties-squares/take-backlog-r34/work/runs/[^ ()]+/final/\d+\.csv)', source[:match.start(1)]):
            legs.append(backlog_run34(member,n,parent,match[2],scratch))
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid Backlog primary leg',error=repr(error))
    ok,proof=prior.fs._trace(parent,n,scratch,active|{(str(path),n)},recorded=inherited)
    return ok,dict(path=str(path),n=n,parent=proof,legs=legs,record=dict(source=source[:match.start(4)],licence=licence),ledger=ledger,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),primary_start=dict(path=str(parent),n=n,snapshot_sha256=match[2]),reason='exact backlog start with its retained take row')


def verify_held_payload34(payload, n, expected):
    """Bind a retained start to the exact submitted row, including its count."""
    import io
    from forensics_adapters30 import numeric_rows
    if not re.fullmatch(r'[a-f0-9]{12,64}', expected) or not hashlib.sha256(payload).hexdigest().startswith(expected):
        raise ValueError('held start bytes differ')
    held = SCRATCH/'gather/round33-2026-11-17a.csv'
    if not public.held(held):
        raise ValueError('submitted held witness differs')
    rows = list(csv.DictReader(io.StringIO(payload.decode())))
    if len(rows) != n or any(int(row.get('n', n)) != n for row in rows):
        raise ValueError('held start count differs')
    st = held.stat()
    if numeric_digest(numeric_rows(rows)) != held_projection(str(held), st.st_size, st.st_mtime_ns)[n]:
        raise ValueError('held start coordinates differ')
    return dict(path=str(held), n=n, reason='submitted own held root',
                snapshot_sha256=public.file_sha(str(held), st.st_size, st.st_mtime_ns))


def rebuild_primary34(path, n, scratch, active=None, recorded=None):
    if '-r34/' not in str(path) or not path.is_file():
        return None
    record, ledger = (recorded, 'retained source record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict):
        return None
    source = record.get('source', '')
    if not isinstance(source, str) or not source.startswith('rebuild lane round '):
        return None
    match = re.search(r' of (take-rebuild-r34/work/held34/(\d+)\.csv) \(sha256 ([a-f0-9]{12,64}), byte copy (take-rebuild-r34/work/pins/[^ ()]+\.csv)\)', source)
    if not match:
        return None
    try:
        if int(match[2]) != n:
            raise ValueError('rebuild source count differs')
        pin = Path(scratch)/match[4]
        if prior.fs.withdrawn(pin, n, scratch):
            raise ValueError('withdrawn rebuild primary bytes')
        parent = verify_held_payload34(pin.read_bytes(), n, match[3])
        if len(list(csv.DictReader(path.open()))) != n:
            raise ValueError('rebuild output count differs')
        return True, dict(path=str(path), n=n, parent=parent, primary_start=str(pin),
                          primary_sha256=hashlib.sha256(pin.read_bytes()).hexdigest(),
                          snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          record=dict(source=source.split('. The start:', 1)[0], licence=record.get('licence', '')),
                          ledger=ledger, reason='exact rebuild primary start at submitted held33a boundary')
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid rebuild held primary binding', error=repr(error))


_trace_before_rebuild34 = prior.fs._trace


def trace_primary34(path, n, scratch, active=None, recorded=None):
    path = Path(path)
    # Every direct-start withdrawal remains effective before ownership adapters.
    if prior.fs.withdrawn(path, n, scratch):
        return False, dict(path=str(path), n=n, reason='explicit byte-pinned withdrawal')
    result = rebuild_primary34(path, n, scratch, active, recorded)
    if result is not None:
        return result
    result = invent_endpoint34(path, n, scratch, active, recorded)
    if result is not None:
        return result
    result = invent_primary34(path, n, scratch, active, recorded)
    if result is not None:
        return result
    return _trace_before_rebuild34(path, n, scratch, active, recorded)


prior.fs._trace = trace_primary34


def bound_file34(path, expected):
    path = Path(path)
    st = path.stat()
    if public.file_sha(str(path), st.st_size, st.st_mtime_ns) != expected:
        raise ValueError('changed retained proof file: '+str(path))
    return path


def invent_endpoint34(path, n, scratch, active=None, recorded=None):
    """Read an endpoint through its receipt and the pinned primary input record."""
    if '-r34/' not in str(path) or not path.is_file():
        return None
    record, ledger = (recorded, 'retained source record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict) or not isinstance(record.get('evidence'), str):
        return None
    evidence_file = Path(record['evidence'])
    if not evidence_file.is_file():
        return None
    packet = json.loads(evidence_file.read_text())
    if packet.get('policy') != 'own-source-r30-extended-endpoint':
        return None
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if int(record.get('n', 0)) != n or record.get('sha256') != digest or packet.get('n') != n or packet.get('input_sha256') != digest:
            raise ValueError('endpoint output hash or count differs')
        ancestry_file = bound_file34(packet['ancestry'], packet['ancestry_sha256'])
        if str(ancestry_file) != record.get('ancestry_file'):
            raise ValueError('endpoint ancestry path differs')
        ancestry = json.loads(ancestry_file.read_text())
        extension = packet['extension']
        receipt_file = bound_file34(extension['worker_receipt'], extension['worker_receipt_sha256'])
        receipt = json.loads(receipt_file.read_text())
        root_record = ancestry['nodes'][ancestry['root']]
        citation = str(receipt_file)+' sha256 '+extension['worker_receipt_sha256']
        if (receipt_file.name != 'done.json' or
                receipt_file.parent.parent != Path(scratch)/'take-invent-r34/work/boxE-raw' or
                receipt_file.parent.name != receipt.get('id') or
                root_record.get('record') != str(receipt_file)+' n='+str(n) or
                citation not in root_record.get('source', '')):
            raise ValueError('endpoint receipt differs from its ancestry root')
        producer = Path(ancestry['path'])
        if (receipt.get('id') != extension['parent_job'] or receipt.get('n') != n or
                receipt.get('sha256') != digest or ancestry.get('n') != n or
                producer != receipt_file.parent/'final'/f'{n}.csv' or
                receipt.get('program') != 'invent_barretain_budget30.py'):
            raise ValueError('endpoint producer receipt differs')
        bound_file34(producer, digest)
        if prior.fs.withdrawn(producer, n, scratch):
            raise ValueError('withdrawn endpoint producer bytes')
        parent_file = bound_file34(extension['parent_evidence'], extension['parent_evidence_sha256'])
        parent = json.loads(parent_file.read_text())
        input_sha = receipt['input_sha256']
        if parent.get('n') != n or parent.get('input_sha256') != input_sha:
            raise ValueError('endpoint primary input differs')
        primary_ancestry_file = bound_file34(parent['ancestry'], parent['ancestry_sha256'])
        primary_ancestry = json.loads(primary_ancestry_file.read_text())
        if primary_ancestry.get('n') != n:
            raise ValueError('endpoint primary ancestry count differs')
        snapshots = {}
        for entry in parent['snapshots']:
            add_snapshot34(snapshots, entry)
        original = primary_ancestry['path']
        input_entry = snapshots[original]
        if input_entry['sha256'] != input_sha:
            raise ValueError('primary source snapshot differs from receipt input')
        input_path = Path(input_entry['retained'])
        if prior.fs.withdrawn(input_path, n, scratch) or prior.fs.declared_withdrawal(dict(path=original, snapshot_sha256=input_sha), scratch):
            raise ValueError('withdrawn endpoint primary input bytes')
        if len(list(csv.DictReader(input_path.open()))) != n or len(list(csv.DictReader(path.open()))) != n:
            raise ValueError('endpoint packing count differs')
        original_record = primary_ancestry['nodes'][primary_ancestry['root']]['record'].split(' n=', 1)[0]
        record_entry = snapshots[original_record]
        primary_record = json.loads(Path(record_entry['retained']).read_text())
        active = set(active or ())
        if (str(path), n) in active:
            raise ValueError('endpoint primary cycle')
        ok, proof = prior.fs._trace(input_path, n, scratch, active | {(str(path), n)}, recorded=primary_record)
        return ok, dict(path=str(path), n=n, parent=proof, snapshot_sha256=digest,
                        reason='hash-bound Invent endpoint receipt and exact primary input record',
                        ledger=ledger, record=record,
                        primary_start=dict(path=original, n=n, snapshot_sha256=input_sha, retained=str(input_path)),
                        bindings=dict(evidence=str(evidence_file), evidence_sha256=hashlib.sha256(evidence_file.read_bytes()).hexdigest(),
                                      receipt=str(receipt_file), receipt_sha256=extension['worker_receipt_sha256'],
                                      producer=str(producer), producer_sha256=digest,
                                      parent_evidence=str(parent_file), parent_sha256=extension['parent_evidence_sha256'],
                                      primary_ancestry=str(primary_ancestry_file), primary_ancestry_sha256=parent['ancestry_sha256'],
                                      primary_record=record_entry))
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid Invent endpoint primary binding', error=repr(error))


def invent_primary34(path, n, scratch, active=None, recorded=None):
    """Follow the original Invent start before its inherited credit text."""
    if '-r34/' not in str(path) or not path.is_file():
        return None
    record, ledger = (recorded, 'retained source record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict):
        return None
    source = record.get('source', '')
    if not isinstance(source, str) or not source.startswith('invent round34:'):
        return None
    start_match = re.search(r'immutable start (/[^ ;]+\.csv) sha256 ([a-f0-9]{64})', source)
    graph_match = re.search(r'full recorded source (/[^ ;]+\.json)', source)
    receipt_match = re.search(r'; receipt (/[^ ;]+/done\.json)', source)
    if not start_match or not graph_match or not receipt_match or '; parent: ' not in source:
        return None
    try:
        if record.get('n') is not None and int(record['n']) != n:
            raise ValueError('Invent output record count differs')
        retained_parent = json.JSONDecoder().raw_decode(source.split('; parent: ', 1)[1])[0]
        if not isinstance(retained_parent, dict) or not retained_parent.get('proof') or not retained_parent.get('sha256'):
            return None
        start = bound_file34(start_match[1], start_match[2])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        graph_file = Path(graph_match[1])
        graph = json.loads(graph_file.read_text())
        if graph.get('n') != n:
            raise ValueError('Invent primary graph count differs')
        original = Path(graph['path'])
        bound_file34(original, start_match[2])
        origin_file = bound_file34(retained_parent['proof'], retained_parent['sha256'])
        if graph['nodes'][graph['root']]['record'].split(' n=', 1)[0] != str(origin_file):
            raise ValueError('Invent original record differs from its root')
        origin = json.loads(origin_file.read_text())
        if origin.get('n') != n or origin.get('snapshot_sha256') != start_match[2]:
            raise ValueError('Invent original input record differs')
        receipt_file = Path(receipt_match[1]);receipt = json.loads(receipt_file.read_text())
        if (receipt_file.parent.parent != Path(scratch)/'take-invent-r34/work/boxE-raw' or
                receipt_file.parent.name != start.stem or receipt.get('id') != start.stem or
                receipt.get('n') != n or receipt.get('input_sha256') != start_match[2] or
                receipt.get('sha256') != digest or receipt.get('program') != 'invent_barretain_budget30.py'):
            raise ValueError('Invent initial worker receipt differs')
        producer = bound_file34(receipt_file.parent/'final'/f'{n}.csv', digest)
        if any(prior.fs.withdrawn(p, n, scratch) for p in (start, original, producer)):
            raise ValueError('withdrawn Invent primary bytes')
        if any(len(list(csv.DictReader(p.open()))) != n for p in (start, path)):
            raise ValueError('Invent initial packing count differs')
        active = set(active or ())
        if (str(path), n) in active:
            raise ValueError('Invent initial input cycle')
        ok, proof = prior.fs.trace(original, n, scratch, active | {(str(path), n)})
        return ok, dict(path=str(path), n=n, parent=proof, snapshot_sha256=digest,
                        reason='hash-bound Invent initial worker and original primary input', ledger=ledger,
                        record=dict(source=source.split('; parent: ', 1)[0], licence=record.get('licence', '')),
                        primary_start=dict(path=str(start), n=n, snapshot_sha256=start_match[2]),
                        bindings=dict(origin=str(origin_file), origin_sha256=retained_parent['sha256'],
                                      graph=str(graph_file), graph_sha256=hashlib.sha256(graph_file.read_bytes()).hexdigest(),
                                      receipt=str(receipt_file), receipt_sha256=hashlib.sha256(receipt_file.read_bytes()).hexdigest(),
                                      producer=str(producer), producer_sha256=digest))
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid Invent initial primary binding', error=repr(error))


def verify_quench_kick34(path,n,parent,source):
    digest=hashlib.sha256(parent.read_bytes()).hexdigest()
    seed=re.search(r'\bseed (\d+)',source)
    if not seed:raise ValueError('missing quench kick seed')
    job=SCRATCH/f'take-quench-r34/work/jobs/fk-{n}-{digest[:10]}-s{seed[1]}'
    if any(prior.fs.withdrawn(candidate,n,SCRATCH) for candidate in [parent,job/'start.csv',job/'final.csv']):
        raise ValueError('withdrawn quench kick input or producer')
    meta=json.loads((job/'meta.json').read_text());kick=json.loads((job/'kick.json').read_text())
    if meta.get('n')!=n or meta.get('source_file')!=str(job/'start.csv') or meta.get('source_sha256')!=digest:
        raise ValueError('quench kick input binding differs')
    if hashlib.sha256((job/'start.csv').read_bytes()).hexdigest()!=digest:
        raise ValueError('quench kick start bytes differ')
    if kick.get('n')!=n or kick.get('seed')!=int(seed[1]) or kick.get('modes')!='lkick,kick':
        raise ValueError('quench kick identity differs')
    output=hashlib.sha256(path.read_bytes()).hexdigest()
    if hashlib.sha256((job/'final.csv').read_bytes()).hexdigest()!=output:
        raise ValueError('quench kick output differs')
    return dict(job=str(job),input_sha256=digest,output_sha256=output,meta_sha256=hashlib.sha256((job/'meta.json').read_bytes()).hexdigest(),kick_sha256=hashlib.sha256((job/'kick.json').read_bytes()).hexdigest())


@old.prior.lru_cache(maxsize=16)
def public_certificate34(path,n,input_sha256,output_sha256,tool_sha256):
    import forensics_audit34 as audit
    parent=Path(path)
    if hashlib.sha256(parent.read_bytes()).hexdigest()!=input_sha256:
        raise ValueError('changed public certificate input')
    if hashlib.sha256(Path(audit.fine.__file__).read_bytes()).hexdigest()!=tool_sha256:
        raise ValueError('changed public certificate tool')
    _,rows,score,error=audit.fine.work((n,list(csv.DictReader(parent.open()))))
    if rows is None or hashlib.sha256(audit.encoded(rows)).hexdigest()!=output_sha256:
        raise ValueError('public certificate does not reproduce exact output')
    return dict(input_sha256=input_sha256,output_sha256=output_sha256,tool_sha256=tool_sha256,score=score,error=error,exact_certificate_reproduced=True)


def verify_public_transport34(path,n,record):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if record.get('n')!=n or record.get('sha256')!=digest:
        raise ValueError('public transport output binding differs')
    parent=Path(record['source_file'])
    if parent.parent!=SCRATCH/f'take-harvest-r34/work/public-transports/{n}' or not re.fullmatch(r'[a-f0-9]{64}',parent.stem) or prior.fs.withdrawn(parent,n,SCRATCH):
        raise ValueError('public transport producer path differs or is withdrawn')
    parent_sha=hashlib.sha256(parent.read_bytes()).hexdigest()
    if parent_sha!=parent.stem:
        raise ValueError('public transport producer bytes differ')
    sidecar=Path(str(parent)+'.json');produced=json.loads(sidecar.read_text())
    if produced.get('sha256')!=parent_sha or any(record.get(key)!=produced.get(key) for key in ['n','kind','licence','parents']):
        raise ValueError('public transport producer record differs')
    sanitized,bindings=verify_public_metadata34(parent,n,dict(produced,queued_sha256=parent_sha))
    raw=re.search(r'raw file ([^ ;]+\.csv)',record.get('source',''))
    if (record.get('source','').split(';',1)[0]!=produced.get('source','').split(';',1)[0] or
            not raw or raw[1]!=bindings[0]['raw']):
        raise ValueError('public transport source identity differs')
    certificate=None
    if parent_sha==digest:
        verify_public_metadata34(path,n,dict(record,queued_sha256=digest))
    else:
        import forensics_audit34 as audit
        tool_sha=hashlib.sha256(Path(audit.fine.__file__).read_bytes()).hexdigest()
        certificate=public_certificate34(str(parent),n,parent_sha,digest,tool_sha)
    direct=dict(source=produced['source'].split(';',1)[0],licence=produced['licence'])
    return direct,bindings,dict(path=str(parent),n=n,snapshot_sha256=parent_sha,source_proof=str(sidecar),sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest(),certificate=certificate)


def public_transport34(path,n,scratch,active=None,recorded=None):
    if '-r34/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict) or record.get('kind') not in ('fresh-public','reopened-public') or '/take-harvest-r34/work/public-transports/' not in record.get('source_file',''):return None
    try:
        direct,bindings,producer=verify_public_transport34(path,n,record)
        ok,parent=prior._trace_before26(path,n,scratch,active,recorded=direct)
        return ok,dict(path=str(path),n=n,parent=parent,producer=producer,record=direct,ledger=ledger,metadata_bindings=bindings,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reason='exact public transport and raw metadata projection')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid public transport binding',error=repr(error))


def held_export34(path, n, active=None):
    """Bind historical held exports before reading their inherited credits."""
    from forensics_adapters30 import numeric_rows
    path = Path(path)
    active = set(active or ())
    if str(path) in active:
        raise ValueError('held export cycle')
    if prior.fs.withdrawn(path, n, SCRATCH):
        raise ValueError('withdrawn direct held-export path')
    if public.held(path):
        return dict(path=str(path), n=n, reason='submitted own held root',
                    snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    origin = Path(str(path)+'.origin.json')
    if origin.is_file():
        record = json.loads(origin.read_text())
        original = Path(record.get('path', ''))
        if original == path or not original.is_file():
            return None
        parent = held_export34(original, n, active | {str(path)})
        if parent is None:
            return None
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if (record.get('n') != n or record.get('snapshot_sha256') != digest or
                hashlib.sha256(original.read_bytes()).hexdigest() != digest):
            raise ValueError('historical held snapshot bytes differ')
        return dict(path=str(path), n=n, snapshot_sha256=digest, parent=parent,
                    reason='exact snapshot of a verified submitted-row export')
    border = SCRATCH/'take-border-r34/work'
    if path.parent == border/'donors':
        witness = border/'held34'/f'{n}.csv'
        if witness.is_file() and hashlib.sha256(path.read_bytes()).digest() == hashlib.sha256(witness.read_bytes()).digest():
            parent = held_export34(witness, n, active | {str(path)})
            if parent is not None:
                return dict(path=str(path), n=n, snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            parent=parent, reason='exact Border copy of a verified submitted-row export')
    if not (path.parent.name == 'held-inputs' or re.fullmatch(r'held\d*', path.parent.name)):
        return None
    sidecar = Path(str(path)+'.json')
    if not sidecar.is_file():
        return None
    record = json.loads(sidecar.read_text())
    if record.get('public_first') or record.get('kind') in ('fresh-public','reopened-public'):
        return None
    donor = Path(record.get('held_file', ''))
    if not public.held(donor):
        parents = record.get('parents', [])
        if len(parents) != 1 or not isinstance(parents[0], list) or len(parents[0]) != 2:
            return None
        donor, count = Path(parents[0][0]), int(parents[0][1])
        if count != n or not public.held(donor):
            raise ValueError('historical held witness is missing or changed')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if int(record.get('n', 0)) != n:
        raise ValueError('historical held export count differs')
    for key in ('row_sha256',):
        if record.get(key) and record[key] != digest:
            raise ValueError('historical held export hash differs')
    if record.get('held_sha256') and record['held_sha256'] != hashlib.sha256(donor.read_bytes()).hexdigest():
        raise ValueError('historical held file hash differs')
    rows = list(csv.DictReader(path.open()))
    st = donor.stat()
    if len(rows) != n or numeric_digest(numeric_rows(rows)) != held_projection(str(donor), st.st_size, st.st_mtime_ns)[n]:
        raise ValueError('historical held export coordinates differ')
    return dict(path=str(path), n=n, snapshot_sha256=digest,
                reason='exact historical submitted-row export',
                parent=dict(path=str(donor), n=n, reason='submitted own held root'),
                binding=dict(record=str(sidecar), record_sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest()))


_before_held_export34 = prior.fs._trace


def trace_held_export34(path, n, scratch, active=None, recorded=None):
    try:
        result = held_export34(path, n)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid submitted-row export binding', error=repr(error))
    if result is not None:
        return True, result
    return _before_held_export34(path, n, scratch, active, recorded)


prior.fs._trace = trace_held_export34
_before_owned_strict34 = prior.strict_uncached


def strict_owned34(path, n, scratch=SCRATCH):
    try:
        proof = held_export34(path, n)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid submitted-row export binding', error=repr(error))
    if proof is None:
        return _before_owned_strict34(path, n, scratch)
    document = dict(path=str(path), n=n, packing_sha256=proof['snapshot_sha256'], evidence=proof)
    payload = json.dumps(document, sort_keys=True, separators=(',', ':')).encode()
    digest = hashlib.sha256(payload).hexdigest()
    directory = WORK/'ancestry'
    directory.mkdir(exist_ok=True)
    retained = directory/(digest+'.json')
    if not retained.is_file():
        retained.write_bytes(payload)
    return True, dict(reason='exact submitted-row ownership boundary', public_roots=[],
                      ancestry=prior.fs.compact_ancestry(proof, str(retained)), notices=[],
                      seed_policy=dict(status='none', seeds=[]),
                      full_ancestry=dict(path=str(retained), sha256=digest),
                      prvsiyan_shares=[], original_seed_shares=[], hard_source_hits=[])


prior.strict_uncached = strict_owned34


_before_intermediate34 = prior.fs._trace


def k123_intermediate34(path, n, scratch=SCRATCH, active=None, recorded=None):
    """Bind non-winning join donors to their retained numerical producer."""
    root = Path(scratch)/'take-k123-r34'
    path = Path(path)
    if not path.is_file() or (path.parent != root/'near' and recorded is None):
        return None
    record, ledger = (recorded, 'retained record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict) or not record.get('numeric_job'):
        return None
    source = record.get('source', '')
    recipe = re.match(r'^k123_join\.py (\d+)(r?)-(\d+)(r?)-j\d+-\d+-s-?\d+;', source)
    if not recipe or not ('unquenched two-band start' in source or 'non-winning two-band intermediate' in source):
        return None
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if int(record.get('n', 0)) != n or record.get('numeric_csv_sha256') != digest:
            raise ValueError('intermediate output count or bytes differ')
        key = record['numeric_job']
        if not re.fullmatch(r'[A-Za-z0-9_-]+', key):
            raise ValueError('invalid intermediate producer identity')
        folder = 'prejoins31' if 'unquenched two-band start' in source else 'intermediates28'
        producer = root/'work'/folder/key/'numeric.csv'
        if hashlib.sha256(producer.read_bytes()).hexdigest() != digest:
            raise ValueError('intermediate numerical producer differs')
        producer_record = Path(str(producer)+'.json')
        produced = json.loads(producer_record.read_text())
        rebinding = rebound_metadata34(produced, record, scratch) if produced != record else None
        if any(prior.fs.withdrawn(p, n, scratch) for p in [path, producer]):
            raise ValueError('withdrawn intermediate input or producer')
        if len(list(csv.DictReader(path.open()))) != n:
            raise ValueError('intermediate output count differs')
        entries = json.JSONDecoder().raw_decode(source.split('pinned donor ancestry: ', 1)[1])[0]
        if sorted(int(v['n']) for v in entries) != sorted([int(recipe[1]), int(recipe[3])]):
            raise ValueError('intermediate parents differ from join recipe')
        groups = []
        for entry in entries:
            parent = bound_file34(entry['ancestry_file'], entry['ancestry_sha256'])
            groups.append(dict(reason='verified immutable donor group', source_proof=str(parent), sha256=entry['ancestry_sha256']))
        # strict_uncached walks each retained group's complete reference closure.
        return True, dict(path=str(path), n=n, snapshot_sha256=digest, group_proofs=groups,
                          reason='exact non-winning K123 join producer and pinned primary groups',
                          producer=dict(path=str(producer), n=n, snapshot_sha256=digest,
                                        record=str(producer_record), record_sha256=hashlib.sha256(producer_record.read_bytes()).hexdigest()),
                          ledger=ledger, record=record, metadata_rebinding=rebinding)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid non-winning K123 producer binding', error=repr(error))


def trace_intermediate34(path, n, scratch, active=None, recorded=None):
    result = k123_intermediate34(path, n, scratch, active, recorded)
    if result is not None:
        return result
    return _before_intermediate34(path, n, scratch, active, recorded)


prior.fs._trace = trace_intermediate34


_before_twoshort_deep34 = prior.fs._trace


def twoshort_deep34(path, n, scratch=SCRATCH, active=None, recorded=None):
    """Read the primary deep-kick chain before its held row's old credits."""
    path = Path(path)
    root = Path(scratch)/'take-twoshort-r34'
    if not path.is_file():
        return None
    record, ledger = (recorded, 'retained record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict):
        return None
    source = record.get('source', '')
    if not isinstance(source, str) or not source.startswith('twoshort round 34:'):
        return None
    primary = source.split('Start row source:', 1)[0]
    if 'midm_scan.py --modes lkick,kick' not in primary:
        return None
    try:
        if f'the held round 33 a row of n={n} ' not in primary:
            raise ValueError('deep-kick held row identity differs')
        members = re.findall(r'($SCRATCH/bounties-squares/take-twoshort-r34/work/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\)', primary)
        baseline = root/'work/starts'/f'{n}-held33a.csv'
        if not any(Path(name) == baseline for name, digest in members):
            raise ValueError('deep-kick baseline binding missing')
        chain = []
        for name, digest in members:
            member = bound_file34(name, digest)
            if prior.fs.withdrawn(member, n, scratch):
                raise ValueError('withdrawn deep-kick primary member')
            if len(list(csv.DictReader(member.open()))) != n:
                raise ValueError('deep-kick member count differs')
            chain.append(dict(path=name, n=n, snapshot_sha256=digest))
        held = verify_held_payload34(baseline.read_bytes(), n, hashlib.sha256(baseline.read_bytes()).hexdigest())
        if len(list(csv.DictReader(path.open()))) != n:
            raise ValueError('deep-kick output count differs')
        if prior.fs.withdrawn(path, n, scratch):
            raise ValueError('withdrawn deep-kick output')
        return True, dict(path=str(path), n=n, snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          parent=held, chain=chain, ledger=ledger,
                          record=dict(source=primary, licence=record.get('licence', '')),
                          reason='complete primary deep-kick chain from an exact submitted row')
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid primary deep-kick chain', error=repr(error))


def trace_twoshort_deep34(path, n, scratch, active=None, recorded=None):
    result = twoshort_deep34(path, n, scratch, active, recorded)
    if result is not None:
        return result
    return _before_twoshort_deep34(path, n, scratch, active, recorded)


prior.fs._trace = trace_twoshort_deep34


_before_classfill_deep34 = prior.fs._trace


def classfill_deep34(path, n, scratch=SCRATCH, active=None, recorded=None):
    """Bind handed held kicks to the job input and retained finish receipt."""
    path = Path(path)
    record, ledger = (recorded, 'retained record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict) or not str(record.get('source', '')).startswith(('classfill r34 handed-held-deep-kick output', 'classfill r34 fresh-row-family output')):
        return None
    root = Path(scratch)/'take-classfill-r34/work'
    try:
        start_binding = re.search(r'; start (take-classfill-r34/work/starts/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\)', record['source'])
        seed = re.search(r' output of (?:midm|invent) \d+ s seed (\d+)', record['source'])
        if not start_binding or not seed:
            raise ValueError('missing Classfill primary start or seed')
        declared_start = Path(scratch)/start_binding[1]
        expected_job = root/'jobs'/f'y{start_binding[2][:12]}s{seed[1]}.json'
        jobfile = Path(record.get('job', expected_job))
        if jobfile != expected_job or jobfile.parent != root/'jobs':
            raise ValueError('held deep-kick job path differs')
        job = json.loads(jobfile.read_text())
        if job.get('n') != n or job.get('kind') not in ('handed-held-deep-kick', 'fresh-row-family'):
            raise ValueError('held deep-kick job identity differs')
        start = bound_file34(job['input_path'], job['input_sha256'])
        if start != declared_start or job['input_sha256'] != start_binding[2] or start.parent != root/'starts':
            raise ValueError('Classfill primary start path or hash differs')
        bound_file34(job['input_snapshot'], job['input_sha256'])
        if job['kind'] == 'handed-held-deep-kick':
            if start != root/'starts'/f'{n}-held33a.csv':
                raise ValueError('held deep-kick baseline path differs')
            parent = verify_held_payload34(start.read_bytes(), n, job['input_sha256'])
        else:
            sidecar = Path(str(start)+'.json')
            copy = json.loads(sidecar.read_text())
            if copy.get('sha256') != job['input_sha256'] or '; producer record: ' not in copy.get('source', ''):
                raise ValueError('fresh family input record differs')
            active = set(active or ())
            if (str(path),n) in active:
                raise ValueError('fresh family primary cycle')
            retained = dict(source=copy['source'].split('; producer record: ',1)[1], licence=copy.get('licence',''))
            if retained['source'] != job.get('source','').partition(': ')[2]:
                raise ValueError('fresh family retained producer differs from its job')
            ok, parent = prior.fs._trace(start,n,scratch,active | {(str(path),n)},recorded=retained)
            if not ok:
                raise ValueError('fresh family primary input refused: '+parent.get('reason',''))
        receiptfile = Path(record.get('receipt', root/job['host']/'out'/('finish-'+job['tag'])/'quench-receipt.json'))
        if receiptfile.parent.name != 'finish-'+job['tag'] or not receiptfile.is_relative_to(root):
            raise ValueError('held deep-kick finish identity differs')
        receipt = json.loads(receiptfile.read_text())
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if record.get('output_sha256', digest) != digest or receipt.get('output_sha256') != digest or not receipt.get('loop_complete'):
            raise ValueError('held deep-kick output receipt differs')
        producer = bound_file34(receiptfile.parent/f'{n}.csv', digest)
        if any(prior.fs.withdrawn(p, n, scratch) for p in [path, start, producer]):
            raise ValueError('withdrawn held deep-kick input or producer')
        if len(list(csv.DictReader(path.open()))) != n:
            raise ValueError('held deep-kick output count differs')
        return True, dict(path=str(path), n=n, snapshot_sha256=digest, parent=parent,
                          reason='exact Classfill held-kick job and finish receipt', ledger=ledger,
                          bindings=dict(job=str(jobfile), job_sha256=hashlib.sha256(jobfile.read_bytes()).hexdigest(),
                                        receipt=str(receiptfile), receipt_sha256=hashlib.sha256(receiptfile.read_bytes()).hexdigest(),
                                        producer=str(producer)),
                          record=dict(source=record['source'][:start_binding.end()], licence='own submitted ancestry'))
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid Classfill held-kick binding', error=repr(error))


def trace_classfill_deep34(path, n, scratch, active=None, recorded=None):
    result = classfill_deep34(path, n, scratch, active, recorded)
    if result is not None:
        return result
    return _before_classfill_deep34(path, n, scratch, active, recorded)


prior.fs._trace = trace_classfill_deep34


def add_snapshot34(snapshots, entry):
    """Accept repeated identical bindings and refuse any identity conflict."""
    retained = bound_file34(entry['path'], entry['sha256'])
    value = dict(entry, retained=str(retained))
    previous = snapshots.get(entry['original'])
    if previous is not None and previous['sha256'] != value['sha256']:
        raise ValueError('conflicting primary snapshot identity')
    snapshots[entry['original']] = value


def rebound_metadata34(produced, record, scratch=SCRATCH):
    """Reproduce K123's path and proof-hash substitutions without writing files."""
    if {k:v for k,v in produced.items() if k != 'source'} != {k:v for k,v in record.items() if k != 'source'}:
        raise ValueError('rebound producer fields differ')
    source = produced['source']
    pools = re.findall(r'immutable input pool (/[^ ;]+\.csv)', record['source'])
    if len(pools) != 1:
        raise ValueError('missing rebound pool identity')
    pool = Path(pools[0]); directory = pool.parent
    if directory.parent != Path(scratch)/'take-k123-r34/work/prepublish-bindings30':
        raise ValueError('rebound pool is outside the producer binding directory')
    receiptfile = directory/'binding-receipt.json'
    receipt = json.loads(receiptfile.read_text())
    mapping = {}
    for pin in receipt['pins']:
        count = int(pin['donor']); original = Path(pin['origin']); snapshot = Path(pin['csv_snapshot']); alias = Path(pin['alias'])
        if alias.parent != directory:
            raise ValueError('rebound packing alias escapes its directory')
        bound_file34(snapshot, pin['csv_sha256']); bound_file34(alias, pin['csv_sha256'])
        if any(prior.fs.withdrawn(p, count, scratch) for p in [original, snapshot, alias]):
            raise ValueError('withdrawn rebound primary packing')
        mapping[str(original)] = str(alias)
        mapping[str(snapshot)] = str(alias)
        if pin['record_name'].endswith('.json'):
            mapping[pin['record_name']] = str(alias)+'.json'
    for old, new in sorted(mapping.items(), key=lambda pair:-len(pair[0])):
        source = source.replace(old, new)
    for name in set(re.findall(r'$DATA/[^\s,;<>"\\]+\.csv', source)):
        old = Path(name)
        if name.startswith(str(directory)) or '/take-k123-' not in name or '/work/' not in name or not (old.stem == old.parent.name or old.stem.startswith('pool-')):
            continue
        digest = hashlib.sha256(old.read_bytes()).hexdigest()
        sibling = Path(str(old)+'.json') if Path(str(old)+'.json').exists() else old.with_suffix('.json')
        rebound = Path(receipt['proofs'].get(str(sibling), str(sibling)))
        if rebound == sibling:
            continue
        body = rebound.read_bytes()
        alias = directory/f'pool-{digest}-{hashlib.sha256(body).hexdigest()[:16]}.csv'
        bound_file34(alias, digest)
        if Path(str(alias)+'.json').read_bytes() != body:
            raise ValueError('rebound pool metadata differs')
        source = source.replace(name, str(alias))
    for old, new in receipt['proofs'].items():
        if old == new or old not in source:
            continue
        oldpath, newpath = Path(old), Path(new)
        if re.fullmatch(r'[a-f0-9]{64}', newpath.stem):
            bound_file34(newpath, newpath.stem)
        source = source.replace(old, new)
        if re.fullmatch(r'[a-f0-9]{64}', oldpath.stem):
            bound_file34(oldpath, oldpath.stem)
            source = re.sub(r'(?<![\w/.-])'+re.escape(oldpath.stem)+r'(?![\w.-])', newpath.stem, source)
    if source != record['source']:
        raise ValueError('rebound source substitutions do not reproduce metadata')
    return dict(receipt=str(receiptfile), receipt_sha256=hashlib.sha256(receiptfile.read_bytes()).hexdigest(), exact_metadata_reproduced=True)


def backlog_run34(path,n,baseline,baseline_sha,scratch=SCRATCH,active=None):
    """Bind a saved Backlog leg to its completed run and ultimate byte copy."""
    path=Path(path);baseline=Path(baseline);active=set(active or ())
    if prior.fs.withdrawn(path,n,scratch):raise ValueError('withdrawn Backlog run path')
    if path==baseline:
        bound_file34(path,baseline_sha)
        return dict(path=str(path),n=n,snapshot_sha256=baseline_sha,reason='exact initial Backlog byte copy')
    root=Path(scratch)/'take-backlog-r34/work/runs'
    if path.name!=f'{n}.csv' or path.parent.name!='final' or path.parent.parent.parent!=root:
        raise ValueError('Backlog leg path is outside its run')
    directory=path.parent.parent
    if str(directory) in active:raise ValueError('Backlog leg cycle')
    jobfile=directory/'job.json';donefile=directory/'done.json'
    job=json.loads(jobfile.read_text());done=json.loads(donefile.read_text())
    if job.get('rid')!=directory.name or done.get('rid')!=directory.name or job.get('n')!=n or done.get('n')!=n or done.get('rc')!=0 or not done.get('quench_from_certified'):
        raise ValueError('Backlog leg run identity or completion differs')
    start=Path(job['start'])
    if any(prior.fs.withdrawn(p,n,scratch) for p in [path,start]):
        raise ValueError('withdrawn Backlog leg input or output')
    import forensics_rect as rectangle
    rows=rectangle.layouts(path)
    if n not in rows:raise ValueError('Backlog leg count differs')
    side,_=rectangle.fc.frame(rows[n]);score=side/math.sqrt(n)-1
    reported=float(done['finals'][str(n)]['new'])
    if abs(score-reported)>5e-12:raise ValueError('Backlog leg output differs from receipt score')
    parent=backlog_run34(start,n,baseline,baseline_sha,scratch,active|{str(directory)})
    return dict(path=str(path),n=n,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),parent=parent,
                reason='completed Backlog leg bound to its primary run input',
                bindings=dict(job=str(jobfile),job_sha256=hashlib.sha256(jobfile.read_bytes()).hexdigest(),done=str(donefile),done_sha256=hashlib.sha256(donefile.read_bytes()).hexdigest()))
