"""Round 26 admission, base bars and remote rectangle scans."""
import csv
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

import forensics_sources29 as fs
import forensics_policy as policy
import forensics_watch as fw

SCRATCH = Path('$SCRATCH/bounties-squares')
WORK = SCRATCH / 'take-forensics-r29/work'
MAC = '$SCRATCH/squares-forensics-r29'
PYTHON = '$SCRATCH/squares-base/venv/bin/python'
CODE = Path(__file__).resolve().parent


@lru_cache(maxsize=32)
def proof_document(path, modified, size):
    data = Path(path).read_bytes()
    return data.decode(), json.loads(data)


def reference_closure(proof):
    """Read retained derivations without expanding them into queue records."""
    texts, seen = [], set()
    def file(path, expected=None):
        path = Path(path)
        if not path.exists():
            if expected:
                raise ValueError('missing referenced ancestry')
            return
        if path.suffix != '.json':
            return
        stat = path.stat()
        text, data = proof_document(str(path), stat.st_mtime_ns, stat.st_size)
        if expected and hashlib.sha256(text.encode()).hexdigest() != expected:
            raise ValueError('changed referenced ancestry')
        if str(path) in seen:
            return
        seen.add(str(path))
        if ('/work/feed/' in str(path) and path.name.endswith('.origin.json') and
                data.get('verified_ancestry') and not data.get('full_ancestry')):
            raise ValueError('round25 snapshot lacks full retained derivation')
        texts.append(text)
        visit(data)
    def visit(value):
        if isinstance(value, dict):
            if fs.declared_withdrawal(value, SCRATCH):
                raise ValueError('withdrawn node in full ancestry')
            full = value.get('full_ancestry')
            if isinstance(full, dict):
                file(full['path'], full.get('sha256'))
            for key in ('source_proof','ancestry_file'):
                if isinstance(value.get(key), str):
                    file(value[key], value.get('ancestry_sha256') if key == 'ancestry_file' else None)
            for key, child in value.items():
                if key != 'full_ancestry':
                    visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str):
            if any(fs.withdrawn(path, n, SCRATCH) for path, n in fs.source_pairs(value)):
                raise ValueError('withdrawn parent identity in retained source string')
    visit(proof)
    return texts


def hard_source_hits(text):
    """Keep the explicit excluded public families independent of share matches."""
    import quench_audit
    return [name for name, pattern in quench_audit.RULES
            if name != 'prvsiyan best-of-1105' and re.search(pattern, text, re.I)]


def strict_uncached(path, n, scratch=SCRATCH):
    """Check retained parents and all declared root notices."""
    path = Path(path)
    try:
        # The 00:19 rule applies the numeric gate only to fetched public starts.
        share = share_gate(path, n)
        if share >= .4:
            return False, dict(reason='excluded public-first source share',
                               prvsiyan_shares=[dict(path=str(path), n=n, share=share)])
        ok, proof = fs.trace(path, n, scratch)
        if not ok:
            return False, proof
        document = dict(path=str(path), n=n, packing_sha256=hashlib.sha256(path.read_bytes()).hexdigest(), evidence=proof)
        encoded = json.dumps(document, sort_keys=True, separators=(',', ':')).encode()
        derivation_sha = hashlib.sha256(encoded).hexdigest()
        directory = WORK/'ancestry'
        directory.mkdir(exist_ok=True)
        derivation = directory/(derivation_sha+'.json')
        if not derivation.exists():
            derivation.with_suffix('.tmp').write_bytes(encoded)
            derivation.with_suffix('.tmp').replace(derivation)
        compact = fs.compact_ancestry(proof, str(derivation))
        references = reference_closure(proof)
        notices = []
        group_texts = []
        groups_seen = set()
        noticed = set()
        def visit(item):
            if isinstance(item, dict):
                if item.get('reason') == 'verified immutable donor group':
                    group_path = Path(item['source_proof'])
                    if str(group_path) not in groups_seen:
                        groups_seen.add(str(group_path))
                        content = group_path.read_bytes()
                        if hashlib.sha256(content).hexdigest() != item['sha256']:
                            raise ValueError('changed immutable group proof')
                        group_texts.append(content.decode())
                if item.get('path') and isinstance(item.get('n'), int):
                    p = Path(item['path'])
                    if p.parent.name == 'gather' and (str(p),item['n']) not in noticed:
                        noticed.add((str(p),item['n']))
                        notices.extend(fw.gather_notices({'root': {'source': [str(p), item['n']]}}))
                for k, value in item.items():
                    if k != 'record':
                        visit(value)
            elif isinstance(item, list):
                for value in item:
                    visit(value)
        visit(proof)
        text = json.dumps(proof) + json.dumps(compact) + json.dumps(notices) + ''.join(group_texts) + ''.join(references)
        original_seeds = []  # Own seed matches are allowed by the 00:19 rule.
        forbidden = ('penguin069/squares-joegun-boxed-certified-union',
                     'prvsiyan/squares-verified-best-of-1105', 'CC BY-SA')
        seed = dict(status='none', seeds=[], rule='round28 own seed confirmed')
        hard_hits = hard_source_hits(text)
        allowed = not any(v in text for v in forbidden) and not hard_hits
        # Check the donor plus every materialised ancestor, including retained references.
        candidates = {(str(path), n)}
        def materialised(item):
            if isinstance(item, dict):
                p, count = item.get('path'), item.get('n')
                if p and isinstance(count, int) and str(p).endswith('.csv') and Path(p).exists():
                    candidates.add((p, count))
                for k, child in item.items():
                    if k != 'record': materialised(child)
            elif isinstance(item, list):
                for child in item: materialised(child)
        materialised(proof)
        for ref in references + group_texts:
            materialised(json.loads(ref))
        shares = []
        for p, count in sorted(candidates):
            pp = Path(p)
            if pp.parent == WORK/'original-seeds':
                st = pp.stat()
                if seed_hash(str(pp), st.st_size, st.st_mtime_ns) != pp.stem:
                    raise ValueError('changed pinned original seed')
            share = share_gate(p, count)
            shares.append(dict(path=p, n=count, share=share))
            if share >= .4: allowed = False
        import forensics_public29
        public_roots = forensics_public29.audit(proof, references + group_texts, WORK, notices, fw.gather_notices, source_matrix)
        if any(not row['allowed'] for row in public_roots):
            allowed = False
        return allowed, dict(reason='round29 clean ancestry' if allowed else 'excluded or unresolved root', public_roots=public_roots,
                             ancestry=compact, notices=notices, seed_policy=seed,
                             full_ancestry=dict(path=str(derivation), sha256=derivation_sha),
                             prvsiyan_shares=shares, original_seed_shares=original_seeds, hard_source_hits=hard_hits)
    except (OSError, ValueError, KeyError, TypeError, RecursionError) as error:
        return False, dict(reason='unresolved ancestry', error=repr(error), path=str(path), n=n)


_SOURCE_CACHE = {}
CACHE_COUNTS = dict(hits=0, walks=0)


def strict(path, n, scratch=SCRATCH, fresh=False):
    """Reuse pinned queue audits. Publication always requests a fresh walk."""
    path = Path(path)
    origin = Path(str(path) + '.origin.json')
    reusable = '/work/feed/' in str(path) and origin.exists()
    try:
        token = tuple((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in (path, origin)) if reusable else None
    except OSError:
        token = None
    key = (str(path), n, str(scratch))
    prior = _SOURCE_CACHE.get(key)
    if not fresh and token is not None and prior and prior[0] == token and time.time()-prior[1] < 600:
        CACHE_COUNTS['hits'] += 1
        return prior[2]
    CACHE_COUNTS['walks'] += 1
    result = strict_uncached(path, n, scratch)
    if token is not None:
        _SOURCE_CACHE[key] = (token, time.time(), result)
    return result


def check_parts(parts, scratch=SCRATCH, fresh=False):
    evidence = []
    for tag in ('A', 'B', 'C'):
        if tag in parts:
            part = parts[tag]
            ok, proof = strict(part['source'][0], int(part['source'][1]), scratch, fresh=fresh)
            evidence.append(dict(tag=tag, admitted=ok, **proof))
    return bool(evidence) and all(r['admitted'] for r in evidence), evidence


def base(scratch, work):
    return {int(r['n']): float(r['bar']) for r in csv.DictReader(
        open(scratch / 'round29-briefs/bar29.tsv'), delimiter='\t')}


def source_policy_hash():
    adapter = Path(__file__).with_name('forensics_twoshort28.py')
    adapter29 = Path(__file__).with_name('forensics_adapters29.py')
    public29 = Path(__file__).with_name('forensics_public29.py')
    rules = Path(__file__).with_name('quench_audit.py')
    return hashlib.sha256(Path(fs.__file__).read_bytes() + Path(__file__).read_bytes() +
                          adapter.read_bytes() + adapter29.read_bytes() + public29.read_bytes() + rules.read_bytes()).hexdigest()


def admission_priority(path):
    """New joins and certified r25 files precede the near archive."""
    if '-reopened-own' in path.name or path.name == '921-29e12ff3.csv':
        rank = -1
    elif re.fullmatch(r'take-.+-r29', path.parent.name):
        rank = 0
    elif 'take-k123-r29/' in str(path):
        rank = 1
    elif '/take-forensics-r29/work/held-inputs/' in str(path):
        rank = 2
    elif '/take-forensics-r29/work/interior/' in str(path):
        rank = 2
    elif '-r29/' in str(path):
        rank = 3
    else:
        rank = 4
    try:
        modified = path.stat().st_mtime
    except OSError:
        modified = 0.
    return rank, -modified


def admission_token(path, n, dependencies, policy_token):
    """Ignore other counts changing in a live take ledger."""
    token = []
    ledger = path.parent / 'take.tsv' if path.stem.isdigit() else None
    for dependency in dependencies:
        if not dependency.exists():
            continue
        if dependency == ledger:
            row, _ = fs.record(path, n)
            encoded = json.dumps(row, sort_keys=True, separators=(',', ':')).encode()
            token.append([str(dependency), 'record-sha256', hashlib.sha256(encoded).hexdigest()])
        else:
            st = dependency.stat()
            token.append([str(dependency), st.st_size, st.st_mtime_ns])
    return token + [['source-policy', policy_token]]


def reusable_refusal(prior, token, now):
    return bool(prior and prior['token'] == token and now-prior['at'] < (300 if prior.get('reason') == 'deferred source walk' else 600))


class AdmissionDeferred(Exception):
    pass


def queue_source_check(path, n, scratch, seconds=30):
    """Bound queue admission. Publication still requires the complete walk."""
    import signal
    def expired(*unused):
        raise AdmissionDeferred('queue source walk exceeded wall budget')
    previous = signal.signal(signal.SIGALRM, expired)
    timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return strict(path, n, scratch, fresh=True)
    finally:
        signal.setitimer(signal.ITIMER_REAL, *timer)
        signal.signal(signal.SIGALRM, previous)


def admit(files, scratch, work):
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
    policy_token = source_policy_hash()
    for path in sorted(files, key=admission_priority):
        # A full walk budget must not hide cleared files later in the list.
        if inspected >= 4 and str(path) not in successes:
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
        is_fresh = '-r29/' in str(path) and not is_held
        if fresh_inspected and not is_fresh:
            continue
        if inspected >= 4:
            continue
        if is_fresh and fresh_inspected >= 4:
            continue
        if is_held and held_inspected >= 4:
            continue
        inspected += 1
        held_inspected += int(is_held)
        fresh_inspected += int(is_fresh)
        (work/'active-admission.json').write_text(json.dumps(dict(path=str(path),n=n,at=time.time())))
        try:
            ok, proof = queue_source_check(path, n, scratch)
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


def repair_feed_mapping(args, work):
    mapping_file = work/'feed-map.json'
    mapping = json.loads(mapping_file.read_text()) if mapping_file.exists() else {}
    feed = work/'feed'
    for arg in args:
        path = Path(arg)
        if path.suffix == '.csv' and path.is_relative_to(feed):
            if not path.is_file():
                raise ValueError('queued feed input disappeared: '+str(path))
            mapping[str(path)] = str(path.relative_to(feed))
    temporary = mapping_file.with_suffix('.tmp')
    temporary.write_text(json.dumps(mapping))
    temporary.replace(mapping_file)
    return mapping


def start_scan(args, run, stop):
    """Run the sole rectangle scanner on boxB using immutable inputs."""
    repair_feed_mapping(args, WORK)
    subprocess.run(['rsync','-az',str(WORK / 'feed')+'/', 'boxB:'+MAC+'/feed/'], check=True)
    subprocess.run(['rsync','-az',str(WORK / 'feed-map.json'), 'boxB:'+MAC+'/feed-map.json'], check=True)
    remote_run = MAC + '/' + run.name
    subprocess.run(['ssh','boxB','mkdir -p '+shlex.quote(remote_run+'/raw')],check=True)
    subprocess.run(['rsync','-az',str(run/'details.csv'),'boxB:'+remote_run+'/details.csv'],check=True)
    # Input paths stay local identities in the output. Only the reader maps them.
    args = list(args[2:])
    args[1],args[2] = remote_run+'/details.csv',remote_run+'/raw'
    args[args.index('--cache')+1] = MAC+'/windows.pkl'
    args[args.index('--gap')+1] = MAC+'/gap.tsv'
    job = dict(args=args, deadline=stop, local_feed=str(WORK/'feed'))
    (run/'job.json').write_text(json.dumps(job))
    subprocess.run(['rsync','-az',str(run/'job.json'),'boxB:'+remote_run+'/job.json'],check=True)
    command = 'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 nohup nice -n 5 '+PYTHON+' -I '+MAC+'/code/forensics_scan25.py '+remote_run+'/job.json'
    with open(run/'rect.log','w') as out:
        return subprocess.Popen(['ssh','boxB',command],stdout=out,stderr=subprocess.STDOUT)


def collect_scans(work):
    subprocess.run(['rsync','-az','--include=scan-*/','--include=raw/','--include=*.csv','--include=*.json',
                    '--exclude=*','boxB:'+MAC+'/',str(work)+'/'],check=True)


# New held rows resolve through the source of that exact submitted row.
def retained_copy(path, n, scratch, active=None):
    """Resolve a copied start only through a byte-identical admitted snapshot."""
    path = Path(path)
    from forensics_adapters29 import backlog_copy
    copied = backlog_copy(path, n, scratch, active, fs.trace, WORK)
    if copied is not None:
        return copied
    match = re.fullmatch(r'(\d+)-(take-[a-z0-9-]+-r(?:26|27|28|29))-([a-f0-9]{12})\.csv', path.name)
    if not match or int(match[1]) != n or not path.exists():
        return False, dict(path=str(path), n=n, reason='unresolved copied start')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if not digest.startswith(match[3]):
        return False, dict(path=str(path), n=n, reason='changed copied start')
    copies = [SCRATCH / ('take-forensics-r%d/work/feed' % rnd) / match[2] /
              ('%d-%s.csv' % (n, digest[:24])) for rnd in (29, 28, 27, 26)]
    pinned = next((p for p in copies if p.exists() and
                   hashlib.sha256(p.read_bytes()).hexdigest() == digest), None)
    if pinned is None:
        return False, dict(path=str(path), n=n, reason='missing exact admitted snapshot for copied start')
    ok, proof = fs.trace(pinned, n, scratch, active)
    return ok, dict(path=str(path), n=n, parent=proof, snapshot=str(pinned),
                    sha256=digest, reason='byte-identical copied start with pinned full ancestry')


_trace_before26 = fs._trace

def trace_submitted(path, n, scratch, active=None, recorded=None):
    path = Path(path)
    if not path.is_absolute() and str(path).startswith(('take-', 'gather/')):
        path = Path(scratch) / path
    if any(part.startswith('take-harvest-r') for part in path.parts):
        from forensics_adapters29 import harvest_follow
        followed = harvest_follow(path, n, scratch, active, fs.trace, WORK)
        if followed is not None:
            return followed
    from forensics_twoshort28 import trace_twoshort, trace_module_pin
    pin = trace_module_pin(path, n, scratch, active, fs.trace)
    if pin is not None:
        return pin
    twoshort = trace_twoshort(path, n, scratch, active, fs.trace)
    if twoshort is not None:
        return twoshort
    if (path.parent.name == 'inputs' and
            any(part.startswith('take-harvest-r') for part in path.parts)):
        sidecar = Path(str(path)+'.json')
        if sidecar.exists():
            record = json.loads(sidecar.read_text())
            if record.get('kind') in ('fresh-public', 'reopened-public'):
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                if record.get('queued_sha256') != digest or int(record.get('n',0)) != n:
                    return False, dict(path=str(path), n=n, reason='changed queued public start')
                source_record = {k:v for k,v in record.items() if k not in ('original','queued_sha256','evidence')}
                ok, proof = _trace_before26(path,n,scratch,active,recorded=source_record)
                return ok, dict(path=str(path),n=n,parent=proof,
                                ancestry_file=str(sidecar),ancestry_sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest(),
                                snapshot_sha256=digest,reason='hash-bound public queue source without transport cycle')
    # Harvest quick readers retain the exact public start under its queue hash.
    if (path.parent.name == 'quick-starts' and
            any(part.startswith('take-harvest-r') for part in path.parts)):
        root = next(p for p in path.parents if p.name.startswith('take-harvest-r'))
        if path.exists():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            snapshot = root/'work/inputs'/(path.stem+'-'+digest[:16]+'.csv')
            sidecar = Path(str(snapshot)+'.json')
            if snapshot.exists() and sidecar.exists():
                record = json.loads(sidecar.read_text())
                if (record.get('queued_sha256') == digest and
                        record.get('original') == str(path) and int(record.get('n', 0)) == n and
                        hashlib.sha256(snapshot.read_bytes()).hexdigest() == digest):
                    source_record = {k: v for k, v in record.items() if k not in ('original', 'queued_sha256', 'evidence')}
                    ok, proof = _trace_before26(snapshot, n, scratch, active, recorded=source_record)
                    return ok, dict(path=str(path), n=n, parent=proof,
                                    ancestry_file=str(sidecar), ancestry_sha256=hashlib.sha256(sidecar.read_bytes()).hexdigest(),
                                    snapshot_sha256=digest, reason='byte-identical fetched public start with pinned source record')
        return False, dict(path=str(path), n=n, reason='missing or changed public start snapshot')
    backlogs = [Path(scratch) / ('take-backlog-r%d' % rnd) for rnd in (26, 27, 28, 29)]
    if any(path.parent == backlog / 'work/starts' for backlog in backlogs):
        return retained_copy(path, n, scratch, active)
    if path.parent in backlogs and path.stem.isdigit():
        backlog = path.parent
        row, ledger = fs.record(path, n)
        source = row.get('source', '') if isinstance(row, dict) else ''
        copied = re.search(r'sha256 ([a-f0-9]{64}), copied to ([^ )]+\.csv)', source)
        if copied and re.search(r'from the certified round (?:26|27|28|29) take ', source):
            parent = Path(copied[2])
            if parent.parent != backlog / 'work/starts' or not parent.exists():
                return False, dict(path=str(path), n=n, reason='missing recorded copied start')
            if hashlib.sha256(parent.read_bytes()).hexdigest() != copied[1]:
                return False, dict(path=str(path), n=n, reason='changed recorded copied start')
            ok, proof = retained_copy(parent, n, scratch, active)
            return ok, dict(path=str(path), n=n, parent=proof, record=row,
                            ledger=ledger, reason='recorded exact copied parent before inherited history')
    if path == Path(scratch) / 'gather/round25-2026-11-14b.csv':
        table = CODE / 'results/round25-best-2026-11-14.tsv'
        row = next((r for r in csv.DictReader(open(table), delimiter='\t') if int(r['n']) == n), None)
        if row:
            names = re.findall(r'take-[a-z-]+-r\d+', row['take'])
            if len(names) != 1:
                return False, dict(path=str(path), n=n, reason='unresolved submitted donor')
            parent = Path(scratch) / names[0] / (str(n)+'.csv')
        else:
            parent = Path(scratch) / 'gather/round23-2026-11-13b.csv'
        ok, proof = fs.trace(parent, n, scratch, active)
        return ok, dict(path=str(path), n=n, parent=proof, reason='submitted row resolved to recorded donor')
    return _trace_before26(path, n, scratch, active, recorded)

fs._trace = trace_submitted


@lru_cache(maxsize=1)
def prv_all():
    from scipy.spatial import cKDTree
    import zipfile, io
    from collections import defaultdict
    reference = SCRATCH / 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
    groups = defaultdict(list)
    with zipfile.ZipFile(reference) as z:
        text = z.read('submission.csv').decode('utf-8-sig')
    for r in csv.DictReader(io.StringIO(text)):
        n = int(str(r.get('n',r.get('id','').split('_')[0])).lstrip('s'))
        groups[n].append([float(str(r['x']).lstrip('s')),float(str(r['y']).lstrip('s'))])
    trees = {}
    for n, rows in groups.items():
        if len(rows) != n: continue
        a = np.asarray(rows); a -= (a.min(0)+a.max(0))/2
        trees[n] = cKDTree(a)
    return trees


@lru_cache(maxsize=1024)
def prv_centres(n):
    from scipy.spatial import cKDTree
    reference = SCRATCH / 'take-harvest-r24/work/public/data/ds/prvsiyan__squares-verified-best-of-1105/data.zip'
    matrix = source_matrix(str(reference))
    if matrix is None: return prv_all().get(n)
    a = matrix[matrix[:,0] == n,1:].copy()
    if len(a) != n: return None
    a -= (a.min(0)+a.max(0))/2
    return cKDTree(a)


@lru_cache(maxsize=1)
def matrix_manifest(path, modified):
    return {row['path']: row for row in json.loads(Path(path).read_text())}


@lru_cache(maxsize=8)
def open_matrix(path):
    return np.load(path, mmap_mode='r')


def source_matrix(path):
    manifest = WORK / 'centres/manifest.json'
    if not manifest.exists(): return None
    rows = matrix_manifest(str(manifest), manifest.stat().st_mtime_ns)
    row = rows.get(str(path))
    if not row: return None
    stat = Path(path).stat()
    if (stat.st_size,stat.st_mtime_ns) != (row['size'],row['modified']): return None
    return open_matrix(str(WORK/'centres'/(row['key']+'.npy')))



@lru_cache(maxsize=8)
def share_layouts(path, modified):
    from collections import defaultdict
    groups = defaultdict(list)
    with open(path) as h:
        for r in csv.DictReader(h):
            try:
                n = int(str(r.get('n',r.get('id','').split('_')[0])).lstrip('s'))
                groups[n].append([float(str(r['x']).lstrip('s')),float(str(r['y']).lstrip('s'))])
            except (ValueError, KeyError, TypeError):
                continue
    return {n: np.asarray(rows) for n,rows in groups.items()}


@lru_cache(maxsize=8192)
def _prvs_share(path, n, size, modified):
    matrix = source_matrix(path)
    loaded = matrix[matrix[:,0] == n,1:].copy() if matrix is not None else share_layouts(path, modified).get(n)
    if loaded is None or len(loaded) != n: raise ValueError('missing requested donor count in share test')
    tree = prv_centres(n)
    if tree is None: return 0.
    a = np.asarray(loaded)[:,:2]; a -= (a.min(0)+a.max(0))/2
    best = 0.
    for sw in (False,True):
        for sx in (-1,1):
            for sy in (-1,1):
                d,_ = tree.query((a[:,::-1] if sw else a)*[sx,sy])
                best = max(best,float((d<1e-3).mean()))
    return best


def prvs_share(path, n):
    stat = Path(path).stat()
    return _prvs_share(str(path),n,stat.st_size,stat.st_mtime_ns)


@lru_cache(maxsize=4)
def seed_hash(path, size, modified):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def original_seed_snapshot():
    path = SCRATCH/'seeds/merged0.csv'
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    folder = WORK/'original-seeds'
    folder.mkdir(exist_ok=True)
    dest = folder/(digest+'.csv')
    if not dest.exists():
        dest.with_suffix('.tmp').write_bytes(payload)
        dest.with_suffix('.tmp').replace(dest)
    return dest, digest


def original_seed_checks(text, notices):
    """Resolve explicit original seeds, then apply the numeric share rule."""
    counts = set()
    patterns = [r'n\s*=\s*(\d+)\s+of\s+Samanyu-dev/squares_in_squares\b',
                r'Samanyu-dev/squares_in_squares\s*\(donor n\s*=\s*(\d+)\)']
    for pattern in patterns:
        counts.update(int(n) for n in re.findall(pattern, text, flags=re.I))
    counts.update(int(n) for n in re.findall(
        r'(\d+)h(?:\d+)?\.[A-Za-z0-9~]+\s*<held: seed merged0>', text))
    counts.update(int(r['n']) for r in notices if r.get('source','').strip() == 'seed merged0')
    if not counts:
        return []
    path, digest = original_seed_snapshot()
    st = path.stat()
    if seed_hash(str(path), st.st_size, st.st_mtime_ns) != digest:
        raise ValueError('changed original seed snapshot')
    return [dict(path=str(path), n=n, sha256=digest,
                 source='original merged0 seed row '+str(n),
                 licence='own discovered seed confirmed by round27 brief',
                 share=prvs_share(path,n)) for n in sorted(counts)]


import numpy as np
sys.modules['forensics_sources'] = fs
policy.label = lambda info: 'round28 own seed confirmed; source exclusions and prvsiyan share checked'


def fetched_public(path):
    """A fetched notebook or dataset start keeps the public-only share rule."""
    p = Path(path)
    harvest = any(part.startswith('take-harvest-') for part in p.parts)
    if not harvest:
        return False
    if any(part.startswith('public') for part in p.parts):
        return True
    sidecar = Path(str(p)+'.json')
    if p.parent.name == 'inputs' and sidecar.exists():
        return json.loads(sidecar.read_text()).get('kind') in ('fresh-public','reopened-public')
    return False


def share_gate(path, n):
    return prvs_share(path, n) if fetched_public(path) else 0.0


policy.label = lambda info: 'own layouts allowed by 00:19 rule; fetched public starts share checked'
