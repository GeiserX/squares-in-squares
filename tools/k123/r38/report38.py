"""Write the round 38 result, its per-count table and the lane notes."""
from collections import Counter
import csv
import json
from pathlib import Path
import subprocess
import sys

from setup38 import LANE, ROW_FIELDS, SCRATCH, TAKE, WORK, write_json

REPO = LANE.parent.parent


def read_json(path, fallback):
    return json.loads(path.read_text()) if path.is_file() else fallback


def rows(path):
    with path.open() as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def records(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def measure():
    csv.field_size_limit(1 << 28)
    bars = {int(row['n']): float(row['bar']) for row in rows(SCRATCH / 'round38-briefs/bar38.tsv')}
    owned = rows(TAKE / 'take.tsv')
    peers = dict(bars)
    for table in SCRATCH.glob('take-*-r38/take.tsv'):
        if table.parent == TAKE:
            continue
        for row in rows(table):
            n = int(row['n'])
            peers[n] = min(peers[n], float(row['new']))
    gain_base = sum(bars[int(row['n'])] - float(row['new']) for row in owned)
    gain_live = sum(peers[int(row['n'])] - float(row['new']) for row in owned)
    assert all(float(row['new']) < min(bars[int(row['n'])], peers[int(row['n'])]) - 1e-10 for row in owned)
    numbers = records(WORK / 'records.jsonl')
    archive = read_json(WORK / 'archives34.json', {})
    states = read_json(WORK / 'collect-state.json', {})
    near = read_json(WORK / 'near-state36.json', {})
    own_follow = read_json(WORK / 'own-state38.json', {})
    feed = read_json(WORK / 'feed38.json', {})
    clean = read_json(WORK / 'cleanup38.json', {})
    near_rows = [job for job in near.values() if job.get('status') == 'published']
    donor_slots = Counter(key.split('-', 1)[0] for key, job in near.items() if job.get('status') == 'published')
    donors = []
    for job in near_rows:
        packing = Path(job['path'])
        notice = read_json(Path(str(packing) + '.json'), {})
        donors.append({
            'n': job['n'],
            'gap': job['gap'],
            'board_room': job['board_room'],
            'held_share_1e3': notice.get('held_share_1e3'),
            'sha256': notice.get('csv_sha256'),
            'path': str(packing),
        })
    donor_examples = []
    if donors:
        for candidate in [donors[0], min(donors, key=lambda row: row['gap']), min(donors, key=lambda row: row['held_share_1e3'])]:
            if candidate not in donor_examples:
                donor_examples.append(candidate)
    native = sorted({job['n'] for job in states.values() if job.get('status') in {'published', 'superseded-peer33'}})
    private = read_json(WORK / 'prejoin-seen31.json', [])
    feed_outcomes = feed.get('outcomes', {})
    scan_kinds = Counter(job['kind'] for job in feed.get('scans', []))
    disposed = Counter(job.get('status') for job in states.values())
    out = {
        'attempts': len(numbers),
        'by_slot': dict(Counter(row['worker'] for row in numbers)),
        'raw_candidates': sum(bool(row.get('raw')) for row in numbers),
        'counts': len({row['n'] for row in numbers}),
        'errors': dict(Counter(row['error'] for row in numbers if row.get('error'))),
        'timeouts': sum(row.get('code') == -2 for row in numbers),
        'live_family_stops': sum(row.get('code') == -3 for row in numbers),
        'scans': len(feed.get('scans', [])),
        'scans_by_kind': dict(scan_kinds),
        'done_scans': sum(
            (WORK / 'taskdone' / (row['tag'] + '.json')).is_file() and
            read_json(WORK / 'taskdone' / (row['tag'] + '.json'), {}).get('rc') == 0
            for row in feed.get('scans', [])
        ),
        'pending_batches': len(feed.get('pending', [])),
        'near_donors': len(near_rows),
        'near_donors_by_slot': dict(donor_slots),
        'donors_within_1e_7': sum(1e-10 < row['gap'] <= 1e-7 for row in near_rows),
        'third_seam_starts': len(list((WORK / 'private-near36').glob('*.csv'))),
        'third_seam_scans': sum(job.get('kind') == 'fresh-third-seam' for job in feed.get('scans', [])),
        'third_seam_attempts': len(private),
        'native_counts': native,
        'processes_left': clean.get('processes_left', -1),
    }
    next_steps = [
        f'Join the next changed held rows and fresh certificates first. Round 38 sent {out["scans"]} scans and completed {out["attempts"]} joins. Keep completed geometry signatures closed.',
        f'Keep one wide 1.005 slot for changed pairs. It completed {out["by_slot"].get("j22w", 0)} joins and produced {donor_slots["j22w"]} eligible donors. The round 37 wide 793/972r donor fed a 793 gain of 5.0868e-6.',
        f'Give unprobed near donors with held share below 0.5 one seed per geometry. Round 38 published {out["donors_within_1e_7"]} donors within 1e-7 of their bar. The 973 fallback shows when to close a count.',
        f'Test a direct third seam only after the inputs change. Round 38 fed {out["third_seam_scans"]} such scans. Round 36 found native 911 and 972 from private intermediates.',
        'Use the single boxD slot for a few fresh scans when boxE guard pauses. Eight rerouted scans this round supplied five recipes.',
        'Preserve the hash on every historical version when binding a producer record. The round 38 repair cleared an uncapped 18-file walk on a real 210 candidate.',
        'Let each producer finish its own 180 s follow before its handoff. Backlog owns the next 180 s follow, and forensics owns the composer and first 900 s seed.',
    ]
    measured = [
        'Round 38 search and certification counts. ' + json.dumps(out, sort_keys=True),
        'Fresh geometry admission. ' + json.dumps({
            'admitted_geometries': len(feed.get('geometries', [])),
            'outcomes': dict(Counter(value.split(' ', 1)[0] for value in feed_outcomes.values())),
            'official_counts': sorted({
                job['n'] for job in feed.get('scans', [])
                if job['kind'] == 'fresh-certificate' and '/near/' not in job['path']
            }),
        }, sort_keys=True),
        'Native raw dispositions. ' + json.dumps(dict(disposed), sort_keys=True),
        'Near donor dispositions. ' + json.dumps(dict(Counter(row.get('status') for row in near.values())), sort_keys=True),
        'Eight early 210 joins cleared bar38 and passed their source walk. The live 210 was lower. Four more peer-lower 210 candidates initially hit the historical pin binding error.',
        'Eligible donor certificates. The first donor, the closest to its bar and the lowest held share. ' + json.dumps(donor_examples, sort_keys=True),
        'Producer follow outcomes. ' + json.dumps(dict(Counter(row.get('status') for row in own_follow.values())), sort_keys=True),
        'Completed geometry history. ' + json.dumps(read_json(WORK / 'history28.json', read_json(WORK / 'setup38.json', {})), sort_keys=True),
        'boxE and boxD reproduced the 444 control at side 21.564693167754. All four live-stop controls passed.',
        'The source controls accepted own 756. They refused excluded public ancestry and a change to a pinned target producer record.',
        'Final source walks. ' + json.dumps(read_json(WORK / 'finalwalk36.json', []), sort_keys=True),
        'Verified box archives. ' + json.dumps(archive, sort_keys=True),
    ]
    for path in sorted(WORK.glob('measurement38-*.txt')):
        measured.append(path.read_text().strip())
    report = {
        'lane': 'k123',
        'improved_n': len(owned),
        'gain': {'against_base_bar': gain_base, 'beyond_other_live_r38': gain_live},
        'take_dir': str(TAKE),
        'summary': f'{len(owned)} rows beat bar38 and every live peer. The lane certified {len(near_rows)} near donors. {len(archive)} box archives passed checksum verification.',
        'what_was_measured': measured,
        'next': next_steps,
        'commits': read_json(WORK / 'commits38.json', []),
        'processes_left': clean.get('processes_left', -1),
        'blocked': read_json(WORK / 'blocked38.json', 'none'),
        'repo': str(REPO),
        'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=REPO, text=True).strip(),
        'worktree': str(REPO),
        'pr': None,
    }
    return report, owned, out


def artifacts(report, owned, metrics):
    table = LANE / 'results/k123-r38-2026-11-18.tsv'
    with table.open('w') as stream:
        writer = csv.DictWriter(stream, ROW_FIELDS, delimiter='\t', lineterminator='\n')
        writer.writeheader()
        writer.writerows(owned)
    section = '\n'.join([
        '## Round 38',
        '',
        f'The lane retained {report["improved_n"]} rows below bar38 and every live take.',
        f'The gain against bar38 was {report["gain"]["against_base_bar"]:.15g}.',
        f'The gain beyond the other live takes was {report["gain"]["beyond_other_live_r38"]:.15g}.',
        f'The boxes completed {metrics["attempts"]} joins across {metrics["counts"]} counts.',
        f'They completed {metrics["done_scans"]} scans and certified {metrics["near_donors"]} near donors.',
        '',
        'The lane joined the new held 683 and 793, then read new certificates from the handoff.',
        'The queue closed 32,452 completed signatures from earlier rounds.',
        f'The wide 1.005 slot completed {metrics["by_slot"].get("j22w", 0)} joins.',
        f'The direct third seam supplied {metrics["third_seam_scans"]} scans.',
        'The producer owned the first 180 s follow of each native improvement.',
        '',
        'Both boxes reproduced the 444 control at side 21.564693167754.',
        'The live-stop control passed all four cases.',
        'A near donor had to be within 1e-6 of its bar and below 0.5 held share.',
        'Each published layout passed finesafe at clearance 2.2e-11.',
        'The full fq loop started from the certified file.',
        'The source walk and live comparison preceded publication.',
        '',
        'See [the round table](../results/k123-r38-2026-11-18.tsv) for the retained rows.',
        'See [the round helpers](../tools/k123/r38/) for the runtime changes.',
        '',
    ])
    section_path = WORK / 'round38-section.md'
    section_path.write_text(section)
    checker = '$STYLE_CHECK/check.py'
    subprocess.run(['/opt/homebrew/bin/python3', checker, '--level', 'default', str(section_path)], check=True)
    document = LANE / 'avenues/k123.md'
    prefix = document.read_text().split('\n## Round 38\n', 1)[0]
    document.write_text(prefix.rstrip() + '\n\n' + section)


if __name__ == '__main__':
    result, owned, metrics = measure()
    if '--artifacts' in sys.argv:
        artifacts(result, owned, metrics)
    if '--final' in sys.argv:
        assert result['processes_left'] == 0, 'workers remain'
        temporary = TAKE / 'report.json.tmp'
        write_json(temporary, result)
        temporary.replace(TAKE / 'report.json')
    else:
        write_json(WORK / 'report-checkpoint38.json', result)
    print(json.dumps(result, indent=2))
