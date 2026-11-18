#!/usr/bin/env python3
"""Spend a bounded local slot on saved distinct-fraction polish starts.

forensics_local.py WORK FQ [--seconds 40] [--limit 12]

The collector and its scanner pause during this batch. Atomic claims on the
boxE prevent duplicate work. Failed or unstarted claims return to boxE.
Successful raw results enter the normal collector. Publication still requires
floatsafe and a boxE quench from the certified file.
"""
import argparse
import contextlib
import csv
import datetime
import json
import math
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time


@contextlib.contextmanager
def local_slot(work):
    paused = []
    try:
        parent = int((work / 'watch.pid').read_text())
        os.kill(parent, signal.SIGSTOP); paused.append(parent)
        rows = subprocess.check_output(['ps', '-axo', 'pid,ppid,command'], text=True)
        for row in rows.splitlines():
            p = row.split(None, 2)
            if (len(p) == 3 and Path(p[2].split()[0]).name.lower().startswith('python')
                    and 'forensics_rect.py' in p[2] and str(work / 'scan-') in p[2]):
                os.kill(int(p[0]), signal.SIGSTOP); paused.append(int(p[0]))
        yield
    finally:
        for pid in reversed(paused):
            try:
                os.kill(pid, signal.SIGCONT)
            except ProcessLookupError:
                pass


def remote_claim(keys, release=False):
    assert all(k.startswith('raw-') and len(k) == 28 and
               all(c in '0123456789abcdef' for c in k[4:]) for k in keys)
    action = 'p.rmdir()' if release else 'p.mkdir()'
    code = "from pathlib import Path\nimport json\nr=Path.home()/'scratch/squares-forensics-r23/claims'\nout=[]\n"
    code += 'for k in ' + repr(keys) + ':\n p=r/k\n try:\n  ' + action + '\n  out.append(k)\n except (FileExistsError,FileNotFoundError):pass\n'
    code += 'print(json.dumps(out))'
    command = '$SCRATCH/squares-base/venv/bin/python -I -c ' + shlex.quote(code)
    result = subprocess.run(['ssh', 'boxE', command], capture_output=True,
                            text=True, timeout=10, check=True)
    return json.loads(result.stdout.strip().splitlines()[-1])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('work', type=Path); parser.add_argument('fq')
    parser.add_argument('--seconds', type=float, default=40)
    parser.add_argument('--limit', type=int, default=12)
    args = parser.parse_args(); work = args.work; scratch = work.parents[1]
    csv.field_size_limit(16 * 1024 * 1024)
    with local_slot(work):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import numpy as np
        import forensics_rect as fr
        import forensics_compose as fc
        import forensics_watch as fw
        import midm_scan as ms
        deadline = min(time.time() + args.seconds,
                       float((work / 'deadline.txt').read_text()) - 300)
        bars = {int(r['n']): float(r['score']) for r in csv.DictReader(
            open(scratch / 'gate/cand-round21-1113a/details.csv'))}
        for rnd in (22, 23):
            for path in scratch.glob('take-*-r%d/take.tsv' % rnd):
                for r in list(csv.reader(open(path), delimiter='\t'))[1:]:
                    try:
                        n, score = int(r[0]), float(r[2])
                        bars[n] = min(bars[n], score)
                    except (ValueError, IndexError):
                        pass
        board = {int(r['n']): float(r['board_L']) / math.sqrt(int(r['n'])) - 1
                 for r in csv.DictReader(open(scratch / 'main-r17/gap-by-n.tsv'), delimiter='\t')}
        tried = set()
        for p in (work / 'received').glob('raw-*.json'):
            r = json.loads(p.read_text())
            if 'scan-diverse/' in r.get('raw', ''):
                tried.add(r['n'])
        candidates = {}
        for p in (work / 'tasks').glob('raw-*.json'):
            r = json.loads(p.read_text()); n = r['n']
            if (r.get('backlog_round') != 22 or r['flags'] != 'p'
                    or 'scan-diverse/' not in r.get('raw', '') or n in tried
                    or (work / 'received' / p.name).exists()):
                continue
            key = (r.get('parts', {}).get('side', 100), p.name)
            if n not in candidates or key < candidates[n][0]:
                candidates[n] = (key, p, r)
        picks = sorted(candidates.values(), key=lambda item: board[item[2]['n']] - bars[item[2]['n']])[:args.limit]
        bykey = {p.stem: r for _, p, r in picks}
        leased = remote_claim(list(bykey)) if bykey and time.time() < deadline else []
        completed = set(); trials = []
        tmp = work / 'local-tmp'; tmp.mkdir(exist_ok=True)
        try:
            for key in leased:
                if time.time() >= deadline:
                    break
                r = bykey[key]; n = r['n']; start_time = time.time()
                q = fr.layouts(work / 'inputs' / (key + '.csv'))[n]
                side, q = fc.frame(q)
                limit = max(.1, min(20, deadline - time.time()))
                end, y = ms.quench(args.fq, str(tmp), side,
                                   np.c_[q[:, :2], np.degrees(q[:, 2])], ms.POLISH,
                                   timeout=limit)
                result = dict(r, start=float(side), end=end,
                              seconds=time.time() - start_time,
                              worker='boxA raw polish', timeout_seconds=limit)
                trials.append(dict(key=key, n=n, end=end, seconds=result['seconds']))
                if y is None:
                    continue
                dest = work / 'received' / (key + '.csv')
                fc.write_csv(str(dest) + '.tmp', n, ms.from_fq(y))
                os.replace(str(dest) + '.tmp', dest)
                fw.atomic_json(work / 'received' / (key + '.json'), result)
                completed.add(key)
                print('LOCAL RAW', n, float(side), end, result['seconds'], flush=True)
        finally:
            outstanding = sorted(set(leased) - completed)
            if outstanding:
                remote_claim(outstanding, release=True)
            output = work / ('local-pilot-%d.json' % int(time.time()))
            output.write_text(json.dumps(dict(trials=trials, completed=sorted(completed),
                                             released=outstanding), indent=2))
        print('LOCAL BATCH', len(trials), 'completed', len(completed), 'released', len(outstanding), flush=True)


if __name__ == '__main__':
    main()
