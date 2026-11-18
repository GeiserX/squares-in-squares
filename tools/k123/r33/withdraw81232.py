from pathlib import Path
import csv,json,hashlib,fcntl,time,shutil
W=Path(__file__).resolve().parent;T=W.parent;S=T.parent;csv.field_size_limit(1<<28)
with (W/'collect.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX);p=T/'812.csv';sha=hashlib.sha256(p.read_bytes()).hexdigest();expected='76738079d602ea73f42792f7d028ed2cf23187b0ff7cd3d763718d45c2d65c42';assert sha==expected,(sha,'changed row needs a new audit')
 rows=list(csv.DictReader((T/'take.tsv').open(),delimiter='\t'));r=next(r for r in rows if r['n']=='812');D=W/'withdrawn';D.mkdir(exist_ok=True);(D/('812-'+sha+'.json')).write_text(json.dumps(r,indent=2));shutil.copy(p,D/('812-'+sha+'.csv'))
 with (T/'take.tsv.tmp').open('w') as f:
  wr=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(r for r in rows if r['n']!='812')
 (T/'take.tsv.tmp').replace(T/'take.tsv');sp=W/'collect-state.json';state=json.load(sp.open())
 for key,value in state.items():
  if value.get('n')==812 and value.get('status')=='published':value['status']='withdrawn-upstream32';value['withdrawal_reason']='stair-c exact ancestor f481913fc01ea0c1 and quench812 e056ca054f0f6889 withdrawn12:42/12:43'
 sp.with_suffix('.tmp').write_text(json.dumps(state,indent=2));sp.with_suffix('.tmp').replace(sp)
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: WITHDRAW own n=812 exact bytes sha256 {sha}, {p}; strict full walk now reaches stair-c-r32 ancestor f481913fc01ea0c1 and quench812 e056ca054f0f6889, withdrawn12:42/12:43. Dropped from take.tsv, CSV kept in place for recorded descendants. Removed gain3.926824865e-9.\n'
 with (S/'handoff-r33.log').open('a') as f:f.write(line)
 with (T/'STATE.txt').open('a') as f:f.write(line)
 print('withdrew812, numeric file preserved',sha)
