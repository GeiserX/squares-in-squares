"""Read exact backlog starts added outside the controller's initial queue."""
import hashlib,json,re
from pathlib import Path
from forensics_adapters29 import backlog_copy as prior, pin_record, sha


def backlog_copy(path,n,scratch,active,trace,work):
    result=prior(path,n,scratch,active,trace,work)
    if result is not None:return result
    path=Path(path);active=set(active or ())
    if (str(path),n) in active:
        return False,dict(path=str(path),n=n,reason='copied-start ancestry cycle')
    active.add((str(path),n));matches=[]
    def visit(v):
        if isinstance(v,dict):
            if v.get('start')==str(path) and v.get('orig'):matches.append(v)
            for child in v.values():visit(child)
        elif isinstance(v,list):
            for child in v:visit(child)
    for filename in ['queue.json','extra.json']:
        p=path.parent.parent/filename
        if p.exists():visit(json.loads(p.read_text()))
    if not matches:return None
    identities={(int(r['n']),r['orig']) for r in matches}
    if len(identities)!=1 or next(iter(identities))[0]!=n:
        return False,dict(path=str(path),n=n,reason='conflicting extra-copy identity or count')
    row=matches[0];original=Path(row['orig'])
    if not path.is_file() or not original.is_file():
        return False,dict(path=str(path),n=n,reason='missing extra-copy packing')
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if hashlib.sha256(original.read_bytes()).hexdigest()!=digest:
        return False,dict(path=str(path),n=n,reason='changed extra-copy bytes')
    suffix=re.search(r'-([a-f0-9]{12})\.csv$',path.name)
    if suffix and not digest.startswith(suffix[1]):
        return False,dict(path=str(path),n=n,reason='extra-copy filename hash differs')
    ok,parent=trace(original,n,scratch,active)
    proof,sha=pin_record(work,row)
    return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=digest,
                   source_proof=proof,record_sha256=sha,reason='exact backlog supplemental copy with pinned record')


from functools import lru_cache
from forensics_twoshort28 import digest,intake_origin
import csv


@lru_cache(maxsize=512)
def held_rows(path,n,size,stamp):
    rows=[]
    with open(path) as stream:
        for r in csv.DictReader(stream):
            count=int(str(r.get('n',r.get('id','').split('_')[0])).lstrip('s'))
            if count==n:rows.append(r)
    if len(rows)!=n:raise ValueError('held count missing')
    return rows


def numeric_rows(rows):
    out=[]
    for r in rows:
        i=r.get('square_id',r.get('id','').split('_')[-1])
        out.append([int(str(i).lstrip('s'))]+[float(str(r[k]).lstrip('s')) for k in ['x','y','angle']])
    return sorted(out)


def held_root(path,n,notices):
    from forensics_public30 import held,file_sha
    p=Path(path)
    if not held(p):return None
    if not 1<=n<=1000:return False,dict(path=str(p),n=n,reason='held count outside submitted range')
    st=p.stat()
    credit=notices({'root':dict(source=[str(p),n])})
    if not credit:return False,dict(path=str(p),n=n,reason='missing submitted held row credit')
    return True,dict(path=str(p),n=n,reason='SHA-pinned submitted held row, own first source',
        held_sha256=file_sha(str(p),st.st_size,st.st_mtime_ns),record=dict(source=credit[0]['source'],licence=credit[0]['licence']),
        ledger=credit[0]['ledger'],requested_ledger=credit[0]['requested_ledger'])


def transport(path,n,scratch,active,trace,raw_trace,work):
    path=Path(path);scratch=Path(scratch);active=set(active or ())
    key=(str(path),n)
    if key in active:return False,dict(path=str(path),n=n,reason='transport ancestry cycle')
    if path.parent==scratch/'take-rebuild-r30/work/pins':
        match=re.fullmatch(r'(\d+)-([a-f0-9]{12,64})\.csv',path.name)
        if match and int(match[1])==n and path.is_file():
            digest_value=sha(path)
            if not digest_value.startswith(match[2]):return False,dict(path=str(path),n=n,reason='rebuild pin filename hash differs')
            held=scratch/'gather/round28-2026-11-15b.csv';st=held.stat();reference=held_rows(str(held),n,st.st_size,st.st_mtime_ns)
            if numeric_rows(list(csv.DictReader(open(path))))==numeric_rows(reference):
                active.add(key);ok,parent=trace(held,n,scratch,active)
                return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=digest_value,reason='byte-pinned exact submitted held row projection')
    if path.parent==scratch/'take-rebuild-r30/work/held28b':
        held=scratch/'gather/round28-2026-11-15b.csv'
        if not path.is_file() or path.stem!=str(n):return False,dict(path=str(path),n=n,reason='held export count mismatch')
        st=held.stat();reference=held_rows(str(held),n,st.st_size,st.st_mtime_ns)
        if numeric_rows(list(csv.DictReader(open(path))))!=numeric_rows(reference):
            return False,dict(path=str(path),n=n,reason='held export differs from submitted rows')
        active.add(key);ok,parent=trace(held,n,scratch,active)
        return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=sha(path),reason='exact coordinate and ID export of submitted held row')
    if path.parent==scratch/'take-border-r30/work/donors':
        match=re.fullmatch(r'(\d+)-([a-f0-9]{12,16})\.csv',path.name)
        if not match or int(match[1])!=n:return None
        if not path.is_file():return False,dict(path=str(path),n=n,reason='missing border copy')
        digest=sha(path)
        if not digest.startswith(match[2]):return False,dict(path=str(path),n=n,reason='border filename pin differs')
        records=[]
        for tag in ['lp','kq']:
            base=path.parent.parent/tag;index=base/'index.json'
            if not index.exists():continue
            record=json.loads(index.read_text()).get(match[2]);copy=base/'nin'/(match[2]+'_'+str(n)+'.csv')
            if record is None:continue
            if int(record.get('n',-1))!=n or record.get('sha256')!=digest or not copy.is_file() or sha(copy)!=digest:
                return False,dict(path=str(path),n=n,reason='changed border producer input binding')
            records.append((record,copy))
        if not records:return None
        identities={(v.get('path'),v.get('sha256')) for v,p in records}
        if len(identities)!=1:return False,dict(path=str(path),n=n,reason='ambiguous border copy origin')
        row,copy=records[0];active.add(key);original=Path(row['path'])
        if isinstance(row.get('row'),dict):
            ok,parent=raw_trace(copy,n,scratch,active,recorded=row['row'])
        elif original.is_file() and sha(original)==digest:ok,parent=trace(original,n,scratch,active)
        else:return False,dict(path=str(path),n=n,reason='missing exact border origin and pinned source row')
        proof,proof_sha=pin_record(work,row)
        return ok,dict(path=str(path),n=n,parent=parent,snapshot_sha256=digest,source_proof=proof,record_sha256=proof_sha,reason='border copy bound to producer input and pinned source row')
    return None



def recovered_projection(path,n,scratch,active,trace,work):
    """Bind a recovered per-count export to its original rows and both hashes."""
    path=Path(path)
    if path.parent!=Path(work)/'held-inputs':return None
    active=set(active or ());key=(str(path),n)
    evidence=dict(path=str(path),n=n)
    if key in active:return False,dict(evidence,reason='recovered projection ancestry cycle')
    try:
        record=json.loads(Path(str(path)+'.json').read_text())
        parents=record['parents']
        if record['n']!=n or len(parents)!=1 or parents[0][1]!=n:
            raise ValueError('recovered projection count or parent mismatch')
        original=Path(parents[0][0])
        if sha(path)!=record['packing_sha256'] or sha(original)!=record['source_sha256']:
            raise ValueError('changed recovered projection or source bytes')
        st=original.stat();rows=list(csv.DictReader(path.open()))
        if len(rows)!=n or numeric_rows(rows)!=numeric_rows(held_rows(str(original),n,st.st_size,st.st_mtime_ns)):
            raise ValueError('recovered projection differs from original coordinates or IDs')
        active.add(key);ok,parent=trace(original,n,scratch,active)
        proof,proof_sha=pin_record(work,record)
        return ok,dict(evidence,parent=parent,snapshot_sha256=record['packing_sha256'],
                       source_proof=proof,record_sha256=proof_sha,
                       reason='hash-bound exact per-count projection with pinned source proof')
    except (OSError,ValueError,KeyError,TypeError) as error:
        return False,dict(evidence,reason=str(error))


def trace_twoshort27(path, n, scratch, active, trace):
    root=None
    for rnd in (27,28,29,30):
        candidate=Path(scratch)/('take-twoshort-r%d/work/boxE%d'%(rnd,rnd))
        try:relative=path.relative_to(candidate);root=candidate;break
        except ValueError:pass
    if root is None:return None
    parts = relative.parts
    raw = (len(parts) == 4 and parts[0] == 'runs' and parts[2] == 'raw')
    start = len(parts) == 2 and parts[0] == 'starts'
    if not raw and not start:
        return None
    key = (str(path), n)
    active = set(active or ())
    evidence = dict(path=str(path), n=n)
    if key in active:
        return False, dict(evidence, reason='cyclic twoshort job chain')
    active.add(key)
    try:
        import forensics_compose as fc
        import forensics_rect as rect
        layouts = rect.layouts(path)
        if set(layouts) != {n}:
            raise ValueError('twoshort count mismatch')
        evidence['snapshot_sha256'] = digest(path)
        if start:
            receipt = root.parent / 'intake' / (path.stem + '.json')
            record = json.loads(receipt.read_text())
            parent = intake_origin(path, record)
            ok, proof = trace(parent, n, scratch, active)
            return ok, dict(evidence, reason='hash-bound immutable twoshort intake',
                            parent=proof, record=record, intake=str(receipt),
                            intake_sha256=digest(receipt))
        run_match = re.fullmatch(r'(.+)-s(\d+)', parts[1])
        name_match = re.fullmatch(r'(\d+)-sl(\d+)-(\d+)\.csv', path.name)
        if not run_match or not name_match:
            raise ValueError('unrecognized twoshort slide identity')
        tag, seed = run_match[1], int(run_match[2])
        if int(name_match[1]) != n or int(name_match[2]) != seed:
            raise ValueError('twoshort filename count or seed mismatch')
        jobs = []
        for job_path in (root / 'jobs').glob('*-' + tag + '-' + str(seed) + '.json'):
            job = json.loads(job_path.read_text())
            if job.get('tag') == tag and job.get('n') == n and job.get('seed') == seed:
                jobs.append((job_path, job))
        if not jobs or len({job['start'] for _, job in jobs}) != 1:
            raise ValueError('missing or ambiguous twoshort start job')
        job_path, job = jobs[0]
        run = path.parent.parent
        table = run / f'slide-{n}-{seed}.tsv'
        iteration = int(name_match[3])
        rows = [line.split('\t') for line in table.read_text().splitlines()
                if line and not line.startswith('#')]
        rows = [row for row in rows if int(row[0]) == iteration]
        side, _ = fc.frame(layouts[n])
        if len(rows) != 1 or abs(side - float(rows[0][4])) > 2e-9:
            raise ValueError('twoshort output differs from recorded slide side')
        parent = Path(job['start'])
        if not parent.is_absolute():
            parent = root / parent
        elif not parent.is_relative_to(root):
            positions = [i for i, part in enumerate(parent.parts)
                         if part in ('squares-twoshort', 'squares-twoshort-r%d'%rnd)]
            if len(positions) != 1:
                raise ValueError('unrecognized remote twoshort start root')
            parent = root.joinpath(*parent.parts[positions[0] + 1:])
        if not parent.is_relative_to(root) or parent.suffix != '.csv':
            raise ValueError('twoshort start outside retained run tree')
        ok, proof = trace(parent, n, scratch, active)
        return ok, dict(evidence, reason='recorded twoshort slide job and iteration',
                        parent=proof, record=job, job=str(job_path), job_sha256=digest(job_path),
                        run_table=str(table), run_table_sha256=digest(table),
                        seed=seed, iteration=iteration, recorded_side=float(rows[0][4]))
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        return False, dict(evidence, reason='unresolved twoshort slide chain', error=str(error))
