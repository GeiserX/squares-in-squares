"""Bind numerical held-row follows to an exact submitted row and source record."""
import csv,functools,hashlib,json
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');HELD=S/'gather/round30-2026-11-15c.csv'
@functools.lru_cache(None)
def held_rows():
    rows={}
    for r in csv.DictReader(HELD.open()):rows.setdefault(int(r['n']),[]).append({k:r[k]for k in ['n','square_id','x','y','angle']})
    return rows
@functools.lru_cache(None)
def held_sha():return hashlib.sha256(HELD.read_bytes()).hexdigest()
def coords(rows):return [(int(r['n']),int(r['square_id']),float(r['x']),float(r['y']),float(r['angle']))for r in rows]
def check(origin):
    assert origin['held_path']==str(HELD)and origin['held_sha256']==held_sha(),'changed held registry'
    p=Path(origin['snapshot']);assert hashlib.sha256(p.read_bytes()).hexdigest()==origin['snapshot_sha256'],'changed held snapshot'
    n=origin['n'];assert coords(list(csv.DictReader(p.open())))==coords(held_rows()[n]),'snapshot differs from held row'
    record=Path(origin['record']);assert hashlib.sha256(record.read_bytes()).hexdigest()==origin['record_sha256'],'changed held source record'
    return dict(ok=True,path=str(HELD),n=n,submitted_held_boundary=True,sha256=held_sha(),source_record=str(record),source_record_sha256=origin['record_sha256'])
def audit(path,n):
    p=Path(path)
    side=p.with_suffix('.json')
    if not side.exists():side=Path(str(p)+'.json')
    if not side.exists():return None
    j=json.loads(side.read_text());origin=j.get('held31_origin')
    if not origin:return None
    assert origin['n']==n
    root=check(origin)
    return dict(n=n,source=str(p)+' immutable sha256 '+hashlib.sha256(p.read_bytes()).hexdigest()+'; numerical follow of own submitted held row; held source proof '+str(origin['record'])+'; '+str(HELD)+' immutable sha256 '+held_sha(),licence=j['modules'][0]['licence'],proof=root)
