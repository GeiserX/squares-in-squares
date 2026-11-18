"""Audit this round's near bytes under the clarified direct-parent rule."""
import hashlib,json,time
from pathlib import Path
from common import T,W,state,hand,write_json
from walk import validate_job


def scan(limit=4):
    path=W/'near-source-audit.json'
    records=json.loads(path.read_text()) if path.exists() else {}
    revision=hashlib.sha256(b''.join((Path(__file__).parent/name).read_bytes() for name in ['policy.py','public_sources.py','held_paths.py','held_boundary.py'])).hexdigest()
    stamp=W/'near-policy-revision.txt'
    if not stamp.exists() or stamp.read_text()!=revision:
        records={};stamp.write_text(revision)
    count=0;start=time.time()
    for csv in sorted((T/'near').glob('*.csv')):
        if count>=limit or time.time()-start>30:break
        sidecar=Path(str(csv)+'.json')
        if not sidecar.is_file():continue
        key=hashlib.sha256(csv.read_bytes()).hexdigest()
        if str(csv) in records and records[str(csv)]['sha256']==key and time.time()-records[str(csv)].get('checked_at',0)<600:continue
        count+=1
        try:validate_job(json.loads(sidecar.read_text()))
        except Exception as exc:
            record=dict(sha256=key,allowed=False,reason=repr(exc))
            target=W/'direct-source-held';target.mkdir(exist_ok=True)
            hand(f'WITHDRAW near exact sha256 {key}, {csv}; direct-parent audit: {str(exc)[:700]}; these bytes only.')
            csv.replace(target/csv.name)
            if sidecar.exists():sidecar.replace(target/sidecar.name)
            state(f'WITHDRAW own near exact bytes {key} after direct-parent audit; record={path}')
        else:record=dict(sha256=key,allowed=True)
        record['checked_at']=time.time()
        records[str(csv)]=record
    write_json(path,records)
    return count
