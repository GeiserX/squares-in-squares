"""Run one boxE fq job with a separate deadline for its stochastic search."""
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import forensics_compose as compose
import forensics_r37 as engine
import forensics_rect as rectangles


def side(path):
    return float(compose.frame(next(iter(rectangles.layouts(path).values())))[0])


def kick(inp, out, n, seconds, seed, target, deadline):
    folder = Path(out + '-kick')
    folder.mkdir(exist_ok=True)
    started = time.time()
    cutoff = min(started + seconds, deadline - 5)
    if cutoff <= started:
        raise TimeoutError('no time remains for the search')
    stop_file = folder / 'search-deadline.txt'
    stop_file.write_text(f'{cutoff}\n')
    code = Path(__file__).resolve().parent
    command = [sys.executable, '-I', str(code / 'midm_scan.py'), '--n', str(n), '--sub', inp,
               '--out', str(folder), '--fq', engine.RBASE + '/fq', '--seconds', str(seconds),
               '--seed', str(seed), '--modes', 'lkick' if seconds == 180 else 'lkick,kick',
               '--deadline', str(stop_file), '--ref', str(target)]
    with (folder / 'kick.log').open('a') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                timeout=max(1, min(seconds + 15, deadline - started)))
    elapsed = time.time() - started
    candidates = [Path(inp), *sorted((folder / 'raw').glob('*.csv'))]
    best = min(candidates, key=side)
    engine.fqloop(str(best), out, target, deadline)
    receipt_path = Path(out + '.json')
    receipt = json.loads(receipt_path.read_text())
    receipt.update(start=side(inp), fq_start=receipt['start'],
                   kick=dict(seconds=seconds, elapsed=elapsed, seed=seed, returncode=result.returncode,
                             candidates=len(candidates), search_cutoff=cutoff))
    receipt_path.write_text(json.dumps(receipt))


def main():
    mode, start, output, *arguments = sys.argv[1:]
    if mode == 'fqloop':
        target, deadline, collide = arguments
        engine.fqloop(start, output, float(target), float(deadline), collide == '1')
    elif mode == 'freshkick':
        count, seconds, seed, target, deadline = arguments
        kick(start, output, int(count), int(seconds), int(seed), float(target), float(deadline))
    else:
        raise SystemExit(f'unknown mode {mode}')


if __name__ == '__main__':
    main()
