"""Stage fresh certificates and changed third seams in arrival order."""
import csv
import hashlib
import json
from pathlib import Path
import re
import time

from classes26 import read
from provenance24 import W, S, credit, key, mlp
from stage24 import current, journal, kj, stage

STATE = W / 'feed38.json'
LOG = S / 'handoff-r38.log'
HELD = S / 'gather/round37-2026-11-18a.csv'
FRESH_PATH = re.compile(r'$DATA/[^\s,;<>]+\.csv\b')
CERTIFIED = re.compile(r'\bcertified\s+(?:row\s+|near donor\s+)?n\s*=\s*(\d+)', re.I)
FAVOURED = {793: [972, 911], 972: [793, 911], 683: [793, 972]}
BATCH_SIZE = 12


def save(state):
    temporary = STATE.with_suffix('.tmp')
    temporary.write_text(json.dumps(state))
    temporary.replace(STATE)


def events(state):
    with LOG.open() as stream:
        stream.seek(state['offset'])
        while line := stream.readline():
            if not line.endswith('\n'):
                break
            match = None if re.search(r'\b(?:claim|withdraw)', line, re.I) else CERTIFIED.search(line)
            paths = FRESH_PATH.findall(line)
            if match and paths:
                path = Path(paths[-1])
                if '-r38/' in str(path):
                    state['pending'].append([int(match[1]), str(path), None])
            state['offset'] = stream.tell()
    private = W / 'reopened-inputs27.txt'
    if private.is_file():
        with private.open() as stream:
            stream.seek(state['private_offset'])
            while line := stream.readline():
                if not line.endswith('\n'):
                    break
                path = Path(line.strip())
                state['pending'].append([int(path.name.split('-', 1)[0]), str(path), None])
                state['private_offset'] = stream.tell()
    # Producer tables also recover certificates written just before a handoff was interrupted.
    for table in sorted(S.glob('take-*-r38/take.tsv')):
        for row in csv.DictReader(table.open(), delimiter='\t'):
            count = int(row['n'])
            path = table.parent / f'{count}.csv'
            if not path.is_file():
                continue
            stamp = f'{path.stat().st_mtime_ns}:{row["new"]}'
            if state['table_stamps'].get(str(path)) != stamp:
                state['pending'].append([count, str(path), None])
                state['table_stamps'][str(path)] = stamp


def fingerprint(path, count):
    if path == HELD:
        return 'held'
    digest = hashlib.sha256(path.read_bytes())
    for sidecar in [Path(str(path) + '.json'), path.with_suffix('.json')]:
        if sidecar.is_file():
            digest.update(sidecar.read_bytes())
    table = path.parent / 'take.tsv'
    if path.stem == str(count) and table.is_file():
        for row in csv.DictReader(table.open(), delimiter='\t'):
            if row['n'] == str(count):
                digest.update(json.dumps(row, sort_keys=True).encode())
                break
    return digest.hexdigest()


def feed():
    if STATE.exists():
        state = json.loads(STATE.read_text())
    else:
        priorities = json.loads((W / 'setup38.json').read_text())['priority']
        state = {
            'pending': [[count, str(HELD), None] for count in priorities],
            'offset': 0, 'private_offset': 0, 'table_stamps': {},
            'seen': {}, 'geometries': [], 'scans': [], 'outcomes': {}, 'sequence': 10000,
        }
    events(state)
    retired_path = W / 'retired-donor-endpoints38.json'
    if retired_path.is_file():
        closed = set(json.loads(retired_path.read_text()).get('closed_counts', []))
        initial_scans = {job['path'] for job in state['scans']}
        state['pending'] = [
            job for job in state['pending']
            if not (
                str(job[0]) in closed and job[1] in initial_scans
                and ('/near/' in job[1] or '/private-near36/' in job[1])
            )
        ]
    def priority(job):
        _, name, remaining, *_ = job
        if remaining is not None:
            return 3
        if name == str(HELD):
            return 0
        return 2 if '/private-near36/' in name else 1
    state['pending'].sort(key=priority)
    save(state)
    if not state['pending']:
        return
    packings, origins = current()
    from base25 import loadpack
    held = loadpack(HELD)
    classes = {n: read(n, packing, kj) for n, packing in packings.items() if n >= 100}
    completed = set(state['geometries'])
    captured = time.monotonic()
    tries = 0
    while state['pending'] and tries < 6 and time.monotonic() - captured < 60:
        count, name, remaining, *expected = state['pending'].pop(0)
        path = Path(name)
        try:
            signature = fingerprint(path, count)
            if expected and signature != expected[0]:
                state['pending'].append([count, name, None])
                save(state)
                continue
            token = f'{count}:{name}:{signature}'
            if remaining is None and token in state['seen']:
                continue
            packing = held[count] if path == HELD else mlp.load(name, {count})[count]
            geometry = key(count, packing)
        except (ValueError, KeyError, OSError):
            state['outcomes'][name] = 'unavailable'
            save(state)
            continue
        if remaining is None:
            if geometry in completed:
                state['seen'][token] = 'duplicate'
                save(state)
                continue
            if count < 100:
                state['seen'][token] = 'below-reader-range'
                state['outcomes'][f'{count}:{name}'] = 'below-reader-range'
                save(state)
                continue
            donor_class = read(count, packing, kj)
            if not donor_class:
                state['seen'][token] = 'no-band'
                state['outcomes'][f'{count}:{name}'] = 'no-band'
                journal(f'FINISH fresh n={count}, no supported band at {path}. Deadline 13:45Z.')
                save(state)
                continue
            try:
                admitted = credit(count, packing, 'held' if path == HELD else name)
            except __import__('admission_budget30').Deferred:
                state['pending'].append([count, name, None])
                save(state)
                return
            if not admitted:
                state['seen'][token] = 'source-refused'
                state['outcomes'][f'{count}:{name}'] = 'source-refused'
                journal(f'DROP source-refused fresh n={count} at {path}. Deadline 13:45Z.')
                save(state)
                continue
            state['seen'][token] = 'admitted'
            completed.add(geometry)
            state['geometries'].append(geometry)
            fraction = mlp.side(packing) % 1
            preferred = FAVOURED.get(count, [])
            remaining = sorted(
                (n for n, types in classes.items() if n != count and types and donor_class & types),
                key=lambda n: (
                    n not in preferred, preferred.index(n) if n in preferred else 0,
                    abs(mlp.side(packings[n]) % 1 - fraction), abs(n - count),
                ),
            )
            remaining.insert(0, count)
            state['outcomes'][f'{count}:{name}'] = f'admitted {len(remaining)} pairs'
            # Save the new geometry with its remaining pairs before the first transfer.
            state['pending'].insert(0, [count, name, remaining, signature])
            save(state)
            continue
        batch = remaining[:BATCH_SIZE]
        tail = remaining[BATCH_SIZE:]
        if tail:
            state['pending'].append([count, name, tail, signature])
        local_packings = {**packings, count: packing}
        local_origins = {**origins, count: 'held' if path == HELD else name}
        state['sequence'] += 1
        tag = f'fresh38{state["sequence"]}'
        kind = 'fresh-held-pick' if path == HELD else 'fresh-third-seam' if '/private-near36/' in name else 'fresh-certificate'
        tries += 1
        if stage(tag, local_packings, local_origins, [(count, n) for n in batch], kind, f'n={count} {path}'):
            state['scans'].append({'n': count, 'path': name, 'tag': tag, 'pairs_requested': len(batch), 'kind': kind})
        save(state)


if __name__ == '__main__':
    feed()
