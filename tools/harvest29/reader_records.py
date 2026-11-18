"""Resolve a reader donor from its named state entry, with exact byte pins."""
import csv
import hashlib
import json
from pathlib import Path
import re
from common import S,W,write_json
from policy import snapshot

EXTRA_PINS={}


def resolve(node):
    state=Path(node['path']);donor=node['donor'];packing=Path(node['snapshot'])
    raw=state.read_bytes();data=json.loads(raw)
    credit_key=node['sha256']
    source=data.get('sources',{}).get(donor)
    matches=[(key,r) for key,r in data.get('seen',{}).items() if r.get('donor')==donor]
    if not isinstance(source,list) or len(source)!=2 or len(matches)!=1:
        raise ValueError('reader state has no unique named donor source')
    if hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()!=credit_key:
        raise ValueError('reader source credit differs from recorded SHA256')
    key,seen=matches[0]
    if hashlib.sha256(packing.read_bytes()).hexdigest()!=key:
        raise ValueError('reader donor snapshot differs from its state hash')
    n=int(donor.split('-',1)[0])
    if int(next(csv.DictReader(packing.open()))['n'])!=n:
        raise ValueError('reader donor count mismatch')
    full,sha=snapshot(state,W/'ancestry-inputs')
    EXTRA_PINS[str(state)]=dict(original=str(state),snapshot=str(full),sha256=sha)
    upstream={}
    if 'areebbb/sis-certified-union-micro-shrink-lb-22-17479' in source[0]:
        credits=S/'take-harvest-r22/work/public/data/nb/areebbb__sis-certified-union-micro-shrink-lb-22-17479/per_n.csv'
        with credits.open() as f:
            row=next(r for r in csv.DictReader(f) if int(r['n'])==n)
        if not row['src'].startswith('notebooks/'):
            raise ValueError('reader upstream dataset terms need a complete source trace')
        upstream=dict(source='areebbb/sis-certified-union-micro-shrink-lb-22-17479 :: per_n.csv, donor n = '+str(n)+', src='+row['src'],
                      licence='Apache 2.0 (Kaggle default for the named public notebooks)')
        full_credit,credit_sha=snapshot(credits,W/'ancestry-inputs')
        EXTRA_PINS[str(credits)]=dict(original=str(credits),snapshot=str(full_credit),sha256=credit_sha)
    record=dict(kind='resolved reader donor' ,donor=donor,n=n,snapshot=str(packing),sha256=key,
                source=source[0],licence=source[1],original_input=seen['path'],credit_sha256=credit_key,
                reader_state_sha256=sha,upstream=upstream)
    digest=hashlib.sha256(json.dumps(record,sort_keys=True).encode()).hexdigest()
    path=W/'reader-source-records'/f'{donor}-{digest[:16]}.json'
    path.parent.mkdir(exist_ok=True)
    if not path.exists():write_json(path,record)
    return dict(kind='pinned reader donor',donor=donor,snapshot=str(packing),sha256=key,
                source_record=str(path),source=source[0],licence=source[1],upstream=upstream)


def transform(value):
    if isinstance(value,dict):
        if ({'original','snapshot','sha256'}.issubset(value)
                and re.search(r'/take-readers-r\d+/work/follow\.json$',str(value.get('original','')))):
            # Full-state bytes verify the selected record; they are not all donor ancestors.
            return dict(kind='reader state byte pin',sha256=value['sha256'])
        if (value.get('kind')=='reader' and re.search(r'/take-readers-r\d+/work/follow\.json$',str(value.get('path','')))
                and {'donor','snapshot','sha256'}.issubset(value)):
            return resolve(value)
        return {k:transform(v) for k,v in value.items()}
    if isinstance(value,list):return [transform(v) for v in value]
    return value
