"""Finish a native join with one producer-owned 180 second follow."""
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

WORK = Path(__file__).resolve().parent
TAKE = WORK.parent
SCRATCH = TAKE.parent
sys.path[:0] = [str(WORK), str(WORK / 'lane')]
from geometry23 import key
import methods_lp
from publication_source26 import check
from publish_certified36 import best_live_score, publish

SSH = ['ssh', '-S', '/tmp/squares-k123-r38-ssh', 'boxE']
SCP = ['scp', '-q', '-o', 'ControlPath=/tmp/squares-k123-r38-ssh']
HANDOFF = SCRATCH / 'handoff-r38.log'
INBOX = WORK / 'own-inbox38'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def log(message, handoff=False):
    stamp = time.strftime('%FT%TZ', time.gmtime())
    line = f'{stamp} k123 -> all: {message}\n'
    for path in [TAKE / 'STATE.txt'] + ([HANDOFF] if handoff else []):
        with path.open('a') as stream:
            stream.write(line)


def atomic(path, value):
    pending = path.with_suffix('.tmp')
    pending.write_text(json.dumps(value, indent=2) + '\n')
    pending.replace(path)


def queue(path, row, result, proof, recipe):
    count = int(row['n'])
    assert result['csv_sha256'] == proof['csv_sha256'] == digest(path)
    assert proof['clean'] and not proof.get('capped')
    geometry = key(count, methods_lp.load(str(path), {count})[count])
    INBOX.mkdir(exist_ok=True)
    record = {'n': count, 'path': str(path), 'row': row, 'result': result, 'proof': proof, 'recipe': recipe}
    packet = INBOX / (geometry + '.json')
    if not packet.exists():
        atomic(packet, record)
        log(f'HOLD native n={count} for its own 180 s follow, {path}. Walk {proof["files"]} files, capped=False.')
    return geometry


def earlier_claim(previous, count, sha, now=None):
    now = time.time() if now is None else now
    for line in previous.splitlines():
        if ' k123 ->' in line or not re.search(r'\bclaim', line, re.I) or re.search(r'\brelease\b', line, re.I):
            continue
        if not re.search(r'\bn\s*=\s*' + str(count) + r'\b', line):
            continue
        try:
            claimed_at = datetime.fromisoformat(line.split(' ', 1)[0]).timestamp()
        except ValueError:
            continue
        duration = re.search(r'\b(180|900)\s*s\b|\b(?:donor|fresh)-(180|900)\b', line)
        seconds = int(duration[1] or duration[2]) if duration else 900
        if now > claimed_at + seconds + 60:
            continue
        if re.search(r'\bheld(?: row| kick| start| n\s*=)', line, re.I):
            if not any(sha.startswith(value) for value in re.findall(r'\b[0-9a-f]{10,64}\b', line)):
                continue
        return True
    return False


def dispatch(token, entry):
    count = entry['n']
    start = Path(entry['path'])
    sha = entry['result']['csv_sha256']
    assert digest(start) == sha
    pin_dir = WORK / 'own-starts38' / token
    pin_dir.mkdir(parents=True, exist_ok=True)
    pin = pin_dir / f'{count}.csv'
    if not pin.exists():
        shutil.copyfile(start, pin)
    assert digest(pin) == sha
    sidecar = Path(str(pin) + '.json')
    if not sidecar.exists():
        atomic(sidecar, entry['row'])
    proof = check(pin, entry['row'])
    if not proof['clean'] or proof['capped']:
        return {'status': 'source-refused', 'hits': proof['hits']}
    score = float(entry['result']['score'])
    if score > best_live_score(count, score) + 1e-12:
        return {'status': 'peer-lower'}
    start_offset = HANDOFF.stat().st_size
    log(f'claim: own 180 s follow n={count}, sha256={sha}, {pin}', handoff=True)
    time.sleep(5)
    with HANDOFF.open('rb') as stream:
        if earlier_claim(stream.read(start_offset).decode(errors='replace'), count, sha):
            return {'status': 'earlier-claim', 'retry_at': time.time() + 60}
    tag = f'own-follow38-{count}-{token[:20]}'
    remote_raw = f'own-starts38/{token}/{count}.csv'
    task = {
        'kind': 'follow37', 'tag': tag, 'n': count, 'out': f'own-follow38/{token}',
        'raw': remote_raw, 'seconds': 180, 'seed': 38180, 'start_score': score, 'start_sha256': sha,
    }
    subprocess.run(SSH + [f'mkdir -p $SCRATCH/squares-k123/own-starts38/{token}'], check=True, timeout=30)
    subprocess.run(SCP + [str(pin), 'boxE:scratch/squares-k123/' + remote_raw], check=True, timeout=60)
    marker = WORK / (tag + '.json')
    atomic(marker, task)
    subprocess.run(SCP + [str(marker), 'boxE:scratch/squares-k123/tasks/' + marker.name + '.incoming'], check=True, timeout=60)
    subprocess.run(SSH + [f'cd $SCRATCH/squares-k123 && mv tasks/{marker.name}.incoming tasks/{marker.name}'], check=True, timeout=30)
    log(f'START boxE own 180 s follow n={count}. Log {WORK / "boxE-final/out" / (tag + ".log")}. Deadline 13:45Z.')
    return {**task, 'status': 'queued', 'pin': str(pin), 'walk_files': proof['files']}


def finish(entry, job, bar):
    done = WORK / 'taskdone' / (job['tag'] + '.json')
    if not done.exists():
        return job
    output = WORK / job['out']
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ['rsync', '-az', '-e', 'ssh -S /tmp/squares-k123-r38-ssh', 'boxE:scratch/squares-k123/' + job['out'] + '/', str(output) + '/'],
        check=True, timeout=90,
    )
    original = Path(entry['path'])
    row = entry['row']
    result = entry['result']
    proof = entry['proof']
    receipt_path = output / 'follow-result37.json'
    if not receipt_path.is_file():
        return {**job, 'status': 'worker-failed', 'remote': json.loads(done.read_text())}
    receipt = json.loads(receipt_path.read_text())
    chosen = original
    if receipt['status'] == 'certified':
        candidate = output / f'{entry["n"]}.csv'
        improved = json.loads((output / 'result36.json').read_text())
        if improved['score'] < result['score'] - 1e-10:
            followed_row = {**row, 'source': f'k123 round 38 own 180 s lkick from {job["pin"]} (sha256 {job["start_sha256"]})'}
            followed_proof = check(candidate, followed_row)
            if followed_proof['clean'] and not followed_proof['capped']:
                chosen, row, proof, result = candidate, followed_row, followed_proof, improved
    # An unchanged native result still needs a current walk after its follow.
    if chosen == original:
        proof = check(chosen, row)
    promotion = None
    if proof['clean'] and not proof['capped']:
        promotion = publish(entry['n'], chosen, row, result, proof, entry['recipe'], bar)
    log(f'FINISH own 180 s follow n={entry["n"]}, numerical state {receipt["status"]}, retained={bool(promotion)}. Receipt {receipt_path}.')
    return {**job, 'status': 'published' if promotion else 'closed', 'receipt': receipt, 'promotion': promotion}


def run():
    csv.field_size_limit(1 << 28)
    state_file = WORK / 'own-state38.json'
    state = json.loads(state_file.read_text()) if state_file.exists() else {}
    bars = {int(row['n']): float(row['bar']) for row in csv.DictReader((SCRATCH / 'round38-briefs/bar38.tsv').open(), delimiter='\t')}
    for path in sorted(INBOX.glob('*.json'), key=lambda item: item.stat().st_mtime_ns):
        token = path.stem
        entry = json.loads(path.read_text())
        previous = state.get(token, {})
        if previous.get('status') == 'earlier-claim' and time.time() >= previous.get('retry_at', 0):
            state.pop(token)
        if token in state:
            if state[token]['status'] == 'queued':
                state[token] = finish(entry, state[token], bars[entry['n']])
                atomic(state_file, state)
            continue
        if time.time() >= float((WORK / 'own-follow-deadline').read_text()):
            return
        if any(job['status'] == 'queued' for job in state.values()):
            return
        state[token] = dispatch(token, entry)
        atomic(state_file, state)
        return


if __name__ == '__main__':
    run()
