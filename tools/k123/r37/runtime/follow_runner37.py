from pathlib import Path
import csv
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path.home() / 'scratch/squares-k123'
os.chdir(ROOT)
sys.path[:0] = [str(ROOT), str(ROOT / 'lane')]
import methods_lp
from live_guard37 import should_stop


def live_score(count, fallback):
    for line in (ROOT / 'bars.tsv').read_text().splitlines():
        values = line.split('\t')
        if int(values[0]) == count:
            return float(values[2])
    return fallback


def run(job_path):
    job = json.loads(Path(job_path).read_text())
    config = json.loads((ROOT / 'runtime33.json').read_text())
    count = int(job['n'])
    output = ROOT / job['out']
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / job['raw']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == job['start_sha256']
    end = min(time.time() + job['seconds'], float((ROOT / 'search-deadline').read_text()))
    command = [config['python'], '-I', 'lane/invent_rest.py', str(count), str(source), str(output / 'search'), '--seconds', str(job['seconds']), '--seed', str(job['seed']), '--modes', 'lkick', '--bar', str((job['start_score'] + 1) * count ** .5), '--deadline', 'deadline', '--plateau-stop', '0']
    stopped = False
    with (output / 'search.log').open('a') as stream:
        process = subprocess.Popen(command, stdout=stream, stderr=stream, start_new_session=True)
        while process.poll() is None:
            if time.time() >= end or should_stop(job['start_score'], live_score(count, job['start_score']), job['start_score']):
                stopped = True
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                break
            try:
                process.wait(timeout=min(2, max(.01, end - time.time())))
            except subprocess.TimeoutExpired:
                pass
    candidates = []
    for candidate in (output / 'search/raw').glob('*.csv'):
        packing = methods_lp.load(str(candidate), {count})[count]
        score = methods_lp.side(packing) / count ** .5 - 1
        candidates.append((score, candidate))
    receipt = {'n': count, 'phase': job['seconds'], 'seed': job['seed'], 'stopped': stopped, 'returncode': process.returncode, 'raw_count': len(candidates), 'status': 'dry', 'start_sha256': job['start_sha256']}
    if candidates:
        score, candidate = min(candidates, key=lambda item: item[0])
        receipt['raw_score'] = score
        if score < live_score(count, job['start_score']) - 1e-10:
            numeric = dict(job, raw=str(candidate.relative_to(ROOT)))
            numeric_path = output / 'numeric-job.json'
            numeric_path.write_text(json.dumps(numeric))
            result = subprocess.run([config['python'], '-I', str(ROOT / 'near_numeric36.py'), str(numeric_path)], timeout=max(1, min(1140, float((ROOT / 'deadline').read_text()) - time.time())))
            receipt.update(status='certified' if result.returncode == 0 else 'numeric-failed', numeric_returncode=result.returncode)
    (output / 'follow-result37.json').write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    run(sys.argv[1])
