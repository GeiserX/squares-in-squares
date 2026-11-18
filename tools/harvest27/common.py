"""Shared immutable queue, certification and take publication for harvest 27."""
import argparse
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import time
L = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(L)); sys.path.insert(0, str(L/'tools'))
from harvest_collect import Collector, rows_write, table
S = Path('$SCRATCH/bounties-squares')
T = S/'take-harvest-r27'
W = T/'work'
END = dt.datetime(2026, 11, 14, 23, 45, tzinfo=dt.timezone.utc).timestamp()


def state(msg):
    line = dt.datetime.now(dt.timezone.utc).isoformat()+' boxA '+msg
    with (T/'STATE.txt').open('a') as f:
        f.write(line+'\n')
    print(line, flush=True)


def hand(msg):
    with (S/'handoff-r27.log').open('a') as f:
        f.write(dt.datetime.now(dt.timezone.utc).isoformat()+' harvest -> all: '+msg+'\n')


def write_json(path, data):
    tmp = Path(str(path)+'.tmp')
    tmp.write_text(json.dumps(data, indent=2)+'\n')
    tmp.replace(path)


def collector():
    return Collector(argparse.Namespace(details=str(W/'bar.csv'), work=str(W/'collector'), own=[],
        live=[str(S/'take-*-r27')], out=[str(T)], exclude=[], host='boxC',
        remote_dir='scratch/squares-harvest/r27', handoff=str(S/'handoff-r27.log'), control=False))


def enqueue(path, meta, priority):
    from policy import snapshot
    dst, key = snapshot(path, W/'inputs')
    target = W/'jobs'/f'{priority:02d}-{key}.json'
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        sidecar=Path(str(dst)+'.json')
        if not sidecar.exists():write_json(sidecar, dict(meta, queued_sha256=key, original=str(path)))
        write_json(target, dict(meta, path=str(dst), sha256=key, queued=time.time(), priority=priority))
    return target


def setup():
    for name in ['jobs','inputs','outcomes','collector','public-results']:
        (W/name).mkdir(exist_ok=True)
    bar = list(csv.DictReader((S/'round27-briefs/bar27.tsv').open(), delimiter='\t'))
    with (W/'bar.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=['n','score']);w.writeheader()
        w.writerows({'n':r['n'], 'score':r['bar']} for r in bar)
    with (W/'base.tsv').open('w') as f:
        import math
        w = csv.DictWriter(f, fieldnames=['n','score','L','reason'], delimiter='\t');w.writeheader()
        w.writerows(dict(n=r['n'],score=r['bar'],L=(float(r['bar'])+1)*math.sqrt(int(r['n'])),reason='ok') for r in bar)
