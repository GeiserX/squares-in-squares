"""Resolve exact backlog copies and harvest follow receipts."""
import hashlib
import json
from pathlib import Path
import re


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin_record(work, record):
    data = json.dumps(record, sort_keys=True, separators=(',', ':')).encode()
    folder = Path(work)/'adapter-proofs'
    folder.mkdir(exist_ok=True)
    target = folder/(hashlib.sha256(data).hexdigest()+'.json')
    if not target.exists():
        target.with_suffix('.tmp').write_bytes(data)
        target.with_suffix('.tmp').replace(target)
    return str(target), hashlib.sha256(data).hexdigest()


def backlog_copy(path, n, scratch, active, trace, work):
    path = Path(path)
    active = set(active or ())
    if (str(path), n) in active:
        return False, dict(path=str(path), n=n, reason='copied-start ancestry cycle')
    active.add((str(path), n))
    state = path.parent.parent/'ctl-state.json'
    if not state.exists() or not path.exists():
        return None
    matches = []
    def visit(value):
        if isinstance(value, dict):
            if value.get('start') == str(path) and value.get('orig'):
                matches.append(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
    visit(json.loads(state.read_text()))
    if not matches:
        return None
    identities = {(int(row['n']), row['orig']) for row in matches}
    if len(identities) != 1 or next(iter(identities))[0] != n:
        return False, dict(path=str(path), n=n, reason='conflicting copied-start records or count')
    row = matches[0]
    original = Path(row['orig'])
    digest = sha(path)
    if not original.exists() or sha(original) != digest:
        return False, dict(path=str(path), n=n, reason='changed bytes in recorded backlog copy')
    suffix = re.search(r'-([a-f0-9]{12})\.csv$', path.name)
    if suffix and not digest.startswith(suffix[1]):
        return False, dict(path=str(path), n=n, reason='copied-start filename pin differs')
    ok, parent = trace(original, n, scratch, active)
    proof, proof_sha = pin_record(work, row)
    return ok, dict(path=str(path), n=n, parent=parent, snapshot_sha256=digest,
                    source_proof=proof, record_sha256=proof_sha,
                    reason='exact backlog copy with pinned producer record')


def harvest_follow(path, n, scratch, active, trace, work):
    path = Path(path)
    active = set(active or ())
    if (str(path), n) in active:
        return False, dict(path=str(path), n=n, reason='harvest follow ancestry cycle')
    active.add((str(path), n))
    sidecar = Path(str(path)+'.json')
    if not sidecar.exists():
        return None
    record = json.loads(sidecar.read_text())
    if record.get('kind') != 'fresh-follow':
        return None
    if int(record.get('n', -1)) != n:
        return False, dict(path=str(path), n=n, reason='harvest follow count differs')
    original = Path(record['original'])
    if not original.exists():
        return False, dict(path=str(path), n=n, reason='missing exact harvest follow parent')
    parent_hash = sha(original)
    if path.parent.name == 'inputs':
        ok = sha(path) == parent_hash == record.get('queued_sha256')
        if not ok:
            return False, dict(path=str(path), n=n, reason='changed harvest queue bytes')
        binding = dict(n=n, source=record['source'], licence=record['licence'],
                       original=str(original), input_sha256=parent_hash)
    else:
        receipt = Path(record.get('proof', ''))
        queued = Path(record.get('source_file', ''))
        if not receipt.is_file() or not queued.is_file():
            return False, dict(path=str(path), n=n, reason='missing harvest follow receipt or queued file')
        result = json.loads(receipt.read_text())
        certified = Path(result.get('file', ''))
        if (int(result.get('n', -1)) != n or result.get('input_hash') != parent_hash or
                sha(queued) != parent_hash or not certified.is_file() or sha(certified) != sha(path)):
            return False, dict(path=str(path), n=n, reason='changed harvest follow receipt binding')
        binding = dict(n=n, source=record['source'], licence=record['licence'],
                       original=str(original), input_sha256=parent_hash,
                       receipt=str(receipt), receipt_sha256=sha(receipt),
                       certified_output_sha256=sha(certified))
    ok, parent = trace(original, n, scratch, active)
    proof, proof_sha = pin_record(work, binding)
    return ok, dict(path=str(path), n=n, parent=parent, source_proof=proof,
                    record_sha256=proof_sha, reason='exact harvest follow queue and receipt binding')
