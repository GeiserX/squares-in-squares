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

import forensics_sources as fs
import forensics_policy as policy
import forensics_watch as fw

SCRATCH = Path('$SCRATCH/bounties-squares')
WORK = SCRATCH / 'take-forensics-r26/work'
MAC = '$SCRATCH/squares-forensics'
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
        if (str(path).startswith(str(WORK/'feed')+'/') and path.name.endswith('.origin.json') and
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


def strict_uncached(path, n, scratch=SCRATCH):
    """Check retained parents and all declared root notices."""
    path = Path(path)
    try:
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
        # This dated quench deferral describes an old audit, not a donor.
        policy_text = re.sub(r'\(deferred at \d{2}:\d{2}Z for an unresolved Samanyu label\)', '', text)
        seed = policy.classify_text(policy_text)
        forbidden = ('penguin069/squares-joegun-boxed-certified-union',
                     'prvsiyan/squares-verified-best-of-1105', 'CC BY-SA',
                     'Samanyu-dev/squares_in_squares', 'seed merged0', 'original clean seed', '921r25c921', '921mo16.F1d', '863-0f92c19d-n.csv', '921-29e12ff3.csv')
        allowed = seed['status'] == 'none' and not any(v in text for v in forbidden)
        def declarations(item):
            if isinstance(item, dict):
                if item.get('seed_policy', {}).get('status', 'none') != 'none':
                    return False
                return all(declarations(v) for k, v in item.items() if k != 'record')
            return all(declarations(v) for v in item) if isinstance(item, list) else True
        allowed = allowed and declarations(proof)
        return allowed, dict(reason='round26 clean ancestry' if allowed else 'excluded or unresolved root',
                             ancestry=compact, notices=notices, seed_policy=seed,
                             full_ancestry=dict(path=str(derivation), sha256=derivation_sha))
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
    """The round 26 bar is the submitted round 25 b file."""
    return {int(r['n']): float(r['score']) for r in csv.DictReader(
        open(scratch / 'gate/cand-round25-1114b/details.csv'))}


def admission_priority(path):
    """New joins and certified r25 files precede the near archive."""
    if 'take-k123-r26/' in str(path):
        rank = 0
    elif re.fullmatch(r'take-.+-r26', path.parent.name):
        rank = 1
    elif '/work/interior/' in str(path):
        rank = 2
    elif '-r26/' in str(path):
        rank = 3
    else:
        rank = 4
    return rank, -path.stat().st_mtime


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
    for path in sorted(files, key=admission_priority):
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
        token = [[str(p),p.stat().st_size,p.stat().st_mtime_ns] for p in dependencies if p.exists()]
        saved = successes.get(str(path))
        if saved and saved['token'] == token and Path(saved['dest']).exists():
            allowed.append(Path(saved['dest']))
            continue
        prior = refusals.get(str(path))
        if prior and prior['token'] == token and time.time()-prior['at'] < 600:
            continue
        if inspected >= 32:
            break
        inspected += 1
        (work/'active-admission.json').write_text(json.dumps(dict(path=str(path),n=n,at=time.time())))
        ok, proof = strict(path, n, scratch)
        audit.append(dict(path=str(path), n=n, admitted=ok, reason=proof['reason']))
        if not ok:
            refusals[str(path)] = dict(token=token,at=time.time(),reason=proof['reason'])
            continue
        refusals.pop(str(path),None)
        payload = path.read_bytes()
        after = [[str(p),p.stat().st_size,p.stat().st_mtime_ns] for p in dependencies if p.exists()]
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
            proof_file = work / 'proofs' / (digest + '.json')
            proof_file.parent.mkdir(exist_ok=True)
            proof_file.write_text(json.dumps(proof, indent=2))
            origin.write_text(json.dumps(dict(path=str(path), n=n, verified_ancestry=True,
                snapshot_sha256=digest, ancestry=proof, source_proof=str(proof_file),
                full_ancestry=proof['full_ancestry'])))
        allowed.append(dest)
        successes[str(path)] = dict(token=token,dest=str(dest))
        mapping[str(dest)] = str(dest.relative_to(feed))
    success_file.write_text(json.dumps(successes))
    refusals_file.write_text(json.dumps(refusals))
    indexfile.write_text(json.dumps(mapping))
    (work / 'source-admission.json').write_text(json.dumps(audit, indent=2))
    return allowed


def start_scan(args, run, stop):
    """Run the sole rectangle scanner on boxB using immutable inputs."""
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
    match = re.fullmatch(r'(\d+)-(take-[a-z0-9-]+-r26)-([a-f0-9]{12})\.csv', path.name)
    if not match or int(match[1]) != n or not path.exists():
        return False, dict(path=str(path), n=n, reason='unresolved copied start')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if not digest.startswith(match[3]):
        return False, dict(path=str(path), n=n, reason='changed copied start')
    pinned = WORK / 'feed' / match[2] / ('%d-%s.csv' % (n, digest[:24]))
    if not pinned.exists() or hashlib.sha256(pinned.read_bytes()).hexdigest() != digest:
        return False, dict(path=str(path), n=n, reason='missing exact admitted snapshot for copied start')
    ok, proof = fs.trace(pinned, n, scratch, active)
    return ok, dict(path=str(path), n=n, parent=proof, snapshot=str(pinned),
                    sha256=digest, reason='byte-identical copied start with pinned full ancestry')


_trace_before26 = fs._trace

def trace_submitted(path, n, scratch, active=None, recorded=None):
    path = Path(path)
    backlog = Path(scratch) / 'take-backlog-r26'
    if path.parent == backlog / 'work/starts':
        return retained_copy(path, n, scratch, active)
    if path.parent == backlog and path.stem.isdigit():
        row, ledger = fs.record(path, n)
        source = row.get('source', '') if isinstance(row, dict) else ''
        copied = re.search(r'sha256 ([a-f0-9]{64}), copied to ([^ )]+\.csv)', source)
        if copied and 'from the certified round 26 take ' in source:
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
