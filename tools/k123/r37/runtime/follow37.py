from pathlib import Path
import csv
import datetime
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

WORK = Path(__file__).resolve().parent
TAKE = WORK.parent
SCRATCH = TAKE.parent
sys.path[:0] = [str(WORK), str(WORK / 'lane')]
from provenance24 import key, mlp
from publication_source26 import check
from publish_certified36 import best_live_score, publish

SSH = ['ssh', '-S', '/tmp/squares-k123-r37-ssh', 'boxE']
SCP = ['scp', '-q', '-o', 'ControlPath=/tmp/squares-k123-r37-ssh']


def stamp():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')


def save(state):
    temporary = WORK / ('follow-state37.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps(state, indent=2))
    temporary.replace(WORK / 'follow-state37.json')


def log(message, handoff=False):
    line = stamp() + ' k123 -> all: ' + message + '\n'
    for destination in [TAKE / 'STATE.txt'] + ([SCRATCH / 'handoff-r37.log'] if handoff else []):
        with destination.open('a') as stream:
            stream.write(line)


def matching_claim(line, count, digest, seconds):
    if not re.search(r'\bclaims?\b', line, re.I) or not re.search(r'\bn\s*=\s*' + str(count) + r'\b', line):
        return False
    if seconds == 900 and ' k123 ->' in line and 'fresh 180 s lkick' in line:
        return False
    hashes = re.findall(r'\b[0-9a-f]{10,64}\b', line)
    return any(digest.startswith(value) for value in hashes)


def producer_record_key(row):
    payload = {name: row.get(name, '') for name in ('n', 'source', 'licence')}
    payload['source_rules_version'] = 'source-alias37-v1'
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def may_retry_source(item, record_key):
    return item.get('status') == 'source-refused' and item.get('producer_record_key') != record_key


def run():
    csv.field_size_limit(1 << 28)
    state_path = WORK / 'follow-state37.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    bars = {int(row['n']): float(row['bar']) for row in csv.DictReader((SCRATCH / 'round37-briefs/bar37.tsv').open(), delimiter='\t')}
    for token, item in state.items():
        if item['status'] != 'queued':
            continue
        done = WORK / 'taskdone' / (item['tag'] + '.json')
        if not done.exists():
            continue
        destination = WORK / item['out']
        destination.mkdir(parents=True, exist_ok=True)
        subprocess.run(['rsync', '-az', '-e', 'ssh -S /tmp/squares-k123-r37-ssh', 'boxE:scratch/squares-k123/' + item['out'] + '/', str(destination) + '/'], check=True, timeout=90)
        receipt_path = destination / 'follow-result37.json'
        if not receipt_path.exists():
            item['status'] = 'worker-failed'
            log('fresh follow failed ' + token + ' rc=' + str(json.loads(done.read_text()).get('rc')))
            save(state)
            continue
        receipt = json.loads(receipt_path.read_text())
        item.update(status=receipt['status'], receipt=receipt)
        if receipt['status'] == 'certified':
            result = json.loads((destination / 'result36.json').read_text())
            packing = destination / (str(item['n']) + '.csv')
            proof = check(packing, item)
            promoted = publish(item['n'], packing, item, result, proof, item['tag'], bars[item['n']]) if proof['clean'] and not proof.get('capped') else None
            item.update(status='published' if promoted else 'superseded', promotion=promoted)
        log('fresh follow completed ' + token + ' ' + json.dumps(receipt), handoff=True)
        save(state)
    if time.time() >= float((WORK / 'search-deadline').read_text()) or any(item['status'] == 'queued' for item in state.values()):
        return
    candidates = []
    for table in SCRATCH.glob('take-*-r37/take.tsv'):
        if table.parent == TAKE:
            continue
        for row in csv.DictReader(table.open(), delimiter='\t'):
            count = int(row['n'])
            packing = table.parent / (str(count) + '.csv')
            if not packing.exists() or float(row['new']) > best_live_score(count, bars[count]) + 1e-12:
                continue
            raw = packing.read_bytes()
            geometry = key(count, mlp.load(str(packing), {count})[count])
            record_key = producer_record_key(row)
            for seconds, seed in [(180, 37180), (900, 37900)]:
                token = str(count) + '-' + geometry[:24] + '-' + str(seconds)
                if token in state and not may_retry_source(state[token], record_key):
                    continue
                earlier = str(count) + '-' + geometry[:24] + '-180'
                if seconds == 900 and (earlier not in state or state[earlier]['status'] not in ('dry', 'superseded', 'published', 'numeric-failed')):
                    continue
                candidates.append((seconds != 180, -packing.stat().st_mtime, token, count, raw, row, seconds, seed, geometry))
                break
    if not candidates:
        return
    _, _, token, count, raw, row, seconds, seed, geometry = min(candidates)
    inputs = WORK / 'follow-inputs37'
    inputs.mkdir(exist_ok=True)
    digest = hashlib.sha256(raw).hexdigest()
    record_key = producer_record_key(row)
    pinned = inputs / (str(count) + '-' + digest + '-' + record_key[:16] + '.csv')
    if not pinned.exists():
        pinned.write_bytes(raw)
        Path(str(pinned) + '.json').write_text(json.dumps({'n': str(count), 'source': row['source'], 'licence': row['licence'], 'csv_sha256': digest}))
    proof = check(pinned, row)
    if not proof['clean'] or proof.get('capped'):
        state[token] = {'status': 'source-refused', 'n': count, 'hits': proof['hits'], 'producer_record_key': record_key}
        save(state)
        return
    timestamp = stamp()
    claim = timestamp + f' k123 -> all: claim: fresh {seconds} s lkick follow n={count}, sha256={digest}, geometry={geometry}, seed={seed}, {pinned}\n'
    with (SCRATCH / 'handoff-r37.log').open('a') as stream:
        stream.write(claim)
    time.sleep(5)
    preceding = (SCRATCH / 'handoff-r37.log').read_text().split(claim, 1)[0].splitlines()
    collisions = [line for line in preceding if matching_claim(line, count, digest, seconds) and timestamp[:10] in line]
    if collisions:
        state[token] = {'status': 'earlier-claim', 'n': count, 'claim': collisions[0]}
        save(state)
        return
    tag = 'fresh-follow37-' + token
    output = 'follow37/' + token
    item = {'kind': 'follow37', 'tag': tag, 'n': count, 'raw': 'follow-inputs37/' + pinned.name, 'out': output, 'seconds': seconds, 'seed': seed, 'start_score': float(row['new']), 'start_sha256': digest, 'geometry': geometry, 'source': row['source'], 'licence': row['licence'], 'producer_record_key': record_key, 'status': 'queued'}
    subprocess.run(SSH + ['mkdir -p $SCRATCH/squares-k123/follow-inputs37'], check=True, timeout=30)
    subprocess.run(SCP + [str(pinned), 'boxE:scratch/squares-k123/' + item['raw']], check=True, timeout=60)
    task = WORK / (tag + '.json')
    task.write_text(json.dumps(item))
    subprocess.run(SCP + [str(task), 'boxE:scratch/squares-k123/tasks/' + task.name + '.incoming'], check=True, timeout=60)
    subprocess.run(SSH + ['mv $SCRATCH/squares-k123/tasks/' + task.name + '.incoming $SCRATCH/squares-k123/tasks/' + task.name], check=True, timeout=30)
    state[token] = item
    save(state)
    log('fresh follow queued ' + token + f' walk_files={proof["files"]} capped=False. ' + str(task), handoff=True)


if __name__ == '__main__':
    with (WORK / 'follow37.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run()
