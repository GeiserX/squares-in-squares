"""Round 32 changed-window admission with pinned held boundaries."""
from pathlib import Path
import csv,hashlib,json,time,re
import forensics_round31 as old
from forensics_round31 import *
prior=old.prior
public=old.public
WORK=SCRATCH/'take-forensics-r32/work'
LOADED_SHA32=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
prior.WORK=WORK
prior.MAC='$SCRATCH/squares-forensics-r32'
public.WORK=WORK

def base(scratch,work):
    return {int(r['n']):float(r['bar']) for r in csv.DictReader(open(Path(scratch)/'round32-briefs/bar32.tsv'),delimiter='\t')}
prior.base=base

def admission_priority(path):
    fresh='-r32/' in str(path)
    rank=(0 if path.parent.name.startswith('take-') else 1 if '/work/interior/' in str(path) else 3 if '/work/held-inputs/' in str(path) else 2) if fresh else 4
    order=[686,464,454,509,741,852,791,548,604,989,971,818,654,864]
    n=int(path.stem) if path.stem.isdigit() else 0
    held_order=order.index(n) if rank==3 and n in order else len(order)
    if str(path) in priority_inputs32():rank=-1
    return rank,held_order,-path.stat().st_mtime
prior.admission_priority=admission_priority

_old_trace=prior.fs._trace

def trace32(path,n,scratch,active=None,recorded=None):
    path=Path(path)
    if public.held(path):
        return True,dict(path=str(path),n=n,reason='submitted own held root under round32 rule2',snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    sidecar=Path(str(path)+'.json')
    if path.parent==WORK/'held-inputs' and sidecar.exists():
        from forensics_adapters30 import numeric_rows
        rec=json.loads(sidecar.read_text());donor=Path(rec['held_file'])
        if rec.get('kind')!='round32-exact-held-export' or rec['n']!=n or not public.held(donor) or hashlib.sha256(donor.read_bytes()).hexdigest()!=rec['held_sha256'] or hashlib.sha256(path.read_bytes()).hexdigest()!=rec['sha256']:
            return False,dict(path=str(path),n=n,reason='changed round32 held binding')
        st=donor.stat()
        if old._numeric_digest(numeric_rows(list(csv.DictReader(path.open()))))!=old._held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
            return False,dict(path=str(path),n=n,reason='held coordinates differ')
        return True,dict(path=str(path),n=n,record=rec,parent=dict(path=str(donor),n=n,reason='submitted own held root'),snapshot_sha256=rec['sha256'],reason='exact round32 own held export')
    transported=public_cert_copy32(path,n,scratch,active,recorded)
    if transported is not None:return transported
    chain=twoshort_held_chain32(path,n,scratch,active,recorded)
    if chain is not None:return chain
    modules=stair_modules32(path,n,scratch,active,recorded)
    if modules is not None:return modules
    primary=primary_quench32(path,n,scratch,active,recorded)
    if primary is not None:return primary
    followed=backlog_primary32(path,n,scratch,active,recorded)
    if followed is not None:return followed
    fetched=public_queue32(path,n,scratch,active,recorded)
    if fetched is not None:return fetched
    peer=peer_held32(path,n,scratch)
    if peer is not None:return peer
    return _old_trace(path,n,scratch,active,recorded)
prior.fs._trace=trace32

_original_withdrawn=prior.fs.withdrawn

@old.prior.lru_cache(maxsize=4)
def _withdrawal_lines(tokens):
    return tuple(l for path,size,mtime in tokens for l in Path(path).read_text().splitlines() if 'WITHDRAW' in l)

def withdrawal_lines():
    paths=[SCRATCH/f'handoff-r{rnd}.log' for rnd in (31,32)]
    return _withdrawal_lines(tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in paths))

def withdrawn32(path,n,scratch):
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

prior.fs.withdrawn=withdrawn32
_source_hash=prior.source_policy_hash

def source_policy_hash():
    return hashlib.sha256((_source_hash()+LOADED_SHA32+'\n'.join(withdrawal_lines())).encode()).hexdigest()
prior.source_policy_hash=source_policy_hash

def admit32(files, scratch, work):
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
        # A full walk budget must not hide cleared files later in the list.
        is_interior = '/take-forensics-r32/work/interior/' in str(path)
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
        is_fresh = '-r32/' in str(path) and not is_held
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

prior.admit=admit32
admit=admit32

# Use the assembler's frozen round31 measurement for every public descendant.
import importlib.util
_spec32=importlib.util.spec_from_file_location('forensics_assembler32',SCRATCH/'take-assemble-r31/scripts/share31.py')
_assembler32=importlib.util.module_from_spec(_spec32)
_spec32.loader.exec_module(_assembler32)
_assembler32.TOLS=(1e-6,1e-3,1e-2)
public_policy31._assembler=_assembler32


def peer_held32(path,n,scratch):
    """Verify peer held exports without reading inherited public history."""
    held_start=path.parent.name=='starts' and path.name==str(n)+'-held31b.csv'
    if '-r32/work/' not in str(path) or (path.parent.name not in ('held','held32','held-inputs') and not held_start) or not path.is_file():return None
    record,ledger=prior.fs.record(path,n)
    if not isinstance(record,dict):
        log=Path(scratch)/'handoff-r32.log'
        declarations=[line for line in log.read_text().splitlines() if str(path) in line and 'held' in line.lower()]
        if not declarations:return None
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        if not any(any(digest.startswith(h) for h in re.findall(r'\b[a-f0-9]{12,64}\b',line)) for line in declarations):return None
        donor=Path(scratch)/'gather/round31-2026-11-16b.csv'
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
    if len(rows)!=n or old._numeric_digest(numeric_rows(rows))!=old._held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
        return False,dict(reason='peer held coordinates differ',path=str(path),n=n)
    return True,dict(path=str(path),n=n,snapshot_sha256=digest,reason='exact round32 peer held projection',parent=dict(path=str(donor),n=n,reason='submitted own held root'),producer_ledger=ledger)


_check_parts32=prior.check_parts

def check_parts(parts,scratch=SCRATCH,fresh=False):
    result=_check_parts32(parts,scratch,fresh=fresh)
    if not result[0]:
        blob=json.dumps(dict(parts=parts,evidence=result[1]),sort_keys=True).encode()
        directory=WORK/'source-refusals32';directory.mkdir(exist_ok=True)
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
def _public_projection32(path,size,mtime,n):
    from forensics_adapters30 import numeric_rows
    rows=[]
    with open(path) as stream:
        for row in csv.DictReader(stream):
            count=int(str(row.get('n',row.get('id','').split('_')[0])).lstrip('s'))
            if count==n:rows.append(row)
    if len(rows)!=n:raise ValueError('public raw count differs')
    return old._numeric_digest(numeric_rows(rows))


def verify_public_metadata32(path,n,record):
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
    if old._numeric_digest(numeric_rows(list(csv.DictReader(open(path)))))!=_public_projection32(str(raw),st.st_size,st.st_mtime_ns,n):raise ValueError('queued public coordinates differ from raw')
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
    sanitized=dict(record);sanitized.pop('parents');sanitized.pop('original',None);sanitized['metadata_parents32']=parents
    return sanitized,bindings


def public_queue32(path,n,scratch,active,recorded):
    if recorded is not None or path.parent!=Path(scratch)/'take-harvest-r32/work/inputs':return None
    sidecar=Path(str(path)+'.json')
    if not sidecar.exists():return None
    record=json.loads(sidecar.read_text())
    if record.get('kind') not in ('fresh-public','reopened-public') or not record.get('parents') or not all(isinstance(v,dict) for v in record['parents']):return None
    try:
        sanitized,bindings=verify_public_metadata32(path,n,record)
        ok,parent=prior._trace_before26(path,n,scratch,active,recorded=sanitized)
        return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=record['queued_sha256'],metadata_bindings=bindings,reason='hash-bound public metadata parents and exact raw projection')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(path=str(path),n=n,reason='invalid public metadata or raw binding',error=repr(error))


def primary_quench32(path,n,scratch,active,recorded=None):
    """Read the one declared quench input before inherited notice history."""
    if '-r32/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'explicit retained record') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('quench lane: one fq quench '):return None
    match=re.match(r'^quench lane: one fq quench .*? of (take-quench-r32/work/starts/[^ ()]+\.csv) \(a byte copy, sha256 ([a-f0-9]{16,64})',source)
    if not match:return False,dict(path=str(path),n=n,reason='unreadable primary quench input')
    parent=Path(scratch)/match[1]
    if parent==path:return False,dict(path=str(path),n=n,reason='primary quench input cycle')
    count=re.match(r'(\d+)',parent.name)
    if not count or int(count[1])!=n or not parent.is_file() or not hashlib.sha256(parent.read_bytes()).hexdigest().startswith(match[2]):
        return False,dict(path=str(path),n=n,reason='missing or changed primary quench input')
    if len(list(csv.DictReader(path.open())))!=n:return False,dict(path=str(path),n=n,reason='quench result count differs')
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='quench ancestry cycle')
    ok,proof=prior.fs.trace(parent,n,scratch,active|{(str(path),n)})
    return ok,dict(path=str(path),n=n,parent=proof,snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),record=dict(record,source=source.split(' | recorded source of the start:',1)[0]),ledger=ledger,reason='hash-bound primary input of one fq quench')


def public_cert_copy32(path,n,scratch,active,recorded=None):
    if '-r32/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict) or record.get('kind') not in ('fresh-public','reopened-public') or not record.get('certified_from'):return None
    parent=Path(record['certified_from'])
    if parent.parent!=Path(scratch)/'take-harvest-r32/work/inputs':return None
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    input_sha=record.get('certified_input_sha256')
    if int(record.get('n',0))!=n or not parent.is_file() or hashlib.sha256(parent.read_bytes()).hexdigest()!=input_sha:
        return False,dict(path=str(path),n=n,reason='public certified-copy input bytes differ')
    producer=None
    if digest!=input_sha:
        original=Path(record.get('path',''))
        if original.parent!=Path(scratch)/'take-harvest-r32/near' or not original.name.startswith(str(n)+'-') or not original.is_file():
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


def stair_modules32(path,n,scratch,active,recorded=None):
    if '-r32/' not in str(path) or not path.is_file():return None
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
def _priority_inputs32(size,mtime):
    return frozenset(json.loads((WORK/'priority-inputs32.json').read_text()))

def priority_inputs32():
    path=WORK/'priority-inputs32.json'
    if not path.exists():return frozenset()
    st=path.stat();return _priority_inputs32(st.st_size,st.st_mtime_ns)


_declared_before32=prior.fs.declared_withdrawal

def declared_withdrawal32(value,scratch):
    """Keep a withdrawn ancestor pinned even after its live path changes."""
    if _declared_before32(value,scratch):return True
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
prior.fs.declared_withdrawal=declared_withdrawal32


def twoshort_held_chain32(path,n,scratch,active,recorded=None):
    """Verify every declared member of an own held lkick chain."""
    if '-r32/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('twoshort round 32:'):return None
    primary=source.split('Held row source:',1)[0]
    if 'invent_rest.py lkick' not in primary or ('from the held round 31 b row of n='+str(n)) not in primary:return None
    owned=Path(scratch)/'take-twoshort-r32/work'
    members=re.findall(r'($SCRATCH/bounties-squares/take-twoshort-r32/work/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\)',primary)
    baseline=owned/'starts'/(str(n)+'-held31b.csv')
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


def backlog_primary32(path,n,scratch,active,recorded=None):
    """Bind a Backlog start to the source row retained by its producer."""
    if '-r32/' not in str(path) or not path.is_file():return None
    record,ledger=(recorded,'retained source') if recorded is not None else prior.fs.record(path,n)
    if not isinstance(record,dict):return None
    source=record.get('source','')
    if not isinstance(source,str) or not source.startswith('backlog lane:'):return None
    match=re.match(r'^backlog lane: .*?from the byte copy ($SCRATCH/bounties-squares/take-backlog-r32/work/starts/[^ ()]+\.csv) \(sha256 ([a-f0-9]{64})\), taken at queue time from the certified round 32 take ([^;]+); its take\.tsv row: (.+)$',source,re.S)
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
