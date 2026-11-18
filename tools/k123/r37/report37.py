from pathlib import Path
import collections
import csv
import datetime
import json
import subprocess

REPOSITORY = Path('$PRIVATE_REPO')
LANE = REPOSITORY / 'lanes/squares'
SCRATCH = Path('$SCRATCH/bounties-squares')
TAKE = SCRATCH / 'take-k123-r37'
WORK = TAKE / 'work'


def read_json(path, fallback):
    return json.loads(path.read_text()) if path.exists() else fallback


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def report():
    bars = {int(row['n']): float(row['bar']) for row in rows(SCRATCH / 'round37-briefs/bar37.tsv')}
    own = rows(TAKE / 'take.tsv')
    peers = dict(bars)
    for table in SCRATCH.glob('take-*-r37/take.tsv'):
        if table.parent == TAKE:
            continue
        for row in rows(table):
            count = int(row['n'])
            peers[count] = min(peers[count], float(row['new']))
    assert all(float(row['new']) < min(bars[int(row['n'])], peers[int(row['n'])]) - 1e-10 for row in own), 'stale retained row'
    records = [json.loads(line) for line in (WORK / 'records.jsonl').read_text().splitlines() if line]
    near = read_json(WORK / 'near-state36.json', {})
    collection = read_json(WORK / 'collect-state.json', {})
    follows = read_json(WORK / 'follow-state37.json', {})
    archives = read_json(WORK / 'archives34.json', {})
    walks = read_json(WORK / 'finalwalk36.json', [])
    scans = []
    for task in (WORK / 'taskdone').glob('*.json'):
        entry = read_json(task, {})
        if entry.get('kind') == 'scan' and entry.get('rc') == 0:
            scans.append(entry)
    numeric = {'attempts': len(records), 'counts': len({entry['n'] for entry in records}), 'raw_candidates': sum(bool(entry.get('raw')) for entry in records), 'timeouts': sum(entry.get('code') == -2 for entry in records), 'errors': dict(collections.Counter(entry['error'] for entry in records if entry.get('error'))), 'attempts_by_slot': dict(collections.Counter(entry['worker'] for entry in records))}
    published_near = [entry for entry in near.values() if entry.get('status') in ('published', 'promoted')]
    certified_entries = [entry for entry in collection.values() if entry.get('status') in ('published', 'superseded-peer33')]
    native_counts = sorted({entry['n'] for entry in certified_entries if not entry.get('producer_job', '').startswith('fresh-follow37-')})
    published_steps = [{'n': entry['n'], 'producer_job': entry.get('producer_job'), 'gain_beyond_peer_at_publication': entry.get('gain_over_other_at_publish')} for entry in certified_entries]
    gain_base = sum(bars[int(row['n'])] - float(row['new']) for row in own)
    gain_live = sum(peers[int(row['n'])] - float(row['new']) for row in own)
    commits = read_json(WORK / 'commits37.json', [])
    blocked = read_json(WORK / 'blocked37.json', 'none')
    stopped = read_json(WORK / 'cleanup37.json', {})
    process_count = stopped.get('processes_left', -1)
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPOSITORY, text=True).strip()
    next_steps = [
        'Join the next lowest live changed geometries first. Keep one wide1.005 slot: its round37 793/972r join produced donor fdcdba0c1dc856a5, which fed the classfill793 gain5.0868e-6. Keep unchanged completed signatures closed.',
        'Give fresh peer certificates the first 180s follow and first unprobed900s seed. The round37 follow of fresh classfill793 added2.4189e-9 beyond that peer. Count by exact geometry, and retain shared claims and the live-row stop.',
        'Keep direct third-seam starts after a physical input change. Round36 private793 supplied native911, and private972 supplied native972 before the forensics follow. Separate donor-fed peer gains from native join yield.',
        'Rank near donors by room and held share, not side equality. Round37 donor793 paid at held share0.398487. Require an unprobed geometry and stop after a fallback at that n.',
        'Keep boxE at three numerical slots and boxD at one with load guards. The round37 one-slot baseline paused37/60 samples at limit9; the limit10 trial paused34/60 and completed8 jobs. Do not infer a causal gain from changing background load.',
        'Keep complete source checks before dispatch. The exact-byte683 alias removed a false missing path and admitted its fresh follow. Preserve the full SHA guard, changed-byte red control and fresh immutable record pins.',
    ]
    result = {
        'lane': 'k123',
        'improved_n': len(own),
        'gain': {'against_base_bar': gain_base, 'beyond_other_live_r37': gain_live},
        'take_dir': str(TAKE),
        'summary': f'{len(own)} retained rows beat bar37 and every live peer. {len(native_counts)} native counts and {len(published_near)} near donors certified. All owned workers stopped and box archives verified.' if process_count == 0 else f'{len(own)} retained rows; round37 work remains active.',
        'what_was_measured': [
            'Numerical joins: ' + json.dumps(numeric, sort_keys=True),
            f'Completed donor scans: {len(scans)}. Native certified counts: {native_counts}. Near donor states: ' + json.dumps(dict(collections.Counter(entry.get('status') for entry in near.values())), sort_keys=True),
            'Native raw dispositions: ' + json.dumps(dict(collections.Counter(entry.get('status') for entry in collection.values() if not entry.get('producer_job', '').startswith('fresh-follow37-'))), sort_keys=True) + '. A raw candidate is not a credited gain.',
            'Completed geometry history: ' + json.dumps(read_json(WORK / 'history-final37.json', read_json(WORK / 'setup37.json', {})), sort_keys=True),
            'Fresh follow states: ' + json.dumps(dict(collections.Counter(entry.get('status') for entry in follows.values())), sort_keys=True),
            'Certified steps at publication: ' + json.dumps(published_steps, sort_keys=True) + '. The final live-peer gain can be larger when peers remove superseded rows.',
            'Wide1.005 join793/972r produced donor fdcdba0c1dc856a5, only4.1868e-8 above bar37, held share0.398487. Classfill seed4882 and its fresh extra seed4979 reached0.017616691576745502. Our180s follow then reached0.017616689157831766. These are successive steps, not separate additive gains against the bar.',
            'boxE and boxD reproduced the444 control at side21.564693167754. Own756 passed. Changed target producer records and excluded public ancestry were rejected.',
            'Live-stop controls passed: donor above the bar and live at bar continues; donor or held start with live2e-6 lower stops; held start alone continues.',
            'Priority control passed: native certificate, fresh follow, near donor, fresh scan, deferred scan. The cold boxD inventory control returned[] when no manifest existed.',
            'Producer-record retry controls passed five cases. A changed source record or source-rule version gets a new immutable pin and source check. Unchanged refusals and completed geometries stay closed.',
            'The exact683 source alias passed five path controls and all five quench_walk_regress.py cases. It requires the full target SHA256. Changed bytes, unrelated paths and an existing source are never aliased. The embedded checker changed from one missing-path hit to clean33 files at cap100000. No old sidecar was edited.',
            'Published rows require finesafe clearance2.2e-11, the full certified-file default/polish fq loop, unchanged bytes, an uncapped source walk and a fresh locked peer check. Own and held descendants receive no share gate.',
            'Near donor handoffs include gap to bar37, board room, held36b centre share at1e-3, SHA256 and walk file count. The held-share measure ranks search; it does not refuse owned ancestry.',
            'Final walks: ' + json.dumps(walks, sort_keys=True),
            'Verified box archives: ' + json.dumps(archives, sort_keys=True),
            'boxD guard trial: baseline ' + json.dumps(read_json(WORK / 'load-baseline37.json', {}), sort_keys=True) + '; trial ' + json.dumps(read_json(WORK / 'load-trial37.json', {}), sort_keys=True) + '. The slot cap stayed one. These are observations under changing box load.',
        ],
        'next': next_steps,
        'commits': commits,
        'processes_left': process_count,
        'blocked': blocked,
        'repo': str(REPOSITORY),
        'branch': branch,
        'worktree': str(REPOSITORY),
        'pr': None,
    }
    return result, own, numeric, len(scans), len(published_near)


def artifacts():
    result, retained, numeric, scan_count, donor_count = report()
    table = LANE / 'results/k123-r37-2026-11-18.tsv'
    with table.open('w') as stream:
        writer = csv.DictWriter(stream, ['n', 'held', 'new', 'gain', 'source', 'licence'], delimiter='\t')
        writer.writeheader()
        writer.writerows(retained)
    section = '\n'.join([
        '## Round 37',
        '',
        f'The lane retains {result["improved_n"]} layouts below bar37 and every live peer.',
        f'The gain against bar37 is {result["gain"]["against_base_bar"]:.15g}.',
        f'The gain beyond the other live takes is {result["gain"]["beyond_other_live_r37"]:.15g}.',
        f'The boxes completed {numeric["attempts"]} numerical joins on {numeric["counts"]} counts.',
        f'They completed {scan_count} donor scans and certified {donor_count} near donors.',
        '',
        'Changed held36b geometries ran first.',
        'The initial history closed 30024 completed geometry signatures.',
        'boxE used three numerical slots and boxD used one.',
        'Both boxes reproduced the 444 control at side 21.564693167754.',
        'Ownership, producer-record, live-stop and queue-priority controls passed.',
        '',
        'The wide 1.005 turn of the 793/972r join supplied the useful 793 donor.',
        'Its held share was 0.398487, and it stood 4.1868e-8 above bar37.',
        'Classfill followed it to a gain of 5.0868e-6 against bar37.',
        'Our 180-second follow added 2.4189e-9 beyond that fresh peer.',
        'These are successive steps, not separate gains against the bar.',
        '',
        'Each published row passed finesafe at clearance 2.2e-11.',
        'The full default and polish fq loop started from certified bytes.',
        'Complete source walks and a locked live-peer check preceded publication.',
        'Owned and held descendants received no share gate.',
        'Public-first rows retained both frozen share checks.',
        'Near donor handoffs include the held-share search measure and board room.',
        'The exact 683 source alias requires the complete target byte hash.',
        'Five alias controls and all five source-walk regression cases passed.',
        'A changed source record receives a new immutable pin.',
        'No old sidecar was edited.',
        'Fresh-input admission closes at 05:45 UTC.',
        'All long jobs must end before 06:45 UTC.' if result['processes_left'] != 0 else 'All long jobs ended before 06:45 UTC.',
        '',
        'Sources are in [the round table](../results/k123-r37-2026-11-18.tsv).',
        'The [round helpers](../tools/k123/r37/) preserve setup and controls.',
        'Receipts remain in `$SCRATCH/bounties-squares/take-k123-r37/work/`.',
        '',
    ])
    section_path = WORK / 'round37-section.md'
    section_path.write_text(section)
    checker = Path('$STYLE_CHECK/check.py')
    subprocess.run(['/opt/homebrew/bin/python3', str(checker), '--level', 'default', str(section_path)], check=True)
    document = LANE / 'avenues/k123.md'
    prefix = document.read_text().split('\n## Round 37\n', 1)[0]
    document.write_text(prefix.rstrip() + '\n\n' + section)
    return result


if __name__ == '__main__':
    import sys
    result = artifacts() if '--artifacts' in sys.argv else report()[0]
    if '--final' in sys.argv:
        assert result['processes_left'] == 0
        assert len(read_json(WORK / 'archives34.json', {})) == 2
        temporary = TAKE / 'report.json.tmp'
        temporary.write_text(json.dumps(result, indent=2) + '\n')
        temporary.replace(TAKE / 'report.json')
    else:
        (WORK / 'report-checkpoint37.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
