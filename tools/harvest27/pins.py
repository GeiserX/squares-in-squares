"""Validate a walked byte snapshot without depending on a producer's live path."""
import hashlib
from pathlib import Path
import re


def verify(job, withdrawals=(), samanyu_only=lambda line: False):
    if not job.get('walk',{}).get('clean'):
        raise ValueError('input did not pass its recorded full source walk')
    if hashlib.sha256(Path(job['path']).read_bytes()).hexdigest()!=job['sha256']:
        raise ValueError('queued input bytes changed')
    pins={p['original']:p for p in job.get('parents',[])}
    pins.setdefault(job['original'],dict(original=job['original'],snapshot=job['path'],sha256=job['sha256']))
    for pin in pins.values():
        if hashlib.sha256(Path(pin['snapshot']).read_bytes()).hexdigest()!=pin['sha256']:
            raise ValueError('pinned source bytes changed: '+pin['snapshot'])
    for name,line in withdrawals:
        if samanyu_only(line) or re.search(r':\s*REINSTATE\b',line,re.I):continue
        absolute=name if name.startswith('/') else '$SCRATCH/bounties-squares/'+name
        if absolute not in pins:continue
        # The complete queue-time walk already assessed earlier withdrawals
        # against the exact version then present at each producer path.
        import datetime as dt
        m=re.match(r'(\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d)?)',line)
        if m:
            stamp=dt.datetime.fromisoformat(m[1]).replace(tzinfo=dt.timezone.utc).timestamp()
            if stamp<=job['queued']:continue
        hashes=re.findall(r'sha256[ =:]+([0-9a-f]{12,64})',line,re.I)
        if hashes and not any(pins[absolute]['sha256'].startswith(h) for h in hashes):continue
        raise ValueError('source withdrawn after queue: '+line[:200])
    return True


def control():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'pin.csv';p.write_bytes(b'packing snapshot')
        key=hashlib.sha256(p.read_bytes()).hexdigest()
        j=dict(path=str(p),sha256=key,original='/gone/producer.csv',walk=dict(clean=True),parents=[],queued=0)
        assert verify(j)
        try:verify(j,[('/gone/producer.csv','2026-11-14T21:00:00Z lane -> all: WITHDRAW source CC BY-SA')])
        except ValueError:pass
        else:raise AssertionError('withdrawal passed')
        assert verify(j,[('/gone/producer.csv','2026-11-14T21:00:00Z lane -> all: REINSTATE; earlier WITHDRAW lifted')])
        p.write_bytes(b'changed')
        try:verify(j)
        except ValueError:pass
        else:raise AssertionError('changed snapshot passed')
    print('CONTROL pinned walk survives missing producer; hard withdrawal and changed snapshot rejected; REINSTATE accepted',flush=True)


if __name__=='__main__':control()
