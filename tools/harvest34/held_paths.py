"""Trace public parents on paths that do not cross a submitted held row."""
import hashlib
import json
from pathlib import Path
import re
from common import S


def boundary_text(text):
    # Import the producer's SHA-pinned catalog without changing its tools.
    if '"path"' not in text:return text
    try:data=json.loads(text)
    except ValueError:return text
    from held_boundary import is_held_node
    def prune(value):
        if isinstance(value,list):return [prune(item) for item in value]
        if not isinstance(value,dict):return value
        if is_held_node(value):return dict(submitted_held_boundary=value['path'],n=value['n'])
        return {key:prune(child) for key,child in value.items()}
    return json.dumps(prune(data))


def direct_nodes(start,texts):
    import walk as A
    Q=A.Q
    labels=set(texts)
    by_basename={}
    for label in labels:
        by_basename.setdefault(Path(label).name,[]).append(label)
    edges={}
    for label,text in texts.items():
        if label.startswith('held '):continue
        text=boundary_text(text)
        links=set(Q.norm(p) for p in Q.PATH.findall(text))
        if label.endswith('.csv'):
            links.update(p for p in (label+'.json',label+'.origin.json',label[:-4]+'.json',label[:-4]+'.origin.json',label+'.provenance.json',label+'.source.json') if p in labels)
        here=Path(label).parent
        m=re.match(re.escape(str(S))+r'/(take-[a-z0-9-]+-r\d+)/',label)
        directories=[str(here)]+([str(S/m[1]/'near'),str(S/m[1]/'work')] if m else [])
        for bare in set(Q.BARE.findall(text)):
            matches=[str(Path(directory)/bare) for directory in directories if str(Path(directory)/bare) in labels]
            if matches:links.add(matches[0])
        for sha in Q.ANC.findall(text):
            links.update(p for p in by_basename.get(sha+'.json',[]) if '/ancestry/' in p)
        edges[label]=links
    seen=set();pending=[str(start)]
    while pending:
        label=pending.pop()
        if label in seen or label.startswith('held '):continue
        seen.add(label);pending.extend(edges.get(label,()))
    return seen


def audit(start,texts,files,nodes,withdrawals=()):
    from public_sources import audit_nodes,direct_public
    from held_policy import void_share
    direct=direct_nodes(start,texts)
    selected=[node for node in nodes if node[0] in direct]
    for original,path,sha in selected:
        if original.endswith('/take-forensics-r22/work/donors/799-986b3b6daebce05b9257.csv') and sha=='94740134aabf0aeed3e34e7f743a44ca68b5f9be4d6e3d3b1d49a694fbb2d8fe':
            raise ValueError('direct withdrawn public donor799 exact bytes named by main13:32:00Z; a held-only route remains exempt')
    audits=audit_nodes(selected,texts,files)
    bad=[a for a in audits if not a['allowed']]
    if bad:raise ValueError('direct public parent fails1105 share: '+json.dumps(bad[:2],sort_keys=True))
    hashes={original:sha for original,path,sha in nodes}
    for name,line in withdrawals:
        if not void_share(line):continue
        absolute=name if name.startswith('/') else str(S/name)
        if absolute not in direct:continue
        pins=re.findall(r'sha256(?: prefix)?[ =:]+([0-9a-f]{8,64})',line,re.I)
        actual=hashes.get(absolute)
        if pins and actual and not any(actual.startswith(h) for h in pins):continue
        # A held-only path is absent from direct. Direct withdrawn public files
        # must keep their byte-bound refusal even if another branch is held.
        if re.search(r'public.first|archived.public',line,re.I):
            raise ValueError('direct withdrawn public parent: '+line[:300])
    return audits,direct
