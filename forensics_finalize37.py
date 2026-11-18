"""Freeze the take without removing source paths, then verify remote cleanup."""
import csv
import json
import math
import os
import shlex
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_r37 as lane


def remote_owned():
    result = lane.ssh('ps -axo pid,command', timeout=30)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return [line for line in result.stdout.splitlines()
            if lane.RDIR + '/' in line and line.split()[0].isdigit()]


def stop():
    groups = {}
    markers = dict(watch='forensics_watch37.py', driver='forensics_r37.py driver',
                   depth16='forensics_depth37.py', freshdepth='forensics_freshdepth37.py',
                   records='forensics_records37.py',
                   audit='forensics_manage37.py audit')
    for name, marker in markers.items():
        filename = lane.WORK / f'{name}.pid'
        if not filename.exists():
            continue
        process_id = int(filename.read_text())
        status = subprocess.run(['ps', '-p', str(process_id), '-o', 'command='], capture_output=True, text=True)
        if marker not in status.stdout:
            continue
        try:
            if os.getpgid(process_id) != process_id:
                raise RuntimeError(f'owned process is not its group leader: {process_id}')
            groups[name] = process_id
            os.killpg(process_id, signal.SIGTERM)
        except ProcessLookupError:
            continue
    for attempt in range(10):
        status = subprocess.run(['ps', '-axo', 'pid,pgid,stat,command'], capture_output=True, text=True)
        remaining = [line for line in status.stdout.splitlines()
                     if len(line.split(None, 3)) == 4 and line.split()[1].isdigit() and
                     int(line.split()[1]) in groups.values() and not line.split()[2].startswith('Z')]
        if not remaining:
            break
        if attempt >= 5:
            active_groups = {int(line.split()[1]) for line in remaining}
            for process_id in active_groups:
                try:
                    os.killpg(process_id, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        time.sleep(.5)
    if remaining:
        raise RuntimeError(remaining)
    for attempt in range(6):
        owned = remote_owned()
        if not owned:
            break
        lane.ssh('kill -' + ('KILL' if attempt >= 3 else 'TERM') + ' ' +
                 ' '.join(line.split()[0] for line in owned), timeout=30)
        time.sleep(.5)
    if remote_owned():
        raise RuntimeError('owned remote workers remain')
    lane.atomic(lane.WORK / 'stop-receipt.json', json.dumps(dict(at=lane.now(), groups=groups,
                                                               local_groups_empty=True, remote_workers=[]), indent=2))
    lane.state(f'STOP all owned drivers, numerical jobs and audit workers; groups={groups}; boxE own worker list empty')
    print('stopped', groups, flush=True)


def proof(count, packing, metadata):
    digest = lane.sha(packing)
    metadata_digest = lane.sha(Path(str(packing) + '.json'))
    for report in sorted((lane.WORK / 'final-audit').glob(f'{count}-{digest[:16]}-*.json'), reverse=True):
        result = json.loads(report.read_text())
        if result.get('ok') and result['csv_sha256'] == digest and result['sidecar_sha256'] == metadata_digest:
            return dict(kind='direct-pandas-audit', files=result['walk']['files'],
                        capped=result['walk']['capped'], at=result['at'])
    walked = metadata.get('walk_at_publish', {})
    receipts = metadata.get('fq_receipts', [])
    loops = len(receipts) >= 2 and all(
        any(not step['flags'] and step.get('end') is not None and math.isfinite(step['end'])
            for step in receipt['steps']) and
        any(step['flags'] and step.get('end') is not None and math.isfinite(step['end'])
            for step in receipt['steps']) for receipt in receipts)
    if lane.walk_accepted(walked, metadata.get('source', {}).get('licence', '')) and loops and metadata.get('take_sha256') == digest:
        return dict(kind='publication-walk-and-finesafe', files=walked['files'], capped=False)
    return None


def freeze():
    if not (lane.WORK / 'stop-receipt.json').exists():
        raise RuntimeError('stop all workers before freezing')
    rows, bars, peers = lane.read_take(), lane.bar_scores(), lane.live_scores()
    folder = lane.WORK / 'finalization'
    folder.mkdir(exist_ok=True)
    shutil.copyfile(lane.TAKE / 'take.tsv', folder / f'take-before-{time.time_ns()}.tsv')
    retained, decisions = {}, {}
    for count, row in rows.items():
        packing = lane.TAKE / f'{count}.csv'
        metadata = json.loads(Path(str(packing) + '.json').read_text())
        evidence = proof(count, packing, metadata)
        score = float(row['new'])
        eligible = bool(score < bars[count] - 1e-10 and score < peers.get(count, (999,))[0] and evidence)
        decisions[count] = dict(eligible=eligible, proof=evidence, score=score, peer=peers.get(count))
        if eligible:
            retained[count] = dict(row, held=repr(bars[count]), gain=repr(bars[count] - score))
        else:
            archive = folder / f'{count}-{lane.sha(packing)}-{lane.sha(Path(str(packing) + ".json"))[:16]}'
            archive.mkdir(exist_ok=True)
            for suffix in ('.csv', '.csv.json'):
                shutil.copyfile(lane.TAKE / f'{count}{suffix}', archive / f'{count}{suffix}')
    lane.write_take(retained)
    destination = lane.LANE / 'results/forensics-r37-2026-11-18.tsv'
    temporary = destination.with_name(destination.name + '.tmp')
    with temporary.open('w', newline='') as output:
        writer = csv.DictWriter(output, fieldnames=['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t')
        writer.writeheader()
        writer.writerows(retained[count] for count in sorted(retained))
    os.replace(temporary, destination)
    lane.atomic(folder / 'receipt.json', json.dumps(dict(at=lane.now(), rows=decisions), indent=2))
    lane.state(f'FINAL retained={sorted(retained)}; table and repository results exported; '
               'all published CSV paths and unchanged source records remain available for peer ancestry')
    print('retained', sorted(retained), 'gain', sum(float(row['gain']) for row in retained.values()), flush=True)


def cleanup():
    if not (lane.WORK / 'stop-receipt.json').exists() or remote_owned():
        raise RuntimeError('workers must be stopped first')
    for count in lane.read_take():
        packing = lane.TAKE / f'{count}.csv'
        metadata = json.loads(Path(str(packing) + '.json').read_text())
        if lane.sha(packing) != metadata['take_sha256']:
            raise RuntimeError(f'published bytes changed at {count}')
        for field in ('cert_first', 'certified', 'raw'):
            if not Path(metadata[field]).is_file():
                raise RuntimeError(f'missing local evidence {count} {field}')
    assert lane.RDIR.endswith('/squares-forensics-r37')
    script = 'import hashlib,json,pathlib;root=pathlib.Path(' + repr(lane.RDIR) + ');'
    script += 'print(json.dumps({str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() '
    script += 'for path in root.rglob("*") if path.is_file()}))'
    result = lane.ssh(lane.RBASE + '/venv/bin/python -I -c ' + shlex.quote(script), timeout=120)
    if result.returncode:
        raise RuntimeError(result.stderr)
    manifest = json.loads(result.stdout)
    rescue = lane.WORK / 'remote-rescue'
    rescue.mkdir(exist_ok=True)
    subprocess.run(['scp', '-q', '-r', f'{lane.REMOTE}:{lane.RDIR}', str(rescue) + '/'], check=True, timeout=600)
    copied = rescue / Path(lane.RDIR).name
    for relative, digest in manifest.items():
        if lane.sha(copied / relative) != digest:
            raise RuntimeError(f'remote copy verification failed: {relative}')
    lane.atomic(rescue / 'manifest.json', json.dumps(manifest, indent=2))
    result = lane.ssh('rm -rf ' + shlex.quote(lane.RDIR), timeout=60)
    if result.returncode or lane.ssh('test ! -e ' + shlex.quote(lane.RDIR), timeout=30).returncode:
        raise RuntimeError('remote scratch cleanup failed')
    lane.atomic(lane.WORK / 'cleanup-receipt.json', json.dumps(dict(at=lane.now(), remote_scratch_removed=lane.RDIR,
                                                                  copied_files=len(manifest), copies_sha256_verified=True,
                                                                  published_copies_verified=True, processes_left=[]), indent=2))
    lane.state(f'STOP cleanup complete; {len(manifest)} boxE scratch files copied and hash-verified before removal; '
               'shared base left unchanged; no owned worker remains')
    print('cleaned', len(manifest), 'verified files', flush=True)


if __name__ == '__main__':
    {'stop': stop, 'freeze': freeze, 'cleanup': cleanup}[sys.argv[1]]()
