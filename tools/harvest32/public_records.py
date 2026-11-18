"""Keep unparsed fetched source records out of the public proof queue."""
import hashlib
import csv
import json
from pathlib import Path
import re
import zipfile
from common import S,W
from policy import snapshot

KNOWN={'per_n.csv','per_n_source_table.csv','submission_sources.csv','sources.csv','per_puzzle_L.csv'}
RICH=re.compile(r'source|provenance|inheritance|merge_report',re.I)
VERSION=2


def inspect(raw,source,capture=False):
    if 'squares-verified-best-of-1105' in source:
        raise ValueError('recorded public source names the excluded1105 file')
    folder=Path(raw).parent
    pins=[];visited=set()
    while True:
        if folder in visited:raise ValueError('cycle in carried public source records')
        visited.add(folder)
        meta=folder/'meta.json'
        if not meta.is_file():raise ValueError('missing public output metadata: '+str(meta))
        data=json.loads(meta.read_text())
        records=[p for p in folder.iterdir() if p.is_file() and p.name!='meta.json' and (p.name in KNOWN or RICH.search(p.name))]
        for candidate in folder.glob('*.csv'):
            with candidate.open() as stream:columns=csv.DictReader(stream).fieldnames or []
            if set(columns)&{'src','source','source_ref','source_file'} and candidate not in records:
                raise ValueError('public source columns need a format adapter: '+candidate.name)
        unknown=[p.name for p in records if p.name not in KNOWN]
        if unknown:raise ValueError('public source records need a format adapter: '+', '.join(sorted(unknown)))
        for p in records:
            with p.open() as stream:fields=csv.DictReader(stream).fieldnames or []
            source_fields=set(fields)&{'src','source','source_ref','source_file'}
            if any(RICH.search(field) or re.search(r'donor|upstream',field,re.I) for field in fields) and not source_fields:
                raise ValueError('public credit columns need an adapter: '+p.name)
            if source_fields and 'per-n origin ' not in source:
                raise ValueError('public credit file lacks a matching per-n trace: '+p.name)
        from harvest_follow import provenance_text
        for p in folder.glob('*.json'):
            if p.name=='meta.json' or p in records:continue
            if p.stat().st_size>8_000_000:raise ValueError('public JSON record exceeds the review limit: '+p.name)
            body=json.loads(p.read_text());text=provenance_text(body)
            if re.search(r'\.csv\b|(?:datasets|notebooks)/|squares-verified-best-of-1105',text,re.I):
                raise ValueError('public JSON ancestry needs a format adapter: '+p.name)
            records.append(p)
        for p in folder.glob('*.zip'):
            with zipfile.ZipFile(p) as archive:
                items=archive.infolist()
                if len(items)>5000:raise ValueError('public archive needs a bounded format adapter: '+p.name)
                names=[Path(item.filename).name for item in items if Path(item.filename).suffix.lower() in ('.json','.csv','.txt','.md','.tsv')]
                budget=32_000_000
                for item in items:
                    if not item.filename.lower().endswith('.json'):continue
                    budget-=item.file_size
                    if item.file_size>8_000_000 or budget<0:raise ValueError('archived JSON exceeds the review limit: '+p.name)
                    text=provenance_text(json.loads(archive.read(item)))
                    if re.search(r'\.csv\b|(?:datasets|notebooks)/|squares-verified-best-of-1105',text,re.I):
                        raise ValueError('archived JSON ancestry needs a format adapter: '+p.name)
            unknown=[name for name in names if RICH.search(name) and name not in KNOWN]
            if unknown:raise ValueError('archived public source records need an adapter: '+p.name)
            records.append(p)
        if capture:
            for p in [meta]+records:
                dst,key=snapshot(p,W/'public-source-inputs')
                pins.append(dict(original=str(p),snapshot=str(dst),sha256=key))
        carried=data.get('carried')
        if not carried:break
        parent=Path(carried)/folder.parent.name/folder.name
        if not parent.resolve().is_relative_to(S.resolve()):raise ValueError('carried source leaves the squares archive')
        folder=parent
    return pins


def check_job(job):
    original=job.get('inherited_job',job)
    if original.get('kind') not in ('fresh-public','reopened-public'):return
    source=original.get('source','')
    if 'squares-verified-best-of-1105' in source:
        raise ValueError('recorded public source names the excluded1105 file')
    raw=re.search(r'raw file ([^;]+?\.csv)(?:;|$)',source)
    if raw:inspect(raw[1],source)
    if original.get('public_records_checked')==VERSION:
        parents=original.get('parents',[])
        if not any(Path(p['original']).name=='meta.json' for p in parents):
            raise ValueError('public source screen lacks pinned metadata')
        for p in parents:
            raw=Path(p['snapshot']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=p['sha256']:raise ValueError('public source record pin changed')
            name=Path(p['original']).name
            if RICH.search(name) and name not in KNOWN:
                raise ValueError('pinned public source record needs an adapter: '+name)
        return
    raw=re.search(r'raw file ([^;]+?\.csv)(?:;|$)',source)
    if raw:inspect(raw[1],source)
    elif original.get('public_records_checked'):
        raise ValueError('public source screen version needs its raw output path')
