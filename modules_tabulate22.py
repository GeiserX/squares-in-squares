#!/usr/bin/env python3
"""Tabulate new modules, then resume unfinished modules from earlier growth steps.

Usage: modules_tabulate22.py LIBDIR IDS.txt OUT.pkl
Each saved checkpoint contains complete tables. Recovered ids are appended to
IDS.txt so the next generator treats their first available tables as new.
"""
import os
from pathlib import Path
import pickle
import sys
import subprocess
import time
import signal

sys.path.insert(0, os.environ.get('LANE', str(Path(__file__).resolve().parent)))
import modules as M

work, idpath, out = map(Path, sys.argv[1:4])
lib = pickle.load((work / 'library.pkl').open('rb'))
lens = pickle.load((work / 'lens.pkl').open('rb'))
initial = list(dict.fromkeys(idpath.read_text().split()))
wanted = list(initial)
for p in sorted(work.glob('new-j*.txt')):
    wanted.extend(p.read_text().split())
order = {q: i for i, q in enumerate(dict.fromkeys(wanted))}
todo = [q for q in lib['mods'] if q['id'] in order and q['id'] not in lens]
todo.sort(key=lambda q: order[q['id']])
result = []
last_collect = time.monotonic()
for q in todo:
    table = M.tabulate(q)
    result.append((q, table))
    with out.with_suffix(out.suffix + '.tmp').open('wb') as h:
        pickle.dump(result, h)
    os.replace(str(out) + '.tmp', out)
    if q['id'] not in initial:
        with idpath.open('a') as h:
            h.write(q['id'] + '\n')
    print(q['id'], 'done', 'recovered' if q['id'] not in initial else '', flush=True)
    if (time.monotonic() - last_collect > 60 and
            work.resolve() == Path('$SCRATCH/bounties-squares/take-modules-r22/work/lib22')):
        # The helper waits here, so certification uses the same local CPU slot.
        collector = Path(os.environ.get('LANE', str(Path(__file__).resolve().parent))) / 'modules_round22.py'
        try:
            with (work.parent / 'logs/fast-collect.out').open('a') as h:
                p = subprocess.Popen([sys.executable, '-I', str(collector), 'collect'], stdout=h,
                                     stderr=subprocess.STDOUT, start_new_session=True)
                try:
                    p.wait(timeout=55)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGTERM)
                    p.wait()
        except subprocess.TimeoutExpired:
            print('fast collector timeout; next table checkpoint will retry', flush=True)
        last_collect = time.monotonic()
print('tables', len(result), 'recovered', sum(q['id'] not in initial for q, t in result))
