"""Follow admitted close compositions and retry failed queue operations."""
import datetime,hashlib,importlib.util,json,sys,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('near_follow29',HERE/'follow-near.py');F=importlib.util.module_from_spec(spec);spec.loader.exec_module(F)
C=F.C
DEAD=datetime.datetime(2026,11,15,11,20,tzinfo=datetime.timezone.utc).timestamp()
STATE=Path(C.WORK)/'follow-driver-state.json'

def offer_options(n,options,seen,offer=None,log=None,deadline=DEAD):
    offer=F.offer if offer is None else offer;log=C.state if log is None else log
    prior=[v['side']for v in seen.values()if v.get('ok')and v['n']==n];attempts=0
    for side,p in sorted(options,key=lambda q:q[0]):
        if time.time()>=deadline or attempts>=2:break
        if prior and side>min(prior)-1e-7:break
        key=str(n)+hashlib.sha256(p.read_bytes()).hexdigest();previous=seen.get(key,{})
        if previous.get('ok'):break
        if previous.get('retry_at',0)>time.time():continue
        attempts+=1
        try:
            offer(p);seen[key]=dict(n=n,side=side,ok=True);return True
        except Exception as ex:
            seen[key]=dict(n=n,side=side,ok=False,reason=str(ex),retry_at=time.time()+600)
            log('DEFER own near '+str(p)+' '+str(ex))
    return False

def main():
    seen=json.loads(STATE.read_text())if STATE.exists()else{}
    while time.time()<DEAD:
        try:
            groups={};bars=C.bar()
            for p in Path(C.TAKE,'near').glob('*.csv'):
                n=int(p.name.split('-')[0]);meta=p.with_suffix('.csv.json')
                if not meta.exists():continue
                j=json.loads(meta.read_text());side=j.get('built')
                if side is not None and F.eligible(n,side-(1+bars[n])*(n**.5)):groups.setdefault(n,[]).append((side,p))
            for n,options in groups.items():offer_options(n,options,seen)
            temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(seen,indent=2));temp.replace(STATE)
        except Exception:traceback.print_exc()
        time.sleep(45)
if __name__=='__main__':main()
