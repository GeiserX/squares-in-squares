"""Bounded admission of fresh round 27 layouts with complete source snapshots."""
import csv
import hashlib
import json
import math
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
sys.path.insert(0,str(L))
from harvest_merge import side_est
from policy import audit,snapshot


def scan(max_items=8):
    import quench_walk as Q
    sp=W/'follow-seen.json'
    seen=json.loads(sp.read_text()) if sp.exists() else {}
    revision=hashlib.sha256(Path(Q.__file__).read_bytes()).hexdigest()
    if seen.get('_policy_revision')!=revision:
        import importlib
        importlib.reload(Q)
        seen={'_policy_revision':revision}
    claim_log=S/'handoff-r27.log'
    claims=[line for line in claim_log.read_text().splitlines() if 'backlog ->' in line and 'claim' in line.lower()] if claim_log.exists() else []
    pending=[]
    bars={int(r['n']):float(r['bar']) for r in table(S/'round27-briefs/bar27.tsv')}
    for ledger in S.glob('take-*-r27/take.tsv'):
        for r in table(ledger):
            n=int(r['n']);bars[n]=min(bars[n],float(r['new']))
    for lane in ['forensics','k123','twoshort','modules','invent','soft','classfill','border','rebuild','midm']:
        t=S/f'take-{lane}-r27'
        entries=list(t.glob('near/*.csv'))+list(t.glob('[0-9]*.csv'))
        for p in sorted(entries,key=lambda p:p.stat().st_mtime,reverse=True):
            stamp=str((p.stat().st_mtime_ns,p.stat().st_size))
            if seen.get(str(p))==stamp:continue
            pending.append((p,stamp,lane))
    # Frozen harvest takes contain certified results dropped only by the old seed rule.
    for old in [S/f'take-harvest-r{r}' for r in range(26,21,-1)]:
        historical=[]
        for pattern in ['[0-9]*.csv','near/*.csv','work/candidates/*.csv','work/clean-candidates/*.csv','work/policy-candidates/*.csv','work/excluded-near/*.csv']:
            historical.extend(old.glob(pattern))
        for p in sorted(set(historical)):
            stamp=str((p.stat().st_mtime_ns,p.stat().st_size))
            if seen.get(str(p))!=stamp:pending.append((p,stamp,'reopened-harvest-take'))
    used=0
    scan_started=time.time()
    for p,stamp,lane in pending:
        if used>=max_items or time.time()-scan_started>90:break
        seen[str(p)]=stamp
        try:
            rows=list(csv.DictReader(p.open()));n=int(rows[0]['n'])
            score=side_est(rows)/math.sqrt(n)-1
            if lane=='reopened-harvest-take' and score>=bars[n]-1e-10:continue
            if lane=='reopened-harvest-take':
                raw_key=hashlib.sha256(p.read_bytes()).hexdigest()
                if any(str(p) in line or raw_key[:12] in line for line in claims):
                    state(f'SKIP backlog claimed saved input {p} sha256={raw_key}')
                    continue
            window=(.015/math.sqrt(n) if lane in ['forensics','k123'] else 2e-6)
            if score>bars[n]+window:continue
            used+=1
            proof=Q.check(str(p))
            if not proof['clean']:
                state(f'SKIP follow n={n} source walk {proof["hits"][:2]} file={p}')
                continue
            ok,ev=audit(rows)
            if not ok:continue
            texts,missing,files,helds,refused=Q.walk(str(p),n)
            pinned=[]
            for f in files:
                if not isinstance(f,str) or not Path(f).is_file():continue
                if Path(f).stat().st_size>20_000_000:continue
                dst,key=snapshot(f,W/'ancestry-inputs')
                pinned.append(dict(original=f,snapshot=str(dst),sha256=key))
            meta=dict(n=n,kind='fresh-follow',source=f'fq follow of {p}; walked source snapshot ',
                licence='own construction; upstream sources in pinned source proof',original=str(p),evidence=ev,
                walk=proof,parents=pinned)
            key=hashlib.sha256(p.read_bytes()).hexdigest()
            proof_data=dict(meta,walked_texts=texts)
            proof_hash=hashlib.sha256(json.dumps(proof_data,sort_keys=True).encode()).hexdigest()
            pp=W/'source-proofs'/f'{key}-{proof_hash[:16]}.json';pp.parent.mkdir(exist_ok=True)
            if not pp.exists():write_json(pp,proof_data)
            meta['source']+=str(pp)
            job=enqueue(p,meta,2 if lane in ['forensics','k123'] else 3)
            state(f'QUEUE follow n={n} lane={lane} gap={score-bars[n]:.3e} proof={pp} job={job} deadline 23:45Z')
        except Exception as e:
            state(f'SKIP follow file={p} error={repr(e)}')
    write_json(sp,seen)
    return used
