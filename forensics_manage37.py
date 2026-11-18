"""Prepare and audit the round 37 rectangle-composition lane."""
import ast
import csv
import json
import os
import pickle
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_r37 as lane

csv.field_size_limit(1 << 30)


def prepare():
    for name in ('share', 'walks', 'inbox', 'fq', 'certified', 'held-picks', 'control'):
        (lane.WORK / name).mkdir(parents=True, exist_ok=True)
    frozen = lane.ROOT / 'take-forensics-r36/work/share/zips.json'
    shutil.copyfile(frozen, lane.WORK / 'share/zips.json')
    lane.atomic(lane.WORK / 'deadline.txt', str(lane.DEADLINE) + '\n')
    if not (lane.TAKE / 'take.tsv').exists():
        lane.write_take({})
    selected = {count: [] for count in lane.PICKS}
    for row in csv.DictReader(open(lane.HELD)):
        count = int(row['n'])
        if count in selected:
            selected[count].append(row)
    for count, rows in selected.items():
        lane.write_rows(lane.WORK / 'held-picks' / f'{count}.csv', rows)
    result = lane.ssh(f'mkdir -p {lane.RDIR}/code {lane.RDIR}/jobs; '
                      f'ps -axo pid,command | grep "{lane.RDIR}/" | grep -v grep || true', timeout=60)
    if result.returncode:
        raise RuntimeError(result.stderr)
    if result.stdout.strip():
        raise RuntimeError('existing round37 remote workers require adoption: ' + result.stdout)
    names = {'forensics_r37.py', 'forensics_rect.py', 'forensics_compose.py', 'midm_scan.py'}
    pending = list(names)
    while pending:
        filename = pending.pop()
        for node in ast.walk(ast.parse((lane.LANE / filename).read_text())):
            modules = [alias.name for alias in node.names] if isinstance(node, ast.Import) else (
                [node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for module in modules:
                dependency = module.split('.')[0] + '.py'
                if dependency not in names and (lane.LANE / dependency).is_file():
                    names.add(dependency)
                    pending.append(dependency)
    subprocess.run(['scp', '-q'] + [str(lane.LANE / name) for name in sorted(names)] +
                   [f'{lane.REMOTE}:{lane.RDIR}/code/'], check=True, timeout=120)
    subprocess.run(['scp', '-q', str(lane.WORK / 'deadline.txt'),
                    f'{lane.REMOTE}:{lane.RDIR}/deadline.txt'], check=True, timeout=60)
    imported = lane.ssh(f'{lane.RBASE}/venv/bin/python -I -c '
                        f'"import sys;sys.path.insert(0,\'{lane.RDIR}/code\');'
                        'import forensics_rect,forensics_compose,midm_scan;print(\'imports ok\')"', timeout=60)
    if imported.returncode:
        raise RuntimeError(imported.stderr)
    lane.state('PREP complete: empty take, near directory, frozen ten-version share table, '
               'round36 held picks, isolated boxE code and shared 06:45Z deadline')


def strict():
    started = time.time()
    lane.seed_cache()
    destination = lane.WORK / 'strict-all-held'
    destination.mkdir(exist_ok=True)
    lane.write_details(destination / 'details.csv')
    command = [lane.PY, '-I', str(lane.LANE / 'forensics_rect.py'),
               str(destination / 'details.csv'), str(destination / 'raw'),
               '--cache', str(lane.WORK / 'windows37.pkl'), '--rescan-cache',
               '--fresh-only', '--fresh-start', '0', '--slack', '0', '--keep', '8',
               '--per-n', '8', '--max-mesh', '400', '--strict-single', '--skip-ties']
    with (destination / 'rect.log').open('w') as output:
        subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True,
                       timeout=min(1800, max(1, lane.DEADLINE - time.time())))
    import forensics_rect as rectangles
    import forensics_compose as composer
    targets = lane.targets()
    jobs = []
    for candidate in sorted((destination / 'raw').glob('*.csv')):
        count = int(candidate.name.split('-')[0])
        side, _ = composer.frame(next(iter(rectangles.layouts(candidate).values())))
        source = dict(original=str(lane.HELD), snapshot=str(lane.HELD),
                      sha256=lane.sha(lane.HELD), n=count, start_walk_clean=True,
                      start_walk_files=2, start_walk_capped=False,
                      licence='own submitted round36 held rows',
                      note='strict all-held scan; part counts are recorded in raw metadata')
        jobs.append([side - targets[count][1], str(candidate), count, source])
    lane.atomic(lane.WORK / 'inbox/strict-all-held.json', json.dumps(jobs))
    result = dict(seconds=time.time() - started, starts=len(jobs),
                  counts=sorted({entry[2] for entry in jobs}),
                  terminal=(destination / 'rect.log').read_text().splitlines()[-1])
    lane.atomic(destination / 'measurement.json', json.dumps(result, indent=2))
    lane.state('STRICT all-held opening ' + json.dumps(result))
    print(json.dumps(result), flush=True)


def bootstrap():
    prepare()
    strict()
    lane.state('START driver: two boxE fq slots, immediate fresh certificate scans, '
               '2e-10 materiality gate, complete held-root walks, physical footprint guard')
    os.execv(lane.PY, [lane.PY, '-I', str(lane.LANE / 'forensics_r37.py'), 'driver'])


def audit():
    import floatsafe as safe
    folder = lane.WORK / 'final-audit'
    folder.mkdir(exist_ok=True)
    selected = {int(value) for value in sys.argv[2:]}
    for count, row in lane.read_take().items():
        if selected and count not in selected:
            continue
        packing = lane.TAKE / f'{count}.csv'
        sidecar = Path(str(packing) + '.json')
        digest, metadata_digest = lane.sha(packing), lane.sha(sidecar)
        result = dict(n=count, csv_sha256=digest, sidecar_sha256=metadata_digest, at=lane.now())
        try:
            walked = lane.walk(packing)
            rows = list(csv.DictReader(open(packing)))
            parsed = safe.via_pandas(rows)
            direct_score, direct_reason = safe.check(count, rows)
            parsed_score, parsed_reason = safe.check(count, parsed)
            direct_clearance = float(safe.clearance(rows))
            parsed_clearance = float(safe.clearance(parsed))
            metadata = json.loads(sidecar.read_text())
            loops = metadata.get('fq_receipts', [])
            loop_ok = len(loops) >= 2 and all(
                any(not step['flags'] and step.get('end') is not None for step in receipt['steps']) and
                any(step['flags'] and step.get('end') is not None for step in receipt['steps'])
                for receipt in loops)
            unchanged = lane.sha(packing) == digest and lane.sha(sidecar) == metadata_digest
            good = bool(lane.walk_accepted(walked, metadata.get('source', {}).get('licence', '')) and
                        len(rows) == count and
                        direct_reason == parsed_reason == 'ok' and
                        min(direct_clearance, parsed_clearance) >= 2e-11 and loop_ok and unchanged and
                        abs(direct_score - float(row['new'])) < 1e-12 and
                        abs(parsed_score - float(row['new'])) < 1e-12)
            result.update(ok=good, walk=walked, loops=loop_ok, unchanged=unchanged,
                          metric=dict(direct=direct_score, pandas=parsed_score,
                                      clearance=direct_clearance, pandas_clearance=parsed_clearance))
        except Exception as error:
            result.update(ok=False, error=repr(error))
        lane.atomic(folder / f'{count}-{digest[:16]}-{time.time_ns()}.json', json.dumps(result, indent=2))
        lane.state(f'AUDIT n={count} ok={result["ok"]} files={result.get("walk", {}).get("files")} '
                   f'capped={result.get("walk", {}).get("capped")} sha256={digest}')
        print(json.dumps({key: value for key, value in result.items() if key != 'walk'}), flush=True)


if __name__ == '__main__':
    {'prepare': prepare, 'strict': strict, 'bootstrap': bootstrap, 'audit': audit}[sys.argv[1]]()
