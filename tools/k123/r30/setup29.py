from pathlib import Path
import shutil,json,datetime,csv,re
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r28/work';W=S/'take-k123-r29/work';T=W.parent
for p in O.glob('*.py'):
 s=p.read_text().replace('/tmp/squares-k123-r28-ssh','/tmp/squares-k123-r30-ssh').replace('handoff-r28.log','handoff-r30.log').replace('round28-briefs/bar28.tsv','round30-briefs/bar30.tsv').replace('take-*-r28','take-*-r30').replace('deadline05:45Z','deadline17:45Z').replace('Deadline05:45Z','Deadline17:45Z').replace('cutoff05:45Z','cutoff17:45Z').replace('deadline06:00Z','deadline18:00Z').replace('deadline06:00','deadline12:00').replace('05:56 UTC','17:56 UTC').replace('take final05:55Z','take final17:55Z').replace('report06:00Z','report18:00Z')
 if p.name=='provenance24.py':s=s.replace('25|26|27|28','25|26|27|28|29')
 if p.name=='base25.py':
  s=s.replace('gather/round26-2026-11-14b.csv','gather/round27-2026-11-15b.csv').replace('gate/cand-round26-1114b','gate/cand-round27-1115b').replace("[(24,'13'),(25,'14'),(26,'14')]","[(24,'13'),(25,'14'),(26,'14'),(27,'15'),(28,'15')]")
  s=s.replace("*S.glob('take-*-r27/take.tsv')","*S.glob('take-*-r28/take.tsv')")
 if p.name=='stage24.py':
  s=s.replace("*S.glob('take-*-r27')","*S.glob('take-*-r28')").replace("endswith('-r28')","endswith('-r29')").replace("['-r27/','-r28/']","['-r28/','-r29/']").replace("1 if '-r27/' in str(p) else 2","1 if '-r29/' in str(p) else 2")
 if p.name in ['resume26.py','deferred28.py']:s=s.replace('take-k123-r27/','take-k123-r28/').replace("tag='resume28'","tag='resume29'").replace("'deferred28'","'deferred29'")
 if p.name=='resident25.py':
  s=s.replace("'resume26.py','storage26.py'","'resume26.py'")
 if p.name=='storage26.py':
  a=s.index("try:runpy.run_path");b=s.index('# Bound warm',a);s=s[:a]+s[b:]
 if p.name=='finish26.py':
  s=s.replace("report28.py","report29.py").replace('round28-section','round29-section').replace('## Round 28','## Round 29').replace('tools/k123/r28','tools/k123/r29').replace('k123-r28-2026','k123-r29-2026').replace('round 28 k123','round 29 k123').replace('05:45Z','17:45Z').replace('06:00Z','18:00Z')
 if p.name=='launch27.py':s=s.replace('Search cutoff05:35','Search cutoff17:35').replace('common hard05:45Z','common hard17:45Z')
 (W/p.name).write_text(s)
shutil.copytree(O/'lane',W/'lane',dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv']:
 shutil.copy(O/name,W/name)
# A fresh cache forces the new source policy through the full walk.
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
(W/'records.jsonl').write_text('')
for name,h,m in [('deadline',11,45),('search-deadline',11,35)]:
 (W/name).write_text(str(datetime.datetime(2026,11,15,h,m,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round27-1115b/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round30-briefs/bar30.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
# Separate intermediate admission from fresh scanning. One slow walk must not stall fresh inputs.
(W/'background29.py').write_text('''import pathlib,sys,time,runpy,traceback,os
W=pathlib.Path(__file__).resolve().parent;os.chdir(W);sys.path[:0]=[str(W),str(W/'lane')]
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
mode=sys.argv[1];script='intermediate28.py' if mode=='third' else 'storage26.py'
while time.time()<float((W/'search-deadline').read_text()):
 t=time.time()
 try:runpy.run_path(str(W/script),run_name='__main__')
 except SystemExit:pass
 except Exception:traceback.print_exc()
 print(time.strftime('%FT%TZ',time.gmtime()),mode,'seconds',time.time()-t,flush=True)
 time.sleep(30)
''')
# Include prior successful near joins in the new fresh intake; their bytes stay frozen.
oldnear=list((O.parent/'near').glob('*-threeway28-*.csv'))
ends=[p for t in S.glob('take-*-r28') for p in t.glob('*.csv')]
rects=list((S/'take-forensics-r28/near').glob('*-rect.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in oldnear+ends+rects]))
print('copied',len(list(W.glob('*.py'))),'helpers; old third-band donors',len(oldnear))
