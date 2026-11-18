"""Round 33 changed-window admission with pinned held boundaries."""
from pathlib import Path
import csv,hashlib,json,time,re
import forensics_round32 as old
from forensics_round31 import *
prior=old.prior
public=old.public
WORK=SCRATCH/'take-forensics-r33/work'
LOADED_SHA33=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
prior.WORK=WORK
prior.MAC='$SCRATCH/squares-forensics-r33'
public.WORK=WORK

def base(scratch,work):
    return {int(r['n']):float(r['bar']) for r in csv.DictReader(open(Path(scratch)/'round33-briefs/bar33.tsv'),delimiter='\t')}
prior.base=base

def admission_priority(path):
    fresh='-r33/' in str(path)
    rank=(0 if path.parent.name.startswith('take-') else 1 if '/work/interior/' in str(path) else 3 if '/work/held-inputs/' in str(path) else 2) if fresh else 4
    order=[488,292,530,585,866,970,909,971,973,864,577,485,999]
    n=int(path.stem) if path.stem.isdigit() else 0
    held_order=order.index(n) if rank==3 and n in order else len(order)
    if str(path) in priority_inputs33():rank=-1
    return rank,held_order,-path.stat().st_mtime
prior.admission_priority=admission_priority

_old_trace=prior.fs._trace

def trace33(path,n,scratch,active=None,recorded=None):
    path=Path(path)
    if public.held(path):
        return True,dict(path=str(path),n=n,reason='submitted own held root under round33 rule2',snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    sidecar=Path(str(path)+'.json')
    if path.parent==WORK/'held-inputs' and sidecar.exists():
        from forensics_adapters30 import numeric_rows
        rec=json.loads(sidecar.read_text());donor=Path(rec['held_file'])
        if rec.get('kind')!='round33-exact-held-export' or rec['n']!=n or not public.held(donor) or hashlib.sha256(donor.read_bytes()).hexdigest()!=rec['held_sha256'] or hashlib.sha256(path.read_bytes()).hexdigest()!=rec['sha256']:
            return False,dict(path=str(path),n=n,reason='changed round33 held binding')
        st=donor.stat()
        if old.old._numeric_digest(numeric_rows(list(csv.DictReader(path.open()))))!=old.old._held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
            return False,dict(path=str(path),n=n,reason='held coordinates differ')
        return True,dict(path=str(path),n=n,record=rec,parent=dict(path=str(donor),n=n,reason='submitted own held root'),snapshot_sha256=rec['sha256'],reason='exact round33 own held export')
    transported=public_transport33(path,n,scratch,active,recorded)
    if transported is not None:return transported
    transported=public_cert_copy33(path,n,scratch,active,recorded)
    if transported is not None:return transported
    chain=twoshort_held_chain33(path,n,scratch,active,recorded)
    if chain is not None:return chain
    modules=stair_modules33(path,n,scratch,active,recorded)
    if modules is not None:return modules
    primary=primary_quench33(path,n,scratch,active,recorded)
    if primary is not None:return primary
    followed=backlog_primary33(path,n,scratch,active,recorded)
    if followed is not None:return followed
    fetched=public_queue33(path,n,scratch,active,recorded)
    if fetched is not None:return fetched
    peer=peer_held33(path,n,scratch)
    if peer is not None:return peer
    return _old_trace(path,n,scratch,active,recorded)
prior.fs._trace=trace33

_original_withdrawn=prior.fs.withdrawn

@old.prior.lru_cache(maxsize=4)
def _withdrawal_lines(tokens):
    return tuple(l for path,size,mtime in tokens for l in Path(path).read_text().splitlines() if 'WITHDRAW' in l)

def withdrawal_lines():
    paths=[SCRATCH/f'handoff-r{rnd}.log' for rnd in (31,32,33)]
    return _withdrawal_lines(tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths))

def withdrawn33(path,n,scratch):
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

prior.fs.withdrawn=withdrawn33
_source_hash=prior.source_policy_hash

def source_policy_hash():
    return hashlib.sha256((_source_hash()+LOADED_SHA33+'\n'.join(withdrawal_lines())).encode()).hexdigest()
prior.source_policy_hash=source_policy_hash

def admit33(files, scratch, work):
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
        if path.parent.name in ('held','held33','held-inputs') and path.parent != WORK/'held-inputs':
            continue
        # A full walk budget must not hide cleared files later in the list.
        is_interior = '/take-forensics-r33/work/interior/' in str(path)
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
        is_fresh = '-r33/' in str(path) and not is_held
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

prior.admit=admit33
admit=admit33

# Use the assembler's frozen round31 measurement for every public descendant.
import importlib.util
_spec33=importlib.util.spec_from_file_location('forensics_assembler33',SCRATCH/'take-assemble-r31/scripts/share31.py')
_assembler33=importlib.util.module_from_spec(_spec33)
_spec33.loader.exec_module(_assembler33)
_assembler33.TOLS=(1e-6,1e-3,1e-2)
public_policy31._assembler=_assembler33


def peer_held33(path,n,scratch):
    """Verify peer held exports without reading inherited public history."""
    held_start=path.parent.name=='starts' and path.name==str(n)+'-held32a.csv'
    if '-r33/work/' not in str(path) or (path.parent.name not in ('held','held33','held-inputs') and not held_start) or not path.is_file():return None
    record,ledger=prior.fs.record(path,n)
    if not isinstance(record,dict):
        log=Path(scratch)/'handoff-r33.log'
        declarations=[line for line in log.read_text().splitlines() if str(path) in line and 'held' in line.lower()]
        if not declarations:return None
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if not any(any(digest.startswith(h) for h in re.findall(r'\b[a-f0-9]{12,64}\b',line)) for line in declarations):return None
        donor=Path(scratch)/'gather/round32-2026-11-16a.csv'
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
    if len(rows)!=n or old.old._numeric_digest(numeric_rows(rows))!=old.old._held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
        return False,dict(reason='peer held coordinates differ',path=str(path),n=n)
    return True,dict(path=str(path),n=n,snapshot_sha256=digest,reason='exact round33 peer held projection',parent=dict(path=str(donor),n=n,reason='submitted own held root'),producer_ledger=ledger)


_check_parts33=old._check_parts32

def check_parts(parts,scratch=SCRATCH,fresh=False):
    result=_check_parts33(parts,scratch,fresh=fresh)
    if not result[0]:
        blob=json.dumps(dict(parts=parts,evidence=result[1]),sort_keys=True).encode()
        directory=WORK/'source-refusals33';directory.mkdir(exist_ok=True)
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
def _public_projection33(path,size,mtime,n):
    from forensics_adapters30 import numeric_rows
    rows=[]
    with open(path) as stream:
        for row in csv.DictReader(stream):
            count=int(str(row.get('n',row.get('id','').split('_')[0])).lstrip('s'))
            if count==n:rows.append(row)
    if len(rows)!=n:raise ValueError('public raw count differs')
    return old.old._numeric_digest(numeric_rows(rows))


def verify_public_metadata33(path,n,record):
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
    if old.old._numeric_digest(numeric_rows(list(csv.DictReader(open(path)))))!=_public_projection33(str(raw),st.st_size,st.st_mtime_ns,n):raise ValueError('queued public coordinates differ from raw')
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
    sanitized=dict(record);sanitized.pop('parents');sanitized.pop('original',None);sanitized['metadata_parents33']=parents
    return sanitized,bindings


def public_queue33(path,n,scratch,active,recorded):
    if recorded is not None or path.parent!=Path(scratch)/'take-harvest-r33/work/inputs':return None
    sidecar=Path(str(path)+'.json')
    if not sidecar.exists():return None
    record=json.loads(sidecar.read_text())
    if record.get('kind') not in ('fresh-public','reopened-public') or not record.get('parents') or not all(isinstance(v,dict) for v in record['parents']):return None
    try:
        sanitized,bindings=verify_public_metadata33(path,n,record)
        ok,parent=prior._trace_before26(path,n,scratch,active,recorded=sanitized)
        return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=record['queued_sha256'],metadata_bindings=bindings,reason='hash-bound public metadata parents and exact raw projection')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid public metadata or raw binding',error=repr(error))


def primary_quench33(path,n,scratch,active,recorded=None):
    """Read the one declared quench input before inherited notice history."""
    if '-r33/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'explicit retained record') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith(('quench lane: one fq quench ','quench lane kick: ')):return None
    match=re.match(r'^quench lane(?:: one fq quench | kick: ).*? of (take-quench-r33/work/starts/[^ ()]+\.csv) \(a byte copy, sha256 ([a-f0-9]{16,64})',source)
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
            producer=verify_quench_kick33(path,n,parent,source)
        parent_record,_=prior.fs.record(parent,n)
        if isinstance(parent_record,dict) and parent_record.get('source','').startswith(f'held n = {n} of round 32 '):
            proof=verify_held_payload33(parent.read_bytes(),n,hashlib.sha256(parent.read_bytes()).hexdigest());ok=True
        else:
            ok,proof=prior.fs.trace(parent,n,scratch,active|{(str(path),n)})
        return ok,dict(path=str(path),n=n,parent=proof,producer=producer,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),record=dict(record,source=source.split(' | recorded source of the start:',1)[0]),ledger=ledger,reason='hash-bound primary input of one fq quench or kick')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid primary quench producer',error=repr(error))


def public_cert_copy33(path,n,scratch,active,recorded=None):
    if '-r33/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict) or record.get('kind') not in ('fresh-public','reopened-public') or not record.get('certified_from'):return None
    parent=Path(record['certified_from'])
    if parent.parent!=Path(scratch)/'take-harvest-r33/work/inputs':return None
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    input_sha=record.get('certified_input_sha256')
    if int(record.get('n',0))!=n or not parent.is_file() or hashlib.sha256(parent.read_bytes()).hexdigest()!=input_sha:
        return False,dict(path=str(path),n=n,reason='public certified-copy input bytes differ')
    producer=None
    if digest!=input_sha:
        original=Path(record.get('path',''))
        if original.parent!=Path(scratch)/'take-harvest-r33/near' or not original.name.startswith(str(n)+'-') or not original.is_file():
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


def stair_modules33(path,n,scratch,active,recorded=None):
    if '-r33/' not in str(path) or not path.is_file():return None
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
def _priority_inputs33(size,mtime):
    return frozenset(json.loads((WORK/'priority-inputs33.json').read_text()))

def priority_inputs33():
    path=WORK/'priority-inputs33.json'
    if not path.exists():return frozenset()
    st=path.stat();return _priority_inputs33(st.st_size,st.st_mtime_ns)


_declared_before33=prior.fs.declared_withdrawal

def declared_withdrawal33(value,scratch):
    """Keep a withdrawn ancestor pinned even after its live path changes."""
    if _declared_before33(value,scratch):return True
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
prior.fs.declared_withdrawal=declared_withdrawal33


def twoshort_held_chain33(path,n,scratch,active,recorded=None):
    """Verify every declared member of an own held lkick chain."""
    if '-r33/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('twoshort round 33:'):return None
    primary=source.split('Held row source:',1)[0]
    if 'invent_rest.py lkick' not in primary or ('from the held round 32 a row of n='+str(n)) not in primary:return None
    owned=Path(scratch)/'take-twoshort-r33/work'
    members=re.findall(r'($SCRATCH/bounties-squares/take-twoshort-r33/work/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\)',primary)
    baseline=owned/'starts'/(str(n)+'-held32a.csv')
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


def backlog_primary33(path,n,scratch,active,recorded=None):
    """Bind a Backlog start to the source row retained by its producer."""
    if '-r33/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('backlog lane:'):return None
    match=re.match(r'^backlog lane: .*?from the byte copy ($SCRATCH/bounties-squares/take-backlog-r33/work/starts/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\), taken at queue time from the certified round 33 take ([^;]+); its take\.tsv row: (.+)$',source,re.S)
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
    inherited=dict(source=match[4],licence=record.get('licence',''))
    ok,proof=prior.fs._trace(parent,n,scratch,active|{(str(path),n)},recorded=inherited)
    return ok,dict(path=str(path),n=n,parent=proof,record=dict(source=source[:match.start(4)],licence=record.get('licence','')),ledger=ledger,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),primary_start=dict(path=str(parent),n=n,snapshot_sha256=match[2]),reason='exact backlog start with its retained take row')


def verify_held_payload33(payload, n, expected):
    """Bind a retained start to the exact submitted row, including its count."""
    import io
    from forensics_adapters30 import numeric_rows
    if not re.fullmatch(r'[a-f0-9]{12,64}', expected) or not hashlib.sha256(payload).hexdigest().startswith(expected):
        raise ValueError('held start bytes differ')
    held = SCRATCH/'gather/round32-2026-11-16a.csv'
    if not public.held(held):
        raise ValueError('submitted held witness differs')
    rows = list(csv.DictReader(io.StringIO(payload.decode())))
    if len(rows) != n or any(int(row.get('n', n)) != n for row in rows):
        raise ValueError('held start count differs')
    st = held.stat()
    if old.old._numeric_digest(numeric_rows(rows)) != old.old._held_projection(str(held), st.st_size, st.st_mtime_ns)[n]:
        raise ValueError('held start coordinates differ')
    return dict(path=str(held), n=n, reason='submitted own held root',
                snapshot_sha256=public.file_sha(str(held), st.st_size, st.st_mtime_ns))


def rebuild_primary33(path, n, scratch, active=None, recorded=None):
    if '-r33/' not in str(path) or not path.is_file():
        return None
    record, ledger = (recorded, 'retained source record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict):
        return None
    source = record.get('source', '')
    if not isinstance(source, str) or not source.startswith('rebuild lane round '):
        return None
    match = re.search(r' of (take-rebuild-r33/work/held33/(\d+)\.csv) \(sha256 ([a-f0-9]{12,64}), byte copy (take-rebuild-r33/work/pins/[^ ()]+\.csv)\)', source)
    if not match:
        return None
    try:
        if int(match[2]) != n:
            raise ValueError('rebuild source count differs')
        pin = Path(scratch)/match[4]
        if prior.fs.withdrawn(pin, n, scratch):
            raise ValueError('withdrawn rebuild primary bytes')
        parent = verify_held_payload33(pin.read_bytes(), n, match[3])
        if len(list(csv.DictReader(path.open()))) != n:
            raise ValueError('rebuild output count differs')
        return True, dict(path=str(path), n=n, parent=parent, primary_start=str(pin),
                          primary_sha256=hashlib.sha256(pin.read_bytes()).hexdigest(),
                          snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                          record=dict(source=source.split('. The start:', 1)[0], licence=record.get('licence', '')),
                          ledger=ledger, reason='exact rebuild primary start at submitted held32a boundary')
    except (OSError, ValueError, KeyError, TypeError) as error:
        return False, dict(path=str(path), n=n, reason='invalid rebuild held primary binding', error=repr(error))


_trace_before_rebuild33 = prior.fs._trace


def trace_primary33(path, n, scratch, active=None, recorded=None):
    path = Path(path)
    # Every direct-start withdrawal remains effective before ownership adapters.
    if prior.fs.withdrawn(path, n, scratch):
        return False, dict(path=str(path), n=n, reason='explicit byte-pinned withdrawal')
    result = rebuild_primary33(path, n, scratch, active, recorded)
    if result is not None:
        return result
    result = invent_endpoint33(path, n, scratch, active, recorded)
    if result is not None:
        return result
    result = invent_primary33(path, n, scratch, active, recorded)
    if result is not None:
        return result
    return _trace_before_rebuild33(path, n, scratch, active, recorded)


prior.fs._trace = trace_primary33


def bound_file33(path, expected):
    path = Path(path)
    st = path.stat()
    if public.file_sha(str(path), st.st_size, st.st_mtime_ns) != expected:
        raise ValueError('changed retained proof file: '+str(path))
    return path


def invent_endpoint33(path, n, scratch, active=None, recorded=None):
    """Read an endpoint through its receipt and the pinned primary input record."""
    if '-r33/' not in str(path) or not path.is_file():
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
        ancestry_file = bound_file33(packet['ancestry'], packet['ancestry_sha256'])
        if str(ancestry_file) != record.get('ancestry_file'):
            raise ValueError('endpoint ancestry path differs')
        ancestry = json.loads(ancestry_file.read_text())
        extension = packet['extension']
        receipt_file = bound_file33(extension['worker_receipt'], extension['worker_receipt_sha256'])
        receipt = json.loads(receipt_file.read_text())
        root_record = ancestry['nodes'][ancestry['root']]
        citation = str(receipt_file)+' sha256 '+extension['worker_receipt_sha256']
        if (receipt_file.name != 'done.json' or
                receipt_file.parent.parent != Path(scratch)/'take-invent-r33/work/boxE-raw' or
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
        bound_file33(producer, digest)
        if prior.fs.withdrawn(producer, n, scratch):
            raise ValueError('withdrawn endpoint producer bytes')
        parent_file = bound_file33(extension['parent_evidence'], extension['parent_evidence_sha256'])
        parent = json.loads(parent_file.read_text())
        input_sha = receipt['input_sha256']
        if parent.get('n') != n or parent.get('input_sha256') != input_sha:
            raise ValueError('endpoint primary input differs')
        primary_ancestry_file = bound_file33(parent['ancestry'], parent['ancestry_sha256'])
        primary_ancestry = json.loads(primary_ancestry_file.read_text())
        if primary_ancestry.get('n') != n:
            raise ValueError('endpoint primary ancestry count differs')
        snapshots = {}
        for entry in parent['snapshots']:
            retained = bound_file33(entry['path'], entry['sha256'])
            if entry['original'] in snapshots:
                raise ValueError('duplicate primary snapshot identity')
            snapshots[entry['original']] = dict(entry, retained=str(retained))
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


def invent_primary33(path, n, scratch, active=None, recorded=None):
    """Follow the original Invent start before its inherited credit text."""
    if '-r33/' not in str(path) or not path.is_file():
        return None
    record, ledger = (recorded, 'retained source record') if recorded is not None else prior.fs.record(path, n)
    if not isinstance(record, dict):
        return None
    source = record.get('source', '')
    if not isinstance(source, str) or not source.startswith('invent round33:'):
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
        start = bound_file33(start_match[1], start_match[2])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        graph_file = Path(graph_match[1])
        graph = json.loads(graph_file.read_text())
        if graph.get('n') != n:
            raise ValueError('Invent primary graph count differs')
        original = Path(graph['path'])
        bound_file33(original, start_match[2])
        origin_file = bound_file33(retained_parent['proof'], retained_parent['sha256'])
        if graph['nodes'][graph['root']]['record'].split(' n=', 1)[0] != str(origin_file):
            raise ValueError('Invent original record differs from its root')
        origin = json.loads(origin_file.read_text())
        if origin.get('n') != n or origin.get('snapshot_sha256') != start_match[2]:
            raise ValueError('Invent original input record differs')
        receipt_file = Path(receipt_match[1]);receipt = json.loads(receipt_file.read_text())
        if (receipt_file.parent.parent != Path(scratch)/'take-invent-r33/work/boxE-raw' or
                receipt_file.parent.name != start.stem or receipt.get('id') != start.stem or
                receipt.get('n') != n or receipt.get('input_sha256') != start_match[2] or
                receipt.get('sha256') != digest or receipt.get('program') != 'invent_barretain_budget30.py'):
            raise ValueError('Invent initial worker receipt differs')
        producer = bound_file33(receipt_file.parent/'final'/f'{n}.csv', digest)
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


def verify_quench_kick33(path,n,parent,source):
    digest=hashlib.sha256(parent.read_bytes()).hexdigest()
    seed=re.search(r'\bseed (\d+)',source)
    if not seed:raise ValueError('missing quench kick seed')
    job=SCRATCH/f'take-quench-r33/work/jobs/fk-{n}-{digest[:10]}-s{seed[1]}'
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
def public_certificate33(path,n,input_sha256,output_sha256,tool_sha256):
    import forensics_audit33 as audit
    parent=Path(path)
    if hashlib.sha256(parent.read_bytes()).hexdigest()!=input_sha256:
        raise ValueError('changed public certificate input')
    if hashlib.sha256(Path(audit.fine.__file__).read_bytes()).hexdigest()!=tool_sha256:
        raise ValueError('changed public certificate tool')
    _,rows,score,error=audit.fine.work((n,list(csv.DictReader(parent.open()))))
    if rows is None or hashlib.sha256(audit.encoded(rows)).hexdigest()!=output_sha256:
        raise ValueError('public certificate does not reproduce exact output')
    return dict(input_sha256=input_sha256,output_sha256=output_sha256,tool_sha256=tool_sha256,score=score,error=error,exact_certificate_reproduced=True)


def verify_public_transport33(path,n,record):
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if record.get('n')!=n or record.get('sha256')!=digest:
        raise ValueError('public transport output binding differs')
    parent=Path(record['source_file'])
    if parent.parent!=SCRATCH/f'take-harvest-r33/work/public-transports/{n}' or not re.fullmatch(r'[a-f0-9]{64}',parent.stem) or prior.fs.withdrawn(parent,n,SCRATCH):
        raise ValueError('public transport producer path differs or is withdrawn')
    parent_sha=hashlib.sha256(parent.read_bytes()).hexdigest()
    if parent_sha!=parent.stem:
        raise ValueError('public transport producer bytes differ')
    sidecar=Path(str(parent)+'.json');produced=json.loads(sidecar.read_text())
    if produced.get('sha256')!=parent_sha or any(record.get(key)!=produced.get(key) for key in ['n','kind','licence','parents']):
        raise ValueError('public transport producer record differs')
    sanitized,bindings=verify_public_metadata33(parent,n,dict(produced,queued_sha256=parent_sha))
    raw=re.search(r'raw file ([^ ;]+\.csv)',record.get('source',''))
    if (record.get('source','').split(';',1)[0]!=produced.get('source','').split(';',1)[0] or
            not raw or raw[1]!=bindings[0]['raw']):
        raise ValueError('public transport source identity differs')
    certificate=None
    if parent_sha==digest:
        verify_public_metadata33(path,n,dict(record,queued_sha256=digest))
    else:
        import forensics_audit33 as audit
        tool_sha=hashlib.sha256(Path(audit.fine.__file__).read_bytes()).hexdigest()
        certificate=public_certificate33(str(parent),n,parent_sha,digest,tool_sha)
    direct=dict(source=produced['source'].split(';',1)[0],licence=produced['licence'])
    return direct,bindings,dict(path=str(parent),n=n,snapshot_sha256=parent_sha,source_proof=str(sidecar),sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest(),certificate=certificate)


def public_transport33(path,n,scratch,active=None,recorded=None):
    if '-r33/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict) or record.get('kind') not in ('fresh-public','reopened-public') or '/take-harvest-r33/work/public-transports/' not in record.get('source_file',''):return None
    try:
        direct,bindings,producer=verify_public_transport33(path,n,record)
        ok,parent=prior._trace_before26(path,n,scratch,active,recorded=direct)
        return ok,dict(path=str(path),n=n,parent=parent,producer=producer,record=direct,ledger=ledger,metadata_bindings=bindings,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reason='exact public transport and raw metadata projection')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid public transport binding',error=repr(error))
