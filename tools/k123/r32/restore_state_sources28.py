from pathlib import Path
import csv,json,fcntl,sys,time
W=Path(__file__).resolve().parent;sys.path.insert(0,str(W));csv.field_size_limit(20000000)
from compact_source28 import source
with (W/'collect.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);T=W.parent;rows={int(r['n']):r for r in csv.DictReader((T/'take.tsv').open(),delimiter='\t')};d=json.loads((W/'collect-state.json').read_text());fixed=[]
 for key,r in d.items():
  if r.get('status')!='published' or r.get('n') not in rows or abs(r.get('score',0)-float(rows[r['n']]['new']))<1e-15:continue
  archive=W/'certs'/key/'final/take.tsv'
  if not archive.exists():continue
  record=next((z for z in csv.DictReader(archive.open(),delimiter='\t') if int(z['n'])==r['n']),None)
  if not record:continue
  assert abs(float(record['new'])-r['score'])<1e-15
  r['source']=source(record['source']);r['original_numeric_source_record']=str(archive);fixed.append(key)
 (W/'collect-state.json.tmp').write_text(json.dumps(d,indent=2));(W/'collect-state.json.tmp').replace(W/'collect-state.json')
 with (T/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' boxA RESTORE historical published-state source text from its exact original certificate for{fixed}; metadata enrichment now rebinds only byte-identical certificates. Current take bytes, source, licence and score are unchanged. Deadline17:15Z.\n')
 print('restored state records',fixed,flush=True)
