"""Separate numerical comparison diagnostics from a public row's real parents."""
import csv
import hashlib
import json
from pathlib import Path
from common import T,W,write_json
from walk import validate_job


def package(job,certificate,score):
    """Preserve public ancestry and exact input bytes in a fresh transport node."""
    if job['kind']!='fresh-public':raise ValueError('transport adapter handles original public rows only')
    validate_job(job)
    n=int(job['n']);raw=Path(job['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=job['sha256']:raise ValueError('changed public per-n input')
    root=W/'public-transports'/str(n);root.mkdir(parents=True,exist_ok=True)
    parent=root/(job['sha256']+'.csv')
    if parent.exists() and parent.read_bytes()!=raw:raise ValueError('changed transport input')
    parent.write_bytes(raw)
    base={k:v for k,v in job.items() if k not in ('path','evidence','share_audit')}
    # The shared source walker explicitly treats `excluded` as non-ancestral.
    # Keep every old diagnostic and the original record there for inspection.
    base['excluded']=dict(comparison_diagnostics=job.get('evidence',[]),original_queue_record=job)
    base.update(path=str(parent),sha256=job['sha256'],public_first=True)
    write_json(Path(str(parent)+'.json'),base)
    output=T/'near'/f'{n}-public33-{job["sha256"][:16]}.csv'
    cert=Path(certificate).read_bytes()
    if output.exists() and output.read_bytes()!=cert:raise ValueError('changed public transport output')
    output.write_bytes(cert)
    meta=dict(base,path=str(output),sha256=hashlib.sha256(cert).hexdigest(),
              source_file=str(parent),source=job['source']+'; certified from '+str(parent),
              score=score,required_offbox_fq=True,
              certification_tool='lanes/squares/tools/border/r28/finesafe.py, clearance2.2e-11')
    write_json(Path(str(output)+'.json'),meta)
    validate_job(meta)
    return output,meta
