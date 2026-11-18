"""Queue three bounded kicks for an unclaimed new certified lane layout."""
from pathlib import Path
import sys,json,csv,hashlib,time,subprocess,shutil,io,re
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
from provenance24 import mlp,credit
SSH=['ssh','-S','/tmp/squares-k123-r34-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh'];statepath=W/'kickfeed30.json';seen=json.load(statepath.open()) if statepath.exists() else {};log=(S/'handoff-r34.log').read_text()
for row in csv.DictReader((T/'take.tsv').open(),delimiter='\t'):
 if time.time()>float((W/'deadline').read_text())-1200:break
 n=int(row['n']);p=T/f'{n}.csv';
 if time.time()-p.stat().st_mtime<600:continue
 raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest();identity=f'{n}-{digest}'
 if identity in seen:continue
 recent=[]
 for l in log.splitlines():
  try:
   if time.time()-__import__('datetime').datetime.fromisoformat(l.split()[0].replace('Z','+00:00')).timestamp()<3600:recent.append(l)
  except (ValueError,IndexError):pass
 claimed=[l for l in recent if 'claim' in l.lower() and 'kick' in l.lower() and str(p) in l and (digest in l or digest[:16] in l) and ' k123 ->' not in l]
 if claimed:seen[identity]={'status':'claimed elsewhere','line':claimed[-1]};continue
 A=mlp.load(str(p),{n})[n];ledger=(T/'take.tsv').read_bytes();c=credit(n,A,str(p));assert c,'own source admission failed'
 assert p.read_bytes()==raw,'changed certified input while queuing'
 D=W/'input-snapshots';D.mkdir(exist_ok=True);snapshot=D/f'{n}-{digest}.csv';snapshot.write_bytes(raw);ls=hashlib.sha256(ledger).hexdigest();producer=D/(ls+'.tsv');producer.write_bytes(ledger)
 c={**c,'input_file_snapshot':str(snapshot),'input_file_sha256':digest,'input_file_mtime':p.stat().st_mtime,'input_record_snapshots':{str(T/'take.tsv'):{'snapshot':str(producer),'sha256':ls}}}
 pool='kickcert30n'+str(n)+'h'+digest[:12];D=W/pool;D.mkdir(exist_ok=True);(D/(pool+'.csv')).write_bytes(raw);(D/('sources-'+pool+'.json')).write_text(json.dumps({str(n):c}));(D/('bars-'+pool+'.tsv')).write_text((W/'bars.tsv').read_text());(D/(pool+'.json')).write_text(json.dumps({'kind':'kick-pool','tag':pool,'source':str(p),'input_sha256':digest}))
 for name in [pool+'.csv','sources-'+pool+'.json','bars-'+pool+'.tsv']:
  subprocess.run(SCP+[str(D/name),'boxE:scratch/squares-k123/'+name],check=True)
 for leg in range(3):
  tag=pool+'-leg'+str(leg);j={'kind':'verify','tag':tag,'kick_leg':True,'n':n,'pool':pool,'seed':303000+n*3+leg,'input_sha256':digest};path=D/(tag+'.json');path.write_text(json.dumps(j));subprocess.run(SCP+[str(path),'boxE:scratch/squares-k123/tasks/'+tag+'.json.tmp'],check=True);subprocess.run(SSH+['cd $SCRATCH/squares-k123 && mv tasks/'+tag+'.json.tmp tasks/'+tag+'.json'],check=True)
 seen[identity]={'status':'queued','pool':pool,'legs':3,'seconds_per_leg':300};statepath.write_text(json.dumps(seen,indent=2))
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: claims900s certified-input kick follow n={n}, three300s legs in the existing boxE scan slot, inputsha256={digest}, source {p}, receipts {D}\n'
 with (S/'handoff-r34.log').open('a') as f:f.write(line)
 with (T/'STATE.txt').open('a') as f:f.write(line.rstrip()+'; common deadline07:25Z.\n')
 print(line.strip(),flush=True)
statepath.write_text(json.dumps(seen,indent=2))
