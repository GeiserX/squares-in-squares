"""Build source-pinned native module joins from six changed owned layouts."""
import csv,hashlib,json,math,os,pickle,sys,time
from pathlib import Path
import numpy as np
import modules as M
import methods_lp as L
import classfill_finish as F

B=Path.cwd()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix(p.suffix+'.tmp')
 with q.open('wb') as h:pickle.dump(x,h)
 q.replace(p)
def pool(j):
 mods=[];layouts=[]
 for donor in j['donors']:
  path=B/donor['remote'];assert sha(path)==donor['sha256'],'changed donor bytes'
  n=donor['n'];d,why=M.cut(M.read_layouts(str(path))[n],n);assert d is not None,(n,why)
  src=donor['local']+' immutable sha256 '+donor['sha256']+'; '+donor['source']
  q=M.modules_of(d,src,donor['licence'],'cj33');twins,ids=M.slid(d,q)
  for x in q+twins:x['ours']=True
  mods+=q+twins
  layouts.append(dict(n=n,tag='cj33',f=d['f'],m=d['m'],c1=d['c1'],c2=d['c2'],s1=d['s1'],s2=d['s2'],ids=[x['id'] for x in q],ids_slide=ids,err1=d['arm'][1]['err'],err2=d['arm'][2]['err']))
 return dict(mods=mods,layouts=layouts)
def config(j):
 M.GRID=np.array(j['grid'],float);M.SLIDE=bool(j.get('slide',True))
 if j.get('exact_native_grid'):
  M.FF=np.unique(np.r_[M.FF,M.GRID]);M._PIT.clear()
def main(j,fq,deadline):
 config(j);out=B/'out'/('compose-'+j['tag']);out.mkdir(exist_ok=True)
 op=j['operation']
 if op=='quench-existing':
  src=B/j['raw_input'];assert sha(src)==j['raw_sha256'],'changed constructed bytes'
  n=int(j['raw_n']);meta=json.loads(src.with_suffix('.json').read_text()) if src.with_suffix('.json').exists() else {}
  dest=out/'raw'/(str(n)+'-'+j['tag']+'.csv');dest.parent.mkdir(exist_ok=True)
  cert=F.certify(src,n);assert cert,'constructed input failed certification';F.write(dest,cert[1])
  F.finish_quench(n,dest,cert[0],fq,deadline,dest.parent)
  final=F.certify(dest,n);assert final,'constructed quench failed certification';F.write(dest,final[1]);side=(1+final[0])*n**.5
  if 'expected_side' in j:assert side<=j['expected_side'],side
  meta.update(n=n,certified_side=side,quench_input_sha256=j['raw_sha256'],construction_job=j['tag'])
  dest.with_suffix('.json').write_text(json.dumps(meta,indent=1)+'\n')
  result=dict(passed=True,n=n,certified_side=side,sha256=sha(dest));(out/'quench-existing.json').write_text(json.dumps(result,indent=1)+'\n');print('COMPOSE_EXISTING_QUENCH_DONE',result,flush=True);return 0
 if op=='control':
  p=pool(j);dump(out/'pool.pkl',p);by={q['id']:dict(id=q['id'],q=q) for q in p['mods']}
  own=next(x for x in p['layouts'] if x['n']==934);ids=own['ids_slide'];got=None
  for up in (0.,1e-4,3e-4,1e-3):
   P,why=M.assemble(None,934,by[ids[2]],by[ids[0]],by[ids[1]],own['s1'],own['s2'],own['f']+up)
   if P is None:continue
   raw=out/'934-control.csv';M.write_layout(str(raw),934,P);cert=F.certify(raw,934)
   if cert and (1+cert[0])*934**.5<math.isqrt(933)+own['f']+0.0011:got=up;break
  assert got is not None,'934 self reconstruction failed: '+str(why)
  bad,reason=M.assemble(None,935,by[ids[2]],by[ids[0]],by[ids[1]],own['s1'],own['s2'],own['f']+got)
  assert bad is None and 'holds 934 squares' in reason,reason
  control=pickle.load(open(B/'control-zone.pkl','rb'));expected=float((B/'control-zone-own.txt').read_text());table=M.tabulate(control)
  assert abs(table['own']-expected)<1e-8,(table['own'],expected)
  result=dict(passed=True,self934_up=got,wrong_count=reason,table703_own=table['own'],expected=expected,modules=len(p['mods']))
  (out/'control.json').write_text(json.dumps(result,indent=1)+'\n');print('COMPOSE33_POSITIVE_CONTROL_PASS',result,flush=True);return 0
 p=pickle.load(open(B/'compose/library.pkl','rb'))
 if op=='self-control':
  n=int(j['control_n']);layout=next(x for x in p['layouts'] if x['n']==n);ids=layout['ids_slide'];by={q['id']:dict(id=q['id'],q=q) for q in p['mods']};got=None
  for up in (0.,1e-4,3e-4,1e-3):
   P,why=M.assemble(None,n,by[ids[2]],by[ids[0]],by[ids[1]],layout['s1'],layout['s2'],layout['f']+up)
   if P is None:continue
   raw=out/(str(n)+'-self-control.csv');M.write_layout(str(raw),n,P);cert=F.certify(raw,n)
   if cert and (1+cert[0])*n**.5<layout['m']+layout['f']+.0011:got=up;break
  assert got is not None,'native self reconstruction failed: '+str(why)
  wrong,reason=M.assemble(None,n+1,by[ids[2]],by[ids[0]],by[ids[1]],layout['s1'],layout['s2'],layout['f']+got)
  assert wrong is None and 'holds '+str(n)+' squares' in reason,reason
  result=dict(passed=True,n=n,self_up=got,certified_side=(1+cert[0])*n**.5,wrong_count=reason)
  (out/'self-control.json').write_text(json.dumps(result,indent=1)+'\n');print('COMPOSE_SELF_CONTROL_PASS',result,flush=True);return 0
 if op=='table':
  q=next(q for q in p['mods'] if q['id']==j['module_id']);t=time.time();table=M.tabulate(q);dump(out/'table.pkl',dict(id=q['id'],table=table,pool_sha256=sha(B/'compose/library.pkl')))
  (out/'table.json').write_text(json.dumps(dict(id=q['id'],seconds=time.time()-t,has_own=table.get('own') is not None),indent=1)+'\n');print('COMPOSE_TABLE_DONE',q['id'],time.time()-t,flush=True);return 0
 if op=='anchor':
  layout=next(x for x in p['layouts'] if x['n']==j['anchor_n']);by={q['id']:q for q in p['mods']};ids=layout['ids_slide'];corner=by[ids[2]]
  table=np.full((len(M.COST),2,len(M.GRID)),np.nan);records=[]
  for i,f in enumerate(M.GRID):
   if not any(abs(float(f)-(layout['f']+delta))<1e-10 for delta in (.0002,.001,.003)):continue
   f=float(f);a=M.far_at(by[ids[0]],f);b=M.far_at(by[ids[1]],f)
   if a is None or b is None:continue
   cy=layout['m']+f-a[0]-layout['s1']*M.pitch(corner['c1'],f);cx=layout['m']+f-b[0]-layout['s2']*M.pitch(corner['c2'],f)
   margin=float(j.get('anchor_margin',1e-6))
   state=M.corner_at(corner,f,cy-margin,cx-margin)
   if state is None:continue
   y,x,P=state;table[:,0,i]=y;table[:,1,i]=x;records.append(dict(f=f,y=y,x=x,cap_y=cy,cap_x=cx,requested_margin=margin))
  variant=dict(corner,id=corner['id']+'.native',ours=True)
  result=dict(id=variant['id'],module=variant,table=dict(id=variant['id'],own=records,tab=table),records=records,grid=M.GRID.tolist(),pool_sha256=sha(B/'compose/library.pkl'))
  dump(out/'anchor.pkl',result);(out/'anchor.json').write_text(json.dumps(dict(id=variant['id'],states=len(records),records=records),indent=1)+'\n');print('COMPOSE_ANCHOR_DONE',variant['id'],records,flush=True);return 0
 if op=='model-control':
  n=int(j.get('control_n',934));lib=M.Library('compose');layout=next(x for x in p['layouts'] if x['n']==n);ids=layout['ids_slide'];corner=lib.byid[ids[2]+'.native'];a=lib.byid[ids[0]];b=lib.byid[ids[1]]
  fit=lib.fit(corner,a,b,layout['m'],layout['s1'],layout['s2']);assert fit and fit[0]<layout['f']+.0005,fit
  P,why=M.assemble(lib,n,corner,a,b,layout['s1'],layout['s2'],fit[0]+1e-5);assert P is not None,why
  raw=out/(str(n)+'-model-control.csv');M.write_layout(str(raw),n,P);cert=F.certify(raw,n);assert cert,'anchored model could not build its own control'
  result=dict(passed=True,n=n,source_f=layout['f'],predicted_f=fit[0],delta=fit[0]-layout['f'],certified_side=(1+cert[0])*n**.5)
  (out/'model-control.json').write_text(json.dumps(result,indent=1)+'\n');print('COMPOSE_MODEL_CONTROL_PASS',result,flush=True);return 0
 if op=='queue':
  candidates=[int(r['n']) for r in csv.DictReader(open('bar.csv')) if int(r['n'])>=300 and float(r['L'])-math.isqrt(int(r['n'])-1)+0.0005>=M.GRID[0]]
  ns=out/'ns.txt';ns.write_text(''.join(str(n)+'\n' for n in candidates))
  M.cmd_queue(['compose','bar.csv',str(out/'queue.tsv'),'--top','3','--slack','0.0005','--depth','0.04','--min-margin','-0.01','--ns',str(ns)])
  return 0
 if op!='build':raise ValueError('unknown compose operation '+op)
 r=j['recipe'];n=int(r['n']);name=str(n)+'-'+j['tag'];rawdir=out/'raw';rawdir.mkdir(exist_ok=True)
 M.cmd_job(['compose',str(rawdir),'bar.csv',name,str(n),r['corner'],r['far1'],r['far2'],str(r['stacks1']),str(r['stacks2']),str(r['f']),'--squeeze','slp'])
 raw=rawdir/(name+'.csv')
 if not raw.exists():return 0
 cert=F.certify(raw,n)
 if cert is None:print('COMPOSE_CERT_REFUSED',n,flush=True);return 0
 F.write(raw,cert[1]);side=(1+cert[0])*n**.5;bar={int(x['n']):float(x['L']) for x in csv.DictReader(open('bar.csv'))}[n]
 meta=json.load(open(raw.with_suffix('.json')));meta['slide']=M.SLIDE;meta['exact_native_grid']=bool(j.get('exact_native_grid'));meta['generator']='classfill native cross-layout module join';meta['generator_sha256']=sha(__file__)
 if side>bar+1e-10 and side<bar+0.0005 and time.time()<deadline-60:
  F.finish_quench(n,raw,cert[0],fq,deadline,rawdir)
  final=F.certify(raw,n)
  if final:F.write(raw,final[1]);side=(1+final[0])*n**.5
 meta['certified_side']=side;meta['live_bar']=bar;meta['construction_job']=j['tag'];raw.with_suffix('.json').write_text(json.dumps(meta,indent=1)+'\n')
 print('COMPOSE_BUILD_DONE',n,'side',repr(side),'margin',repr(bar-side),flush=True);return 0
