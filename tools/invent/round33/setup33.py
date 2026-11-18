import pathlib,shutil,datetime,json,subprocess
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r33/work';O=S/'take-invent-r32/work'
if (W/'jobs.json').exists():raise SystemExit('Already initialized. Adopt the existing campaign and guardian from STATE.txt. Never rerun this one-time bootstrap.')
for p in O.glob('*.py'):
 text=p.read_text().replace('take-invent-r32/work','take-invent-r33/work').replace("QUENCH_LIVE_ROUND']='32'","QUENCH_LIVE_ROUND']='33'").replace("Q.LIVE='32'","Q.LIVE='33'")
 if p.name=='source_gate28.py':text=text.replace('3[012]','3[0123]').replace("S.glob('take-*-r32/work/ancestry')","S.glob('take-*-r33/work/ancestry')")
 (W/p.name).write_text(text)
for name in ('historical756-proof.json',):shutil.copyfile(O/name,W/name)
for name in ('starts','boxE-raw','ancestry','evidence','pins','lane'):(W/name).mkdir(exist_ok=True)
for p in (O/'boxE-raw/lane').glob('*.py'):shutil.copyfile(p,W/'lane'/p.name)
shutil.copyfile(O/'finesafe.py',W/'lane/finesafe.py')
(W/'deadline').write_text(str(datetime.datetime(2026,11,17,0,0,tzinfo=datetime.UTC).timestamp()))
(W/'search-deadline').write_text(str(datetime.datetime(2026,11,16,23,32,tzinfo=datetime.UTC).timestamp()))
# Reserve 15 minutes for archive and push, then a final peer-only comparison.
for src,dst in [('campaign32base.py','campaign33base.py'),('campaign32.py','campaign33.py'),('worker32-final.py','worker33.py'),('remote_close32.py','remote_close33.py')]:
 text=(W/src).read_text().replace('round32','round33').replace('-r32','-r33').replace('campaign32base','campaign33base').replace('worker32-final','worker33').replace('worker32-stream','worker33').replace('worker32.py','worker33.py').replace('worker[123]','worker[1234]').replace('STOP32FINAL','STOP33').replace('32.tsv','33.tsv')
 if dst=='campaign33.py':
  text=text.replace('range(21,32)','range(21,33)').replace('if room and not(W/\'late989-admitted\').exists():new.extend(initial989(peer))','')
  text=text.replace('room=max(0,5-len(pending))','room=max(0,6-len(pending))').replace("3231,None,None","3331,None,None")
  text=text.replace("wide=kind=='fresh'and", "wide=False and kind=='fresh'and")
  text=text.replace("root=S/f'take-{lane}-r33'", "root=S/f'take-{lane}-r33'")
  text=text.replace("if movement>(1e-9 if j['kind']=='leg'else 1e-6):", "if movement>1e-6 and d['new']<=peer[n]+1e-6/math.sqrt(n):")
  text=text.replace("if n<50:continue", "if n<50:continue\n   if lattice(p):continue\n   if p.parent==root and v['side']>(peer[n]+1)*math.sqrt(n)+1e-8:continue")
  text=text.replace("def init_history():", "def lattice(p):\n a=np.array([float(r['angle']) for r in csv.DictReader(open(p))])%90\n tilted=a[np.minimum(a,90-a)>1e-6]\n return len(tilted)>0 and bool(np.all(np.abs(tilted-45)<1e-6))\n\ndef init_history():")
  text=text.replace('deadline17:00Z','deadline00:00Z')
 if dst=='remote_close33.py':text=text.replace('worker33.py \'not in cmd and \'worker33.py \'not in cmd and \'worker33.py ', 'worker33.py ')
 (W/dst).write_text(text)
p=W/'held32.py';text=p.read_text().replace("SUBMITTED={", "SUBMITTED={'round32-2026-11-16a.csv',");p.write_text(text)
jobs=[j for j in json.load(open(O/'jobs.json'))if j['id']in('control2','control907','all-finish-control')]
for j in jobs:
 shutil.copyfile(O/j['start'],W/j['start'])
 if j['id']=='all-finish-control':
  target=W/j['id']/'raw';target.mkdir(parents=True,exist_ok=True)
  for p in(O/'boxE-raw'/j['id']/'raw').glob('*.csv'):shutil.copyfile(p,target/p.name)
(W/'jobs.json').write_text(json.dumps(jobs));(W/'queue.json').write_text(json.dumps(jobs));(W/'extra-controls.json').write_text('[]')
subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-invent-r33'],check=True)
files=['deadline','search-deadline','queue.json','worker33.py','certify31.py','invent_barretain_budget30.py','early32.py']
subprocess.run(['rsync','-a',*[str(W/p)for p in files],str(W/'lane'),str(W/'starts'),str(W/'all-finish-control'),'boxE:scratch/squares-invent-r33/'],check=True)
print('SETUP controls',len(jobs),'four slots admission23:32Z; numeric00:00Z; cleanup00:15Z')
