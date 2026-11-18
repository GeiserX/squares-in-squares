"""One remote proof worker with a shared search deadline and atomic takes."""
import csv
import hashlib
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from policy import audit
from pins import verify
C=collector()
results={}
p=W/'results.json'
if p.exists(): results={int(k):v for k,v in json.loads(p.read_text()).items()}


def publish():
    best={n:(Path(v['path']),v['row']) for n,v in results.items()}
    C.publish(best,set())
    write_json(p,results)


while time.time()<END-150:
    jobs=[]
    for job in sorted((W/'jobs').glob('*.json')):
        if not (W/'outcomes'/job.name).exists():
            jobs.append(job)
    if not jobs:
        publish()
        time.sleep(10)
        continue
    job=jobs[0];j=json.loads(job.read_text());n=int(j['n']);t0=time.time()
    outcome=dict(job=str(job),n=n)
    try:
        if j['kind']=='fresh-public' and n==916:
            raise ValueError('inherited public source chain lacks per-n clearance')
        if j['kind']=='fresh-public' and n in (639,691,745,858,918):
            raise ValueError('public union-sensitive count lacks a complete independent source trace')
        if j['kind']=='fresh-follow':
            import quench_walk as Q
            Q.load_withdrawn()
            verify(j,Q.WITHDRAWN_LINES,Q.samanyu_only)
        assert hashlib.sha256(Path(j['path']).read_bytes()).hexdigest()==j['sha256']
        cert=C.cert(j['path'],n)
        if cert is None: raise ValueError('not certifiable')
        ok,ev=audit(list(csv.DictReader(cert[1].open())))
        outcome.update(input_score=cert[0],input_audit=ev)
        if not ok: raise ValueError('remaining share exclusion')
        state(f'START remote fq n={n} kind={j["kind"]} input={cert[1]} log={W}/collector/remote-{cert[2]}.log deadline 23:45Z')
        res,proof=C.remote(cert,n)
        ok,ev2=audit(list(csv.DictReader(res[1].open())))
        outcome.update(score=res[0],proof=proof,output_audit=ev2,polish_gain=cert[0]-res[0],path=str(res[1]))
        if not ok: raise ValueError('quenched share exclusion')
        if j['kind']=='fresh-follow':
            Q.load_withdrawn()
            verify(j,Q.WITHDRAWN_LINES,Q.samanyu_only)
        bars=C.bars({n})
        if res[0]<bars[n]-1e-10:
            row=dict(n=n,held=repr(C.held[n]),new=repr(res[0]),gain=repr(C.held[n]-res[0]),
                source=f'{j["source"]}; input {j["path"]} (sha256 {j["sha256"]}); audit {W}/outcomes/{job.name}',
                licence=j['licence'],start=repr(cert[0]),polish_gain=repr(cert[0]-res[0]),remote_quench=proof,
                _candidate_hash=cert[2])
            if n not in results or res[0]<float(results[n]['row']['new']):
                results[n]=dict(path=str(res[1]),row=row)
            outcome['outcome']='certified take';publish()
        else:
            outcome['outcome']='no live crossing'
            if cert[0]-res[0]>1e-8:
                near=T/'near'/f'{n}-fq27-{res[2][:12]}.csv'
                rows_write(near,list(csv.DictReader(res[1].open())))
                write_json(Path(str(near)+'.json'),dict(j,score=res[0],start_score=cert[0],proof=proof,source=j['source'],source_file=j['path'],evidence=ev2))
                hand(f'certified near n={n}, score={res[0]}, over bar={res[0]-bars[n]:.3e}; source and proof in sidecar {near}')
        state(f'FINISH fq n={n} start={cert[0]} score={res[0]} gain={cert[0]-res[0]:.3e} outcome={outcome["outcome"]} seconds={time.time()-t0:.1f}')
    except Exception as e:
        outcome['error']=repr(e)
        state(f'FINISH n={n} error={repr(e)}')
    outcome['seconds']=time.time()-t0
    write_json(W/'outcomes'/job.name,outcome)
publish();state('STOP proof worker at common deadline; no remote launches remain')
