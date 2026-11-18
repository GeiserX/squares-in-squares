"""Measure extra corner-window choices before queuing new held compositions."""
import json
import math
import pickle
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as composer
import forensics_r37 as lane
import forensics_rect as rectangles


def scan(folder, cache, keep, extra):
    folder.mkdir(parents=True, exist_ok=True)
    lane.write_details(folder / 'details.csv')
    command = [lane.PY, '-I', str(lane.LANE / 'forensics_rect.py'), str(folder / 'details.csv'),
               str(folder / 'raw'), '--cache', str(cache), '--keep', str(keep)] + extra
    with (folder / 'rect.log').open('w') as output:
        subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True,
                       timeout=min(1800, max(1, lane.DEADLINE - time.time())))
    return list((folder / 'raw').glob('*.csv'))


def key(path):
    count, squares = next(iter(rectangles.layouts(path).items()))
    return count, lane.geometry_key(squares)


def main():
    started = time.time()
    folder = lane.WORK / (sys.argv[1] if len(sys.argv) > 1 else 'depth16')
    folder.mkdir(exist_ok=True)
    cache = folder / 'windows16.pkl'
    lane.state('START depth16 ablation: top8 had no strict start. Keep16 changes the number of '
               'collision-compatible corner choices. A raised539 control runs before comparison. '
               'Only geometries absent from the matched top8 pass receive fq slots; deadline06:45Z.')
    scan(folder / 'seed', cache, 16, ['--only', '2', '--max-mesh', '0', str(lane.HELD)])
    control = scan(folder / 'control', cache, 16,
                   ['--rescan-cache', '--fresh-only', '--fresh-start', '0', '--only', '539',
                    '--raise', '539:0.001', '--strict-single', '--skip-ties'])
    assert any(path.name.startswith('539-') for path in control), 'held539 reconstruction control failed'
    lane.state(f'CONTROL depth16 held539 reconstruction writes539 with raised target; files={len(control)}')
    common = ['--rescan-cache', '--fresh-only', '--fresh-start', '0', '--slack', '0.001',
              '--per-n', '8', '--max-mesh', '400', '--strict-single', '--skip-ties', '--collide', '0.01']
    baseline_cache = folder / 'windows8.pkl'
    shutil.copyfile(lane.WORK / 'windows37.pkl', baseline_cache)
    with baseline_cache.open('rb') as source:
        baseline_table = pickle.load(source)
    baseline_table['src'] = [entry for entry in baseline_table['src'] if str(entry[0][0]) == str(lane.HELD)]
    with baseline_cache.open('wb') as output:
        pickle.dump(baseline_table, output)
    with cache.open('rb') as source:
        expanded_sources = pickle.load(source)['src']
    assert {entry[0] for entry in baseline_table['src']} == {entry[0] for entry in expanded_sources}
    baseline = scan(folder / 'baseline8', baseline_cache, 8, common)
    baseline_keys = {key(path) for path in baseline}
    expanded = scan(folder / 'expanded16', cache, 16, common)
    targets = lane.targets()
    jobs = []
    seen = set(baseline_keys)
    for candidate in expanded:
        signature = key(candidate)
        if signature in seen:
            continue
        seen.add(signature)
        count, squares = next(iter(rectangles.layouts(candidate).items()))
        side, _ = composer.frame(squares)
        source = dict(original=str(lane.HELD), snapshot=str(lane.HELD),
                      sha256=lane.sha(lane.HELD), n=count, start_walk_clean=True,
                      start_walk_files=2, start_walk_capped=False,
                      licence='own submitted round36 held rows',
                      note='top16 corner choices, geometry absent from matched top8 pass')
        jobs.append([side - targets[count][1], str(candidate), count, source])
    jobs.sort()
    selected = jobs[:64]
    lane.atomic(lane.WORK / 'inbox' / f'{folder.name}.json', json.dumps(selected))
    result = dict(seconds=time.time() - started, control_starts=len(control),
                  baseline_starts=len(baseline), expanded_starts=len(expanded),
                  unique_baseline=len(baseline_keys), new_geometries=len(jobs),
                  matched_sources=len(expanded_sources),
                  queued=len(selected), counts=sorted({entry[2] for entry in selected}))
    lane.atomic(folder / 'measurement.json', json.dumps(result, indent=2))
    lane.state('DEPTH16 ' + json.dumps(result))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
