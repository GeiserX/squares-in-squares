"""Round 31 bars, exact held exports and writable source caches."""
from pathlib import Path
import csv, hashlib, json, math
import forensics_round30 as prior
import forensics_public30 as public

SCRATCH = prior.SCRATCH
WORK = SCRATCH / 'take-forensics-r31/work'
prior.WORK = WORK
prior.MAC = '$SCRATCH/squares-forensics-r31'
public.WORK = WORK


def base(scratch, work):
    return {int(r['n']): float(r['bar']) for r in csv.DictReader(
        open(Path(scratch)/'round31-briefs/bar31.tsv'), delimiter='\t')}
prior.base = base

_original_trace = prior.fs._trace

def trace31(path, n, scratch, active=None, recorded=None):
    path = Path(path)
    sidecar = Path(str(path)+'.json')
    if path.parent == WORK/'held-inputs' and sidecar.is_file():
        from forensics_adapters30 import numeric_rows
        rec = json.loads(sidecar.read_text())
        if rec.get('kind') == 'round31-exact-held-export':
            donor = Path(rec['held_file'])
            if not donor.is_file() or hashlib.sha256(donor.read_bytes()).hexdigest() != rec['held_sha256']:
                return False, dict(reason='changed held source',path=str(path),n=n)
            if rec['n'] != n or hashlib.sha256(path.read_bytes()).hexdigest() != rec['sha256']:
                return False, dict(reason='changed held export',path=str(path),n=n)
            st=donor.stat()
            if _numeric_digest(numeric_rows(list(csv.DictReader(open(path))))) != _held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
                return False, dict(reason='held coordinates differ',path=str(path),n=n)
            result=prior.fs.trace(donor,n,scratch,active)
            return result[0], dict(path=str(path),n=n,parent=result[1],snapshot_sha256=rec['sha256'],reason='exact own held export',record=rec)
    copied=_bound_border_copy31(path,n,scratch,active)
    if copied is not None:return copied
    peer=_peer_held_copy(path,n,scratch,active)
    if peer is not None:return peer
    followed=_primary_held_follow(path,n,scratch,active)
    if followed is not None:return followed
    chain=_twoshort_held_chain31(path,n,scratch,active)
    if chain is not None:return chain
    copied=_backlog_copy31(path,n,scratch,active)
    if copied is not None:return copied
    return _original_trace(path,n,scratch,active,recorded)
prior.fs._trace=trace31

for _name in dir(prior):
    if not _name.startswith('_') and _name not in globals():
        globals()[_name]=getattr(prior,_name)

def admission_priority(path):
    fresh='-r31/' in str(path)
    rank=(0 if path.parent.name.startswith('take-') else 1 if '/work/interior/' in str(path) else 3 if '/work/held-inputs/' in str(path) else 2) if fresh else 4
    try: modified=path.stat().st_mtime
    except OSError: modified=0.
    return rank,-modified
prior.admission_priority=admission_priority

# Imported public policy checks every archived version at both required scales.
# It runs only at public-first roots, beyond the held boundary.
import importlib.util
_spec=importlib.util.spec_from_file_location('forensics_public_policy31',Path(__file__).parent/'tools/harvest31/policy.py')
public_policy31=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(public_policy31)

@prior.lru_cache(maxsize=2048)
def public_audit31(path,n,size,modified):
    rows=public_policy31.A.read(path,[n])[n]
    return public_policy31.audit(rows)

def prvs_share(path,n):
    if n==228:return 0.
    p=Path(path);st=p.stat();ok,proof=public_audit31(str(p),n,st.st_size,st.st_mtime_ns)
    return max((max(r['share1e3'],r['share1e2']) for r in proof),default=0.)
prior.prvs_share=prvs_share

_public_audit=public.audit

def audit_public31(proof,references,work,notices,gather=None,matrix=None):
    rows=_public_audit(proof,references,work,notices,gather,matrix)
    for row in rows:
        p=Path(row['snapshot']);st=p.stat();n=int(row['n'])
        ok,detail=public_audit31(str(p),n,st.st_size,st.st_mtime_ns) if n!=228 else (True,[])
        row.update(round31_comparisons=detail,allowed=ok and row['licence_allowed'])
    return rows
public.audit=audit_public31

_source_policy=prior.source_policy_hash

def source_policy_hash():
    return hashlib.sha256((_source_policy()+hashlib.sha256(Path(__file__).read_bytes()).hexdigest()+hashlib.sha256(Path(public_policy31.__file__).read_bytes()).hexdigest()+hashlib.sha256(Path(rules31.__file__).read_bytes()).hexdigest()).encode()).hexdigest()
prior.source_policy_hash=source_policy_hash


def _numeric_digest(rows):
    return hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest()

@prior.lru_cache(maxsize=2)
def _held_projection(path,size,modified):
    from forensics_adapters30 import numeric_rows
    groups={}
    with open(path) as stream:
        for row in csv.DictReader(stream):
            n=int(str(row.get('n',row.get('id','').split('_')[0])).lstrip('s'))
            groups.setdefault(n,[]).append(row)
    return {n:_numeric_digest(numeric_rows(rows)) for n,rows in groups.items()}


def admit31(files, scratch, work):
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
        is_interior = '/take-forensics-r31/work/interior/' in str(path)
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
        is_fresh = '-r31/' in str(path) and not is_held
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

prior.admit=admit31
admit=admit31


def _peer_held_copy(path,n,scratch,active):
    """Bind a claimed or recorded held export to exact submitted rows."""
    if '-r31/work/' not in str(path) or '/public' in str(path) or not path.is_file():return None
    declared,ledger=prior.fs.record(path,n)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    # Border retains an exact producer export next to its pinned donor copies.
    if declared is None:
        root=next((p for p in path.parents if p.name.startswith('take-') and p.name.endswith('-r31')),None)
        candidate=root/'work/held31'/(str(n)+'.csv') if root else None
        if candidate and candidate!=path and candidate.is_file() and Path(str(candidate)+'.json').is_file():
            if hashlib.sha256(candidate.read_bytes()).hexdigest()==digest:
                ok,parent=prior.fs.trace(candidate,n,scratch,active)
                return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=digest,
                    reason='byte-identical peer copy of a pinned held export')
    log=Path(scratch)/'handoff-r31.log'
    lines=[line for line in log.read_text().splitlines() if str(path) in line and 'held' in line.lower()]
    donor=Path(scratch)/'gather/round30-2026-11-15c.csv'
    if isinstance(declared,dict):
        explicit=(declared.get('held_file')==str(donor) and declared.get('sha256')==digest and int(declared.get('n',0))==n and 'held' in declared.get('source','').lower())
        claimed=any('held round 30 c row' in line.lower() or 'held30c' in line.lower() for line in lines)
        public_first=declared.get('public_first') or declared.get('kind') in ('fresh-public','reopened-public') or str(declared.get('source','')).lstrip().startswith('public ')
        if public_first or not (explicit or claimed):return None
        if explicit and declared.get('held_sha256')!=public.held_paths().get(str(donor),{}).get('sha256'):
            return False,dict(path=str(path),n=n,reason='peer held source pin differs')
    elif not lines:return None
    if not public.held(donor):return False,dict(path=str(path),n=n,reason='held registry pin failed')
    from forensics_adapters30 import numeric_rows
    rows=list(csv.DictReader(open(path)));st=donor.stat()
    if len(rows)!=n or any(int(r.get('n',n))!=n for r in rows):
        return False,dict(path=str(path),n=n,reason='wrong peer held count')
    if _numeric_digest(numeric_rows(rows))!=_held_projection(str(donor),st.st_size,st.st_mtime_ns)[n]:
        return False,dict(path=str(path),n=n,reason='peer held coordinates differ')
    declared_hashes=[h for line in lines for h in prior.re.findall(r'\b[a-f0-9]{12,64}\b',line)]
    if declared_hashes and not any(digest.startswith(h) for h in declared_hashes):
        return False,dict(path=str(path),n=n,reason='peer claim hash differs')
    ok,parent=prior.fs.trace(donor,n,scratch,active)
    return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=digest,record=declared,
        producer_claim=lines[-1] if lines else None,ledger=ledger,
        reason='exact current held export with a producer binding')


def _primary_held_follow(path,n,scratch,active):
    if path.parent!=Path(scratch)/'take-rebuild-r31' or path.name!=str(n)+'.csv':return None
    row,ledger=prior.fs.record(path,n)
    if not isinstance(row,dict):return None
    primary=row.get('source','').split('. The start:',1)[0]
    match=prior.re.search(r'of (take-rebuild-r31/work/held31/(\d+)\.csv) \(sha256 ([a-f0-9]{12,64})',primary)
    if not match:return None
    parent=Path(scratch)/match[1]
    if int(match[2])!=n or not parent.is_file() or not hashlib.sha256(parent.read_bytes()).hexdigest().startswith(match[3]):
        return False,dict(path=str(path),n=n,reason='changed primary held kick input')
    ok,evidence=prior.fs.trace(parent,n,scratch,active)
    return ok,dict(path=str(path),n=n,parent=evidence,record=row,ledger=ledger,
        snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        reason='recorded primary held kick; upstream history remains below held boundary')


def _twoshort_held_chain31(path,n,scratch,active):
    if path.parent!=Path(scratch)/'take-twoshort-r31' or path.name!=str(n)+'.csv':return None
    row,ledger=prior.fs.record(path,n)
    if not isinstance(row,dict):return None
    source=row.get('source','');primary=source.split('Held row source:',1)[0]
    if not primary.startswith('twoshort round 31:') or '--modes lkick,kick' not in primary:return None
    if ('kick chain from the held round 30 c row of n='+str(n)) not in primary:return None
    if any(word in source for word in ['prvsiyan/squares-verified-best-of-1105','penguin069/squares-joegun-boxed-certified-union','CC BY-SA']):return None
    matches=prior.re.findall(r'($SCRATCH/bounties-squares/take-[^ ()]+\.csv) \(sha256 ([a-f0-9]{12,64})\)',primary)
    if not matches:return None
    owned=Path(scratch)/'take-twoshort-r31/work';chain=[]
    for filename,want in matches:
        p=Path(filename)
        if not p.is_relative_to(owned) or not p.is_file() or not hashlib.sha256(p.read_bytes()).hexdigest().startswith(want):
            return False,dict(path=str(path),n=n,reason='missing or changed recorded held-chain member',member=filename)
        rows=list(csv.DictReader(open(p)))
        if len(rows)!=n or any(int(r['n'])!=n for r in rows):return False,dict(reason='held-chain count differs',path=str(path),n=n)
        chain.append(dict(path=filename,n=n,snapshot_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    baseline=owned/'starts'/(str(n)+'-held30c.csv')
    if not any(filename==str(baseline) for filename,want in matches):return None
    ok,parent=prior.fs.trace(baseline,n,scratch,active)
    return ok,dict(path=str(path),n=n,parent=parent,chain=chain,record=dict(source=primary,licence=row.get('licence','')),
        producer_record_sha256=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(),ledger=ledger,
        snapshot_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),reason='complete pinned own kick chain from exact held baseline')


import forensics_rules31 as rules31

def hard_source_hits(text):
    import quench_audit
    return rules31.hits(text,quench_audit.RULES)
prior.hard_source_hits=hard_source_hits


def _backlog_copy31(path,n,scratch,active):
    root=Path(scratch)/'take-backlog-r31'
    if path.parent!=root/'work/starts' or not path.is_file():return None
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='backlog copy cycle')
    from forensics_adapters30 import backlog_copy
    current=backlog_copy(path,n,scratch,active,prior.fs.trace,WORK)
    if current is not None and current[0]:return current
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    match=prior.re.fullmatch(r'(\d+)-(take-[a-z0-9-]+-r31)-([a-f0-9]{12})\.csv',path.name)
    if not match or int(match[1])!=n or not digest.startswith(match[3]):return current
    original=Path(scratch)/match[2]/(str(n)+'.csv')
    snapshot=WORK/'feed'/match[2]/(str(n)+'-'+digest[:24]+'.csv')
    origin=Path(str(snapshot)+'.origin.json')
    if not snapshot.is_file() or not origin.is_file():return current
    rec=json.loads(origin.read_text())
    if (rec.get('path')!=str(original) or not rec.get('verified_ancestry') or rec.get('snapshot_sha256')!=digest
        or hashlib.sha256(snapshot.read_bytes()).hexdigest()!=digest):
        return False,dict(path=str(path),n=n,reason='changed retained backlog producer snapshot')
    ok,parent=prior.fs.trace(snapshot,n,scratch,active|{(str(path),n)})
    return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=digest,
        reason='exact backlog bytes retained with immutable producer record')


def _bound_border_copy31(path,n,scratch,active):
    """Follow an explicit border copy binding only while both hashes match."""
    root=Path(scratch)/'take-border-r31'
    if path.parent!=root/'work/donors' or not path.is_file():return None
    match=prior.re.fullmatch(r'(\d+)-([a-f0-9]{12,64})\.csv',path.name)
    if not match or int(match[1])!=n:return None
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if not digest.startswith(match[2]):return False,dict(path=str(path),n=n,reason='border copy filename hash differs')
    active=set(active or ())
    if (str(path),n) in active:return False,dict(path=str(path),n=n,reason='border copy ancestry cycle')
    records=[]
    row,ledger=prior.fs.record(root/(str(n)+'.csv'),n)
    if isinstance(row,dict):records.append((row,ledger))
    for p in sorted((root/'work/chain').glob(str(n)+'-*.csv.json')):
        row=json.loads(p.read_text())
        if isinstance(row,dict) and int(row.get('n',0))==n:records.append((row,str(p)))
    pattern=r'pinned copy '+prior.re.escape(str(path))+r' \(sha256 ([a-f0-9]{12,64})\) of ($SCRATCH/bounties-squares/[^\s,;()]+\.csv)'
    bindings=[(Path(parent),want,row,ledger) for row,ledger in records
              for want,parent in prior.re.findall(pattern,row.get('source',''))]
    if not bindings:return None
    if len({(str(p),want) for p,want,row,ledger in bindings})!=1:
        return False,dict(path=str(path),n=n,reason='conflicting border copy bindings')
    parent,want,row,ledger=bindings[0]
    if not digest.startswith(want) or not parent.is_file() or hashlib.sha256(parent.read_bytes()).hexdigest()!=digest:
        return False,dict(path=str(path),n=n,reason='changed bound border copy')
    rows=list(csv.DictReader(open(path)))
    if len(rows)!=n or any(int(r['n'])!=n for r in rows):
        return False,dict(path=str(path),n=n,reason='bound border copy count differs')
    ok,evidence=prior.fs.trace(parent,n,scratch,active|{(str(path),n)})
    return ok,dict(path=str(path),n=n,parent=evidence,snapshot_sha256=digest,ledger=ledger,
        record=dict(source='pinned byte copy of '+str(parent),sha256=digest),
        producer_record_sha256=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(),
        reason='explicit producer binding to byte-identical border parent')
