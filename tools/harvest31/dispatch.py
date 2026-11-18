"""Certify pinned candidates and hand off off-box solver work within the budget."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from policy import audit
from walk import validate_job,public_job


def drain(limit=8):
    C=collector();count=0
    jobs=sorted((W/'jobs').glob('*.json'))
    for job in jobs:
        if count>=limit or time.time()>END-120:break
        target=W/'outcomes'/job.name
        if target.exists():continue
        count+=1;started=time.time();j=json.loads(job.read_text());n=int(j['n'])
        outcome=dict(n=n,job=str(job))
        try:
            validate_job(j)
            if hashlib.sha256(Path(j['path']).read_bytes()).hexdigest()!=j['sha256']:raise ValueError('changed candidate bytes')
            cert=C.cert(j['path'],n)
            if cert is None:raise ValueError('not certifiable')
            is_public=public_job(j)
            ok,evidence=audit(list(csv.DictReader(cert[1].open()))) if is_public else (True,[])
            if not ok:raise ValueError('public geometry share at1e3 or1e2')
            bar=C.bars({n})[n]
            outcome.update(input_score=cert[0],bar=bar,input_audit=evidence)
            # Pure fq followers have measured no crossing from public files far
            # above bar. Do not spend another lane's slots on unchanged misses.
            if cert[0]>bar+1e-10:
                outcome['outcome']='certified above live bar; no solver requested'
            else:
                near=T/'near'/f'{n}-cert31-{cert[2][:16]}.csv'
                raw=cert[1].read_bytes();near.write_bytes(raw)
                meta=dict(j,path=str(near),sha256=hashlib.sha256(raw).hexdigest(),
                          source_file=j['path'],source_job=str(job),certified_from=j['path'],
                          certified_input_sha256=cert[2],score=cert[0],public_first=is_public,
                          required_offbox_fq=True)
                # Bind the original unmodified queue in a source receipt. Its
                # data path remains the raw input, so no producer metadata moves.
                meta['source']=j['source']+'; certified from '+j['path']+'; pinned source job '+str(job)
                if j['kind']!='fresh-public':
                    meta=dict(n=n,kind='certified-unquenched',path=str(near),sha256=hashlib.sha256(raw).hexdigest(),
                              source=meta['source'],licence=j['licence'],inherited_job=j,source_job=str(job),
                              source_file=j['path'],score=cert[0],public_first=is_public,required_offbox_fq=True)
                write_json(Path(str(near)+'.json'),meta)
                if j['kind']=='fresh-public':
                    from transports import package
                    near,meta=package(j,cert[1],cert[0])
                hand(f'quench-ready certified n={n} score={cert[0]:.17g} live_gain={bar-cert[0]:.9g} sha256={meta["sha256"]}; required certified-input fq on an assigned off-box slot, source/pins in sidecar {near}')
                state(f'HANDOFF certified n={n} score={cert[0]:.17g} live_gain={bar-cert[0]:.9g} file={near}; no unquenched row counted')
                outcome.update(outcome='certified handoff; offbox fq required',path=str(near))
        except Exception as exc:
            outcome.update(error=repr(exc),outcome='source or certification refused')
            state(f'REFUSE dispatch n={n}: {exc}')
        outcome['seconds']=time.time()-started;write_json(target,outcome)
    write_json(C.cache_path,C.cache)
    return count
