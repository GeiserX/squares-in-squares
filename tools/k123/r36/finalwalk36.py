"""Reuse complete walks only for unchanged bytes and unchanged withdrawal rules."""
from pathlib import Path
import sys,csv,json,hashlib,time
W=Path(__file__).resolve().parent;T=W.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from publication_source26 import check
from policy27 import lines
stamp=hashlib.sha256(json.dumps(lines(),sort_keys=True).encode()).hexdigest();cachepath=W/'finalwalk-cache36.json';cache=json.load(open(cachepath)) if cachepath.exists() else {};result=[]
state=json.load(open(W/'collect-state.json')) if (W/'collect-state.json').exists() else {}
for r in csv.DictReader(open(T/'take.tsv'),delimiter='\t'):
 n=int(r['n']);p=T/f'{n}.csv';h=hashlib.sha256(p.read_bytes()).hexdigest();key=str(n)+'-'+h
 old=cache.get(key)
 if old and old.get('clean') and not old.get('capped') and old.get('withdrawal_stamp')==stamp:result.append({**old,'reused':True});continue
 start=time.time();j=check(p,r);unchanged=h==hashlib.sha256(p.read_bytes()).hexdigest()
 certificates=[k for k,v in state.items() if v.get('n')==n and (q:=W/'certs'/k/'final'/f'{n}.csv').is_file() and hashlib.sha256(q.read_bytes()).hexdigest()==h]
 entry={'n':n,'sha256':h,'clean':j['clean'] and bool(certificates) and unchanged,'files':j['files'],'capped':j.get('capped',False),'hits':j['hits'],'seconds':time.time()-start,'withdrawal_stamp':stamp,'certificate_keys':certificates,'unchanged':unchanged,'time':time.strftime('%FT%TZ',time.gmtime())};cache[key]=entry;result.append(entry);cachepath.write_text(json.dumps(cache));(W/'finalwalk36.json').write_text(json.dumps(result));print(json.dumps(entry),flush=True)
(W/'finalwalk36.json').write_text(json.dumps(result));assert all(r['clean'] and not r['capped'] for r in result),result
