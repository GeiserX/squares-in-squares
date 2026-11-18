"""Recover explicitly named archived public donors, without gating own nodes."""
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from common import S,W

PATTERN=re.compile(r'archived public donor n\s*=\s*(\d+)\s*:\s*([\w.-]+/[\w.-]+)\s*::\s*([^\s|;<>]+\.csv)',re.I)
CACHE={}
EXTRA_PINS={}


def write_exact(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=raw:raise ValueError('archived public source snapshot changed: '+str(path))
    else:
        tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(raw);tmp.replace(path)
    return dict(original=str(path),snapshot=str(path),sha256=hashlib.sha256(raw).hexdigest())


def recover(n,ref,name,roundno):
    key=(n,ref,name,roundno)
    if key not in CACHE:
        base=S/f'take-harvest-r{roundno}'/'work/public/data'
        candidates=[base/kind/ref.replace('/','__')/name.replace('/','__') for kind in ('nb','ds')]
        source=next((p for p in candidates if p.is_file()),None)
        if source is None:raise ValueError(f'archived public donor{n} needs its original round{roundno} source: {ref} :: {name}')
        raw=source.read_bytes();archive_sha=hashlib.sha256(raw).hexdigest()
        reader=csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
        fields=reader.fieldnames;rows=[r for r in reader if int(r['n'])==n]
        if len(rows)!=n:raise ValueError('archived public donor has the wrong row count')
        stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
        row_raw=stream.getvalue().encode();row_sha=hashlib.sha256(row_raw).hexdigest()
        identity=hashlib.sha256(json.dumps([key,archive_sha]).encode()).hexdigest()
        folder=W/'public-ancestor-inputs';row=folder/f'{n}-archived-{identity[:20]}.csv'
        meta=dict(n=n,kind='fresh-public',public_first=True,source=f'{ref} :: {name}',
                  archive_source=f'https://www.kaggle.com/code/{ref}',archive_sha256=archive_sha,packing_sha256=row_sha)
        # The whole archive is an audit byte pin. Its other n are not parents.
        pins=[write_exact(folder/(archive_sha+'.blob'),raw),write_exact(row,row_raw),
              write_exact(Path(str(row)+'.source.json'),(json.dumps(meta,sort_keys=True)+'\n').encode())]
        CACHE[key]=((str(row),str(row),row_sha),pins)
    node,pins=CACHE[key]
    for pin in pins:
        if hashlib.sha256(Path(pin['snapshot']).read_bytes()).hexdigest()!=pin['sha256']:
            raise ValueError('archived public donor pin changed')
    return node,pins


def nodes(texts,is_public,capture=False):
    if capture:EXTRA_PINS.clear()
    result=[];seen=set()
    for label,text in texts.items():
        declaration=text
        if not label.startswith('held '):
            try:data=json.loads(text)
            except ValueError:
                if not label.endswith('.csv'):continue
            else:
                from harvest_follow import provenance_text
                declaration=provenance_text(data)
        for match in PATTERN.finditer(declaration):
            n=int(match[1]);ref=match[2];name=match[3]
            if not is_public(f'{ref} :: {name}'):continue
            rounds=re.findall(r'take-harvest-r(\d+)/'+str(n)+r'\.csv\b',text)
            if not rounds:raise ValueError('archived public donor has no bound source round')
            rounds=set(map(int,rounds))
            if len(rounds)!=1:raise ValueError('archived public donor source round is ambiguous')
            key=(n,ref,name,next(iter(rounds)))
            if key in seen:continue
            seen.add(key);node,pins=recover(*key);result.append(node)
            if capture:
                for pin in pins:EXTRA_PINS[pin['original']]=pin
    return result
