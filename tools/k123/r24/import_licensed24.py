import pathlib,json,csv,sys,shutil,subprocess,time,hashlib
from provenance24 import W,S,key
sys.path.insert(0,str(W/'lane'));import methods_lp as m
D=W/'licensed365';D.mkdir(exist_ok=True);r=json.load(open(W/'cc0/join/result.json'));pool='licensed365';shutil.copy(W/'cc0/join/licensedjoin.csv',D/(pool+'.csv'));manifest={}
for n,p,recipe in [(365,W/'cc0/rebuild365/365-licensed-kick.csv','rigidsoft_band.fault BR8:14, 300s midm kick seed19, row flips and fq'),(790,W/'cc0/join/790-licensed.csv','forensics_rect.py opposite rectangle windows from public123 and the licensed365 reconstruction, then fq')]:
 src='samanyu1808/sis-final-packings :: data.zip!submission.csv, CC0: Public Domain; '+recipe+'; actual public input '+str(W/'cc0/365.csv')+' and '+str(W/'cc0/123.csv')+'; transformation evidence '+str(W/'cc0/rebuild365/kick-result.json')+' and '+str(W/'cc0/join/result.json')
 meta=dict(n=n,source=src,licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no',parents=[str(W/'cc0/365.csv'),str(W/'cc0/123.csv')]);pathlib.Path(str(p)+'.json').write_text(json.dumps(meta,indent=2));manifest[str(n)]=dict(clean=True,n=n,origin=str(p),evidence=str(p)+'.json',source=src,licence=meta['licence'],sha256_geometry=key(n,m.load(str(p),{n})[n]))
 out=W.parent/'near'/f'{n}-cc0-rebuilt.csv';shutil.copy(p,out);pathlib.Path(str(out)+'.json').write_text(json.dumps(meta,indent=2))
 msg=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: licensed CC0 reconstruction n={n}, side={m.side(m.load(str(p),{n})[n]):.15g}, only actual publicCC0 inputs and own transformations. No GitHub seed input. Complete source sidecar, {out}\n'
 with open(S/'handoff-r24.log','a') as f:f.write(msg)
 with open(W.parent/'STATE.txt','a') as f:f.write(msg)
(D/('sources-'+pool+'.json')).write_text(json.dumps(manifest,indent=2));shutil.copy(W/'bars.tsv',D/('bars-'+pool+'.tsv'))
records=[];O=D/'remoteout';O.mkdir(exist_ok=True)
for i in range(2):
 raw=W/'cc0/join'/f'quench{i}'/'raw';paths=list(raw.glob('*.csv'))
 if not paths:continue
 start=pathlib.Path(r['starts'][i]);tag=start.stem.split('581-join-')[1];dest=O/f'{pool}-581-{tag}'/'raw';dest.mkdir(parents=True,exist_ok=True)
 for p in paths:shutil.copy(p,dest/p.name)
 side=min(m.side(m.load(str(p),{581})[581]) for p in paths)
 records.append(dict(n=581,tag=tag,pool=pool,worker='j22licensed',bar=24.6066,side=side,raw=len(paths),code=0,licensed_reconstruction=True,source=dict(public='samanyu1808/sis-final-packings',licence='CC0: Public Domain'),time=time.strftime('%H:%M:%SZ',time.gmtime())))
(D/'licensed-records.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in records));subprocess.run(['rsync','-e','ssh -S /tmp/squares-k123-r24-ssh','-az',str(O)+'/','boxE:scratch/squares-k123/out/j22licensed/'],check=True);subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r24-ssh','-q',str(D/'licensed-records.jsonl'),'boxE:scratch/squares-k123/'],check=True);subprocess.run(['ssh','-S','/tmp/squares-k123-r24-ssh','boxE','cd $SCRATCH/squares-k123 && cat licensed-records.jsonl >> out/j22licensed/done.jsonl'],check=True);print('actual licensed join records',[(q['tag'],q['side']) for q in records])
