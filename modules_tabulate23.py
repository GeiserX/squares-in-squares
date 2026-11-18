#!/usr/bin/env python3
"""Tabulate new modules, then resume unfinished modules from earlier growth steps.

Usage: modules_tabulate23.py LIBDIR IDS.txt OUT.pkl
Each saved checkpoint contains complete tables. Recovered ids are appended to
IDS.txt so the next generator treats their first available tables as new.
"""
import os
import hashlib
import json
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
failed_path = work / 'failed-tables.json'
failed = json.loads(failed_path.read_text()) if failed_path.exists() else {}
code = Path(M.__file__).read_bytes()
def fingerprint(q):
    return hashlib.sha256(code + pickle.dumps(q)).hexdigest()
todo = [q for q in lib['mods'] if q['id'] in order and q['id'] not in lens
        and failed.get(q['id']) != fingerprint(q)]
todo.sort(key=lambda q: order[q['id']])
result = []
last_collect = time.monotonic()
for q in todo:
    table = M.tabulate(q)
    valid = table.get('tab') is not None if q['kind'] == 'corner' else table.get('knots') is not None
    if not valid:
        failed[q['id']] = fingerprint(q)
        failed_path.with_suffix('.tmp').write_text(json.dumps(failed))
        os.replace(failed_path.with_suffix('.tmp'), failed_path)
        print(q['id'], 'no table, cached until geometry or solver changes', flush=True)
    result.append((q, table))
    with out.with_suffix(out.suffix + '.tmp').open('wb') as h:
        pickle.dump(result, h)
    os.replace(str(out) + '.tmp', out)
    if valid and q['id'] not in initial:
        with idpath.open('a') as h:
            h.write(q['id'] + '\n')
    print(q['id'], 'done', 'recovered' if q['id'] not in initial else '', flush=True)
    if (time.monotonic() - last_collect > 60 and
            work.resolve() == Path('$SCRATCH/bounties-squares/take-modules-r23/work/lib23')):
        # The helper waits here, so certification uses the same local CPU slot.
        collector = Path(os.environ.get('LANE', str(Path(__file__).resolve().parent))) / 'modules_round23.py'
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
