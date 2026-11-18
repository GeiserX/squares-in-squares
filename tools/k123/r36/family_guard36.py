"""Close a producer's old input pair at a certified count, while new geometry stays eligible."""
from pathlib import Path
import json,hashlib,csv,re,os,time
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent

def family_key(n,geometries):
 return hashlib.sha256(json.dumps([int(n),*sorted(geometries)],separators=(',',':')).encode()).hexdigest()

def job_family(key,n):
 m=re.search(r'-(\d+r?-\d+r?-j\d+-\d+-s-?\d+)$',key)
 if not m:return None
 prefix=key[:m.start()];worker,pool=prefix.split('-',1);tag=m[1];numbers=re.match(r'(\d+)r?-(\d+)r?-j',tag).groups()
 ps=[W/pool/('sources-'+pool+'.json'),W/('sources-'+pool+'.json'),W/'boxE-final'/('sources-'+pool+'.json')];p=next((p for p in ps if p.is_file()),None)
 if not p:return None
 meta=json.load(open(p));geometries=[meta[z]['sha256_geometry'] for z in numbers]
 return family_key(n,geometries),{'n':int(n),'geometries':geometries,'pool':pool,'producer_job':key}

def refresh():
 csv.field_size_limit(1<<28);p=W/'closed-families36.json';closed=json.load(open(p)) if p.exists() else {};before=len(closed)
 state=json.load(open(W/'collect-state.json')) if (W/'collect-state.json').exists() else {}
 for key,row in state.items():
  if row.get('status')!='published':continue
  item=job_family(row.get('producer_job',key),row['n'])
  if item:closed.setdefault(item[0],{**item[1],'reason':'own native certificate','time':time.strftime('%FT%TZ',time.gmtime())})
 near=json.load(open(W/'near-state36.json')) if (W/'near-state36.json').exists() else {}
 for table in S.glob('take-*-r36/take.tsv'):
  if table.parent==T:continue
  for row in csv.DictReader(open(table),delimiter='\t'):
   try:n=int(row['n'])
   except (ValueError,KeyError):continue
   for key,j in near.items():
    if j.get('status')!='published' or j.get('n')!=n or not j.get('path') or j['path'].replace(str(S)+'/','') not in row.get('source',''):continue
    item=job_family(key,n)
    if item:closed.setdefault(item[0],{**item[1],'reason':'peer certificate from this near family','peer':table.parent.name,'time':time.strftime('%FT%TZ',time.gmtime())})
 tmp=p.with_name(p.name+'.'+str(os.getpid())+'.tmp');tmp.write_text(json.dumps(closed));tmp.replace(p)
 if len(closed)>before:
  with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA CLOSE producer input pairs: '+str(len(closed)-before)+' new, '+str(len(closed))+' total; new geometry hashes stay eligible. deadline23:45Z\n')
 return closed
if __name__=='__main__':print(json.dumps({'closed_families':len(refresh())}))
