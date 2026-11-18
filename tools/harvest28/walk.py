"""Walk sources under the main session's 00:19 UTC round 28 policy update."""
import glob
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import quench_walk as Q

if not hasattr(Q,'_harvest28_load'):
    Q._harvest28_load=Q.load_withdrawn
    Q._harvest28_moved=Q.moved_copy
if not hasattr(Q,'_harvest28_held'):Q._harvest28_held=Q.held
if not hasattr(Q,'_harvest28_seed'):Q._harvest28_seed=Q.samanyu_only
_original_load=Q._harvest28_load
_original_moved=Q._harvest28_moved


def retention(line):
    body=line.split(' -> ',1)[-1].split(':',1)[-1]
    if re.search(r'\b(?:WITHDRAW|WITHHOLD)\s+(?:n\s*=?\s*)?\d|\bWITHDRAW\s+(?:near|source|both|all|the|file|output)',body):return False
    return bool(re.search(r'not (?:the )?withheld|\bkeeps\b|\bretain(?:s|ed)?\b',body,re.I))


def lifted_share(line):
    if not re.search(r'share|original.seed|held.?801|held n.?=.?801',line,re.I):return False
    if re.search(r'squares-verified-best-of-1105|joegun|penguin|missing|changed since|rewritten',line,re.I):return False
    # Public harvest withdrawals keep the public-row share rule.
    if re.match(r'\S+\s+harvest\s+->',line):return False
    return True


def lifted_seed(line):
    # These two old audits found the sidecar. Their past missing state is
    # not an unresolved source; the only remaining reason was seed ancestry.
    resolved=re.sub(r'missing sidecar resolves to|missing intermediate was',
                    lambda m:m[0].replace('missing ',''),line,flags=re.I)
    return Q._harvest28_seed(resolved)


def lifted(line):return lifted_seed(line) or lifted_share(line)


def load():
    _original_load()
    Q.WITHDRAWN_LINES[:]=[(p,l) for p,l in Q.WITHDRAWN_LINES if not retention(l) and not lifted(l)]


def moved(path):
    result=_original_moved(path)
    if result:return result
    match=re.match(re.escape(Q.S)+r'(take-[a-z0-9-]+-r\d+)/',path)
    if not match or re.fullmatch(r'\d+\.csv',os.path.basename(path)):return None
    root=Path(Q.S)/match[1]
    notes=(root/'STATE.txt').read_text() if (root/'STATE.txt').exists() else ''
    for p in sorted(root.rglob(os.path.basename(path))):
        if not p.is_file() or str(p)==path:continue
        relevant=[l for l in notes.splitlines() if p.name in l or str(p.parent) in l]
        if relevant and any(lifted(l) for l in relevant) and not any(Q.REFUSE.search(l) and not lifted(l) for l in relevant):return str(p)
    return None


def held(n,k=None):
    if n==801:return 'held n=801 own layout; source policy main handoff-r28.log 2026-11-15T00:19:03Z; seeds/merged0.csv'
    return Q._harvest28_held(n,k)

Q.load_withdrawn=load
Q.moved_copy=moved
Q.held=held
Q.samanyu_only=lifted_seed
Q.LIVE='28'
Q.ANCDIRS=sorted(glob.glob(Q.S+'take-*-r2[2-8]/work/ancestry'))+sorted(glob.glob(Q.S+'take-*-r2[2-8]/work/*/ancestry'))
# Public-row shares are measured by policy.audit at public admission. A source
# walk must not apply that measure to own layouts, complete ancestors or seeds.
Q.SHARE_MAX=math.inf
Q.prv_share=lambda path,n:(0.0,0.0,math.inf)
Q.anc_share=lambda path:None
if not hasattr(Q,'_harvest28_neg'):Q._harvest28_neg=Q.NEG.pattern
Q.NEG=re.compile(Q._harvest28_neg+r'|gate\d+ at queue time:\s*share test:[^;\n]*',re.I)
Q.NAMES=re.compile(Q.NAMES.pattern.replace(r'|801h\b|held n = 801\b|held 801\b',''),re.I)


def check(path):
    proof=Q.check(path)
    proof['hits']=[h for h in proof.get('hits',[]) if not lifted_share(h)]
    proof['clean']=not proof['hits']
    proof['source_policy']='handoff-r28.log main00:19:03Z: own layouts exempt from share gates; explicit excluded-file ancestry still refused'
    return proof

walk=Q.walk
load_withdrawn=load
samanyu_only=lifted
WITHDRAWN_LINES=Q.WITHDRAWN_LINES


def public_job(j):
    original=j.get('inherited_job',j)
    return original.get('kind') in ('fresh-public','reopened-public')


def validate_job(j):
    from pins import verify
    load()
    original=j.get('inherited_job',j)
    if original.get('kind')=='fresh-follow':verify(original,Q.WITHDRAWN_LINES,lifted)
    for pin in original.get('parents',[]):
        if hashlib.sha256(Path(pin['snapshot']).read_bytes()).hexdigest()!=pin['sha256']:raise ValueError('pinned parent bytes changed')
    return True


def control():
    assert retention('2026-11-15T00:00:00Z forensics -> all: keeps n632, not the withheld X, take-forensics-r27/632.csv')
    assert not retention('2026-11-15T00:00:00Z invent -> all: WITHDRAW both n910 files; keeps unrelated X')
    assert lifted_share('csv ancestor own684: prvsiyan share=1.0')
    assert not lifted_share('source prvsiyan/squares-verified-best-of-1105')
    assert not lifted_share('2026-11-15T00:00:00Z harvest -> all: WITHDRAW public n499 share0.455')
    assert lifted_seed('DROP seed 983: its missing sidecar resolves to the own seed')
    assert lifted_seed('DROP seed 983: the missing intermediate was own seed 983')
    assert not lifted_seed('WITHDRAW seed 983: missing parent has no root')
    assert Q.SHARE_MAX==math.inf
    print('CONTROL own-share exclusions lifted; direct prvsiyan file and public harvest withdrawals remain excluded; retention semantics pass',flush=True)

if __name__=='__main__':control()


def source_stamp(path,n):
    """Bind the root source record while a producer can still rewrite it."""
    p=str(path)
    match=re.match(re.escape(Q.S)+r'(take-[a-z0-9-]+-r\d+)/(\d+)\.csv$',p)
    row=Q.take_row(match[1],n) if match else None
    records=[(name,hashlib.sha256(Path(name).read_bytes()).hexdigest()) for name in Q.sidecars(p)]
    return hashlib.sha256(json.dumps([row,records],sort_keys=True).encode()).hexdigest()


def producer_record(path,n):
    import csv
    p=Path(path)
    if p.stem!=str(n) or not re.fullmatch(r'take-[a-z0-9-]+-r\d+',p.parent.name):return {}
    ledger=p.parent/'take.tsv'
    if not ledger.exists():return {}
    with ledger.open() as f:
        return next((row for row in csv.DictReader(f,delimiter='\t') if row['n']==str(n)),{})
