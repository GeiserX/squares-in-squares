"""Try contact LP on the closest certified bar-input result, then quench its certificate."""
import csv,hashlib,json,math,os,subprocess,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import methods_lp as M
import floatsafe as F

def write(path,n,P):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w')as h:
        w=csv.writer(h);w.writerow(['n','square_id','x','y','angle'])
        w.writerows((n,k,repr(float(x)),repr(float(y)),repr(float(a)))for k,(x,y,a)in enumerate(P))

def main():
    n=int(sys.argv[1])if len(sys.argv)>1 else 812
    out=Path(sys.argv[2]if len(sys.argv)>2 else'lp-bridge');out.mkdir(exist_ok=True)
    P=M.load('control975.csv',{975})[975];initial=M.side(P)
    Q=P.copy();centre=Q[:,:2].mean(0);Q[:,:2]=centre+(Q[:,:2]-centre)*1.0001
    loose=M.side(Q);Q,side,steps=M.slp(Q,iters=40)
    assert loose-side>.001 and side<=initial+1e-5,(initial,loose,side)
    broken=Q.copy();broken[1]=broken[0];assert M.min_gap(broken)<-.99
    control=dict(passed=True,initial=initial,inflated=loose,result=side,steps=steps,gap=M.min_gap(Q))
    (out/'control.json').write_text(json.dumps(control,indent=2));print('CONTROL contact LP975',json.dumps(control),flush=True)
    source=Path(f'lp-input/{n}.csv');meta=json.load(open(source.with_suffix('.json')))
    P=M.load(str(source),{n})[n];start=M.side(P);t=time.time();Q,side,steps=M.slp(P,iters=60)
    raw=out/f'{n}-raw.csv';write(raw,n,Q)
    rows=list(csv.DictReader(open(raw)));_,certified,score,why=F.work((n,rows));assert certified is not None,why
    cert=out/f'{n}-cert.csv'
    with cert.open('w')as h:
        w=csv.DictWriter(h,['n','square_id','x','y','angle']);w.writeheader();w.writerows(certified)
    result=dict(n=n,start=start,lp_side=side,certified_side=(1+score)*math.sqrt(n),steps=steps,seconds=time.time()-t,input_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (out/'receipt.json').write_text(json.dumps(result,indent=2))
    meta.update(built=result['certified_side'],predicted=result['certified_side'],whole_layout_follow=True,whole_kick=False,after_kick=True,lp_receipt=result)
    meta.pop('source_kick',None);cert.with_suffix('.json').write_text(json.dumps(meta))
    subprocess.run([sys.executable,'-I','quench22.py',str(cert),f'final/{n}-contact-lp.csv'],check=True)
    print('CONTACT LP'+str(n),json.dumps(result),flush=True)

if __name__=='__main__':main()
