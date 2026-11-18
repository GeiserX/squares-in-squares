import pathlib,json,csv,shutil,time,os
W=pathlib.Path(__file__).resolve().parent;T=W.parent;S=T.parent;csv.field_size_limit(1<<28)
rows=list(csv.DictReader(open(T/'take.tsv'),delimiter='\t'));bad={699,932};D=W/'withdrawn-seed503';D.mkdir(exist_ok=True)
for row in rows:
 n=int(row['n'])
 if n not in bad:continue
 p=T/f'{n}.csv';shutil.copy(p,D/p.name);(D/f'{n}.csv.json').write_text(json.dumps(row));p.unlink()
 line=time.strftime('%FT%TZ',time.gmtime())+f' k123 -> all: WITHDRAW n={n}, original seed503 in its walked ancestry has prvsiyan share1.0 within1e-3. Exact original merged0 source selected by assembler seedsrc; this is the share rule, not a Samanyu-name refusal. Drop descendants of {p}; evidence {W}/seed-ancestors27.json; archived {D}/{n}.csv\n'
 for log in [S/'handoff-r29.log',T/'STATE.txt']:
  with log.open('a') as f:f.write(line)
with (T/'take.tsv.tmp').open('w') as f:
 wr=csv.DictWriter(f,['n','held','new','gain','source','licence'],delimiter='\t');wr.writeheader();wr.writerows(r for r in rows if int(r['n'])not in bad)
(T/'take.tsv.tmp').replace(T/'take.tsv')
state=json.load(open(W/'collect-state.json'))
for k,r in state.items():
 if r.get('status')=='published' and r['n'] in bad:r['status']='withdrawn-original-seed503-share'
(W/'collect-state.json').write_text(json.dumps(state,indent=2))
# Near files of these published recipes are no longer available as starts.
for p in (T/'near').glob('*.csv'):
 if not any(p.name.startswith(str(n)+'-') for n in bad):continue
 shutil.move(str(p),D/p.name)
 for q in [pathlib.Path(str(p)+'.json'),p.with_suffix('.json')]:
  if q.exists():shutil.move(str(q),D/q.name)
print('retained',[int(r['n']) for r in rows if int(r['n'])not in bad],flush=True)
