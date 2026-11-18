"""Queue the certified, licence-checked public starts handed off by harvest."""
import csv
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
import round22 as r


def main():
    dbp=r.W/'queue-state.json'
    db=json.loads(dbp.read_text());seen=set(db['seen'])
    bars=r.live_bars();transfer=[];count=0
    for d in sorted((r.B/'take-harvest-r22/work/public/starts').iterdir()):
        for row in r.rows(d/'take.tsv'):
            n=int(row['n']);sc=float(row['new']);f=d/('%d.csv'%n)
            if not f.exists() or sc>bars[n]+1e-6:
                continue
            digest=hashlib.sha256(f.read_bytes()).hexdigest()
            if digest in seen:
                continue
            k=2000+n
            while (r.W/('r%d.tsv'%k)).exists():
                k+=1000
            rd=r.W/('r%d'%k);rd.mkdir(exist_ok=True);shutil.copyfile(f,rd/f.name)
            source=row['source']+'; exact public start '+str(f)+'; '+str(d/'take.tsv')
            table='n\tscore\tdir\tsource\tlicence\tclass\n%d\t%r\ttake-harvest-r22\t%s\t%s\t1\n'%(n,sc,source,row['licence'])
            r.atomic(r.W/('r%d.tsv'%k),table)
            priority=.125 if n<440 else (.25 if n<640 else 1.4)
            j=dict(k=k,n=n,sub='r%d/%d.csv'%(k,n),seed=n+2200,seconds=150 if n<700 else (225 if n<800 else 450),sigma=.04,priority=priority,created=f.stat().st_mtime,leg=0,source='take-harvest-r22',public=True,slot=2)
            r.atomic(r.W/'jobs'/('%d-%d.json'%(k,n)),json.dumps(j))
            transfer.append(str(rd));seen.add(digest);db['previous'].append([n,sc,'take-harvest-r22']);count+=1
            r.state('QUEUE fresh public n=%d k=%d source=%s licence=%s deadline15:20Z'%(n,k,row['source'],row['licence']))
    db['seen']=sorted(seen);r.atomic(dbp,json.dumps(db))
    if transfer:
        r.run(['rsync','-a']+transfer+[r.REMOTE])
        r.run(['rsync','-a',str(r.W/'jobs')+'/',r.REMOTE+'jobs/'])
    r.state('FINISH public start handoff: %d queued; source tables copied before jobs'%count)


if __name__=='__main__':
    main()
