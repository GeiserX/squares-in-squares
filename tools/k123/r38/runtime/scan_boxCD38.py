"""Run one pinned scan in the existing boxD slot."""
import json
import fcntl
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path.home() / 'scratch/squares-k123'


def scan(tag):
    work = ROOT / 'scan-on-boxCD38' / tag
    job = json.loads((work / 'incoming' / (tag + '.json')).read_text())
    points = json.loads((work / f'sources-{tag}.json').read_text())
    assert all(parent.get('seed_share_gate') == 'v6' for parent in points.values())
    pairs = (work / f'pairs-{tag}.txt').read_text().split()
    deadline = float((ROOT / 'search-deadline').read_text())
    if time.time() >= deadline:
        raise RuntimeError('Search deadline reached')
    diverse = job.get('diversity_scan', False)
    scanner = ROOT / 'lane' / ('k123_join_diverse29.py' if diverse else 'k123_join.py')
    args = [str(scanner), 'scan', f'{tag}.csv', f'bars-{tag}.tsv', f'scan{tag}', *pairs,
            '--rmax', '.3', '--pmax', '.3', '--room', '-.1', '--mmin', '10']
    if diverse:
        args.extend(['--seam-bins', str(job['seam_bins'])])
    log = f'scan{tag}.log'
    with (work / log).open('w') as stream:
        subprocess.run([sys.executable, '-I', *args], cwd=work, stdout=stream, stderr=stream,
                       timeout=max(1, min(45, deadline - time.time())), check=True)
    board = work / 'board.tsv'
    if not board.exists():
        shutil.copyfile(ROOT / 'board.tsv', board)
    selector = ROOT / ('divsel29.py' if diverse else 'sel21.py')
    selection = work / f'q{tag}.txt'
    subprocess.run([sys.executable, '-I', str(selector), selection.name,
                    str(job.get('starts_per_count', 4)), log],
                   cwd=work, timeout=10, check=True)
    recipes = []
    for line in selection.read_text().splitlines():
        fields = line.split('\t')
        if float(fields[3]) <= .09 and float(fields[5]) <= .05:
            recipes.append(line + '\t' + tag + '\n')
    result = {**job, 'rc': 0, 'ended': time.strftime('%FT%TZ', time.gmtime()),
              'worker_box': 'boxD', 'recipes': len(recipes)}
    (work / 'recipes.tsv').write_text(''.join(recipes))
    (work / 'receipt.json').write_text(json.dumps(result))
    print(json.dumps(result), flush=True)


def install(tag):
    inbox = ROOT / 'routed-boxCD38' / tag
    done = ROOT / 'taskdone' / (tag + '.json')
    queue = ROOT / 'queue.tsv'
    with (ROOT / 'routed-boxCD38.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not done.exists():
            old = {line for line in queue.read_text().splitlines() if line.endswith('\t' + tag)}
            batch = ''.join(line + '\n' for line in (inbox / 'recipes.tsv').read_text().splitlines() if line not in old)
            with queue.open('a') as stream:
                stream.write(batch)
            receipt = done.with_suffix('.tmp')
            receipt.write_text((inbox / 'receipt.json').read_text())
            receipt.replace(done)
        (ROOT / 'routed38' / (tag + '.json')).unlink(missing_ok=True)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[2] == '--install':
        install(sys.argv[1])
    else:
        scan(sys.argv[1])
