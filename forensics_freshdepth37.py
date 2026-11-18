"""Compare window depths on a pinned fresh certificate, not the spent held set."""
import json
import pickle
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as composer
import forensics_depth37 as depth
import forensics_r37 as lane
import forensics_rect as rectangles


def scan(folder, cache, keep, packing):
    folder.mkdir(parents=True, exist_ok=True)
    lane.write_details(folder / 'details.csv')
    command = [lane.PY, '-I', str(Path(__file__).resolve()), 'child',
               str(folder / 'details.csv'), str(folder / 'raw'), '--cache', str(cache),
               '--keep', str(keep), '--fresh-only', '--slack', '0.004', '--per-n', '8',
               '--max-mesh', '400', '--strict-single', '--skip-ties', '--collide', '0.03', str(packing)]
    with (folder / 'rect.log').open('w') as output:
        subprocess.run(command, stdout=output, stderr=subprocess.STDOUT, check=True,
                       timeout=min(900, max(1, lane.SCAN_STOP - time.time())))
    return sorted((folder / 'raw').glob('*.csv'))


def main():
    count = int(sys.argv[1])
    started = time.time()
    packing = lane.TAKE / f'{count}.csv'
    digest, record_digest = lane.sha(packing), lane.sha(Path(str(packing) + '.json'))
    folder = lane.WORK / f'freshdepth-{count}-{digest[:16]}-{time.time_ns()}'
    folder.mkdir(exist_ok=False)
    pinned = folder / f'{count}.csv'
    shutil.copyfile(packing, pinned)
    shutil.copyfile(str(packing) + '.json', str(pinned) + '.json')
    assert lane.sha(packing) == lane.sha(pinned) == digest
    assert lane.sha(Path(str(pinned) + '.json')) == record_digest
    metadata = json.loads(Path(str(pinned) + '.json').read_text())
    licence = metadata['source']['licence']
    walked = lane.walk(pinned)
    assert lane.walk_accepted(walked, licence), walked
    measured = lane.WORK / 'depth16-matched'
    assert json.loads((measured / 'measurement.json').read_text())['control_starts'] > 0
    sources = []
    caches = {}
    for keep in (8, 16):
        cache = folder / f'windows{keep}.pkl'
        shutil.copyfile(measured / f'windows{keep}.pkl', cache)
        with cache.open('rb') as source:
            table = pickle.load(source)
        sources.append([entry[0] for entry in table['src']])
        caches[keep] = cache
    assert sources[0] == sources[1]
    lane.state(f'START freshdepth n{count} keep8/16 on pinned fresh SHA{digest}; '
               f'prior raised539 control passed; matched{len(sources[0])} held sources; '
               f'full source walk{walked["files"]} uncapped; not a held-only rescan')
    baseline = scan(folder / 'baseline8', caches[8], 8, pinned)
    seen = {depth.key(path) for path in baseline}
    expanded = scan(folder / 'expanded16', caches[16], 16, pinned)
    jobs = []
    targets = lane.targets()
    for candidate in expanded:
        signature = depth.key(candidate)
        if signature in seen:
            continue
        seen.add(signature)
        output_count, squares = next(iter(rectangles.layouts(candidate).items()))
        side, _ = composer.frame(squares)
        source = dict(original=str(pinned), snapshot=str(pinned), sha256=digest,
                      n=count, licence=licence, start_walk_clean=True,
                      start_walk_files=walked['files'], start_walk_capped=False,
                      note='keep16 geometry absent from matched keep8 fresh-source scan')
        jobs.append([side - targets[output_count][1], str(candidate), output_count, source])
    lane.atomic(lane.WORK / 'inbox' / f'{folder.name}.json', json.dumps(sorted(jobs)))
    result = dict(n=count, seconds=time.time() - started, baseline_starts=len(baseline),
                  expanded_starts=len(expanded), new_geometries=len(jobs),
                  counts=sorted({entry[2] for entry in jobs}), sha256=digest,
                  matched_held_sources=len(sources[0]))
    lane.atomic(folder / 'measurement.json', json.dumps(result, indent=2))
    lane.state('FRESHDEPTH ' + json.dumps(result))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'child':
        import forensics_memory36 as memory
        memory.start_guard('freshdepth37 scan')
        sys.argv = [str(lane.LANE / 'forensics_rect.py')] + sys.argv[2:]
        rectangles.main(sys.argv)
    else:
        main()
