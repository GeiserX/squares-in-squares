"""Write new byte-pinned source records without changing the inherited records."""
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_r37 as lane
import forensics_memory36 as memory

AUDIT = re.compile(r'(?:$SCRATCH/bounties-squares/)?take-[a-z0-9-]+-r\d+/work/(?:walks|share|final-audit)/[A-Za-z0-9_./-]+\.json')


def rewrite(value, paths):
    if isinstance(value, dict):
        return {key: rewrite(item, paths) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite(item, paths) for item in value]
    if not isinstance(value, str):
        return value
    value = AUDIT.sub('[audit reference omitted]', value)
    for old, new in paths:
        value = value.replace(old, new)
    return value


def table_row(path, count):
    table = path.parent / 'take.tsv'
    if not table.is_file():
        return None
    return next((row for row in csv.DictReader(table.open(), delimiter='\t')
                 if int(row['n']) == count), None)


def standard(path):
    import quench_walk as walker
    import forensics_held37 as held
    sys.path.insert(0, str(lane.LANE / 'tools/harvest31'))
    import policy
    frozen = json.loads((lane.WORK / 'share/zips.json').read_text())
    archives = []
    for name, digest in frozen:
        archive = Path(name)
        assert lane.sha(archive) == digest
        archives.append(archive)
    policy.archive_paths = lambda: tuple(archives)
    walker.held_gather = held.held_gather
    memory.start_guard(str(path))
    result = walker.check(str(path), cap=100000)
    result.update(cap=100000, source_aliases_used=False, audit_text_filter_used=False,
                  csv_sha256=lane.sha(path), sidecar_sha256=lane.sha(Path(str(path) + '.json')))
    print(json.dumps(result), flush=True)
    return result


def main(start):
    memory.start_guard(str(start))
    count = int(next(csv.DictReader(start.open()))['n'])
    notices = [(table_row(start, count) or {}).get('licence', '')]
    for suffix in ('.json', '.source.json', '.origin.json'):
        sidecar = Path(str(start) + suffix)
        if sidecar.is_file():
            value = json.loads(sidecar.read_text())
            if isinstance(value, dict):
                notices.append(value.get('licence', ''))
                if isinstance(value.get('source'), dict):
                    notices.append(value['source'].get('licence', ''))
    assert any(lane.approved_notices(notice) for notice in notices), 'approved public licence required'
    checked = lane.walk(start)
    assert checked.get('clean') and not checked.get('capped', True) and checked.get('pubfirst'), checked
    assert not checked.get('helds'), 'this repair handles public-only source trees'
    arguments = sys.argv
    sys.argv = [__file__]
    import forensics_walk37 as walked
    sys.argv = arguments
    _, missing, seen, helds, refused = walked.qw.walk(str(start), count, cap=100000)
    assert not missing and not helds and not refused and len(seen) < 100000
    folder = lane.WORK / 'source-records' / f'{count}-{lane.sha(start)[:16]}-{time.time_ns()}'
    folder.mkdir(parents=True)
    nodes = {}
    for name in sorted(value for value in seen if isinstance(value, str) and value.endswith('.csv')):
        original = Path(name)
        data = original.read_bytes()
        counts = {int(row['n']) for row in csv.DictReader(original.open())}
        if counts != {count}:
            continue
        records = {Path(sidecar): Path(sidecar).read_bytes() for sidecar in walked.qw.sidecars(name)}
        digest = hashlib.sha256(data).hexdigest()
        identity = hashlib.sha256(str(original).encode() + b''.join(records.values())).hexdigest()
        destination = folder / f'{digest[:24]}-{identity[:16]}' / f'{count}.csv'
        destination.parent.mkdir()
        destination.write_bytes(data)
        nodes[name] = dict(path=destination, data=data, records=records, row=table_row(original, count))
    assert str(start) in nodes
    mapping = {}
    for old, node in nodes.items():
        mapping[old] = str(node['path'])
        mapping[old.removeprefix(str(lane.ROOT) + '/')] = str(node['path'])
        for record in node['records']:
            suffix = str(record)[len(old):]
            mapping[str(record)] = str(node['path']) + suffix
            mapping[str(record).removeprefix(str(lane.ROOT) + '/')] = str(node['path']) + suffix
    for alias, (target, digest) in walked.source_aliases.items():
        assert lane.sha(Path(target)) == digest, 'source alias bytes changed'
        mapping[alias] = mapping.get(target, target)
    replacements = sorted(mapping.items(), key=lambda item: -len(item[0]))
    for old, node in nodes.items():
        records = node['records']
        values = {str(path)[len(old):]: json.loads(data) for path, data in records.items()}
        base = values.get('.json', {})
        if not isinstance(base, dict):
            base = dict(original_record=base)
        if node['row']:
            base['producer_take_row'] = node['row']
            base['producer_take_table'] = str(Path(old).parent / 'take.tsv')
        base['numeric_input_identity'] = dict(csv_sha256=hashlib.sha256(node['data']).hexdigest(),
                                              producer=Path(old).parts[len(lane.ROOT.parts)],
                                              filename=Path(old).name)
        values['.json'] = base
        for suffix, value in values.items():
            updated = rewrite(lane.clean_notice_fields(value), replacements)
            lane.atomic(str(node['path']) + suffix, json.dumps(updated, indent=1))
    for old, node in nodes.items():
        assert Path(old).read_bytes() == node['data'], f'input changed during record repair: {old}'
        for path, data in node['records'].items():
            assert path.read_bytes() == data, f'original source record changed: {path}'
    root = nodes[str(start)]['path']
    assert lane.sha(root) == lane.sha(start)
    with (folder / 'standard-walk.json').open('w') as output:
        subprocess.run([lane.PY, '-I', str(Path(__file__).resolve()), 'standard', str(root)],
                       stdout=output, stderr=subprocess.STDOUT, check=True, timeout=900)
    proof = json.loads((folder / 'standard-walk.json').read_text())
    assert proof['clean'] and not proof['capped'], proof
    result = dict(at=lane.now(), n=count, csv_sha256=lane.sha(root), original=str(start),
                  root=str(root), files=proof['files'], capped=proof['capped'],
                  copied_csv_nodes=len(nodes), original_records_unchanged=True,
                  alias_used=False, audit_text_filter_used=False,
                  mapping={old: str(node['path']) for old, node in nodes.items()})
    lane.atomic(folder / 'receipt.json', json.dumps(result, indent=2))
    lane.state('SOURCE-RECORDS ' + json.dumps({key: value for key, value in result.items() if key != 'mapping'}))
    with lane.HANDOFF.open('a') as output:
        output.write(f'{lane.now()} forensics -> all: NEW COMPLETE RECORD GRAPH for n{count}, '
                     f'byte-identical to {start}, sha256 {result["csv_sha256"]}: {root}. '
                     f'Standard quench_walk cap100000 clean {proof["files"]} files, not capped, '
                     'no source alias and no audit-text filter. Every per-count CSV is byte-pinned; '
                     'all original CSVs/sidecars unchanged. New records retain real ancestry and '
                     f'canonical licences, omit audit prose/paths. Receipt {folder}/receipt.json. '
                     'This changes no geometry and claims no new numerical seed.\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'mapping'}), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'standard':
        standard(Path(sys.argv[2]))
    else:
        main(Path(sys.argv[1]))
