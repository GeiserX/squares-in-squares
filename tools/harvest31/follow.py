"""Bounded admission of fresh round 31 layouts with complete source snapshots."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import sys
import signal
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sys.path.insert(0,str(L))
from harvest_merge import side_est
from policy import audit,snapshot


def source_timeout(signum,frame):
    raise TimeoutError('source admission exceeded60s; unchanged input deferred')


def file_stamp(path):
    try:
        st=path.stat();return (st.st_mtime_ns,st.st_size)
    except FileNotFoundError:return None


def geometry_score(path,cache):
    try:
        raw=path.read_bytes();key=hashlib.sha256(raw).hexdigest()
        if key not in cache:
            rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
            n=int(rows[0]['n'])
            if len(rows)!=n:return None,math.inf
            value=side_est(rows)/math.sqrt(n)-1
            if not math.isfinite(value):return None,math.inf
            cache[key]=[n,value]
        return tuple(cache[key])
    except (OSError,ValueError,KeyError,IndexError):return None,math.inf


def gap_rank(item,bars,cache):
    n,score=geometry_score(item[0],cache)
    return (score-bars[n] if n in bars else math.inf,-(file_stamp(item[0]) or (0,0))[0])


def queued_follow(key,priority):
    for value in dict.fromkeys([priority,1]):
        path=W/'jobs'/f'{value:02d}-{key}.json'
        try:job=json.loads(path.read_text())
        except (OSError,ValueError):continue
        if (job.get('sha256')==key and job.get('kind')=='fresh-follow'
                and job.get('walk',{}).get('clean') is True):return True
        if job.get('sha256')==key and job.get('kind')=='self-certified' and job.get('continuation_pin',{}).get('sha256')==key:return True
    return False


def scan(max_items=8):
    import walk as Q
    sp=W/'follow-seen.json'
    seen=json.loads(sp.read_text()) if sp.exists() else {}
    revision=hashlib.sha256(b''.join(path.read_bytes() for path in [Path(Q.__file__),Path(__file__)]+[Path(__file__).parent/name for name in ['common.py','reader_records.py','versions.py','claims.py','public_sources.py','policy.py','continuations.py','archived_sources.py','held_policy.py','held_paths.py']])).hexdigest()
    if seen.get('_policy_revision')!=revision:
        import importlib
        importlib.reload(Q)
        import continuations
        importlib.reload(continuations)
        seen={'_policy_revision':revision}
    claim_log=S/'handoff-r31.log'
    claims=[line for line in claim_log.read_text().splitlines() if 'backlog ->' in line and 'claim' in line.lower()] if claim_log.exists() else []
    pending=[]
    bars={int(r['n']):float(r['bar']) for r in table(S/'round31-briefs/bar31.tsv')}
    for ledger in S.glob('take-*-r31/take.tsv'):
        for r in table(ledger):
            n=int(r['n']);bars[n]=min(bars[n],float(r['new']))
    for lane in ['forensics','k123','twoshort','modules','invent','soft','classfill','border','rebuild','midm','backlog','stair-c','quench','self']:
        t=T if lane=='self' else S/f'take-{lane}-r31'
        entries=list(t.glob('near/*.csv'))+(list(t.glob('[0-9]*.csv')) if lane!='self' else [])
        for p in sorted(entries,key=lambda p:(file_stamp(p) or (0,0))[0],reverse=True):
            if lane=='self' and any(tag in p.name for tag in ('-cert31-','-public31-')):continue
            stamp=file_stamp(p)
            if stamp is None:continue
            stamp=str(stamp)
            if seen.get(str(p))==stamp:continue
            pending.append((p,stamp,lane))
    # Frozen harvest takes contain certified results dropped only by the old seed rule.
    for old in [S/f'take-harvest-r{r}' for r in range(30,29,-1)]:
        historical=[]
        for pattern in ['[0-9]*.csv','near/*.csv','work/candidates/*.csv','work/clean-candidates/*.csv','work/policy-candidates/*.csv','work/excluded-near/*.csv']:
            historical.extend(old.glob(pattern))
        for p in sorted(set(historical)):
            if lane=='self' and any(tag in p.name for tag in ('-cert31-','-public31-')):continue
            stamp=file_stamp(p)
            if stamp is None:continue
            stamp=str(stamp)
            if seen.get(str(p))!=stamp:pending.append((p,stamp,'reopened-harvest-take'))
    # A prolific rectangle lane must not starve a fresh join or certified end.
    from collections import defaultdict,deque
    groups=defaultdict(deque)
    historical=[]
    for item in pending:
        if item[2]=='reopened-harvest-take':historical.append(item)
        else:groups[item[2]].append(item)
    geometry_cache=seen.setdefault('_geometry_scores',{})
    for lane in groups:
        groups[lane]=deque(sorted(groups[lane],key=lambda item:gap_rank(item,bars,geometry_cache)))
    order=list(groups)
    if order:
        turn=seen.get('_lane_turn',0)%len(order)
        order=order[turn:]+order[:turn]
        seen['_lane_turn']=turn+8
    pending=[]
    # Certified continuations need no new live-path walk. Feed a small batch
    # before the slower external source checks, then keep lane rotation.
    for _ in range(min(3,len(groups.get('self',[])))):
        pending.append(groups['self'].popleft())
    while any(groups.values()):
        for lane in order:
            if groups[lane]:pending.append(groups[lane].popleft())
    pending+=historical
    used=0
    scan_started=time.time()
    for p,stamp,lane in pending:
        if used>=max_items or time.time()-scan_started>90:break
        seen[str(p)]=stamp
        previous_handler=signal.signal(signal.SIGALRM,source_timeout)
        signal.setitimer(signal.ITIMER_REAL,60)
        try:
            queue_started=time.time()
            pinned=snapshot(p,W/'inputs')
            rows=list(csv.DictReader(io.StringIO(pinned[0].read_text())));n=int(rows[0]['n'])
            priority=2 if lane in ['forensics','k123'] else 3
            # enqueue() cannot replace this immutable job. Repeating its source
            # walk only delays new inputs when a producer rewrites equal bytes.
            if queued_follow(pinned[1],priority):continue
            record_stamp=Q.source_stamp(p,n)
            producer=Q.producer_record(p,n)
            score=side_est(rows)/math.sqrt(n)-1
            if lane=='reopened-harvest-take' and score>=bars[n]-1e-10:continue
            from claims import claimed
            if claimed(p,pinned[1],claims):
                state(f'SKIP backlog claimed exact input {p} sha256={pinned[1]}')
                continue
            window=(.015/math.sqrt(n) if lane in ['forensics','k123'] else 2e-5)
            if lane!='self' and score>bars[n]+window:continue
            if score<bars[n]-1e-10:priority=1
            used+=1
            if lane=='self':
                import continuations
                job=continuations.queue(p,pinned,score,priority)
                state(f'QUEUE pinned own continuation n={n} job={job} deadline00:15Z')
                continue
            proof=Q.check(str(p))
            if not proof['clean']:
                state(f'SKIP follow n={n} source walk {proof["hits"][:2]} file={p}')
                continue
            public_first=bool(proof.get('public_first_root'))
            if lane=='reopened-harvest-take' and not proof.get('helds'):
                import re
                public_first=bool(re.match(r'^(?:public )?[\w.-]+/[\w.-]+\s*::',producer.get('source','')))
            if lane=='self':
                for sidecar in Q.Q.sidecars(str(p)):
                    record=json.loads(Path(sidecar).read_text())
                    if isinstance(record,dict) and Q.public_job(record):public_first=True
            ok,ev=audit(rows) if public_first else (True,[])
            if not ok:
                state(f'SKIP historical public n={n} remaining public share exclusion; file={p}')
                continue
            texts,missing,files,helds,refused=Q.last_walk()
            pinned_parents=[]
            for f in files:
                if not isinstance(f,str) or not Path(f).is_file():continue
                if Path(f).stat().st_size>20_000_000:continue
                dst,key=snapshot(f,W/'ancestry-inputs')
                pinned_parents.append(dict(original=f,snapshot=str(dst),sha256=key))
            from reader_records import EXTRA_PINS
            pinned_parents.extend(EXTRA_PINS.values())
            from versions import EXTRA_PINS as VERSION_PINS
            pinned_parents.extend(VERSION_PINS.values())
            from archived_sources import EXTRA_PINS as ARCHIVED_PINS
            pinned_parents.extend(ARCHIVED_PINS.values())
            by_original={pin['original']:pin['sha256'] for pin in pinned_parents}
            for label,text in texts:
                if str(label).startswith('held '):continue
                for match in Q.Q.PIN.finditer(text):
                    original=Q.Q.norm(match[1]);want=match[2].lower()
                    if original in by_original and not by_original[original].startswith(want):
                        raise ValueError('pinned ancestor changed during queueing: '+original)
            if hashlib.sha256(p.read_bytes()).hexdigest()!=pinned[1] or Q.source_stamp(p,n)!=record_stamp:
                raise ValueError('producer input or source record changed during queueing')
            if any(pin['original']==str(p) and pin['sha256']!=pinned[1] for pin in pinned_parents):
                raise ValueError('walked input version differs from queued snapshot')
            parent_source=('; producer source '+producer['source']) if producer.get('source') else ''
            meta=dict(n=n,kind='fresh-follow',public_first=public_first,source=f'fq follow of {p}{parent_source}; walked source snapshot ',
                licence=producer.get('licence') or 'own construction; upstream sources in pinned source proof',original=str(p),evidence=ev,
                walk=proof,parents=pinned_parents,queue_started=queue_started,root_record_sha256=record_stamp,producer_record=producer,score_estimate=score)
            key=pinned[1]
            proof_data=dict(meta,walked_texts=texts)
            proof_hash=hashlib.sha256(json.dumps(proof_data,sort_keys=True).encode()).hexdigest()
            pp=W/'source-proofs'/f'{key}-{proof_hash[:16]}.json';pp.parent.mkdir(exist_ok=True)
            if not pp.exists():write_json(pp,proof_data)
            meta['source']+=str(pp)
            job=enqueue(p,meta,priority,pinned=pinned)
            state(f'QUEUE follow n={n} lane={lane} gap={score-bars[n]:.3e} proof={pp} job={job} deadline 00:15Z')
        except Exception as e:
            if isinstance(e,FileNotFoundError) or 'changed during queueing' in str(e) or 'version differs' in str(e):seen.pop(str(p),None)
            state(f'SKIP follow file={p} error={repr(e)}')
        finally:
            signal.setitimer(signal.ITIMER_REAL,0)
            signal.signal(signal.SIGALRM,previous_handler)
    write_json(sp,seen)
    return used
