"""One-time round 35 bootstrap: port the round 34 invent campaign forward (three boxE slots)."""
import pathlib,shutil,datetime,json,subprocess,re
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r35/work';O=S/'take-invent-r34/work'
if (W/'jobs.json').exists():raise SystemExit('Already initialized. Adopt the existing campaign and guardian from STATE.txt. Never rerun this one-time bootstrap.')
def utc(*a):return str(datetime.datetime(*a,tzinfo=datetime.UTC).timestamp())
IDS=r'\b(campaign|worker|remote_close|start_remote|finish|record|held-shapes|controls|STOP|source-control|watchdog|wd_remote|controls_geometry|controls-geometry)34'
TIMES=[('admission06:37Z, numeric07:05Z, archive/push before07:20Z; final peer comparison07:34:40Z','admission15:37Z, numeric16:05Z, archive/push before16:20Z; final peer comparison16:34:40Z'),('Search and quench stop by 07:05 UTC','Search and quench stop by 16:05 UTC'),('take.tsv frozen before07:35Z','take.tsv frozen before16:35Z'),('deadline07:05Z','deadline16:05Z'),('datetime.datetime(2026,11,17,7,34,40','datetime.datetime(2026,11,17,16,34,40')]
SKIP=('setup34.py','setup35.py')
for p in O.glob('*.py'):
 if p.name in SKIP or re.search(r'(2[0-9]|3[0-3])(base|-v2|v2|-final|-stream)?\.py$',p.name) and re.match(IDS[2:].replace('34',''),p.name):continue
 text=p.read_text().replace('take-invent-r34/work','take-invent-r35/work').replace("QUENCH_LIVE_ROUND']='34'","QUENCH_LIVE_ROUND']='35'").replace("Q.LIVE='34'","Q.LIVE='35'")
 if p.name=='source_gate28.py':text=text.replace('3[01234]','3[012345]').replace("S.glob('take-*-r3[34]/work/ancestry')","S.glob('take-*-r3[345]/work/ancestry')")
 if p.name=='held32.py':text=text.replace("SUBMITTED={","SUBMITTED={'round34-2026-11-17a.csv',")
 name=p.name
 if re.match(IDS[2:],name) or re.search(r'34\.py$',name):
  text=text.replace('round34','round35').replace('Round 34','Round 35').replace('-r34','-r35').replace('bar34','bar35').replace('live_r34','live_r35').replace('r34 SCRATCH','r35 SCRATCH')
  text=text.replace('gather/round33-2026-11-17a.csv','gather/round34-2026-11-17a.csv').replace('submitted_round34','submitted_round35')
  text=re.sub(IDS,lambda m:m[1]+'35',text)
  for a,b in TIMES:text=text.replace(a,b)
  name=re.sub(r'34\.py$','35.py',name)
 (W/name).write_text(text)
for name in ('historical756-proof.json','deferred32.json','shape-cache32.json'):shutil.copyfile(O/name,W/name)
for name in ('starts','boxE-raw','ancestry','evidence','pins','lane'):(W/name).mkdir(exist_ok=True)
for p in (O/'lane').glob('*.py'):shutil.copyfile(p,W/'lane'/p.name)
shutil.copyfile(O/'finesafe.py',W/'lane/finesafe.py')
(W/'deadline').write_text(utc(2026,11,17,16,5))
(W/'search-deadline').write_text(utc(2026,11,17,15,37))
print('PORTED',sorted(q.name for q in W.glob('*.py')))
