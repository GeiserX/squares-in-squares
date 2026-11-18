"""Supervise the forensics driver and close out its round 38 take."""
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_r38 as lane

WORK = lane.WORK
TAKE = lane.TAKE
REPO = lane.CODE.parents[1]
DRIVER = lane.CODE / 'forensics_r38.py'
RESULTS = lane.CODE / 'results/forensics-r38-2026-11-18.tsv'
DOC = lane.CODE / 'avenues/forensics.md'
FREEZE = datetime.fromisoformat('2026-11-18T13:54:10+00:00').timestamp()
CERT = re.compile(r'Certified packing (\S+?\.csv) \(sha256 ([0-9a-f]{64})\)')


def driver_pid():
    filename = WORK / 'driver.pid'
    try:
        pid = int(filename.read_text())
    except (OSError, ValueError):
        return None
    status = subprocess.run(['ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True, errors="replace")
    if str(DRIVER) in status.stdout and not status.returncode:
        return pid
    return None


def start():
    if driver_pid() is not None:
        return driver_pid()
    if time.time() >= lane.LAST_WALK:
        return None
    lane.reap_remote('')
    command = ['nohup', 'nice', '-n', '5', lane.PY, '-B', '-I', str(DRIVER)]
    with (WORK / 'driver.log').open('a') as log:
        child = subprocess.Popen(command, cwd=WORK, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                 env=dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1'),
                                 start_new_session=True)
    time.sleep(2)
    if child.poll() is not None or driver_pid() != child.pid:
        raise RuntimeError(f'driver {child.pid} failed its startup check')
    lane.state(f'START verified driver pid={child.pid}; command={DRIVER}; log={WORK}/driver.log; '
               'persistent jobs and pending finishes requeued; deadline=13:45 UTC')
    return child.pid


def stop():
    pid = driver_pid()
    if pid:
        if os.getpgid(pid) != pid:
            raise RuntimeError(f'unexpected worker group for pid {pid}')
        os.killpg(pid, signal.SIGTERM)
        time.sleep(2)
        if driver_pid() == pid:
            os.killpg(pid, signal.SIGKILL)
    workers = local_workers()
    for line in workers:
        identifier, command = line.split(None, 1)
        current = subprocess.run(['ps', '-p', identifier, '-o', 'command='], capture_output=True, text=True, errors="replace")
        if current.stdout.strip() == command.strip():
            os.kill(int(identifier), signal.SIGTERM)
    lane.reap_remote('')
    remaining = local_workers() + lane.remote_workers()
    if remaining:
        raise RuntimeError(f'owned workers still present: {remaining}')
    lane.save(WORK / 'stop-receipt.json', dict(driver_pid=pid, workers=[], at=lane.prior.now()))
    lane.state('STOP verified that the driver, boxA workers and boxE workers exited')


def local_workers():
    status = subprocess.run(['ps', '-axo', 'pid,command'], capture_output=True, text=True, errors="replace", check=True)
    markers = ('forensics_rect.py ', 'forensics_walk38.py ', 'forensics_manage38.py strict',
               'forensics_r38.py', 'scp ', 'ssh ')
    out = []
    for line in status.stdout.splitlines():
        words = line.strip().split(None, 1)
        if len(words) != 2 or not words[0].isdigit():
            continue
        pid, command = int(words[0]), words[1]
        if pid == os.getpid() or 'forensics_finish38.py' in command:
            continue
        if ((str(TAKE) in command or lane.REMOTE in command) and any(mark in command for mark in markers)
                or command.endswith(' -I ' + str(DRIVER))):
            out.append(line.strip())
    return out


def cleanup():
    path = WORK / 'cleanup-receipt.json'
    if path.exists():
        return lane.load(path)
    if not (WORK / 'stop-receipt.json').exists() or local_workers() or lane.remote_workers():
        raise RuntimeError('stop and verify all workers before copying boxE scratch')
    remote = '$SCRATCH/squares-forensics-r38'
    assert lane.REMOTE == remote
    script = ('import hashlib,json,pathlib; root=pathlib.Path(' + repr(remote) + '); '
              'assert root.is_dir(); print(json.dumps({str(p.relative_to(root)): '
              'hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}))')
    command = [f'{lane.prior.RBASE}/venv/bin/python', '-B', '-I', '-c', script]
    listing = lane.ssh(shlex.join(command), timeout=120)
    manifest = json.loads(listing.stdout)
    rescue = WORK / 'remote-rescue'
    rescue.mkdir(exist_ok=True)
    subprocess.run(['scp', '-q', '-r', f'boxE:{remote}', str(rescue) + '/'], check=True, timeout=600)
    local = rescue / Path(remote).name
    files = {str(p.relative_to(local)) for p in local.rglob('*') if p.is_file()}
    if files != set(manifest):
        raise RuntimeError('boxE scratch copy differs from the remote file list')
    for name, digest in manifest.items():
        if lane.sha(local / name) != digest:
            raise RuntimeError(f'boxE scratch copy hash differs: {name}')
    lane.save(rescue / 'manifest.json', manifest)
    lane.ssh(f'rm -rf {shlex.quote(remote)} && test ! -e {shlex.quote(remote)}')
    result = dict(copied_files=len(files), removed=remote, sha256_verified=True, at=lane.prior.now())
    lane.save(path, result)
    lane.state(f'FINISH boxE cleanup; copied and verified {len(files)} files before removing {remote}')
    return result


def verified(row):
    import csv
    import floatsafe

    match = CERT.search(row['source'])
    if not match:
        return False, 'no exact source path and digest'
    source, digest = Path(match[1]), match[2]
    alias = TAKE / f'{row["n"]}.csv'
    if lane.sha(source) != digest or lane.sha(alias) != digest:
        return False, 'copy changed since publication'
    metadata = lane.load(lane.metadata(source))
    proof = lane.load(source.parent / 'publication-proof.json')
    if proof['sha256'] != digest or proof['record_sha256'] != lane.sha(lane.metadata(source)):
        return False, 'source record changed since its walk'
    if not lane.accepted(proof['walk'], metadata['licence']):
        return False, 'source walk was incomplete'
    loops = metadata['fq_receipts']
    if len(loops) < 2 or not all(lane.complete(loop) for loop in loops):
        return False, 'full fq receipts missing'
    if lane.sha(Path(metadata['certified_fq_input'])) != loops[-1]['input_sha256']:
        return False, 'certified fq input bytes changed'
    n = int(row['n'])
    with source.open() as handle:
        rows = list(csv.DictReader(handle))
    float_rows = floatsafe.via_pandas(rows)
    score = float(row['new'])
    for parsed, clearance in ((rows, 2.2e-11), (float_rows, 2e-11)):
        measured, reason = floatsafe.check(n, parsed)
        if reason != 'ok' or abs(score - measured) >= 1e-12 or floatsafe.clearance(parsed) < clearance:
            return False, 'metric or clearance differs from the certificate'
    return True, 'passed the exact source walk, both metric parsers and certified-file fq'


def freeze():
    rows = lane.table(TAKE / 'take.tsv')
    peer = lane.live(exclude_own=True)
    keep, decisions = {}, {}
    for n, row in rows.items():
        score = float(row['new'])
        try:
            eligible, why = verified(row)
        except (ValueError, OSError, KeyError) as error:
            eligible, why = False, str(error)
        if lane.bars()[n] - score <= lane.MIN_GAIN or score >= peer.get(n, math.inf):
            eligible, why = False, 'superseded or within the held threshold'
        decisions[n] = dict(retained=eligible, reason=why, score=score,
                            peer=peer.get(n), source=row['source'])
        if eligible:
            keep[n] = row
        else:
            lane.state(f'FINAL drop n={n}: {why}; published paths stay available for ancestry')
    lane.write_take(keep)
    temporary = RESULTS.with_suffix('.tsv.tmp')
    shutil.copyfile(TAKE / 'take.tsv', temporary)
    temporary.replace(RESULTS)
    snapshot = dict(at=lane.prior.now(), decisions=decisions, counts=sorted(keep),
                    gain=dict(against_base=sum(float(r['gain']) for r in keep.values()),
                              beyond_other_live_r38=sum(min(lane.bars()[n], peer.get(n, math.inf)) - float(r['new'])
                                                        for n, r in keep.items())))
    lane.save(WORK / 'final-receipt.json', snapshot)
    lane.state(f'FINAL take frozen; counts={sorted(keep)} gain={snapshot["gain"]["against_base"]:.17g}')
    return snapshot


def measurements():
    strict = lane.load(WORK / 'strict-all-held/measurement.json')
    scans = Counter(lane.load(file)['result'] for file in (WORK / 'scans').glob('*/done.json'))
    jobs = Counter(lane.load(file)['kind'] for file in (WORK / 'completed').glob('*.json'))
    receipts = [lane.load(file) for file in (WORK / 'fq').glob('*.csv.json')]
    loops = Counter(receipt['kind'] for receipt in receipts if lane.complete(receipt))
    recovery = lane.load(WORK / 'recovery-control.json')
    source_controls = lane.load(WORK / 'control/source-controls.json')
    old_proof = lane.load(WORK / 'control/683-proof-reuse.json')
    endpoints = [lane.load(file) for file in sorted((WORK / 'donor-endpoints').glob('*.json'))]
    cleanup_receipt = lane.load(WORK / 'cleanup-receipt.json') if (WORK / 'cleanup-receipt.json').exists() else {}
    published = {}
    for file in (WORK / 'published').glob('*/*-proof.json'):
        if file.name != 'publication-proof.json':
            continue
        proof = lane.load(file)
        if lane.accepted(proof['walk'], 'checked independently'):
            published[file.parent.name] = proof['sha256']
    return dict(strict=strict, scans=scans, jobs=jobs, loops=loops, recovery=recovery,
                source_controls=source_controls, old_proof=old_proof, cleanup=cleanup_receipt, endpoints=endpoints,
                published=published, pending=len(list((WORK / 'pending-finishes').glob('*.json'))))


def donor_measurements(measured):
    groups = {}
    for endpoint in measured['endpoints']:
        count = int(endpoint['job'].split('-')[2])
        groups.setdefault(count, []).append(endpoint)
    notes = []
    for count, items in sorted(groups.items()):
        best = min(item['score'] for item in items)
        gap = best - lane.bars()[count]
        scores = [item['score'] for item in items]
        notes.append(f'{len(items)} donor seeds at {count} returned no take. The best endpoint was {gap:+.3e} from bar38.')
        if any(item['repeated'] for item in items):
            notes.append(f'The endpoints at {count} span {max(scores) - min(scores):.3e} in score. The count closed after the repeat.')
        elif any(item['held'] for item in items):
            notes.append(f'The {count} donor queue closed after a seed returned to the held geometry.')
    return notes


def fresh_measurements():
    path = WORK / 'control/n210-metric.json'
    if not path.is_file():
        return []
    control = lane.load(path)
    beyond = control['live_peer_at_publication'] - control['score']
    notes = [f'The 210 certificate scored {control["score"]:.17g}. '
             f'It was {beyond:.3e} below the live peer row at publication.',
             f'Its {control["files"]}-file walk and both clearance checks passed.']
    repair = WORK / 'source-records/937-2c2a988fd302b75a/receipt.json'
    if repair.is_file():
        proof = lane.load(repair)['walk']
        notes.append(f'The new 937 record passed {proof["files"]} files uncapped after the prior '
                     'quench take row left its live table.')
        notes.append('The pending journal reused the existing 900 second search output.')
    audit = WORK / 'control/n937-metric.json'
    if audit.is_file():
        proof = lane.load(audit)
        gain = proof['peer_at_publication'] - proof['score']
        notes.append(f'The repaired 937 certificate scored {proof["score"]:.17g}, {gain:.3e} below the live row at publication.')
        notes.append(f'Its final {proof["files"]}-file walk and both metric readers passed.')
    return notes


def write_doc(snapshot, measured):
    counts = snapshot['counts']
    if counts:
        picks = ', '.join(str(n) for n in counts)
        result = f'The final take holds {picks}. The gain against bar38 is {snapshot["gain"]["against_base"]:.10g}.'
    else:
        result = 'The final take is empty.'
    loops, jobs, scans = measured['loops'], measured['jobs'], measured['scans']
    section = '\n'.join([
        '', '### Round 38', '', result,
        '[Round 38 results](../results/forensics-r38-2026-11-18.tsv)', '',
        f'The strict held scan took {measured["strict"]["seconds"]:.1f} seconds and produced {measured["strict"]["starts"]} starts.',
        'The separate scans of the submitted 683 and 793 picks produced zero starts.',
        f'The round completed {scans["composed"]} source scans including those two picks.',
        f'The scheduler closed {jobs["fresh-900"]} fresh seeds, {jobs["rectangle"]} rectangle jobs and {jobs["donor-900"]} donor seeds.',
        f'boxE returned {sum(loops.values())} complete fq receipts including the positive control and certification loops.',
        '',
        'The two-square control reduced side 2.05 to 2.0000000000002576.',
        'The restart control recovered the exact packing after the final source record was written.',
        'It reused the certification receipt and cleared the pending entry.',
        'The four live-stop controls and five walker regressions passed.',
        'The submitted 683 rows match the 49-file round 37 proof by full SHA256.',
        'Frozen share31 exempted every comparison for 228 and kept nine comparisons for 972.',
        'The second 210 seed stopped when two CSV hashes resolved to the same canonical geometry.',
        'A separate search deadline now bounds each stochastic search before the fq loop.', '',
        'Start the composer and first 900 second seed when a peer publishes a fresh certificate.',
        'Only run a donor seed when the near geometry and held share meet the round filter.',
        'The idle scheduler leaves the numerical slots empty.', '',
    ])
    notes = donor_measurements(measured) + fresh_measurements()
    if notes:
        section += '\n' + '\n'.join(notes) + '\n'
    draft = WORK / 'round38-doc.md'
    draft.write_text(section)
    checker = '$STYLE_CHECK/check.py'
    subprocess.run(['/opt/homebrew/bin/python3', checker, '--level', 'default', str(draft)], check=True)
    existing = DOC.read_text()
    if '\n### Round 38\n' not in existing:
        with DOC.open('a') as handle:
            handle.write(section)
    elif not existing.endswith(section):
        raise RuntimeError('round 38 doc section differs from final measurements')


def git(*arguments, timeout=45):
    return subprocess.run(['git', *arguments], cwd=REPO, capture_output=True, text=True,
                          timeout=timeout, check=True).stdout.strip()


def commit():
    paths = [str(p.relative_to(REPO)) for p in (DRIVER, lane.CODE / 'forensics_walk38.py',
             Path(__file__).resolve(), lane.CODE / 'forensics_worker38.py', DOC, RESULTS)]
    if git('status', '--porcelain', '--', *paths):
        git('add', '--', *paths)
        git('commit', '--only', '-m', 'Record round 38 forensics work and results', '--', *paths)
    head = git('log', '-1', '--format=%H', '--', *paths)
    changed = set(git('show', '--format=', '--name-only', head).splitlines())
    if not changed or changed - set(paths):
        raise RuntimeError(f'unexpected paths in commit {head}: {changed}')
    git('show', '--stat', '--oneline', head)
    try:
        git('pull', '--rebase', '--autostash', 'origin', 'main', timeout=50)
        git('push', 'origin', 'HEAD:main', timeout=40)
    except (OSError, subprocess.SubprocessError) as error:
        lane.state(f'GIT push retry after {error!r}')
        git('pull', '--rebase', '--autostash', 'origin', 'main', timeout=35)
        git('push', 'origin', 'HEAD:main', timeout=35)
    head = git('log', '-1', '--format=%H', '--', *paths)
    lane.state(f'GIT pushed round 38 commit {head}')
    return head


def report(snapshot, measured, commits, blocked):
    processes = [line for line in local_workers() if ' forensics_finish38.py ' not in line]
    processes.extend(lane.remote_workers())
    if processes:
        raise RuntimeError(f'cannot publish report while owned workers run: {processes}')
    counts, loops, jobs = snapshot['counts'], measured['loops'], measured['jobs']
    summary = (f'Final certified counts are {", ".join(map(str, counts))}.' if counts else
               'No exclusive row clears the round 38 bar and the final peer comparison.')
    result = dict(lane='forensics', improved_n=len(counts),
                  gain=dict(snapshot['gain'], asof_utc=snapshot['at']), take_dir=str(TAKE), summary=summary,
                  what_was_measured=[
                      f'The strict all-held scan finished in {measured["strict"]["seconds"]:.3f} seconds with '
                      f'{measured["strict"]["starts"]} starts. The two additional held-pick scans at 683 and 793 produced zero starts.',
                      f'The source queue recorded {dict(measured["scans"])}. Closed numerical requests were {dict(jobs)}.',
                      f'The full default-and-polish fq receipt counts were {dict(loops)}.',
                      *donor_measurements(measured),
                      *fresh_measurements(),
                      f'{len(measured["published"])} exact source walks cleared publication. '
                      f'{measured["pending"]} entries remain in the pending-certification journal.',
                      'The four live-stop controls passed. The live boxE control moved the two-square side from '
                      '2.05 to 2.0000000000002576 and returned both fq passes.',
                      'The interruption control recovered from the written final source record while preserving its '
                      'SHA256. It reused the existing numerical result and cleared the pending entry.',
                      f'The submitted 683 rows match the exact round 37 source graph with {measured["old_proof"]["files"]} files and no cap.',
                      f'All {measured["source_controls"]["legacy_walker_regressions"]} walker regressions passed. '
                      f'Frozen share31 kept {measured["source_controls"]["comparison_versions_972"]} versions for 972 and none for 228.',
                      'The first strict launch exited before scanning. The session-detached retry completed the full scan.',
                      'The 210 seed stopped after a different CSV hash matched the geometry of an earlier peer claim. '
                      'The updated claim check catches that case before dispatch.',
                      'The initial 937 producer follow hit its wrapper timeout inside a solver call. '
                      'A separate midm deadline fixed the overrun in boxE control. The first 937 winner '
                      'stayed in the journal until a lower peer row superseded it.',
                      'An invalid byte in boxE process list stopped the idle driver. '
                      'The corrected decoder passed its control, and the driver restarted with no numerical work lost.',
                      f'boxE copy preserved {measured["cleanup"].get("copied_files", 0)} files with verified SHA256 hashes.',
                  ], next=[
                      'Give each fresh certificate its rectangle scan and first 900 second seed. '
                      'The round 38 seed at 937 added 2.091e-7 beyond the preceding live row.',
                      'Pin each producer row by bytes and keep the pending-certification journal. '
                      'The 937 repair recovered the finished search after its upstream live row disappeared.',
                      'Keep held-only slots empty after the opening scan. The strict round 38 pass and both held-pick '
                      'rescans produced zero starts. Keep the unchanged 910 and widened window families closed.',
                      'Admit low-share k123 donors near the bar only while their geometry is unprobed and the count '
                      'has no fallback. The round 37 donor 793 fed a gain of 5.09e-6. '
                      'Both round 38 seeds at 973 returned to the same endpoint above the bar.',
                  ], commits=commits, processes_left=processes, blocked=blocked,
                  repo='private repo', branch='main', worktree=str(REPO), pr=None)
    lane.save(TAKE / 'report.json', result)
    lane.state(f'REPORT wrote {TAKE}/report.json; final rows={counts}; processes_left=[]')
    return result


def supervise():
    (WORK / 'supervisor.pid').write_text(str(os.getpid()) + '\n')
    while time.time() < lane.LAST_WALK:
        try:
            if not driver_pid():
                start()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            lane.state(f'HEALTH supervisor start retry {error!r}')
        time.sleep(min(30, max(1, lane.LAST_WALK - time.time())))
    while driver_pid() and time.time() < lane.DEADLINE - 180:
        time.sleep(20)
    blocked = []
    for attempt in range(3):
        try:
            stop()
            cleanup()
            break
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            lane.state(f'RETRY cleanup attempt {attempt + 1}: {error!r}')
            if attempt == 2:
                blocked.append(f'boxE cleanup: {error}')
            time.sleep(10)
    while time.time() < FREEZE:
        time.sleep(min(30, max(1, FREEZE - time.time())))
    snapshot = freeze()
    measured = measurements()
    commit_file = WORK / 'tool-commit.txt'
    commits = commit_file.read_text().splitlines() if commit_file.exists() else []
    try:
        write_doc(snapshot, measured)
        commits.append(commit())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        head = git('log', '-1', '--format=%H', '--', str(RESULTS.relative_to(REPO)))
        if head:
            commits.append(head)
        blocked.append(f'Final documentation or Git push: {error}')
    report(snapshot, measured, commits, blocked)


if __name__ == '__main__':
    action = sys.argv[1]
    {'start': start, 'stop': stop, 'cleanup': cleanup, 'freeze': freeze, 'supervise': supervise}[action]()
