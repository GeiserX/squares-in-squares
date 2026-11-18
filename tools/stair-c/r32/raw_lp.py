"""Apply one contact LP directly to an own raw kick return before its final fq."""
import csv,hashlib,json,math,os,subprocess,sys,time
from pathlib import Path
sys.path[:0]=['lane','.']
import methods_lp as M
import stair_finesafe as F

def write(p,n,rows):
 p=Path(p);p.parent.mkdir(exist_ok=True,parents=True)
 with p.open('w')as f:
  w=csv.DictWriter(f,['n','square_id','x','y','angle']);w.writeheader();w.writerows(rows)
def main():
 n=int(sys.argv[1]);name=sys.argv[2];root=Path('raw-contact-lp')/name;root.mkdir(parents=True,exist_ok=True)
 if not Path('raw-contact-lp/control.json').exists():
  P=M.load('control975.csv',{975})[975];initial=M.side(P);Q=P.copy();centre=Q[:,:2].mean(0);Q[:,:2]=centre+(Q[:,:2]-centre)*1.0001
  loose=M.side(Q);Q,side,steps=M.slp(Q,iters=40)
  assert loose-side>.001 and side<=initial+1e-5
  bad=Q.copy();bad[1]=bad[0];assert M.min_gap(bad)<-.99
  result=dict(passed=True,initial=initial,inflated=loose,end=side,steps=steps)
  Path('raw-contact-lp/control.json').write_text(json.dumps(result));print('CONTROL raw-contact LP975',json.dumps(result),flush=True)
 meta=json.loads(Path('cert-in',name+'.json').read_text());rawdir=Path('whole-kicks')/name/'raw';options=[]
 for p in rawdir.glob('*.csv'):
  P=M.load(str(p),{n})[n];options.append((M.side(P),p,P))
 if not options:print('NO_RAW',n,flush=True);return
 start,p,P=min(options,key=lambda x:x[0]);t=time.time();Q,side,steps=M.slp(P,iters=60)
 rows=[dict(n=str(n),square_id=str(i),x=repr(float(x)),y=repr(float(y)),angle=repr(float(a)))for i,(x,y,a)in enumerate(Q)]
 _,safe,score,why=F.work((n,rows));assert safe is not None,why
 cert=root/f'{n}-cert.csv';write(cert,n,safe)
 receipt=dict(n=n,input_file=str(p),input_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),start=start,lp_side=side,certified_side=(1+score)*math.sqrt(n),steps=steps,seconds=time.time()-t)
 (root/'receipt.json').write_text(json.dumps(receipt))
 meta.update(n=n,whole_kick=False,whole_layout_follow=True,raw_contact_lp=True,lp_receipt=receipt,built=receipt['certified_side'],predicted=receipt['certified_side'])
 meta.pop('source_kick',None);meta.pop('certified_file_quench',None);cert.with_suffix('.json').write_text(json.dumps(meta))
 subprocess.run([sys.executable,'-I','quench22.py',str(cert),f'final/{n}-raw-lp-{name}.csv'],check=True)
 print('RAW_CONTACT_LP',json.dumps(receipt),flush=True)
if __name__=='__main__':main()
