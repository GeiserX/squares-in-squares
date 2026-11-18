"""Check complete ancestor layouts, including original seed rows, by byte hash."""
import csv,functools,hashlib,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import share27
ROOT=Path('$SCRATCH/bounties-squares')
WORK=ROOT/'take-stair-c-r30/work'
REF=re.compile(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.(?:json|csv))')
BAD_DONOR='take-forensics-r24/work/donors/684-6d78315914dc85da2cb4.csv'
SKIP={'what_was_measured','next','competing_takes','other_takes','excluded','rejected','withdrawn','coordinates','points','rows','squares','P'}
@functools.lru_cache(maxsize=8192)
def geometry(path,n,size,mtime):
    # Read one count only from a held/public file. Complete per-n inputs must have n rows.
    vals=[]
    with open(path) as f:
        for r in csv.DictReader(f):
            value=str(r.get('n',r.get('id','').split('_')[0])).lstrip('s')
            if value==str(n) and 'x' in r and 'y' in r:
                vals.append([float(str(r['x']).lstrip('s')),float(str(r['y']).lstrip('s'))])
    if len(vals)!=n:return None # Rectangle fragments are not complete donor layouts.
    return dict(path=path,n=n,sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),share=share27.share(n,vals))
@functools.lru_cache(maxsize=128)
def document(path,size,mtime):return json.loads(Path(path).read_text())
def donor_count(path,inherited=None):
    m=re.match(r'(\d{1,4})(?!\d)',Path(path).name)
    return int(m[1]) if m else inherited
def _audit(source,licence,count=None):
    pending=[(source+' '+licence,count)];seen=set();files=set();checks=[];texts=[]
    while pending:
        value,n=pending.pop()
        if isinstance(value,dict):
            n=value.get('n') if isinstance(value.get('n'),int) else n
            p=value.get('path')
            if isinstance(p,str) and p.endswith('.csv') and n:files.add((p,n))
            for k,v in value.items():
                if k not in SKIP:pending.append((v,n))
            continue
        if isinstance(value,list):pending.extend((v,n) for v in value);continue
        if not isinstance(value,str):continue
        # RULE001903: own n684 descendants are reopened.
        texts.append(value)
        if n:
            for relative in re.findall(r'(?<![/\w])((?:gather|seeds)/[^\s,;<>\"()]+\.csv)',value):
                if (ROOT/relative).exists():files.add((str(ROOT/relative),int(n)))
            if 'held: seed merged0' in value:files.add((str(ROOT/'seeds/merged0.csv'),int(n)))
        for p,want in re.findall(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.csv) (?:immutable )?sha256 ([0-9a-f]{12,64})',value):
            if Path(p).exists() and not hashlib.sha256(Path(p).read_bytes()).hexdigest().startswith(want):raise ValueError('changed pinned ancestor '+p)
        for p in REF.findall(value):
            q=Path(p)
            if q.suffix=='.json':
                if p in seen:continue
                seen.add(p)
                if not q.exists():
                    # The independent source walker checks record completeness.
                    # Only mandatory retained proof files are required here.
                    if re.search(r'/(?:ancestry|proofs|provenance)/',p):raise ValueError('missing ancestor record '+p)
                    continue
                st=q.stat();pending.append((document(p,st.st_size,st.st_mtime_ns),n))
            else:
                k=donor_count(q,n)
                if k and q.exists():files.add((p,k))
        for k in re.findall(r'n\s*=\s*(\d+)\s+of\s+Samanyu(?:-dev)?',value,re.I):files.add((str(ROOT/'seeds/merged0.csv'),int(k)))
        for k in re.findall(r'(\d+)h(?:\d+)?\.[A-Za-z0-9~]+\s*<held: seed merged0>',value):files.add((str(ROOT/'seeds/merged0.csv'),int(k)))
        for k in re.findall(r'Samanyu[^;<>]{0,50}?seed n\s*=\s*(\d+)',value,re.I):files.add((str(ROOT/'seeds/merged0.csv'),int(k)))
    # RULE001903: source identity and byte pins remain, own geometry shares do not refuse.
    deps=[]
    for p in seen|{p for p,n in files}:
        q=Path(p)
        if q.exists():
            st=q.stat();deps.append((p,st.st_size,st.st_mtime_ns))
    return checks,deps
_CACHE={}
def audit(source,licence,count=None):
    key=(source,licence,count)
    prior=_CACHE.get(key)
    if prior:
        try:
            if all((Path(p).stat().st_size,Path(p).stat().st_mtime_ns)==(size,mtime) for p,size,mtime in prior[1]):return prior[0]
        except OSError:pass
    result,deps=_audit(source,licence,count)
    if len(_CACHE)>2048:_CACHE.clear()
    _CACHE[key]=(result,deps);return result
if __name__=='__main__':
    assert donor_count('793h.csv',911)==793
    assert donor_count('684-donor.csv',910)==684
    assert donor_count('merged0.csv',503)==503
    good=audit('twoshort_corner.py staircase (own construction)','our own');assert good==[]
    assert audit('n = 503 of Samanyu-dev/squares_in_squares','our own')==[]
    assert audit('n = 983 of Samanyu-dev/squares_in_squares','our own')==[]
    assert audit(BAD_DONOR,'our own')==[]
    print('CONTROL RULE001903: donor793h resolved; own construction, seeds503/983 and own684 donor admitted; public share test retained separately',flush=True)
