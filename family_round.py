#!/usr/bin/env python3
"""Run fresh family follows and audited carry jobs with one common deadline."""
import argparse,csv,datetime,hashlib,json,os,re,shutil,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import family_loop as fl
from family_clean import Audit
from family_rescue import Rescue

def fresh_name(job, deadline, now):
    if int(job[:4])<=1049:
        return job
    return '1050-%06d-%s' % (max(0,int(deadline-now)),job[5:])

def quarantine_revoked(work):
    w=Path(work)
    revoked=json.loads((w/'revoked-donors.json').read_text()) if (w/'revoked-donors.json').exists() else []
    for folder in ['raw','steps']:
        for p in w.glob('*-out*/'+folder+'/*.csv'):
            if any(re.search(r'from'+re.escape(dn)+r'(?:[+.]|$)',p.name) for dn in revoked):
                dest=w/'quarantine'/p.parent.parent.name/folder/p.name
                dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dest))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('work');ap.add_argument('--scratch',required=True);ap.add_argument('--lane',required=True)
    ap.add_argument('--deadline',type=float,required=True);ap.add_argument('--follow-until',type=float,required=True)
    ap.add_argument('--every',type=float,default=120);ap.add_argument('--once',action='store_true');ap.add_argument('--carry',action='store_true')
    a=ap.parse_args();w=Path(a.work);s=Path(a.scratch);take=w.parent;d=w/'deploy'
    audit=Audit(s,a.lane,w);fl.FOLLOW_AUDIT=audit
    rescue=Rescue(w,s)
    fl.WALK_MISSES=1;fl.FILL_HERE=True;fl.NEAR_COPY=1e-6;fl.NEAR_OUT=1e-4;fl.STAIR_ENV='SQ_CUTREACH=9 SQ_STAIRCUT=1 '
    bx=fl.boxes(str(w));follow=argparse.Namespace(round='r24',scratch=str(s),fresh=[],logs=[],gate=str(s/'gate/cand-round23-1113a/gate.json'),best=str(Path(a.lane)/'results/round23-best-2026-11-13.tsv'),held=str(s/'gather/round23-2026-11-13a.csv'),first=['stair-c','corners','readers','twoshort','border','modules'],newall=True)
    def state(msg):
        with (take/'STATE.txt').open('a') as h:h.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+' boxA '+msg+'\n')
    (w/'loop.pid').write_text(str(os.getpid())+'\n');state('START audited fresh-follow collector. Existing remote budget3/2. Common deadline22:15Z. Log work/loop.out.')
    if a.carry:
        jobs=json.loads((w/'carried-jobs.json').read_text());fl.deal(str(w),bx,jobs)
        state('ADOPT %d source-admitted carried follow jobs. Fresh jobs sort ahead of these jobs. Saved draws stay closed.'%len(jobs))
    previous={};lastcheck=0
    while time.time()<a.deadline and not (w/'STOPLOOP').exists():
        t0=time.time();takes=fl.other_takes(str(take),'r24',str(s));beats=[x+'/take.tsv' for x in takes.values()]
        fl.collect(str(w),bx)
        quarantine_revoked(w)
        strict=w/'strict-publication'
        keep,qj=fl.certify_after_quench(str(w),str(strict),str(d/'details.csv'),beats,bx)
        qj+=rescue.cycle(takes,bx,enqueue=time.time()<a.follow_until,strict=strict)
        selected={r['n']:float(r['new']) for r in csv.DictReader(open(take/'take.tsv'),delimiter='\t')}
        keep=[line for line in keep if selected.get(line.split()[1])==float(line.split()[3])]
        fl.prune(str(w),str(take));fl.announce(str(w),str(take),follow,keep)
        fl.near_out(str(w),str(take),follow,beats)
        fl.push_beats(str(w),bx,takes)
        fj=fl.follow_pass(str(w),str(take),follow,takes) if time.time()<a.follow_until else []
        # All new starts take precedence over the inherited near queue.
        renamed=[]
        for j in fj:
            new=fresh_name(j,a.deadline,time.time())
            if new!=j:(d/'jobs'/j).replace(d/'jobs'/new)
            renamed.append(new)
        got=fl.deal(str(w),bx,qj+renamed);audit.save()
        current={r.split()[1]:r for r in keep}
        for n,line in current.items():
            if previous.get(n)!=line:
                state('PUBLISHED '+line+' after remote quench from certified input.')
                proof=w/('published-'+n+'-first.json')
                if not proof.exists():
                    row=next(r for r in csv.DictReader(open(take/'take.tsv'),delimiter='\t') if r['n']==n)
                    old=next(float(r['score']) for r in csv.DictReader(open(d/'details.csv')) if r['n']==n)
                    bar=old
                    for path in beats:
                        for r in csv.DictReader(open(path),delimiter='\t'):
                            if r['n']==n:bar=min(bar,float(r['new']))
                    proof.write_text(json.dumps(dict(n=int(n),new=float(row['new']),gain_candidate=old-float(row['new']),gain_live=bar-float(row['new']),source=row['source'],licence=row['licence'],sha256=hashlib.sha256((take/(n+'.csv')).read_bytes()).hexdigest()),indent=2)+'\n')
        previous=current
        fl.log(str(w),'cycle kept%d quenches%d fresh%d accepted_sources%d rejected_sources%d dealt%s elapsed%.1fs'%(len(keep),len(qj),len(fj),len(audit.proofs),len(audit.rejected),got,time.time()-t0))
        if time.time()-lastcheck>=600:
            state('CHECK handoff-r24.log and all live take/near folders read. Current n='+','.join(sorted(current))+'; workers remain3/2.');lastcheck=time.time()
        if a.once:break
        end=min(t0+a.every,a.deadline)
        while time.time()<end and not (w/'STOPLOOP').exists():time.sleep(min(5,end-time.time()))
    state('FINISH collector cycle loop. Remote workers keep their common deadline. Final cleanup remains with the deadline guard.')

if __name__=='__main__':main()
