"""Measure shares only on recorded public-first packing nodes, including ancestors."""
import csv
import hashlib
import json
from pathlib import Path
import re
import numpy as np
from common import S,W,write_json
from policy import prvsiyan,share

CACHE={}
OWN=re.compile(r'family[_ -](?:step|read)|k123|rectangle|modules?|stair|corner|one border|border_sweep|twoshort|our own|own construction|forensics',re.I)


def direct_public(source):
    import walk as A
    if not isinstance(source,str):return False
    source=re.sub(r'^results/[^:]+ n\s*=\s*\d+:\s*','',source.strip())
    source=re.sub(r'^take-[^:]+/take\.tsv:\s*','',source)
    source=re.sub(r'^public\s+','',source)
    source=re.sub(r'^certified start; start [^;]{0,160}? from\s+','',source)
    match=A.Q.PUBFIRST.match(source)
    if not match:return False
    ref=re.search(r'[\w.-]+/[\w.-]+\s*::',match[0])
    if ref is None:return False
    name=ref[0].split('::',1)[0].strip()
    if name in ('Samanyu-dev/squares_in_squares','franciscouzo/square-packing'):return False
    return not OWN.search(match[0][:ref.start()])


def source_record_public(data,n):
    import walk as A
    if not isinstance(data,dict):return False
    if data and all(str(k).isdigit() for k in data):return source_record_public(data.get(str(n)),n)
    if data.get('public_first') or data.get('kind') in ('fresh-public','reopened-public'):return True
    if isinstance(data.get('inherited_job'),dict) and source_record_public(data['inherited_job'],n):return True
    if any(direct_public(data.get(key)) for key in ['source','src']):return True
    path=str(data.get('path',''))
    held=re.search(r'(?:^|/)gather/round(\d+)-[^/]+\.csv$',path)
    if held and int(data.get('n',n))==n:
        return direct_public(A.held(n,int(held[1])))
    return False


def packing(path):
    try:
        with Path(path).open() as f:
            reader=csv.DictReader(f)
            if not {'n','x','y'}.issubset(reader.fieldnames or []):return None
            rows=[];n=None
            for r in reader:
                k=int(r['n'])
                if n is not None and k!=n:return None  # aggregate rows are checked through per-n snapshots
                n=k;rows.append((float(r['x']),float(r['y'])))
            if n is None or len(rows)!=n:return None
            return n,np.array(rows)
    except (OSError,ValueError,KeyError):return None


def public_node(original,n,texts,files,seen=None):
    seen=set() if seen is None else seen
    if original in seen:return False
    seen.add(original)
    if '/seeds/' in original or original.startswith('seeds/'):return False
    if re.search(r'/work/public\w*/starts/|/work/public\d+/quick-starts/|/work/near-pub',original):return True
    text=texts.get(original,'')
    if direct_public(text.split(' || ',1)[0]):return True
    sources=[text.split(' || ',1)[0]]
    links=[]
    names=[original+'.json',original+'.origin.json',original[:-4]+'.json',original[:-4]+'.origin.json',original+'.provenance.json',original+'.source.json']
    for name in names:
        raw=texts.get(name)
        if raw is None:
            actual=files.get(name,Path(name))
            try:raw=Path(actual).read_text()
            except OSError:continue
        try:data=json.loads(raw)
        except (ValueError,TypeError):continue
        if source_record_public(data,n):return True
        if isinstance(data,dict):
            sources.append(data.get('source',''))
            if data.get('kind')=='fresh-follow' and data.get('original'):links.append(data['original'])
    for source in sources:
        if not isinstance(source,str):continue
        linked=re.match(r'^fq (?:follow|quench(?: check)?) of\s+([^ ;]+\.csv)',source)
        if linked:links.append(linked[1])
    for linked in links:
        if not linked.startswith('/'):
            linked=str(S/linked) if linked.startswith(('take-','gather/','seeds/')) else str(Path(original).parent/linked)
        packed=packing(files.get(linked,linked))
        if packed is not None and packed[0]==n and public_node(linked,n,texts,files,seen):return True
    return False


def audit_nodes(nodes,texts,files):
    audits=[]
    for original,path,key in nodes:
        if not original.endswith('.csv'):continue
        value=packing(path)
        if value is None:continue
        n,coords=value
        if not public_node(original,n,texts,files):continue
        cache_key=(key,n)
        if cache_key not in CACHE:
            centred=coords-(coords.min(0)+coords.max(0))/2
            target=prvsiyan().get(n)
            if target is None:raise ValueError('public-first row lacks a comparison packing')
            CACHE[cache_key]=share(centred,target)
        measured=CACHE[cache_key]
        audits.append(dict(original=original,snapshot=str(path),sha256=key,n=n,share1e3=measured[1],share1e6=measured[0],allowed=measured[1]<.4))
    return audits


def check_live(start,walked):
    texts={str(k):v for k,v in walked[0]};files={str(p):str(p) for p in walked[2] if isinstance(p,str) and Path(p).is_file()}
    nodes=[]
    for original,path in files.items():
        if original.endswith('.csv'):nodes.append((original,path,hashlib.sha256(Path(path).read_bytes()).hexdigest()))
    from archived_sources import nodes as archived_nodes
    nodes.extend(archived_nodes(texts,direct_public,capture=True))
    return audit_nodes(nodes,texts,files)


def job_view(job):
    original=job.get('inherited_job',job)
    parents=original.get('parents',[])
    files={p['original']:p['snapshot'] for p in parents}
    texts={}
    matches=re.findall(r'walked source snapshot ($SCRATCH/bounties-squares/take-harvest-r\d+/work/source-proofs/[^ ;]+\.json)',original.get('source',''))
    if matches:
        proof=Path(matches[-1]);data=json.loads(proof.read_text())
        digest=hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
        if proof.stem.rsplit('-',1)[-1]!=digest[:16]:raise ValueError('canonical source proof changed')
        texts={str(k):v for k,v in data.get('walked_texts',[])}
    nodes=[(p['original'],p['snapshot'],p['sha256']) for p in parents]
    root=original.get('original',original['path'])
    nodes.append((root,job['path'],job['sha256']))
    files.setdefault(root,job['path'])
    metadata={key:original[key] for key in ['kind','source','original','public_first','inherited_job'] if key in original}
    texts.setdefault(root+'.source.json',json.dumps(metadata))
    return nodes,texts,files,root


def root_public(job):
    nodes,texts,files,root=job_view(job)
    value=packing(job['path'])
    return value is not None and public_node(root,value[0],texts,files)


def check_job(job):
    nodes,texts,files,root=job_view(job)
    from archived_sources import nodes as archived_nodes
    nodes.extend(archived_nodes(texts,direct_public))
    audits=audit_nodes(nodes,texts,files)
    bad=[a for a in audits if not a['allowed']]
    if bad:raise ValueError('public-first ancestor fails1105 share: '+json.dumps(bad[:2],sort_keys=True))
    return audits
