"""Apply source withdrawals to queued starts and all raw descendants of those starts."""
import json
import hashlib
from pathlib import Path
import re
import shutil
import fcntl

PROOF_CACHE = {}
VERDICT_CACHE = {}


def withdrawal_paths(hand):
    paths=set()
    for line in hand.splitlines():
        if re.search(r'\b(?:WITHDRAW|RETRACT|DROP|WITHHOLD)(?=\b|\d)',line.upper()):
            paths.update(re.findall(r'$SCRATCH/bounties-squares/[^ ,;]+\.csv',line))
            relative=re.findall(r'(?<![/\w-])(take-[^ ,;\"()]+\.csv)',line)
            paths.update('$SCRATCH/bounties-squares/'+name for name in relative)
            spaced=re.findall(r'(take-[a-z0-9-]+-r\d+)\s+(near/[^ ,;\"()]+\.csv)',line)
            paths.update('$SCRATCH/bounties-squares/'+lane+'/'+name for lane,name in spaced)
    return paths



def source_signature(record):
    notice=json.dumps([record.get('source',''),record.get('licence','')],sort_keys=True)
    return hashlib.sha256(notice.encode()).hexdigest()


def cleared_versions(r,hand):
    path=r.W/'cleared-versions.json'
    versions=json.loads(path.read_text()) if path.exists() else {}
    changed=False
    for line in hand.splitlines():
        count=re.search(r'CLEAN REPLACEMENT\s*(\d+)',line)
        hashed=re.search(r'sha256\s*([0-9a-f]{64})',line)
        owner=re.match(r'\S+\s+([a-z0-9-]+)\s*->',line)
        if not(count and hashed and owner):continue
        n=int(count[1]);target=r.B/('take-'+owner[1]+'-r25')/(str(n)+'.csv')
        known=versions.setdefault(str(target),[])
        if any(v['sha256']==hashed[1] for v in known):continue
        if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest()!=hashed[1]:continue
        record=next((v for v in r.rows(target.parent/'take.tsv') if v['n']==str(n)),None)
        if not record or not r.source_evidence(target,n):continue
        if hashlib.sha256(target.read_bytes()).hexdigest()!=hashed[1]:continue
        known.append(dict(sha256=hashed[1],signature=source_signature(record)))
        changed=True;r.state('ADOPT source-audited replacement version n%d hash%s'%(n,hashed[1]))
    if changed:r.atomic(path,json.dumps(versions))
    return versions


def qualified_version(proof,path,versions):
    allowed=versions.get(path,[])
    if not allowed:return False
    hashes={v['sha256'] for v in allowed};signatures={v['signature'] for v in allowed};checks=[]
    def visit(value):
        if isinstance(value,list):
            for child in value:visit(child)
        elif isinstance(value,dict):
            if value.get('path')==path and ('input_sha256' in value or isinstance(value.get('record'),dict)):
                rec=value.get('record',{})
                checks.append(value.get('input_sha256') in hashes or source_signature(rec) in signatures)
            for child in value.values():visit(child)
    visit(proof)
    return bool(checks) and all(checks)

def _apply(r):
    hand=(r.B/'handoff-r25.log').read_text()
    withdrawn=withdrawal_paths(hand)
    cleared=cleared_versions(r,hand)
    codehash=hashlib.sha256(b''.join((Path(__file__).parent/name).read_bytes() for name in ('revoke25.py','sources25.py','round25.py'))).hexdigest()
    policy=hashlib.sha256(json.dumps([sorted(withdrawn),cleared,codehash],sort_keys=True).encode()).hexdigest()
    cachefile=r.W/'verdict-cache.json'
    if cachefile.exists():
        try:VERDICT_CACHE.update(json.loads(cachefile.read_text()))
        except (OSError,ValueError):pass
    def stamp(name):
        if not name:return None
        try:
            st=Path(name).stat();return [st.st_mtime_ns,st.st_size]
        except OSError:return None
    saved=r.W/'revoked-keys.json'
    canceled=[];previous=set(json.loads(saved.read_text())) if saved.exists() else set();keys=set()
    for table in r.W.glob('r[0-9]*.tsv'):
        token=[table.stat().st_mtime_ns,table.stat().st_size,policy]
        cached=VERDICT_CACHE.get(str(table))
        if isinstance(cached,dict) and cached.get('token')==token and stamp(cached.get('proof'))==cached.get('proof_stamp') and stamp(cached.get('point'))==cached.get('point_stamp'):
            bad=cached['bad']
        else:
            text=table.read_text();proof_data={};proof=None;data=[]
            if hasattr(r,'captured_proof'):
                data=r.rows(table)
                proof=r.captured_proof(data[0]['source']) if data else None
                if proof and Path(proof).exists():
                    proof_data=json.loads(Path(proof).read_text());text+=' '+json.dumps(proof_data)
            text=re.sub(r'(take-[a-z0-9-]+-r\d+)\s+(near/[^ \t\n,;\"()\\]+\.csv)',lambda m:'$SCRATCH/bounties-squares/'+m[1]+'/'+m[2],text)
            bad=next((p for p in withdrawn if p in text and not qualified_version(proof_data,p,cleared)),None)
            public=re.findall(r'$SCRATCH/bounties-squares/take-harvest-r25/work/public/starts/\d+\.csv',text)
            if bad is None:bad=next((p for p in public if not Path(p).exists()),None)
            if bad is None and hasattr(r,'captured_proof'):
                data=r.rows(table)
                if data:
                    proof=r.captured_proof(data[0]['source'])
                    point=r.W/table.stem/(data[0]['n']+'.csv')
                    if proof and point.exists() and not Path(proof).name.startswith(hashlib.sha256(point.read_bytes()).hexdigest()):
                        bad='input proof does not bind captured coordinates'
            if bad is None and not r.clean_declared(text):bad='excluded ancestry in retained input proof'
            if bad is None and proof and Path(proof).exists():
                import sources25
                if proof not in PROOF_CACHE:PROOF_CACHE[proof]=sources25.audit_evidence(json.loads(Path(proof).read_text()))[0]
                if not PROOF_CACHE[proof]:bad='unresolved relative or frozen ancestry in input proof'
            point=str(r.W/table.stem/(data[0]['n']+'.csv')) if data else None
            VERDICT_CACHE[str(table)]=dict(token=token,bad=bad,proof=proof,proof_stamp=stamp(proof),point=point,point_stamp=stamp(point))
        if bad is None:continue
        key=int(table.stem[1:]);keys.add(key)
        for folder in ('jobs','remote-jobs'):
            for job in (r.W/folder).glob(str(key)+'-*.json'):
                marker=r.W/'cancel'/job.stem;marker.parent.mkdir(exist_ok=True)
                if not marker.exists():
                    marker.touch();canceled.append(marker);r.state('WITHDRAW k%d: %s; cancel job %s and descendants'%(key,bad,job.stem))
    restored=previous-keys;removed=[]
    for key in sorted(restored):
        for marker in (r.W/'cancel').glob(str(key)+'-*'):
            removed.append(marker.name);marker.unlink()
        r.state('RESTORE source-audited k%d after withdrawal directive recheck'%key)
    if removed and not (r.W/'REMOTE_REMOVED').exists():
        r.run(['ssh','boxE','rm -f '+' '.join(r.SD+'/cancel/'+name for name in removed)])
    oldquarantine=r.W/'withdrawn'
    for p in oldquarantine.glob('*.csv'):
        match=re.search(r'@run_s(\d+)',p.name)
        if match and int(match[1]) in restored:
            for folder in ('raw-in','raw-fq'):
                if p.name.startswith(folder+'-'):
                    target=r.W/folder/p.name[len(folder)+1:];target.parent.mkdir(exist_ok=True);shutil.move(str(p),target);break
    r.atomic(saved,json.dumps(sorted(keys)))
    r.atomic(cachefile,json.dumps(VERDICT_CACHE))
    if canceled and not (r.W/'REMOTE_REMOVED').exists():r.run(['rsync','-a']+[str(p) for p in canceled]+[r.REMOTE+'cancel/'])
    quarantine=r.W/'withdrawn';quarantine.mkdir(exist_ok=True)
    for folder in ('raw-in','raw-fq'):
        for p in (r.W/folder).glob('*.csv'):
            match=re.search(r'@run_s(\d+)',p.name)
            if match and int(match[1]) in keys:
                shutil.move(str(p),quarantine/(folder+'-'+p.name))
    for side in (r.T/'near').glob('*.csv.json'):
        if json.loads(side.read_text()).get('source_key') in keys:
            packing=Path(str(side)[:-5])
            if packing.exists():shutil.move(str(packing),quarantine/packing.name)
            origin=Path(str(packing)+'.origin.json')
            if origin.exists():shutil.move(str(origin),quarantine/origin.name)
            index=r.W/'near-seen.json'
            if index.exists():
                seen=json.loads(index.read_text());seen.pop(str(json.loads(side.read_text()).get('n')),None);r.atomic(index,json.dumps(seen))
            shutil.move(str(side),quarantine/side.name)
    return keys


def apply(r):
    with (r.W/'revoke.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        return _apply(r)
