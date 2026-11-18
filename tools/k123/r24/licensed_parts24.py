import pathlib,sys,subprocess,json,time

def run(j):
 R=pathlib.Path.home()/'scratch/squares-k123';sys.path.insert(0,str(R/'lane'));import methods_lp as m,family_step as fs
 from midm_scan import to_fq,from_fq,quench
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');fq=str(pathlib.Path.home()/'scratch/squares-base/fq');D=R/'out/cc0-parts';D.mkdir(exist_ok=True);(D/'tmp').mkdir(exist_ok=True);end=float((R/'deadline').read_text())
 with open(D/'compose.log','w') as h:subprocess.run([PY,'-I','lane/forensics_rect.py','details-eligible24.csv',str(D/'rect'),'--only','534,847','--no-single','--keep','12','--slack','.02','--per-n','4',str(R/'cc0/581-certified.csv'),str(R/'cc0/123.csv')],stdout=h,stderr=h,check=True,timeout=150)
 result=[]
 for n in [534,847]:
  paths=list((D/'rect').glob(f'{n}-*.csv'));print('CONTROL CC0 rectangle',n,'starts',len(paths),flush=True)
  if not paths:continue
  p=min(paths,key=lambda p:m.side(m.load(str(p),{n})[n]));P=m.load(str(p),{n})[n];s,X=to_fq(P);ss,XX=quench(fq,str(D/'tmp'),s,X,[],timeout=min(100,max(1,end-time.time())))
  if ss is not None and ss<s:s,P=ss,from_fq(XX)
  out=D/f'{n}-licensed-parts.csv';fs.write_rows(str(out),n,P);meta=json.load(open(str(p)+'.json'));info=dict(n=n,side=s,output=str(out),composition=str(p),composition_meta=meta,source='forensics_rect.py two opposite rectangle windows from actual licensed581 and actual publicCC0 n123, then fq',licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no');pathlib.Path(str(out)+'.json').write_text(json.dumps(info,indent=2));result.append(info);print('SAVED CC0 part composition',n,s,out,flush=True)
 (D/'result.json').write_text(json.dumps(result,indent=2))
