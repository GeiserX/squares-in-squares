"""One-time round 34 bootstrap: port the round 33 invent campaign forward."""
import pathlib,shutil,datetime,json,subprocess
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r34/work';O=S/'take-invent-r33/work'
if (W/'jobs.json').exists():raise SystemExit('Already initialized. Adopt the existing campaign and guardian from STATE.txt. Never rerun this one-time bootstrap.')
def utc(*a):return str(datetime.datetime(*a,tzinfo=datetime.UTC).timestamp())
for p in O.glob('*.py'):
 if p.name in('setup33.py','patch_admission33.py','upgrade_freeze33.py'):continue
 text=p.read_text().replace('take-invent-r33/work','take-invent-r34/work').replace("QUENCH_LIVE_ROUND']='33'","QUENCH_LIVE_ROUND']='34'").replace("Q.LIVE='33'","Q.LIVE='34'")
 if p.name=='source_gate28.py':text=text.replace('3[0123]','3[01234]').replace("S.glob('take-*-r33/work/ancestry')","S.glob('take-*-r3[34]/work/ancestry')")
 if p.name=='held32.py':text=text.replace("SUBMITTED={","SUBMITTED={'round33-2026-11-17a.csv',")
 (W/p.name).write_text(text)
for name in ('historical756-proof.json',):shutil.copyfile(O/name,W/name)
# Keep r33 source deferrals and the shape cache: an unchanged sidecar stays deferred.
for name in ('deferred32.json','shape-cache32.json'):shutil.copyfile(O/name,W/name)
for name in ('starts','boxE-raw','ancestry','evidence','pins','lane'):(W/name).mkdir(exist_ok=True)
for p in (O/'lane').glob('*.py'):shutil.copyfile(p,W/'lane'/p.name)
shutil.copyfile(O/'finesafe.py',W/'lane/finesafe.py')
(W/'deadline').write_text(utc(2026,11,17,7,5))
(W/'search-deadline').write_text(utc(2026,11,17,6,37))
TIMES=[('admission23:32Z, numeric00:00Z, archive/push before00:15Z; final peer comparison00:24:40Z','admission06:37Z, numeric07:05Z, archive/push before07:20Z; final peer comparison07:34:40Z'),('Search and quench stop by 00:00 UTC','Search and quench stop by 07:05 UTC'),('take.tsv frozen before00:25Z','take.tsv frozen before07:35Z'),('deadline00:00Z','deadline07:05Z'),('datetime.datetime(2026,11,17,0,24,40','datetime.datetime(2026,11,17,7,34,40')]
for src,dst in [('campaign33base.py','campaign34base.py'),('campaign33.py','campaign34.py'),('worker33.py','worker34.py'),('remote_close33.py','remote_close34.py'),('start_remote33.py','start_remote34.py'),('finish33.py','finish34.py'),('record33.py','record34.py'),('controls33.py','controls34.py')]:
 text=(O/src).read_text()
 # Held file of round 33 replaces the round 32 file before the generic rename.
 text=text.replace('gather/round32-2026-11-16a.csv','gather/round33-2026-11-17a.csv').replace('submitted_round32','submitted_round33')
 text=text.replace('round33','round34').replace('Round 33','Round 34').replace('-r33','-r34').replace('bar33','bar34').replace('live_r33','live_r34').replace('r33 SCRATCH','r34 SCRATCH')
 for a in ('campaign33base','campaign33','worker33','remote_close33','finish33','record33','held-shapes33','controls33','STOP33','source-control33'):text=text.replace(a,a.replace('33','34'))
 for a,b in TIMES:text=text.replace(a,b)
 if dst=='campaign34.py':
  text=text.replace('range(21,33)','range(21,34)').replace('for rnd in (33,32)','for rnd in (34,33)').replace('rnd<33','rnd<34').replace('rnd==33','rnd==34').replace('3331,None,None','3431,None,None')
 if dst=='finish34.py':
  text=text.replace('round32 fresh runs moved23/36, versus2/26 legs','round33 fresh runs moved9/24, versus0/1 legs')
 if dst=='controls34.py':
  text=text.replace("G.Q.LIVE=='33'","G.Q.LIVE=='34'").replace("'handoff-r33.log'","'handoff-r34.log'")
 if dst=='record34.py':
  text=text.replace('2026-11-16 to 2026-11-17','2026-11-17').replace('Measure round 34','Measure round 34')
 (W/dst).write_text(text)
jobs=[j for j in json.load(open(O/'jobs.json'))if j['id']in('control2','control907','all-finish-control')]
for j in jobs:
 shutil.copyfile(O/j['start'],W/j['start'])
 if j['id']=='all-finish-control':
  target=W/j['id']/'raw';target.mkdir(parents=True,exist_ok=True)
  for p in(O/'boxE-raw'/j['id']/'raw').glob('*.csv'):shutil.copyfile(p,target/p.name)
(W/'jobs.json').write_text(json.dumps(jobs));(W/'queue.json').write_text(json.dumps(jobs));(W/'extra-controls.json').write_text('[]')
subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-invent-r34'],check=True)
files=['deadline','search-deadline','queue.json','worker34.py','certify31.py','invent_barretain_budget30.py','early32.py']
subprocess.run(['rsync','-a',*[str(W/p)for p in files],str(W/'lane'),str(W/'starts'),str(W/'all-finish-control'),'boxE:scratch/squares-invent-r34/'],check=True)
print('SETUP controls',len(jobs),'four slots admission06:37Z; numeric07:05Z; cleanup07:20Z')
