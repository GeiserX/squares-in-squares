"""Gate direct public inputs while stopping numeric walks at submitted held rows."""
from pathlib import Path
from functools import lru_cache
import hashlib,json
import forensics_public29 as prior

WORK=Path('$SCRATCH/bounties-squares/take-forensics-r30/work')


@lru_cache(maxsize=4)
def held_catalog(path,stamp):
    return json.loads(Path(path).read_text())


def held_paths():
    p=WORK/'submitted-held30.json'
    if not p.exists():p=Path(__file__).resolve().parent/'results/forensics-held-r30-2026-11-15.json'
    return held_catalog(str(p),p.stat().st_mtime_ns) if p.exists() else {}


@lru_cache(maxsize=8192)
def file_sha(path,size,stamp):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def held(path):
    p=Path(path);entry=held_paths().get(str(p))
    if not entry or not p.is_file():return False
    st=p.stat();expected=entry.get('sha256');return isinstance(expected,str) and len(expected)==64 and file_sha(str(p),st.st_size,st.st_mtime_ns)==expected


def is_held_node(value):
    return isinstance(value,dict) and value.get('path') and isinstance(value.get('n'),int) and held(value['path'])


def direct_graph(proof):
    visited=set();boundaries=[]
    def load(path,expected=None):
        p=Path(path)
        if p.suffix!='.json' or not p.is_file():return None
        key=str(p)
        if key in visited:return None
        visited.add(key);blob=p.read_bytes()
        if expected and hashlib.sha256(blob).hexdigest()!=expected:raise ValueError('changed direct-path proof')
        return prune(json.loads(blob))
    def prune(value):
        if isinstance(value,list):return [prune(v) for v in value]
        if not isinstance(value,dict):return value
        if is_held_node(value):
            boundaries.append(dict(held_file=value['path'],held_n=value['n']))
            return dict(submitted_held_boundary=value['path'],held_n=value['n'])
        result={};links=[]
        for key,child in value.items():
            if key=='record':result[key]=child;continue
            result[key]=prune(child)
            if key=='full_ancestry' and isinstance(child,dict) and child.get('path'):
                loaded=load(child['path'],child.get('sha256'))
                if loaded is not None:links.append(loaded)
            elif key in ('source_proof','ancestry_file') and isinstance(child,str):
                loaded=load(child,value.get('ancestry_sha256') if key=='ancestry_file' else None)
                if loaded is not None:links.append(loaded)
        if links:result['direct_path_proofs']=links
        return result
    return prune(proof),boundaries


def audit(proof,references,work,notices,gather=None,matrix=None):
    graph,boundaries=direct_graph(proof)
    rows=prior.audit(graph,[],work,notices,gather,matrix)
    for row in rows:row['direct_path_checked']=True
    return rows
