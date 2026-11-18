"""Apply source withdrawals to queued starts and all raw descendants of those starts."""
import json
import hashlib
from pathlib import Path
import re
import shutil


def apply(r):
    hand=(r.B/'handoff-r24.log').read_text()
    withdrawn=set()
    for line in hand.splitlines():
        if 'WITHDRAW' in line.upper() or 'RETRACT' in line.upper():
            withdrawn.update(re.findall(r'$SCRATCH/bounties-squares/[^ ,;]+\.csv',line))
    saved=r.W/'revoked-keys.json'
    canceled=[];keys=set(json.loads(saved.read_text())) if saved.exists() else set()
    for table in r.W.glob('r[0-9]*.tsv'):
        text=table.read_text();bad=next((p for p in withdrawn if p in text),None)
        public=re.findall(r'$SCRATCH/bounties-squares/take-harvest-r24/work/public/starts/\d+\.csv',text)
        if bad is None:bad=next((p for p in public if not Path(p).exists()),None)
        if bad is None and hasattr(r,'captured_proof'):
            data=r.rows(table)
            if data:
                proof=r.captured_proof(data[0]['source'])
                point=r.W/table.stem/(data[0]['n']+'.csv')
                if proof and point.exists() and not Path(proof).name.startswith(hashlib.sha256(point.read_bytes()).hexdigest()):
                    bad='input proof does not bind captured coordinates'
        if bad is None:continue
        key=int(table.stem[1:]);keys.add(key)
        for folder in ('jobs','remote-jobs'):
            for job in (r.W/folder).glob(str(key)+'-*.json'):
                marker=r.W/'cancel'/job.stem;marker.parent.mkdir(exist_ok=True)
                if not marker.exists():
                    marker.touch();canceled.append(marker);r.state('WITHDRAW k%d: %s; cancel job %s and descendants'%(key,bad,job.stem))
    r.atomic(saved,json.dumps(sorted(keys)))
    if canceled:r.run(['rsync','-a']+[str(p) for p in canceled]+[r.REMOTE+'cancel/'])
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
            shutil.move(str(side),quarantine/side.name)
    return keys
