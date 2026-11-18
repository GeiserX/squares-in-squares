"""Resolve frozen twoshort slide outputs through jobs and immutable intake."""
import hashlib
import json
from pathlib import Path
import re


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def intake_origin(path, record):
    if digest(path) != record['sha256']:
        raise ValueError('changed immutable twoshort intake')
    origin = Path(record['origin'])
    if not origin.is_file() or digest(origin) != record['sha256']:
        raise ValueError('missing or changed original twoshort intake')
    return origin


def trace_module_pin(path, n, scratch, active, trace):
    if path.parent != Path(scratch) / 'take-modules-r28/pins':
        return None
    match = re.fullmatch(r'(\d+)-rect-([a-f0-9]{16})\.csv', path.name)
    if not match:
        return None
    evidence = dict(path=str(path), n=n)
    try:
        sha = digest(path)
        if int(match[1]) != n or not sha.startswith(match[2]):
            raise ValueError('changed or mismatched module pin')
        parent = Path(scratch) / 'take-stair-c-r28/work/donors' / f'r28-{n}-{sha[:12]}.csv'
        if not parent.is_file() or digest(parent) != sha:
            raise ValueError('no byte-identical module pin with retained ancestry')
        active = set(active or ())
        key = (str(path), n)
        if key in active:
            raise ValueError('cyclic module pin')
        active.add(key)
        ok, proof = trace(parent, n, scratch, active)
        return ok, dict(evidence, reason='byte-identical module pin with retained ancestry',
                        snapshot_sha256=sha, matching_snapshot=str(parent), parent=proof)
    except (OSError, ValueError) as error:
        return False, dict(evidence, reason='unresolved module pin', error=str(error))


def trace_twoshort(path, n, scratch, active, trace):
    root = Path(scratch) / 'take-twoshort-r26/work/boxE26'
    try:
        relative = path.relative_to(root)
    except ValueError:
        return None
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
                         if part in ('squares-twoshort', 'squares-twoshort-r26')]
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
