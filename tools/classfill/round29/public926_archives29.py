from common29 import *
import zipfile,io
from light29 import load,key
from prvsim29 import check
out=[]
for ref,ns in [('jazivxt/boxed-in',[696]),('jonathan1506/50-top-2-6-22-1793-fault-dp-fq-stretch',[750,923])]:
 variants={n:[] for n in ns}
 for kind in ['nb','ds']:
  for folder in sorted(S.glob('harvest*/'+kind+'/'+ref.replace('/','__'))):
   files=list(folder.glob('submission.csv'))+list(folder.glob('data.zip'))
   for archive in files:
    sources=[]
    if archive.suffix=='.zip':
     z=zipfile.ZipFile(archive);sources=[(name,io.TextIOWrapper(z.open(name),encoding='utf-8-sig')) for name in z.namelist() if name=='submission.csv']
    else:sources=[(archive.name,archive.open(encoding='utf-8-sig'))]
    for name,stream in sources:
     rr=csv.DictReader(stream)
     if not {'x','y','angle'}<=set(rr.fieldnames or []):continue
     selected={n:[] for n in ns}
     for row in rr:
      n=int(row['n']) if 'n' in row else int(row['id'].split('_')[0])
      if n in selected:selected[n].append(dict(n=str(n),square_id=str(len(selected[n])),x=row['x'].lstrip('s'),y=row['y'].lstrip('s'),angle=row['angle'].lstrip('s')))
     for n,rows_ in selected.items():
      assert len(rows_)==n,(archive,n,len(rows_));folder_out=W/'926-public-rows';folder_out.mkdir(exist_ok=True);p=folder_out/f'{n}-{hashlib.sha256((str(archive)+name).encode()).hexdigest()[:12]}.csv'
      with p.open('w',newline='')as f:w=csv.DictWriter(f,fieldnames=CSV);w.writeheader();w.writerows(rows_)
      variants[n].append(dict(row=blob(p),archive=blob(archive),notice=blob(folder/'meta.json'),geometry=key(load(p,{n})[n],10),share=check(p,n)['share']))
     stream.close()
 for n,items in variants.items():
  geometries={v['geometry'] for v in items};out.append(dict(ref=ref,n=n,versions=len(items),unique_geometries=len(geometries),variants=items));print(ref,n,len(items),len(geometries),[(v['share'],v['archive']['path'])for v in items],flush=True)
atomic(W/'926-public-archive-audit.json',out)
