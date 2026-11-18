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
from pins import verify,job_matches
from walk import validate_job,public_job
C=collector()
results={}
results_path=W/'results.json'
if results_path.exists(): results={int(k):v for k,v in json.loads(results_path.read_text()).items()}


def publish():
    best={n:(Path(v['path']),v['row']) for n,v in results.items()}
    for n, (_,r) in list(best.items()):
        candidates=sorted((W/'jobs').glob('*-'+r['_candidate_hash']+'.json'))
        matches=[path for path in candidates if job_matches(r,json.loads(path.read_text()))]
        if matches:
            try:validate_job(json.loads(matches[0].read_text()))
            except Exception as e:
                state(f'WITHDRAW n={n} source failed current audit {e}')
                best.pop(n);results.pop(n,None)
    C.publish(best,set())
    write_json(results_path,results)


def choose_fresh(items,bars,prior,cache):
    import re,math
    grouped={}
    for path,item in items:
        m=re.search(r'/take-([a-z0-9-]+)-r30/',item.get('original',''))
        lane=m[1] if m else 'saved'
        n=int(item['n']);score=item.get('score_estimate',cache.get(item['sha256']))
        if score is None or not math.isfinite(float(score)):score=bars[n]
        rank=(float(score)-bars[n],-item['queued'])
        if lane not in grouped or rank<grouped[lane][2]:grouped[lane]=(path,item,rank)
    order=sorted(grouped)
    lane=next((name for name in order if name>prior),order[0])
    path,item,_=grouped[lane]
    return path,item,lane


def choose_urgent(items,bars,cache):
    from follow import geometry_score
    def rank(pair):
        path,item=pair;n=int(item['n']);score=item.get('score_estimate')
        if score is None:_,score=geometry_score(Path(item['path']),cache)
        return (int(path.name.split('-',1)[0]),float(score)-bars[n],-item['queued'])
    return min(items,key=rank)

def main():
    while time.time()<END-150:
        jobs=[]
        for job in sorted((W/'jobs').glob('*.json')):
            if not (W/'outcomes'/job.name).exists():
                jobs.append(job)
        if not jobs:
            publish()
            time.sleep(10)
            continue
        valid=[]
        for queued_path in jobs:
            try:
                queued_job=json.loads(queued_path.read_text())
                if not isinstance(queued_job,dict) or not {'n','path','sha256','kind','source','licence','queued'}.issubset(queued_job):
                    raise ValueError('invalid immutable queue schema')
                valid.append(queued_path)
            except Exception as e:
                dest=W/'bad-jobs';dest.mkdir(exist_ok=True)
                (dest/queued_path.name).write_bytes(queued_path.read_bytes())
                write_json(W/'outcomes'/queued_path.name,dict(job=str(queued_path),n=0,error=repr(e),outcome='invalid queue metadata'))
                state(f'REFUSE invalid queue record {queued_path}: {e}')
        jobs=valid
        if not jobs:continue
        urgent=[p for p in jobs if int(p.name.split('-',1)[0])<=1]
        if urgent:
            items=[(path,json.loads(path.read_text())) for path in urgent]
            bars=C.bars({int(item['n']) for _,item in items})
            job,j=choose_urgent(items,bars,{})
        else:
            items=[(path,json.loads(path.read_text())) for path in jobs]
            bars=C.bars({int(item['n']) for _,item in items})
            turn_path=W/'worker-lane-turn.json'
            prior=json.loads(turn_path.read_text()) if turn_path.exists() else ''
            job,j,next_lane=choose_fresh(items,bars,prior,C.cache)
            write_json(turn_path,next_lane)
        n=int(j['n']);t0=time.time()
        outcome=dict(job=str(job),n=n)
        try:
            from claims import claimed
            if claimed(j.get('original',j['path']),j['sha256'],(S/'handoff-r30.log').read_text().splitlines()):
                outcome['outcome']='backlog claimed exact input';write_json(W/'outcomes'/job.name,outcome)
                state(f'SKIP pending backlog claim n={n} sha256={j["sha256"]}')
                continue
            if j['kind']=='fresh-public' and n==916:
                raise ValueError('inherited public source chain lacks per-n clearance')
            if j['kind']=='fresh-public' and n in (639,691,745,858,918):
                raise ValueError('public union-sensitive count lacks a complete independent source trace')
            if j['kind']=='fresh-follow':
                import walk as Q
                Q.load_withdrawn()
                verify(j,Q.WITHDRAWN_LINES,Q.samanyu_only)
            validate_job(j)
            assert hashlib.sha256(Path(j['path']).read_bytes()).hexdigest()==j['sha256']
            cert=C.cert(j['path'],n)
            if cert is None: raise ValueError('not certifiable')
            ok,ev=audit(list(csv.DictReader(cert[1].open()))) if public_job(j) else (True,[])
            outcome.update(input_score=cert[0],input_audit=ev)
            if not ok: raise ValueError('remaining share exclusion')
            state(f'START remote fq n={n} kind={j["kind"]} input={cert[1]} log={W}/collector/remote-{cert[2]}.log deadline 17:45Z')
            res,proof=C.remote(cert,n)
            ok,ev2=audit(list(csv.DictReader(res[1].open()))) if public_job(j) else (True,[])
            outcome.update(score=res[0],proof=proof,output_audit=ev2,polish_gain=cert[0]-res[0],path=str(res[1]))
            if not ok: raise ValueError('quenched share exclusion')
            validate_job(j)
            bars=C.bars({n})
            if res[0]<bars[n]-1e-10:
                row=dict(n=n,held=repr(C.held[n]),new=repr(res[0]),gain=repr(C.held[n]-res[0]),
                    source=f'{j["source"]}; input {j["path"]} (sha256 {j["sha256"]}); audit {W}/outcomes/{job.name}',
                    licence=j['licence'],start=repr(cert[0]),polish_gain=repr(cert[0]-res[0]),remote_quench=proof,
                    _candidate_hash=j['sha256'])
                if n not in results or res[0]<float(results[n]['row']['new']):
                    results[n]=dict(path=str(res[1]),row=row)
                outcome['outcome']='certified take';publish()
            else:
                outcome['outcome']='no live crossing'
            if (cert[0]-res[0])*math.sqrt(n)>1e-9:
                near=T/'near'/f'{n}-fq30-{res[2][:12]}.csv'
                rows_write(near,list(csv.DictReader(res[1].open())))
                write_json(Path(str(near)+'.json'),dict(j,score=res[0],start_score=cert[0],proof=proof,source=j['source'],source_file=j['path'],evidence=ev2))
                hand(f'certified continuation n={n}, score={res[0]}, over bar={res[0]-bars[n]:.3e}; source and proof in sidecar {near}')
            state(f'FINISH fq n={n} start={cert[0]} score={res[0]} gain={cert[0]-res[0]:.3e} outcome={outcome["outcome"]} seconds={time.time()-t0:.1f}')
        except Exception as e:
            outcome['error']=repr(e)
            state(f'FINISH n={n} error={repr(e)}')
        outcome['seconds']=time.time()-t0
        write_json(W/'outcomes'/job.name,outcome)
        write_json(C.cache_path,C.cache)
    publish();state('STOP proof worker at common deadline; no remote launches remain')


if __name__=='__main__':main()
