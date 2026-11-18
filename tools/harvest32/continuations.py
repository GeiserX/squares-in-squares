"""Continue this lane's certified outputs from their exact saved source proof."""
import copy
import hashlib
import json
import math
from pathlib import Path
from common import T,W,enqueue
from policy import snapshot
from walk import validate_job


def prepare(path,pinned,score):
    path=Path(path)
    if path.parent.resolve()!=(T/'near').resolve():raise ValueError('continuation is outside own near directory')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=pinned[1]:raise ValueError('continuation input changed')
    sidecar=Path(str(path)+'.json');sidecar_raw=sidecar.read_bytes();parent=json.loads(sidecar_raw)
    validate_job(parent)
    if (parent['start_score']-parent['score'])*math.sqrt(int(parent['n']))<=1e-9:
        raise ValueError('continuation already reached the side-gain stop threshold')
    parent_input=Path(parent['path'])
    if hashlib.sha256(parent_input.read_bytes()).hexdigest()!=parent['sha256']:
        raise ValueError('continuation parent input changed')
    receipt_path=Path(parent['proof']);receipt_raw=receipt_path.read_bytes();receipt=json.loads(receipt_raw);certificate=Path(receipt['file'])
    if receipt['input_hash']!=parent['sha256']:raise ValueError('continuation receipt has the wrong certified input')
    if int(receipt['n'])!=int(parent['n']) or certificate.read_bytes()!=raw:
        raise ValueError('continuation differs from its certified output')
    artifacts=[]
    expected={str(path):pinned[1],str(sidecar):hashlib.sha256(sidecar_raw).hexdigest(),str(parent_input):parent['sha256'],
              str(receipt_path):hashlib.sha256(receipt_raw).hexdigest(),str(certificate):pinned[1]}
    for item in [path,sidecar,parent_input,receipt_path,certificate]:
        dst,key=snapshot(item,W/'continuation-inputs')
        if key!=expected[str(item)]:raise ValueError('continuation record changed while queueing')
        artifacts.append(dict(original=str(item),snapshot=str(dst),sha256=key))
    base=copy.deepcopy(parent.get('inherited_job',parent))
    existing={pin['original']:pin for pin in base.get('parents',[])}
    for pin in artifacts:
        if pin['original'] in existing and existing[pin['original']]['sha256']!=pin['sha256']:
            raise ValueError('continuation source versions conflict')
        existing[pin['original']]=pin
    base['parents']=list(existing.values())
    continuation=dict(path=str(pinned[0]),sha256=pinned[1],original=str(path),walk=dict(clean=True),parents=artifacts,queued=0)
    meta=dict(n=parent['n'],kind='self-certified',original=str(path),source=f'fq continuation of {path}; pinned parent source {base["source"]}',
              licence=parent['licence'],inherited_job=base,continuation_pin=continuation,score_estimate=score)
    validate_job(dict(meta,path=str(pinned[0]),sha256=pinned[1]))
    return meta


def queue(path,pinned,score,priority):
    return enqueue(path,prepare(path,pinned,score),priority,pinned=pinned)
