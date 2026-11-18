from pathlib import Path
import csv,json,sys
csv.field_size_limit(16000000)
W=Path(__file__).parent;R=W/'boxE29';rows=[]
for p in R.glob('done/*.json'):
 d=json.load(open(p))
 if 'start_side' not in d or d.get('tag','').startswith('control'):continue
 rows.append(dict(kind='kick',n=d['n'],run=d['tag'],seed=d['seed'],tries=d['tries'],start=d['start_side'],best=d['best'],bar=d['bar'],side_gain=d['start_side']-d['best'],seconds=d['seconds_used'],source=d['source'],licence=d['licence']))
for p in R.glob('designs/*/builds/*.json'):
 if p.parent.parent.name.startswith('control'):continue
 d=json.load(open(p));b=d.get('built');rows.append(dict(kind='build',n=d['n'],run=p.parent.parent.name+'/'+p.stem,seed='',tries=1,start=d.get('start',''),best=b,bar=d.get('held',''),side_gain='' if b is None else d['start']-b,seconds=sum(d.get('seconds',{}).values()),source=json.dumps(d.get('modules',[])),licence='; '.join(sorted({m['licence'] for m in d.get('modules',[])}))))
cols=['kind','n','run','seed','tries','start','best','bar','side_gain','seconds','source','licence'];p=Path(sys.argv[1]) if len(sys.argv)>1 else W/'results-current.tsv'
with p.open('w',newline='') as f:
 cw=csv.DictWriter(f,fieldnames=cols,delimiter='\t');cw.writeheader();cw.writerows(sorted(rows,key=lambda r:(r['kind'],int(r['n']),r['run'],r['seed'])))
print('measurements',len(rows),'kicks',sum(r['kind']=='kick' for r in rows),'builds',sum(r['kind']=='build' for r in rows))

import os
sys.stdout.flush();sys.stderr.flush();os._exit(0)
