"""Walk sources under the main session's round 34 brief policy (overrides 2 and 3 unchanged from round 33)."""
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
import importlib
import reader_records,versions,public_sources,archived_sources
importlib.reload(reader_records);importlib.reload(versions);importlib.reload(public_sources);importlib.reload(archived_sources)

if not hasattr(Q,'_harvest30_load'):
    Q._harvest30_load=Q.load_withdrawn
    Q._harvest30_moved=Q.moved_copy
if not hasattr(Q,'_harvest30_held'):Q._harvest30_held=Q.held
if not hasattr(Q,'_harvest30_seed'):Q._harvest30_seed=Q.samanyu_only
if not hasattr(Q,'_harvest30_covers'):Q._harvest30_covers=Q.snapshot_covers
if not hasattr(Q,'_harvest30_jtext'):Q._harvest30_jtext=Q._jtext
if not hasattr(Q,'_harvest30_walk'):Q._harvest30_walk=Q.walk
from withdrawals import load_withdrawn as _original_load
_original_moved=Q._harvest30_moved


def retention(line):
    body=line.split(' -> ',1)[-1].split(':',1)[-1]
    if re.search(r'\b(?:WITHDRAW|WITHHOLD)\s+(?:n\s*=?\s*)?\d|\bWITHDRAW\s+(?:near|source|both|all|the|file|output)',body):return False
    return bool(re.search(r'not (?:the )?withheld|\bnot (?:a|the) withdrawal\b|\bretention of new bytes\b|\bkeeps\b|\bretain(?:s|ed)?\b',body,re.I)
                or re.search(r'\bPRIORITY clean new\d+.*passes both source walks and differs from withdrawn\d* bytes',body))


def lifted_share(line):
    from held_policy import void_share
    if void_share(line):return True
    if re.search(r'public.first',line,re.I) and not re.search(r'no public.first|not public.first',line,re.I):return False
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
    return Q._harvest30_seed(resolved)


def lifted(line):return lifted_seed(line) or lifted_share(line)


def false_join_withdrawal(line):
    # Main 07:34:54Z corrected these exact r28 withdrawals; real source
    # names, public-first shares and missing parents still run independently.
    return (line.startswith('2026-11-15T01:51:44.') and 'forensics ->' in line
            and 'explicit rule-a family' in line and 'r23 forensics donor745/858' in line)


ALL_WITHDRAWN_LINES=[]

def load():
    _original_load()
    ALL_WITHDRAWN_LINES[:]=Q.WITHDRAWN_LINES
    Q.WITHDRAWN_LINES[:]=[(p,l) for p,l in Q.WITHDRAWN_LINES if not retention(l) and not lifted(l) and not false_join_withdrawal(l)]


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


def scoped_jtext(path,n):
    from reader_records import transform
    raw=Q._harvest30_jtext(path,n)
    try:data=json.loads(raw)
    except ValueError:return raw
    from versions import transform as resolve_versions
    return json.dumps(resolve_versions(transform(data)))

Q._jtext=scoped_jtext
Q._jt.clear()

def canonical_covers(rec,path):
    """A content-hashed node record covers its vanished original packing."""
    if Q._harvest30_covers(rec,path):return True
    if not isinstance(rec,str) or '/ancestry/' not in rec:return False
    proof=Path(rec)
    try:
        raw=proof.read_bytes();data=json.loads(raw)
    except (OSError,ValueError):return False
    return (bool(re.fullmatch(r'[0-9a-f]{64}',proof.stem))
            and hashlib.sha256(raw).hexdigest()==proof.stem
            and isinstance(data,dict) and Q.norm(str(data.get('path') or ''))==path
            and bool(re.fullmatch(r'[0-9a-f]{64}',str(data.get('packing_sha256',''))))
            and isinstance(data.get('evidence'),dict) and bool(data['evidence']))


def snapshot_covers(rec,path):
    if canonical_covers(rec,path):return True
    # An origin sidecar binds both the actual snapshot and its canonical tree.
    if not isinstance(rec,str) or not rec.endswith('.csv.origin.json'):return False
    try:
        data=json.loads(Path(rec).read_text());snapshot=Path(rec[:-len('.origin.json')])
        full=data['full_ancestry'];proof=Path(full['path'])
        return (Q.norm(data.get('path',''))==path and snapshot.is_file()
                and hashlib.sha256(snapshot.read_bytes()).hexdigest()==data['snapshot_sha256']
                and hashlib.sha256(proof.read_bytes()).hexdigest()==full['sha256']
                and canonical_covers(str(proof),path))
    except (OSError,ValueError,KeyError,TypeError):return False

Q.snapshot_covers=snapshot_covers

def held(n,k=None):
    if n==801:return 'held n=801 own layout; source policy round35-briefs/quench.txt overrides2/3; seeds/merged0.csv'
    return Q._harvest30_held(n,k)

Q.load_withdrawn=load
Q.moved_copy=moved
Q.held=held
Q.samanyu_only=lifted_seed
Q.LIVE='35'
Q.ANCDIRS=sorted(glob.glob(Q.S+'take-*-r*/work/ancestry'))+sorted(glob.glob(Q.S+'take-*-r*/work/*/ancestry'))
if not hasattr(Q,'_harvest30_anc'):Q._harvest30_anc=Q.ANC

class UniqueAncestors:
    """Keep the first occurrence of each content hash in one source text."""
    def __init__(self,pattern):self._pattern=pattern
    def findall(self,text):return list(dict.fromkeys(self._pattern.findall(text)))
    def __getattr__(self,name):return getattr(self._pattern,name)

Q.ANC=UniqueAncestors(Q._harvest30_anc)
# Public-row shares are measured by policy.audit at public admission. A source
# walk must not apply that measure to own layouts, complete ancestors or seeds.
Q.SHARE_MAX=math.inf
Q.prv_share=lambda path,n:(0.0,0.0,math.inf,0.0)
Q.anc_share=lambda path:None
Q.quench_audit.RULES=[(name,r'745r-858r|858r-745r|858-ec97a452|745-64c4b4f8' if name=='r22 745/858 join' else pattern) for name,pattern in Q.quench_audit.RULES]
if not hasattr(Q,'_harvest30_neg'):Q._harvest30_neg=Q.NEG.pattern
Q.NEG=re.compile(Q._harvest30_neg+r'|gate\d+ at queue time:\s*share test:[^;\n]*',re.I)
Q.NAMES=re.compile(Q.NAMES.pattern.replace(r'|801h\b|held n = 801\b|held 801\b',''),re.I)


def captured_walk(start,n,cap=3000):
    result=Q._harvest30_walk(start,n,cap)
    if len(result[2])>=cap:result[1].append('source graph reaches node cap; completeness unproved')
    Q._harvest30_last_walk=result
    return result

Q.walk=captured_walk


def check(path):
    proof=Q.check(path)
    proof['hits']=[h for h in proof.get('hits',[]) if not lifted_share(h)
                   and not (h.startswith('refused by its lane: ') and retention(h.split('refused by its lane: ',1)[1]))]
    # The five original areebbb rows have a recorded penguin union source.
    # A missing old per-n credit table cannot turn them into own geometry.
    for file in list(Q.LAST_VIA)+[str(path)]:
        m=re.fullmatch(re.escape(Q.S)+r'take-harvest-r22/(639|691|745|858|918)\.csv',str(file))
        if m:proof['hits'].append('explicit excluded penguin union row: '+str(file))
    audits=public_sources.check_live(str(path),Q._harvest30_last_walk)
    proof['public_first_audits']=audits
    proof['prv_share_measured']=False
    proof['public_first_root']=any(item['original']==str(path) for item in audits)
    for item in audits:
        if not item['allowed']:proof['hits'].append('public-first ancestor '+item['original']+' share='+str(item['share1e3'])+' against prvsiyan/squares-verified-best-of-1105')
        if item['original']==str(path):
            proof['prv_share']=[item['share1e6'],item['share1e3'],float('inf')];proof['prv_share_measured']=True
    proof['clean']=not proof['hits']
    proof['source_policy']='round35-briefs/quench.txt overrides2/3: own layouts exempt from share gates; explicit excluded-file ancestry still refused'
    return proof

walk=Q.walk
load_withdrawn=load
samanyu_only=lifted
WITHDRAWN_LINES=Q.WITHDRAWN_LINES


def public_job(j):
    original=j.get('inherited_job',j)
    return original.get('public_first',False) or original.get('kind') in ('fresh-public','reopened-public') or public_sources.root_public(j)


def validate_job(j):
    from pins import verify
    from public_records import check_job as check_public_records
    check_public_records(j)
    load()
    if j.get('continuation_pin'):verify(j['continuation_pin'],Q.WITHDRAWN_LINES,lifted)
    original=j.get('inherited_job',j)
    if original.get('kind')=='fresh-follow':
        if original.get('walk',{}).get('files',0)>=3000:raise ValueError('recorded source walk reached its node cap')
        verify(original,Q.WITHDRAWN_LINES,lifted)
    for pin in original.get('parents',[]):
        if hashlib.sha256(Path(pin['snapshot']).read_bytes()).hexdigest()!=pin['sha256']:raise ValueError('pinned parent bytes changed')
    public_sources.check_job(j)
    return True


def control():
    assert retention('2026-11-15T17:00:00Z forensics -> all: keeps n632, not the withheld X, take-forensics-r27/632.csv')
    assert not retention('2026-11-15T17:00:00Z invent -> all: WITHDRAW both n910 files; keeps unrelated X')
    assert retention('2026-11-15T09:37:43Z PRIORITY clean new641 n092718x641x113 promoted ahead of near rows. Its rebuilt rectangle passes both source walks and differs from withdrawn641 bytes.')
    assert not retention('2026-11-15T09:37:43Z invent -> all: WITHDRAW n641. PRIORITY clean new641 passes both source walks and differs from withdrawn641 bytes.')
    assert retention('2026-11-15T10:16:22Z harvest -> all: source note was a retention of new bytes, not a withdrawal; actual source checks still run.')
    assert lifted_share('csv ancestor own684: prvsiyan share=1.0')
    assert not lifted_share('source prvsiyan/squares-verified-best-of-1105')
    assert not lifted_share('2026-11-15T17:00:00Z harvest -> all: WITHDRAW public n499 share0.455')
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


def last_walk():
    """Return the complete walk just captured by check() in this process."""
    return Q._harvest30_last_walk
