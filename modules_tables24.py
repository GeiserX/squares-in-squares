"""Send missing tables to the idle remote slot and collect completed solves."""
import hashlib
import json
import pickle
import os
import time
from pathlib import Path


def enqueue(libdir, out):
    lib = pickle.load((libdir / 'library.pkl').open('rb'))
    lens = pickle.load((libdir / 'lens.pkl').open('rb'))
    out.mkdir(exist_ok=True)
    fresh = []
    for p in sorted(libdir.glob('new-j*.txt'), reverse=True):
        fresh.extend(p.read_text().split())
    order = {v: i for i, v in reversed(list(enumerate(fresh)))}
    from modules_policy24 import piece
    byid = {q['id']: q for q in lib['mods']}
    todo = [q for q in lib['mods'] if q['id'] in order and q['id'] not in lens and piece(q)['status']=='none']
    todo.sort(key=lambda q: (q['kind'] != 'corner', order[q['id']]))
    pending_path = libdir.parent / 'turn-pending.txt'
    pending = pending_path.read_text().split() if pending_path.exists() else []
    turns = [dict(byid[i], id=i+'t', turn=True) for i in pending
             if i in byid and i+'t' not in byid and not byid[i].get('turn') and piece(byid[i])['status']=='none']
    # First try fresh turned corners. The pending list already ranks their fit.
    todo = turns[:20] + todo[:40]
    # A newer fresh batch outranks older pending tables on the remote slot.
    now = time.time()
    for i, q in enumerate(todo[:60]):
        name = hashlib.sha1(q['id'].encode()).hexdigest()
        p = out / f'{name}.ready'
        if not p.exists():
            with p.open('wb') as h:
                pickle.dump(q, h)
            os.utime(p, (now-i, now-i))
    return len(todo)


def collect(libdir, directory, seenpath):
    seen = set(json.loads(seenpath.read_text())) if seenpath.exists() else set()
    pairs = []
    for p in directory.glob('*.pkl'):
        if p.name in seen:
            continue
        pairs.extend(pickle.load(p.open('rb')))
        seen.add(p.name)
    seenpath.write_text(json.dumps(sorted(seen)))
    if not pairs:
        return []
    import os
    lib = pickle.load((libdir / 'library.pkl').open('rb'))
    lens = pickle.load((libdir / 'lens.pkl').open('rb'))
    byid = {q['id']: q for q in lib['mods']}
    for q, t in pairs:
        if q['id'] not in byid:
            lib['mods'].append(q)
        lens[q['id']] = t
    for name, value in [('library', lib), ('lens', lens)]:
        p = libdir / (name + '.pkl')
        with p.with_suffix('.tmp').open('wb') as h:
            pickle.dump(value, h)
        os.replace(p.with_suffix('.tmp'), p)
    return pairs
