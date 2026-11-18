"""Recut source-complete returned geometry into fresh corner and far-zone modules."""
import csv,datetime,hashlib,json,math,os,pickle,subprocess,sys,time,traceback
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H)]
import coordinator as C
from provenance import pin
W=Path(C.WORK);STATE=W/'feedback-final-state.json';END=float((W/'box/search-deadline').read_text())
def main():
 seen=json.loads(STATE.read_text())if STATE.exists()else{}
 while time.time()<END:
  try:
   bars=C.bar();files=[]
   for p in W.glob('boxcopy/*/final/*.json'):
    j=json.loads(p.read_text());n=j['n']
    if j.get('control_only')or not j.get('certified_file_quench',{}).get('completed'):continue
    if not j.get('whole_layout_follow'):continue
    data=p.with_suffix('.csv').read_bytes();sha=hashlib.sha256(data).hexdigest();key=str(n)+sha
    if key in seen:continue
    k=j.get('source_kick',{});side=j.get('built',float('inf'))
    if k.get('end')is not None:side=min(side,k['end'])
    if side>(1+bars[n])*math.sqrt(n)+.0002:continue
    if not(k.get('start',side)-side>1e-6 or side<(1+C.H[n])*math.sqrt(n)-1e-10*math.sqrt(n)):continue
    files.append((n!=805,side-(1+bars[n])*math.sqrt(n),p,j,key))
   for _,margin,p,j,key in sorted(files,key=lambda x:(x[0],x[1]))[:3]:
    if key in seen:continue
    n=j['n'];packing=C.M.np.asarray(C.M.read_layouts(str(p.with_suffix('.csv')))[n],float);cut,reason=C.M.cut(packing,n)
    if cut is None:seen[key]=dict(n=n,status='unreadable',reason=reason);C.state('SCREEN returned geometry '+str(p)+' '+str(reason));continue
    meta=C.manifest(j);record=C.full_admission(str(p.with_suffix('.csv')),n,meta)
    if record is None:continue
    _,fr,score,_=C.cert_cache.certify(str(p.with_suffix('.csv')),n)
    if fr is None:continue
    snapshot=W/'donors'/f'{n}-feedback-{key[3:15]}.csv';C.write(str(snapshot),fr)
    sha=hashlib.sha256(snapshot.read_bytes()).hexdigest();short,licence=pin(meta['source']+'; full-input source walk '+record['source'],meta['licence'])
    source=f'{snapshot} immutable sha256 {sha}; '+short
    if not C.clean(source,licence):C.state('DEFER returned module record '+str(p));continue
    snapshot.with_suffix('.json').write_text(json.dumps(dict(meta,source=source,licence=licence,feedback_original=str(p.with_suffix('.csv')),feedback_original_sha256=hashlib.sha256(p.with_suffix('.csv').read_bytes()).hexdigest())))
    cut,reason=C.M.cut(C.M.np.asarray(C.M.read_layouts(str(snapshot))[n],float),n)
    if cut is None:seen[key]=dict(n=n,status='uncut after certification',reason=reason);continue
    mods=C.M.modules_of(cut,source,licence,'r31feedback'+sha[:12])
    packet=W/'donors'/f'r31-live-feedback-{n}-{sha[:12]}.pkl';pickle.dump(dict(mods=mods,lens={},origin='certified whole-return recut after full source admission'),packet.open('wb'))
    for host,_ in C.HOSTS:subprocess.run(['rsync','-a',str(packet),host+':scratch/squares-stair-c/inbox/'],capture_output=True,timeout=40,check=True)
    seen[key]=dict(n=n,status='staged',side=(1+score)*math.sqrt(n),sha256=sha,source=str(p),packet=str(packet),modules=[q['id']for q in mods])
    C.state(f'FEEDBACK certified returned n={n} side{(1+score)*math.sqrt(n)} sha{sha} into{len(mods)} module states on all three serial workers; source full admission passed. Log worker.log; deadline00:15Z.')
    print('FEEDBACK',n,len(mods),sha,flush=True)
   temp=STATE.with_suffix('.tmp');temp.write_text(json.dumps(seen,indent=2));temp.replace(STATE)
  except Exception:traceback.print_exc()
  time.sleep(45)
if __name__=='__main__':main()
