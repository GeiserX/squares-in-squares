"""Initialize a new lane directory once. Resume existing work from STATE.txt."""
import pathlib,shutil,datetime,json
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-invent-r25/work';O=S/'take-invent-r24/work';R=pathlib.Path('.')
if (W/'jobs.json').exists():raise SystemExit('Existing jobs found. Resume from STATE.txt instead of resetting this round.')
W.mkdir(exist_ok=True,parents=True)
(W/'deadline').write_text(str(datetime.datetime(2026,11,14,2,45,tzinfo=datetime.timezone.utc).timestamp()))
(W/'search-deadline').write_text(str(datetime.datetime(2026,11,14,2,15,tzinfo=datetime.timezone.utc).timestamp()))
(W/'starts').mkdir(exist_ok=True);L=W/'lane';L.mkdir(exist_ok=True)
for p in (O/'lane').glob('*.py'):shutil.copy(p,L/p.name)
shutil.copy(O/'lane/invent_plateau23.json',L/'invent_plateau23.json')
for name in ('midm_scan.py','midm_fqonce.py'):shutil.copy(R/name,L/name)
for name in ('invent_shape22.py','enrich23.py'):shutil.copy(O/name,W/name)
for name in ('worker25.py','claim25.py','controller25.py','ancestry25.py','measure25.py'):
 source=R/'tools/invent/round25'/name
 if source.resolve()!=(W/name).resolve():shutil.copy(source,W/name)
shutil.copy(O/'starts/control907.csv',W/'starts/control907.csv')
ctl=dict(id='ctl907',n=907,start='starts/control907.csv',seconds=420,seed=2,kind='control',fq=False,bar=30.6195806,side=30.619580679,source='positive control: stopped original block construction 907; take-invent-r20/work/boxE/907-stop.csv',licence='our own construction')
(W/'jobs.json').write_text(json.dumps([ctl]))
for slot in (1,2,3):(W/f'queue{slot}.json').write_text(json.dumps([ctl]if slot==1 else[]))
(W.parent/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
print('initialized immutable control, lane dependencies and common deadline')
