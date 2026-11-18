"""Run the round 38 rectangle queue and first 900 second fresh follows."""
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time
from threading import Lock, Semaphore

sys.dont_write_bytecode = True
CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
import forensics_r37 as prior
import forensics_compose as compose
import forensics_rect as rectangles

ROOT = prior.ROOT
TAKE = ROOT / 'take-forensics-r38'
WORK = TAKE / 'work'
HANDOFF = ROOT / 'handoff-r38.log'
BAR = ROOT / 'round38-briefs/bar38.tsv'
HELD = ROOT / 'gather/round37-2026-11-18a.csv'
REMOTE = '$SCRATCH/squares-forensics-r38'
PY = prior.PY
DEADLINE = datetime.fromisoformat('2026-11-18T13:45:00+00:00').timestamp()
LAST_WALK = DEADLINE - 3600
MIN_GAIN = 1e-10
SLOTS = 3
HANDOFF_LINE = re.compile(r'^(\S+) ([\w-]+) -> [\w,.-]+: (.*)$')
PACKING_PATH = re.compile(r'$SCRATCH/bounties-squares/take-[\w-]+-r38/[^\s,;()]+?\.csv(?=$|[\s,;)])')
AUDIT_TEXT = re.compile(r'deep25|\bunwalked\b|/work/(?:walks|final-audit|walkcache)/', re.I)


def state(message):
    with (TAKE / 'STATE.txt').open('a') as output:
        output.write(f'{prior.now()} boxA {message}\n')


def handoff(message):
    with HANDOFF.open('a') as output:
        output.write(f'{prior.now()} forensics -> all: {message}\n')


def load(path):
    return json.loads(path.read_text())


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'{path.name}.{time.time_ns()}.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def immutable(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f'immutable file changed: {path}')
        return
    temporary = path.with_name(f'{path.name}.{time.time_ns()}.tmp')
    temporary.write_bytes(data)
    temporary.replace(path)


def record(path, value):
    data = json.dumps(value, indent=2) + '\n'
    if AUDIT_TEXT.search(data):
        raise ValueError(f'audit text in source record: {path}')
    immutable(path, data.encode())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path):
    return Path(f'{path}.json')


def table(path):
    try:
        with path.open() as handle:
            return {int(row['n']): row for row in csv.DictReader(handle, delimiter='\t')}
    except FileNotFoundError:
        return {}


@functools.lru_cache(maxsize=1)
def bars():
    return {count: float(row['bar']) for count, row in table(BAR).items()}


def live(exclude_own=False):
    scores = {}
    for filename in ROOT.glob('take-*-r38/take.tsv'):
        if exclude_own and filename.parent == TAKE:
            continue
        for n, row in table(filename).items():
            score = float(row['new'])
            scores[n] = min(scores.get(n, math.inf), score)
    return scores


def target(n):
    return min(bars()[n], live().get(n, math.inf))


def geometry(path):
    layouts = rectangles.layouts(path)
    if len(layouts) != 1:
        raise ValueError(f'expected one layout: {path}')
    n, squares = next(iter(layouts.items()))
    side, _ = compose.frame(squares)
    return n, float(side) / math.sqrt(n) - 1, prior.geometry_key(squares)


def stop_for_peer(start, bar, peer):
    return peer < min(start, bar) - 1e-6


def improves(n, score):
    return bars()[n] - score > MIN_GAIN and score < live().get(n, math.inf)


def complete(receipt):
    return (receipt.get('end') is not None and all(
        any(bool(step['flags']) == polish and step.get('end') is not None and math.isfinite(step['end'])
            for step in receipt.get('steps', ())) for polish in (False, True)))


def read_handoff():
    # Only the current round's bounded, append-only feed enters the scheduler.
    with HANDOFF.open(errors='replace') as handle:
        return [line.rstrip('\n') for line in handle if line.endswith('\n')]


def sources(lines):
    for line in lines:
        match = HANDOFF_LINE.match(line)
        if not match:
            continue
        when, producer, body = match.groups()
        if producer == 'forensics' or not re.match(r'certified\b', body, flags=re.I):
            continue
        paths = PACKING_PATH.findall(body)
        if not paths:
            continue
        path = Path(paths[-1])
        near = '/near/' in str(path)
        if near and (producer != 'k123' or not re.match(r'certified near donor\b', body, re.I)):
            continue
        if not path.parent.name.startswith(f'take-{producer}-r38') and not near:
            continue
        digest = re.search(r'\bsha256[=: ]+([0-9a-f]{12,64})\b', body, re.I)
        yield dict(path=str(path), producer=producer, when=when, near=near, line=body,
                   announced_sha=digest[1] if digest else None)


def earlier_seed(body, producer, job):
    digest = job['sha256']
    signature = job['geometry']
    lower = body.lower()
    if digest[:12] in lower or signature[:12] in lower:
        return True
    pin = re.search(r'\bsha256[=: ]+([0-9a-f]{12,64})\b', lower)
    if not pin:
        return job['path'].lower() in lower
    count = job['n']
    root = ROOT / f'take-{producer}-r38'
    candidates = [Path(path) for path in PACKING_PATH.findall(body)]
    candidates.append(root / 'work' / 'starts' / pin[1][:16] / f'{count}.csv')
    for path in candidates:
        if path.is_file() and sha(path).startswith(pin[1]) and geometry(path)[2] == signature:
            return True
    return False


def claim(job):
    n = job['n']
    digest = job['sha256']
    kind = job['kind']
    marker = f'claim {kind} n={n} geometry={job["geometry"]} sha256={digest}'
    line = f'{marker}, {job["path"]}'
    if not any(line in entry for entry in read_handoff()):
        handoff(line)
        time.sleep(5)
    for entry in read_handoff():
        if line in entry:
            return True
        match = HANDOFF_LINE.match(entry)
        if not match or match[2] == 'forensics':
            continue
        producer, body = match[2], match[3]
        lowered = body.lower()
        if not re.match(r'claims?\b', lowered) or not re.search(rf'\bn\s*=?\s*{n}\b', lowered):
            continue
        shared_composer = kind == 'composer' and 'composer' in lowered
        shared_seed = kind in ('fresh-900', 'donor-900') and '900' in lowered and earlier_seed(body, producer, job)
        if shared_composer or shared_seed:
            release = f'release {marker}; earlier {producer} claim covers the same work, {job["path"]}'
            if not any(release in record for record in read_handoff()):
                handoff(release)
                state(f'CLAIM-RELEASE {kind} n={n}; earlier {producer} claim covers the same work')
            return False
    return False


def ssh(command, timeout=45):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                           '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
                           'boxE', command], capture_output=True, text=True, errors="replace", timeout=timeout, check=True)


def remote_workers(tag=''):
    return [line for line in ssh('ps -axo pid,command').stdout.splitlines()
            if f'{REMOTE}/jobs/{tag}' in line and line.split()[0].isdigit()]


def reap_remote(tag):
    owned = remote_workers(tag)
    for signal in ('TERM', 'KILL'):
        if not owned:
            break
        pids = ' '.join(line.split()[0] for line in owned)
        ssh(f'kill -{signal} {pids} 2>/dev/null || true')
        time.sleep(1)
        owned = remote_workers(tag)
    if owned:
        raise RuntimeError(f'remote processes remain for {tag}')


def run_remote(inp, job_id, n, kind, end, start_score=None, seed=0, collide=False):
    """Persist downloaded outputs before accepting a completed numerical job."""
    local = WORK / 'fq' / f'{job_id}.csv'
    receipt_file = metadata(local)
    if receipt_file.exists():
        receipt = load(receipt_file)
        if receipt.get('input_sha256') == sha(inp) and (
                receipt.get('end') is None or local.is_file() and receipt['output_sha256'] == sha(local)):
            return local, receipt
        raise ValueError(f'numerical receipt bytes changed: {receipt_file}')
    if time.time() >= end - 30:
        return local, {'end': None, 'closed': 'deadline'}
    local.parent.mkdir(exist_ok=True)
    remote_in, remote_out = (f'{REMOTE}/jobs/{job_id}{part}.csv' for part in ('-start', '-out'))
    if remote_workers(job_id):
        reap_remote(job_id)
    subprocess.run(['scp', '-q', str(inp), f'boxE:{remote_in}'], timeout=90, check=True)
    side = (target(n) + 1) * math.sqrt(n)
    command = ['env', 'OPENBLAS_NUM_THREADS=1', 'OMP_NUM_THREADS=1', 'nohup', 'nice', '-n', '5',
               f'{prior.RBASE}/venv/bin/python', '-I', f'{REMOTE}/code/forensics_r37.py']
    if kind in ('fresh-900', 'donor-900', 'producer-180', 'control'):
        seconds = {'fresh-900': 900, 'donor-900': 900, 'producer-180': 180, 'control': 3}[kind]
        if time.time() + seconds + 30 >= end:
            return local, {'end': None, 'closed': 'deadline'}
        command += ['freshkick', remote_in, remote_out, str(n), str(seconds), str(seed), repr(side), repr(end)]
    else:
        command += ['fqloop', remote_in, remote_out, repr(side), repr(end), str(int(collide))]
    with subprocess.Popen(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
                           '-o', 'ServerAliveInterval=10', '-o', 'ServerAliveCountMax=2',
                           'boxE', 'exec ' + shlex.join(command)],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace") as process:
        state(f'START boxE {kind} n={n} {job_id}; SSH pid={process.pid}; input={inp}; '
              f'receipt={receipt_file}; deadline={datetime.fromtimestamp(end, timezone.utc).isoformat()}')
        while True:
            try:
                _, error = process.communicate(timeout=10)
                break
            except subprocess.TimeoutExpired:
                peer = live(exclude_own=True).get(n, math.inf)
                overtaken = start_score is not None and stop_for_peer(start_score, bars()[n], peer)
                fallback = kind == 'donor-900' and donor_closed(n)
                if overtaken or fallback or time.time() >= end:
                    try:
                        reap_remote(job_id)
                    finally:
                        process.kill()
                        process.communicate()
                    why = 'donor count closed' if fallback else 'peer' if overtaken else 'deadline'
                    state(f'STOP boxE {kind} n={n} {job_id} reason={why} peer={peer}')
                    return local, {'end': None, 'closed': why}
        if process.returncode:
            raise RuntimeError(f'{job_id}: {error[-400:]}')
    temp = local.with_suffix('.download')
    subprocess.run(['scp', '-q', f'boxE:{remote_out}.json', str(temp)], timeout=90, check=True)
    receipt = load(temp)
    temp.unlink()
    if receipt.get('end') is not None:
        subprocess.run(['scp', '-q', f'boxE:{remote_out}', str(temp)], timeout=90, check=True)
        remote_hash = ssh(f'shasum -a 256 {shlex.quote(remote_out)}').stdout.split()[0]
        if sha(temp) != remote_hash:
            raise ValueError(f'copy verification failed for {job_id}')
        temp.replace(local)
        receipt['output_sha256'] = remote_hash
    receipt.update(input_sha256=sha(inp), kind=kind, n=n)
    save(receipt_file, receipt)
    state(f'FINISH boxE {kind} n={n} {job_id} start={receipt["start"]!r} end={receipt["end"]!r} '
          f'full_fq={complete(receipt)} steps={len(receipt["steps"])}')
    return local, receipt


def walker(path, end=LAST_WALK + 1800):
    if time.time() >= LAST_WALK:
        return {'clean': False, 'capped': True, 'hits': ['final walk cutoff']}
    command = [PY, '-B', '-I', str(CODE / 'forensics_walk38.py'), str(path)]
    with local_slots:
        if time.time() >= LAST_WALK:
            return {"clean": False, "capped": True, "hits": ["final walk cutoff"]}
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=max(1, min(1800, end - time.time())))
    if not result.stdout.strip():
        raise RuntimeError(result.stderr[-500:])
    return json.loads(result.stdout.splitlines()[-1])


def layout_row(path, n):
    return table(path.parent / 'take.tsv').get(n, {})


def source_licence(path, n):
    notices = [layout_row(path, n).get('licence', '')]
    for suffix in ('.json', '.source.json', '.origin.json', '.provenance.json'):
        info = Path(str(path) + suffix)
        if info.is_file():
            value = load(info)
            if isinstance(value, dict):
                notices.extend(value.get(key, '') for key in ('licence', 'license'))
                source = value.get('source')
                if isinstance(source, dict):
                    notices.extend(source.get(key, '') for key in ('licence', 'license'))
    return '; '.join(sorted({label for notice in notices for label in prior.approved_notices(notice)}))


def accepted(proof, licence):
    return (proof.get('clean') and not proof.get('capped', True) and
            (not proof.get('pubfirst') or bool(licence)))


def source_record(path, n, licence):
    return dict(n=n, licence=licence, parent=f'{path} (sha256 {sha(path)})')


def snapshot(path, n, licence, proof, digest):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f"source bytes changed during snapshot: {path}")
    identity = hashlib.sha256(str(path).encode()).hexdigest()[:12]
    snap = WORK / 'sources' / f'{digest}-{identity}' / f'{n}.csv'
    immutable(snap, data)
    record(metadata(snap), dict(n=n, licence=licence, parent=f"{path} (sha256 {digest})"))
    save(snap.parent / 'dispatch-proof.json', dict(sha256=digest, proof=proof))
    producer_row = layout_row(path, n)
    if producer_row and sha(path) == digest:
        capture = snap.parent / 'producer-row-capture.json'
        if not capture.exists():
            save(capture, dict(path=str(path), sha256=digest, row=producer_row))
    return snap


def rect_scan(folder, args):
    folder.mkdir(parents=True, exist_ok=True)
    details = folder / 'details.csv'
    scores = live()
    with details.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(('n', 'L', 'score'))
        for n, bar in bars().items():
            score = min(bar, scores.get(n, math.inf))
            writer.writerow((n, (score + 1) * math.sqrt(n), score))
    command = [PY, '-B', '-I', str(CODE / 'forensics_rect.py'), str(details), str(folder / 'raw')] + args
    with local_slots, (folder / 'rect.log').open('w') as log:
        subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT,
                       timeout=max(1, min(600, LAST_WALK - time.time())))
    return list((folder / 'raw').glob('*.csv'))


def raw_parents(raw, snap, licence):
    meta = load(metadata(raw))
    parents = []
    for tag in ('A', 'B'):
        part = meta.get(tag)
        if not part:
            continue
        name, n = part['source']
        path = Path(name)
        if path == HELD:
            parents.append(dict(n=n, path=name, held=f'held n={n} of round 37'))
        elif path == snap:
            parents.append(source_record(path, n, licence))
        else:
            raise ValueError(f'unwalked rectangle source: {name}')
    if not parents:
        raise ValueError(f'rectangle without ancestry: {raw}')
    return parents


def job_key(kind, n, signature):
    return f'{kind}-{n}-{signature[:24]}'


def queue_job(kind, path, licence, parents, *, donor_score=None):
    n, score, signature = geometry(path)
    key = job_key(kind, n, signature)
    desk = WORK / 'jobs' / f'{key}.json'
    if desk.exists():
        return
    entry = dict(id=key, n=n, kind=kind, path=str(path), score=score, geometry=signature,
                 sha256=sha(path), licence=licence, parents=parents, at=prior.now())
    if donor_score is not None:
        entry['donor_score'] = donor_score
    save(desk, entry)
    state(f'QUEUE {kind} n={n} {key} score={score!r} from {path}')


def donor_closed(n):
    if (WORK / 'fallbacks' / f'{n}.json').is_file():
        return True
    for line in read_handoff():
        match = HANDOFF_LINE.match(line)
        if match and match[2] in ('k123', 'classfill', 'backlog') and re.match(
                rf'CLOSED donor count n={n}\b', match[3], re.I):
            return True
    return False


def donor_allowed(source, n, score, digest, signature):
    if n in {367, 372, 591, 634, 642} or not -MIN_GAIN <= score - bars()[n] <= 1e-7:
        return False
    metadata_line = source['line']
    share = re.search(r'held_share_1e3=([0-9.eE+-]+)', metadata_line)
    sha_field = re.search(r'\bsha256=([0-9a-f]{64})\b', metadata_line)
    if not share or float(share[1]) >= 0.5 or not sha_field or sha_field[1] != digest:
        return False
    if donor_closed(n) or target(n) < bars()[n] - MIN_GAIN:
        return False
    if (WORK / 'jobs' / f'{job_key("donor-900", n, signature)}.json').exists():
        return False
    for logfile in (ROOT / 'handoff-r37.log', HANDOFF):
        with logfile.open(errors='replace') as handle:
            for line in handle:
                if 'claim' in line.lower() and '900' in line and (
                        digest[:16] in line or signature[:16] in line or source['path'] in line):
                    return False
    return True


def claim_source(kind, path, n, signature):
    return claim(dict(kind=kind, n=n, sha256=sha(path), geometry=signature, path=str(path)))


def prepare_source(source, progress):
    path = Path(source['path'])
    if not path.is_file():
        return 'missing'
    digest = sha(path)
    announced = source.get('announced_sha')
    if announced and not digest.startswith(announced):
        return 'waiting for matching take row'
    n, score, signature = geometry(path)
    near = source['near']
    held_pick = path.parent == WORK / 'held-picks'
    origin = 'held' if held_pick else 'fresh'
    composed = WORK / 'compositions' / f'{origin}-{n}-{signature}.json'
    if not near and composed.exists():
        return 'geometry already composed'
    if near and not donor_allowed(source, n, score, digest, signature):
        return 'ineligible donor'
    if not near and path.parent != WORK / 'held-picks':
        listed = layout_row(path, n)
        if not listed or abs(float(listed['new']) - score) > MIN_GAIN:
            return 'waiting for matching take row'
        if bars()[n] - score <= MIN_GAIN:
            return 'at held bar'
    if (progress / 'walk.json').exists():
        proof = load(progress / 'walk.json')
    else:
        proof = walker(path)
        save(progress / 'walk.json', proof)
    licence = source_licence(path, n)
    if sha(path) != digest:
        return 'bytes changed during walk'
    if not accepted(proof, licence):
        state(f'REFUSE source n={n} {path} licence={licence!r} files={proof.get("files")} '
              f'capped={proof.get("capped")} hits={str(proof.get("hits"))[:240]}')
        return 'failed source proof'
    state(f'WALK source n={n} {path} files={proof["files"]} capped={proof["capped"]} sha256={digest}')
    if not licence:
        licence = 'own submitted or constructed packing'
    snap = snapshot(path, n, licence, proof, digest)
    if near:
        if claim_source('donor-900', path, n, signature):
            queue_job('donor-900', snap, licence, [source_record(snap, n, licence)], donor_score=score)
        return 'donor settled'
    if (not held_pick and score <= target(n) + 2e-11 and time.time() + 1200 < LAST_WALK and
            not (WORK / 'jobs' / f'{job_key("fresh-900", n, signature)}.json').exists() and
            claim_source('fresh-900', path, n, signature)):
        queue_job('fresh-900', snap, licence, [source_record(snap, n, licence)])
    if not held_pick and not claim_source('composer', path, n, signature):
        return 'composer already claimed'
    cache = progress / 'windows.pkl'
    shutil.copyfile(WORK / 'windows38.pkl', cache)
    args = ['--cache', str(cache), '--fresh-only', '--keep', '8', '--per-n', '8', '--max-mesh', '400',
            '--strict-single', '--skip-ties', '--slack', '0' if held_pick else '0.004']
    if not held_pick:
        args += ['--collide', '0.03']
    begin = time.time()
    try:
        packed = rect_scan(progress, args + [str(snap)])
    finally:
        cache.unlink(missing_ok=True)
    for raw in packed:
        queue_job('rectangle', raw, licence, raw_parents(raw, snap, licence))
    save(composed, dict(n=n, source=str(path), sha256=digest, starts=len(packed)))
    state(f'FINISH composer n={n} {path} starts={len(packed)} seconds={time.time() - begin:.1f}; '
          f'log={progress / "rect.log"}')
    return 'composed'


def write_take(rows):
    filename = TAKE / 'take.tsv'
    temporary = filename.with_name(f'{filename.name}.{time.time_ns()}.tmp')
    with temporary.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, ('n', 'held', 'new', 'gain', 'source', 'licence'), delimiter='\t')
        writer.writeheader()
        writer.writerows(rows[n] for n in sorted(rows))
    temporary.replace(filename)


def export(job, final, proof, score):
    with publication_lock:
        n = job['n']
        rows = table(TAKE / 'take.tsv')
        digest = sha(final)
        if not improves(n, score):
            current = rows.get(n, {})
            if str(final) in current.get('source', '') and current.get('new') == repr(score):
                announce(job, proof, score, digest)
                return True
            return False
        alias = TAKE / f'{n}.csv'
        source = (f'forensics round 38 {job["kind"]}. Certified packing {final} (sha256 {digest}). '
                  f'Inputs {source_credits(job["parents"])}')
        alias_info = dict(n=n, parent=f'{final} (sha256 {digest})', licence=job['licence'])
        temporary = alias.with_suffix(f'.csv.{job["id"]}.tmp')
        shutil.copyfile(final, temporary)
        temporary.replace(alias)
        save(metadata(alias), alias_info)
        rows[n] = dict(n=n, held=repr(bars()[n]), new=repr(score), gain=repr(bars()[n] - score),
                       source=source, licence=job['licence'])
        write_take(rows)
        announce(job, proof, score, digest)
        state(f'PUBLISH n={n} score={score!r} gain={bars()[n] - score:.3e} sha256={digest} source={final}')
        return True


def source_credits(parents):
    from forensics_watch34 import gather_notices

    credits = set()
    for node in parents:
        if 'held' in node:
            notices = gather_notices({'A': {'source': [node['path'], node['n']]}})
            credits.update(notice['ledger'] for notice in notices)
            credits.add(node['path'])
        elif 'parent' in node:
            credits.add(node['parent'].split(' (sha256 ', 1)[0])
    return ', '.join(sorted(credits))


def announce(job, proof, score, digest):
    n = job['n']
    fingerprint = f'sha256={digest}, {TAKE}/{n}.csv'
    if not any(' forensics -> all: certified ' in line and fingerprint in line for line in read_handoff()):
        handoff(f'certified n={n} score={score!r}, gain={bars()[n] - score:.3e}, {job["kind"]}, '
                f'walk files={proof["files"]} capped={proof["capped"]}, {fingerprint}')


def certify_file(path, n, destination):
    score, rows = prior.certify(path, n)
    if score is None:
        return None
    destination.parent.mkdir(parents=True, exist_ok=True)
    prior.write_rows(destination, rows)
    return score


def pending_file(job):
    return WORK / 'pending-finishes' / f'{job["id"]}.json'


def finish(job, record_only=False):
    """Recover from the recorded first winner or from its immutable final record."""
    n, key, kind = job['n'], job['id'], job['kind']
    journal = pending_file(job)
    pending = load(journal)
    raw = Path(pending['output'])
    loops = [pending['receipt']]
    folder = WORK / 'published' / key
    final = folder / f'{n}.csv'
    if metadata(final).is_file():
        item = load(metadata(final))
        if sha(final) != item['take_sha256']:
            raise ValueError(f'final packing bytes changed: {final}')
        score = item['score']
    else:
        first = folder / 'first.csv'
        score = certify_file(raw, n, first)
        if score is None or not improves(n, score):
            return 'first certification was above target'
        best = first
        # A material own find receives its producer follow before the handoff line.
        material = job['score'] - score > 2e-10 or kind in ('fresh-900', 'rectangle', 'donor-900') and (
            bars()[n] - score > 2e-10 and (live(exclude_own=True).get(n, math.inf) - score > 2e-10))
        if material and time.time() + 300 < LAST_WALK:
            record(metadata(first), dict(n=n, licence=job['licence'], parents=job['parents']))
            pre_follow = folder / 'producer-dispatch-proof.json'
            proof = load(pre_follow) if pre_follow.exists() else walker(first)
            save(pre_follow, proof)
            if accepted(proof, job['licence']):
                extra, receipt = run_remote(first, key + '-producer', n, 'producer-180', LAST_WALK,
                                            start_score=score, seed=int(job['geometry'][:8], 16))
            else:
                receipt = {}
                state(f'REFUSE producer follow n={n} files={proof.get("files")} hits={str(proof.get("hits"))[:240]}')
            if complete(receipt):
                improved = folder / 'after-producer.csv'
                second = certify_file(extra, n, improved)
                if second is not None and second < score:
                    score, best = second, improved
                    loops.append(receipt)
        fq_start = best
        polished, receipt = run_remote(fq_start, key + '-certified', n, 'certified-fq', LAST_WALK)
        if not complete(receipt):
            return 'certified-file fq loop incomplete'
        loops.append(receipt)
        last = folder / 'after-fq.csv'
        polished_score = certify_file(polished, n, last)
        if polished_score is not None and polished_score < score:
            score, best = polished_score, last
        if not improves(n, score):
            return 'certification fell behind live row'
        immutable(final, best.read_bytes())
        record(metadata(final), dict(n=n, score=score, take_sha256=sha(final), licence=job['licence'],
                                      parents=job['parents'], method=kind, fq_receipts=loops,
                                      certified_fq_input=str(fq_start)))
    if record_only:
        return 'final record written'
    proof_file = folder / 'publication-proof.json'
    if proof_file.exists():
        saved = load(proof_file)
        if saved['sha256'] != sha(final) or saved['record_sha256'] != sha(metadata(final)):
            raise ValueError(f'publication proof bytes changed: {final}')
        proof = saved['walk']
    else:
        if not improves(n, score):
            existing = table(TAKE / 'take.tsv').get(n, {})
            if str(final) in existing.get('source', '') and float(existing['new']) == score:
                raise RuntimeError('published record lacks its immutable walk receipt')
            return 'pre-walk superseded'
        state(f'START final source walk n={n} {final}; cap=100000; log={proof_file}')
        proof = walker(final)
        save(proof_file, dict(sha256=sha(final), record_sha256=sha(metadata(final)), walk=proof))
    if not accepted(proof, job['licence']):
        state(f'REFUSE final n={n} {final} files={proof.get("files")} capped={proof.get("capped")} '
              f'hits={str(proof.get("hits"))[:240]}')
        return 'final proof refused'
    if export(job, final, proof, score):
        return 'published'
    return 'already published or superseded'


def done_file(job):
    return WORK / 'completed' / f'{job["id"]}.json'


def execute(job):
    n, key, kind = job['n'], job['id'], job['kind']
    path = Path(job['path'])
    pending = pending_file(job)
    if pending.is_file():
        result = finish(job)
    elif time.time() >= LAST_WALK - 120:
        result = 'cutoff'
    elif kind == 'fresh-900' and job['score'] > target(n) + 2e-11:
        result = 'superseded before seed'
    elif kind == 'donor-900' and (stop_for_peer(job['score'], bars()[n], target(n)) or donor_closed(n)):
        result = 'superseded or fell back before donor seed'
    elif kind == 'rectangle' and (job['score'] - target(n)) * math.sqrt(n) > 0.008:
        result = 'rectangle fell behind live target'
    else:
        if sha(path) != job['sha256']:
            raise ValueError(f'queued packing bytes changed: {path}')
        out, receipt = run_remote(path, key, n, kind, LAST_WALK - 60,
                                  start_score=job['score'] if kind.endswith('900') else None,
                                  seed=int(job['geometry'][:8], 16),
                                  collide=kind == 'rectangle' and path.name.split('-')[1].startswith('c'))
        if not complete(receipt):
            result = receipt.get('closed', 'incomplete full fq loop')
        else:
            score = receipt['end'] / math.sqrt(n) - 1
            if improves(n, score):
                save(pending, dict(output=str(out), receipt=receipt, n=n, job=job))
                result = finish(job)
            else:
                result = f'no gain: score={score:.17g}'
                if kind == 'donor-900':
                    donor_endpoint(job, out, score)
    save(done_file(job), dict(at=prior.now(), result=result, n=n, kind=kind))
    pending.unlink(missing_ok=True)
    state(f'DONE {key} {result}')
    return result


def donor_endpoint(job, path, score):
    from scipy.spatial import cKDTree
    import numpy as np
    n = job['n']
    held = next(iter(rectangles.layouts(held_packing(n)).values()))
    _, clean = compose.frame(held)
    tree = cKDTree(clean[:, :2])
    side, candidate = compose.frame(next(iter(rectangles.layouts(path).values())))
    same = any(float(np.max(tree.query(q[:, :2])[0])) < 1e-3 for _, q in rectangles.sym8(candidate, side))
    current = WORK / 'donor-endpoints' / f'{job["id"]}.json'
    previous = [load(p) for p in current.parent.glob(f'donor-900-{n}-*.json') if p != current]
    repeat = any(abs(score - item['score']) <= MIN_GAIN for item in previous)
    if same or repeat:
        save(WORK / 'fallbacks' / f'{n}.json', dict(job=job['id'], score=score, held=same, repeated=repeat))
    save(current, dict(score=score, job=job['id'], held=same, repeated=repeat))


def held_packing(n, rows=None):
    path = WORK / 'held-picks' / f'{n}.csv'
    if not path.exists():
        if rows is None:
            with HELD.open() as handle:
                rows = [row for row in csv.DictReader(handle) if int(row['n']) == n]
        if len(rows) != n:
            raise ValueError(f'held count {n} has {len(rows)} rows')
        path.parent.mkdir(exist_ok=True)
        prior.write_rows(path, rows)
        record(metadata(path), dict(n=n, parent=str(HELD), held=f'held n={n} of round 37'))
    return path


def held_picks():
    result = CODE / 'results/round37-best-2026-11-18.tsv'
    groups = {n: [] for n in table(result)}
    with HELD.open() as handle:
        for row in csv.DictReader(handle):
            n = int(row['n'])
            if n in groups:
                groups[n].append(row)
    return [dict(path=str(held_packing(n, rows)), near=False, producer='held', at=prior.now())
            for n, rows in groups.items()]


@functools.lru_cache(maxsize=4096)
def version_digest(path, size, stamp):
    return sha(path)


def source_key(source):
    path = Path(source['path'])
    try:
        info = path.stat()
        digest = version_digest(path, info.st_size, info.st_mtime_ns)
    except FileNotFoundError:
        return None
    announced = source.get('announced_sha')
    if announced and not digest.startswith(announced):
        return None
    return hashlib.sha256(f'{path}:{digest}'.encode()).hexdigest()[:24]


def run_source(source, folder):
    folder.mkdir(parents=True, exist_ok=True)
    state(f'START source {source["path"]}; source work={folder}; walk cutoff=12:45 UTC')
    reason = prepare_source(source, folder)
    save(folder / 'done.json', dict(result=reason, source=source['path'], time=time.time()))
    return reason


def queued(active, has_fresh):
    kind_rank = {'fresh-900': 1, 'rectangle': 2, 'donor-900': 3}
    jobs = []
    for path in (WORK / 'jobs').glob('*.json'):
        job = load(path)
        if job['id'] in active or done_file(job).exists():
            continue
        pending = pending_file(job).is_file()
        if job['kind'] == 'donor-900' and has_fresh and not pending:
            continue
        jobs.append((0 if pending else kind_rank[job['kind']], job['score'] - target(job['n']), job['id'], job))
    return [task[-1] for task in sorted(jobs)]


def driver():
    (WORK / 'driver.pid').write_text(str(os.getpid()) + '\n')
    source_pool = ThreadPoolExecutor(max_workers=2)
    boxE = ThreadPoolExecutor(max_workers=SLOTS)
    source_tasks, runs, retry = {}, {}, {}
    opening = held_picks()
    heartbeat = 0
    idle = False
    while time.time() < LAST_WALK and not (WORK / 'STOP').exists():
        for active in (source_tasks, runs):
            for key, future in list(active.items()):
                if not future.done():
                    continue
                del active[key]
                try:
                    future.result()
                    retry.pop(key, None)
                except Exception as error:
                    state(f'RETRY {key} after {error!r}')
                    retry[key] = time.time() + 90
        now = time.time()
        lines = read_handoff()
        newcomers = {item['path']: item for item in sources(lines)}
        items = sorted(newcomers.values(), key=lambda src: (src['near'], src['when'])) + opening
        fresh_to_prepare = False
        for source in items:
            key = source_key(source)
            if not key or now < retry.get(key, 0):
                continue
            if key in source_tasks:
                fresh_to_prepare |= not source['near']
                continue
            folder = WORK / 'scans' / key
            finished = folder / 'done.json'
            if finished.exists():
                settled = load(finished)
                again = settled['result'] == 'waiting for matching take row'
                if not again or now - settled['time'] < 90:
                    continue
            if source['near'] and (source_tasks or runs or fresh_to_prepare):
                continue
            fresh_to_prepare |= not source['near']
            if len(source_tasks) < 2 and now + 180 < LAST_WALK:
                source_tasks[key] = source_pool.submit(run_source, source, folder)
        candidates = queued(runs, fresh_to_prepare)
        for job in candidates:
            if len(runs) == SLOTS:
                break
            if now >= retry.get(job['id'], 0):
                runs[job['id']] = boxE.submit(execute, job)
        new_idle = not runs and not source_tasks
        if new_idle and not idle:
            state('IDLE no eligible fresh source or donor; no numerical workers running')
        idle = new_idle
        if now >= heartbeat:
            try:
                owned = remote_workers()
            except (OSError, subprocess.SubprocessError) as error:
                state(f'HEALTH boxE status failed {error!r}')
                owned = []
            logical = [line for line in owned if '/code/forensics_r37.py ' in line]
            state(f'HEALTH boxE numerical workers={len(logical)}/{SLOTS} pids={[line.split()[0] for line in logical]}; '
                  f'active_jobs={list(runs)} active_sources={list(source_tasks)} take={sorted(table(TAKE / "take.tsv"))}')
            heartbeat = now + 300
        time.sleep(5)
    state('STOP source intake at the final-walk cutoff; collecting active receipts')
    source_pool.shutdown()
    boxE.shutdown()
    state('FINISH driver; all local worker futures settled')


publication_lock = Lock()
local_slots = Semaphore(2)

if __name__ == '__main__':
    driver()
