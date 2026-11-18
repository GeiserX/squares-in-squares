"""Recover clean-source steps under the round24 main session's revised bar."""
import csv,hashlib,json,math,os,re,shutil,time
from pathlib import Path
import family_loop as fl
from family_lineage import Lineage,declared_status
HELD={228,459,503,534,550,581,597,599,648,698,735,753,790,809,847,866,868,927,935,990}

class Rescue:
    def __init__(self,work,scratch):
        self.w=Path(work);self.s=Path(scratch);self.take=self.w.parent;self.lineage=Lineage(scratch,work)
        self.a={int(r['n']):r for r in csv.DictReader(open(self.w/'deploy/details.csv'))}
        b={int(r['n']):r for r in csv.DictReader(open(self.s/'gate/cand-round22-1113b/details.csv'))}
        self.rows={n:(b[n] if n in HELD else r) for n,r in self.a.items()}
        self.details=self.w/'deploy/clean-details.csv'
        with self.details.open('w',newline='') as h:
            wr=csv.DictWriter(h,fieldnames=list(next(iter(self.a.values())).keys()));wr.writeheader();wr.writerows(self.rows.values())
    def label(self,n,source,licence):
        return self.lineage.classify(n,source,licence)
    def cycle(self,takes,boxes,enqueue=True,strict=None):
        w=self.w;src=fl.sources(str(w));classified={};changed=False
        def classify(donor):
            nonlocal changed
            if donor not in classified:
                fields=src.get(donor,'\t\t').split('\t')
                if not fields[1]:return dict(status='unknown',licence='')
                q=self.label(int(donor.split('-')[0]),fields[1],fields[2]);classified[donor]=q
                if q['status']!='unknown' and q['licence']!=fields[2]:
                    src[donor]='\t'.join((donor,fields[1],q['licence']));changed=True
            return classified[donor]
        bars={n:float(r['score']) for n,r in self.rows.items()};peerrows=[]
        for directory in takes.values():
            for row in csv.DictReader(open(Path(directory)/'take.tsv'),delimiter='\t'):
                n=int(row['n'])
                if n not in HELD:continue
                status=declared_status(row.get('licence',''))
                if status is None:status=self.label(n,row.get('source',''),row.get('licence',''))['status']
                if status=='no':
                    bars[n]=min(bars[n],float(row['new']));peerrows.append(dict(n=n,new=row['new']))
        beat=w/'deploy/clean-beat.tsv'
        with beat.open('w',newline='') as h:
            wr=csv.DictWriter(h,fieldnames=['n','new'],delimiter='\t');wr.writeheader();wr.writerows(peerrows)
        revoked=set(json.loads((w/'revoked-donors.json').read_text())) if (w/'revoked-donors.json').exists() else set()
        views=[]
        for phase in ['stage','quench']:
            folder=w/('clean-view-'+phase);raw=folder/'raw';raw.mkdir(parents=True,exist_ok=True)
            for p in raw.glob('*.csv'):p.unlink()
            inputs=list(w.glob('*-out-quench-clean-*/raw/*.csv')) if phase=='quench' else list(w.glob('*-out*/steps/*.csv'))
            for p in inputs:
                m=re.match(r'(\d+)-(up|down)\d+from(.+)\.csv$',p.name)
                if not m:continue
                n=int(m[1]);dn=m[3]
                if n not in HELD or '+' in dn or dn in revoked:continue
                q=classify(dn)
                if q['status']!='no':continue
                P=fl.fs.load(str(p),{n})[n]
                if fl.fs.canon(P)[0] >= (bars[n]+1)*math.sqrt(n)-1e-9:continue
                (raw/p.name).unlink(missing_ok=True);(raw/p.name).symlink_to(p)
            views.append(folder)
        if changed:fl.save_sources(str(w),src)
        keep=[];jobs=[]
        if enqueue:
            stage=w/'clean-certified'
            staged=fl.certify(str(w),str(stage),str(self.details),[str(beat)],outdirs=[str(views[0])],table=str(w/'clean-stage-table.tsv'))
            done=fl.seen(str(w),'clean-quench')
            for line in staged:
                q=line.split();n,tag=q[1],q[5];path=stage/(n+'.csv');version=hashlib.sha256(path.read_bytes()).hexdigest()[:16];key=tag+'@'+version
                if key in done:continue
                done.add(key);sub=w/'deploy/qin'/('clean-'+version);sub.mkdir(parents=True,exist_ok=True);shutil.copy2(path,sub/(tag+'.csv'))
                job='0100-quench-clean-'+version+'.job'
                (w/'deploy/jobs'/job).write_text('$PY -I -u near_polish.py out-quench-clean-%s clean-details.csv 150 qin/clean-%s/%s.csv --beat clean-beat.tsv\n'%(version,version,tag));jobs.append(job)
            fl.save_seen(str(w),'clean-quench',done)
        pub=w/'clean-publication'
        ck=fl.certify(str(w),str(pub),str(self.details),[str(beat)],outdirs=[str(views[1])],table=str(w/'clean-publication-table.tsv'))
        rows={};proofs={};paths={};strict=Path(strict) if strict else self.take
        if (strict/'take.tsv').exists():
            for row in csv.DictReader(open(strict/'take.tsv'),delimiter='\t'):
                n=int(row['n']);q=self.label(n,row['source'],row['licence'])
                if q['status']=='unknown':continue
                row['licence']=q['licence'];rows[n]=row;proofs[n]=q;paths[n]=strict/(str(n)+'.csv')
        for row in csv.DictReader(open(pub/'take.tsv'),delimiter='\t'):
            n=int(row['n']);old=rows.get(n)
            if old is None or 'Samanyu ancestry: yes' in old['licence'] or float(row['new'])<float(old['new']):
                rows[n]=row;paths[n]=pub/(str(n)+'.csv');proofs[n]=self.label(n,row['source'],row['licence'])
        for n,parent in paths.items():
            dest=self.take/(str(n)+'.csv')
            if parent==dest or (dest.exists() and parent.read_bytes()==dest.read_bytes()):continue
            tmp=dest.with_suffix('.csv.tmp');shutil.copy2(parent,tmp);os.replace(tmp,dest)
        path=self.take/'take.tsv'
        with path.with_suffix('.tsv.tmp').open('w',newline='') as h:
            wr=csv.DictWriter(h,fieldnames=['n','held','new','gain','source','licence'],delimiter='\t',lineterminator='\n');wr.writeheader();wr.writerows(rows[n] for n in sorted(rows))
        path.with_suffix('.tsv.tmp').replace(path)
        announced=fl.seen(str(w),'clean-announced')
        for row in rows.values():
            n=int(row['n'])
            if n not in HELD or 'Samanyu ancestry: no' not in row['licence']:continue
            key=str(n)+'@'+row['new']
            if key not in announced:
                with (self.s/'handoff-r24.log').open('a') as h:h.write(time.strftime('%H:%M:%SZ',time.gmtime())+' family -> all: source-clean exception n=%d, score%s, gain%s against held round22; Samanyu ancestry:no; certified-file remote quench complete, %s\n'%(n,row['new'],row['gain'],self.take/(str(n)+'.csv')))
                announced.add(key)
        fl.save_seen(str(w),'clean-announced',announced)
        (w/'lineage-publication.json').write_text(json.dumps({str(n):dict(status=q['status'],seeds=q['seeds'],unknown=q['unknown']) for n,q in proofs.items()},indent=2)+'\n')
        if jobs:
            for b in boxes:fl.sh('rsync -a %s %s %s:%s/'%(self.details,beat,b['host'],b['dir']),120)
        return jobs
