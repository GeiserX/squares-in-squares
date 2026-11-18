import pathlib,json,csv,shutil,sys,subprocess,time
from provenance24 import W,S,key
from eligible24 import BARS
sys.path.insert(0,str(W/'lane'));import methods_lp as m
csv.field_size_limit(20000000);pool='licensed581parts';D=W/pool;D.mkdir(exist_ok=True);r581=next(r for r in csv.DictReader(open(W.parent/'take.tsv'),delimiter='\t') if r['n']=='581');P=m.load(str(W/'cc0/581-certified.csv'),{581})[581];manifest={'581':dict(clean=True,n=581,origin=str(W/'cc0/581-certified.csv'),source=r581['source'],licence=r581['licence'],sha256_geometry=key(581,P))};public=json.load(open(W/'cc0/123.csv.json'));P123=m.load(str(W/'cc0/123.csv'),{123})[123];manifest['123']=dict(clean=True,n=123,origin=str(W/'cc0/123.csv'),source=public['source'],licence=public['licence'],sha256_geometry=key(123,P123))
with open(D/(pool+'.csv'),'w') as f:
 wr=csv.writer(f);wr.writerow(['n','square_id','x','y','angle'])
 for n,A in [(581,P),(123,P123)]:wr.writerows((n,i,*row) for i,row in enumerate(A))
(D/('sources-'+pool+'.json')).write_text(json.dumps(manifest,indent=2));shutil.copy(W/'bars.tsv',D/('bars-'+pool+'.tsv'));records=[]
for info in json.load(open(W/'cc0/parts/result.json')):
 n=info['n'];src=W/'cc0/parts'/pathlib.Path(info['output']).name;meta=info['composition_meta'];donors=sorted({int(meta[z]['source'][1]) for z in ['A','B']});tag=f'cc0-rect{n}';dest=D/'remoteout'/f'{pool}-{n}-{tag}'/'raw';dest.mkdir(parents=True,exist_ok=True);shutil.copy(src,dest/f'{n}-cc0-parts.csv')
 recipe='forensics_rect.py: two opposite rectangle windows from actual licensed581/publicCC0 n123, then fq; actual composition '+json.dumps(meta,separators=(',',':'))+'; transform evidence '+str(W/'cc0/parts/result.json')
 records.append(dict(n=n,tag=tag,pool=pool,worker='j22licensed',bar=BARS[n],side=float(m.side(m.load(str(src),{n})[n])),raw=1,code=0,licensed_reconstruction=True,source=dict(recipe_text=recipe,donors=donors),time=time.strftime('%H:%M:%SZ',time.gmtime())))
 out=W.parent/'near'/f'{n}-cc0-parts.csv';shutil.copy(src,out);pathlib.Path(str(out)+'.json').write_text(json.dumps(dict(n=n,source=recipe+'; licensed parent '+str(W/'cc0/581-certified.csv'),licence='CC0: Public Domain; own mathematical transformations; Samanyu-dev seed ancestry: no'),indent=2))
 msg=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: fresh CC0-only rectangle n={n}, side={records[-1]["side"]:.15g}, required certification pending. Actual licensed581 parent, complete source sidecar, {out}\n'
 with open(S/'handoff-r24.log','a') as f:f.write(msg)
(D/'records.jsonl').write_text(''.join(json.dumps(q)+'\n' for q in records));subprocess.run(['rsync','-e','ssh -S /tmp/squares-k123-r24-ssh','-az',str(D/'remoteout')+'/','boxE:scratch/squares-k123/out/j22licensed/'],check=True);subprocess.run(['scp','-o','ControlPath=/tmp/squares-k123-r24-ssh','-q',str(D/'records.jsonl'),'boxE:scratch/squares-k123/parts-records.jsonl'],check=True);subprocess.run(['ssh','-S','/tmp/squares-k123-r24-ssh','boxE','cd $SCRATCH/squares-k123 && cat parts-records.jsonl >> out/j22licensed/done.jsonl'],check=True);print('actual licensed composition records',[(q['n'],q['side']) for q in records])
