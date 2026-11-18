"""Shared immutable queue, certification and take publication for harvest round 34."""
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
from harvest_collect import Collector as BaseCollector, rows_write, table
import glob
import math
import importlib.util
_spec=importlib.util.spec_from_file_location('border_finesafe',L/'tools/border/r28/finesafe.py')
finesafe=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(finesafe)
S = Path('$SCRATCH/bounties-squares')
T = S/'take-harvest-r34'
W = T/'work'
END = dt.datetime(2026, 11, 17, 7, 25, tzinfo=dt.timezone.utc).timestamp()


def state(msg):
    line = dt.datetime.now(dt.timezone.utc).isoformat()+' boxA '+msg
    with (T/'STATE.txt').open('a') as f:
        f.write(line+'\n')
    print(line, flush=True)


def hand(msg):
    with (S/'handoff-r34.log').open('a') as f:
        f.write(dt.datetime.now(dt.timezone.utc).isoformat()+' harvest -> all: '+msg+'\n')


def write_json(path, data):
    tmp = Path(str(path)+'.tmp')
    tmp.write_text(json.dumps(data, indent=2)+'\n')
    tmp.replace(path)


class Collector(BaseCollector):
    """Published peers already carry certificates; compare their current ledgers."""
    def cert(self, path, n):
        raw=Path(path).read_bytes();key=hashlib.sha256(raw).hexdigest()
        if key not in self.cache:
            with Path(path).open() as f:
                rows=[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(f)]
            if len(rows)!=n or any(int(r['n'])!=n for r in rows):self.cache[key]=None
            else:
                _,fr,score,error=finesafe.work((n,rows))
                if fr is None:self.cache[key]=None
                else:
                    rows_write(self.cache_dir/(key+'.csv'),fr);self.cache[key]=score
        score=self.cache[key]
        return None if score is None else (score,self.cache_dir/(key+'.csv'),key)

    def remote(self,*args,**kwargs):
        raise RuntimeError('round34 harvest has no assigned offbox solver seat; use certified handoffs')

    def bars(self, ns, limits=None, force=()):
        bars={n:self.held[n] for n in ns}
        for pattern in self.args.live:
            for directory in glob.glob(pattern):
                if str(Path(directory).resolve()) in self.args.out+self.args.exclude:continue
                for r in table(Path(directory)/'take.tsv'):
                    n=int(r['n'])
                    if n not in ns or not (Path(directory)/(str(n)+'.csv')).is_file():continue
                    value=float(r['new'])
                    if math.isfinite(value):bars[n]=min(bars[n],value)
        return bars


def collector():
    return Collector(argparse.Namespace(details=str(W/'bar.csv'), work=str(W/'collector'), own=[],
        live=[str(S/'take-*-r34')], out=[str(T)], exclude=[], host='unassigned',
        remote_dir='scratch/squares-harvest/r34', handoff=str(S/'handoff-r34.log'), control=False))


def enqueue(path, meta, priority, pinned=None):
    from policy import snapshot
    dst, key = pinned if pinned is not None else snapshot(path, W/'inputs')
    target = W/'jobs'/f'{priority:02d}-{key}.json'
    target.parent.mkdir(exist_ok=True)
    if not target.exists():
        sidecar=Path(str(dst)+'.json')
        if not sidecar.exists():write_json(sidecar, dict(meta, queued_sha256=key, original=str(path)))
        write_json(target, dict(meta, path=str(dst), sha256=key, queued=meta.get("queue_started",time.time()), priority=priority))
    return target


def setup():
    for name in ['jobs','inputs','outcomes','collector','public-results']:
        (W/name).mkdir(exist_ok=True)
    bar = list(csv.DictReader((S/'round34-briefs/bar34.tsv').open(), delimiter='\t'))
    with (W/'bar.csv.tmp').open('w') as f:
        w = csv.DictWriter(f, fieldnames=['n','score']);w.writeheader()
        w.writerows({'n':r['n'], 'score':r['bar']} for r in bar)
    (W/'bar.csv.tmp').replace(W/'bar.csv')
    with (W/'base.tsv.tmp').open('w') as f:
        import math
        w = csv.DictWriter(f, fieldnames=['n','score','L','reason'], delimiter='\t');w.writeheader()
        w.writerows(dict(n=r['n'],score=r['bar'],L=(float(r['bar'])+1)*math.sqrt(int(r['n'])),reason='ok') for r in bar)

    (W/'base.tsv.tmp').replace(W/'base.tsv')
