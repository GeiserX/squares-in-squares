from pathlib import Path
import shutil,csv,json,datetime
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r30/work';W=Path(__file__).resolve().parent;T=W.parent
for p in O.glob('*.py'):
 if p.name.startswith('setup'):continue
 s=p.read_text()
 for a,b in [('/tmp/squares-k123-r30-ssh','/tmp/squares-k123-r31-ssh'),('handoff-r30.log','handoff-r31.log'),('round30-briefs/bar30.tsv','round31-briefs/bar31.tsv'),('take-*-r30','take-*-r31'),('17:45','00:15'),('17:35','00:05'),('17:55','00:25'),('17:56','00:26'),('18:00Z','00:30Z')]:s=s.replace(a,b)
 if p.name=='base25.py':
  s=s.replace('gather/round28-2026-11-15b.csv','gather/round30-2026-11-15c.csv').replace('gate/cand-round28-1115b','gate/cand-round30-1115c').replace("*S.glob('take-*-r29/take.tsv')","*S.glob('take-*-r30/take.tsv')").replace("(28,'15')]","(28,'15'),(29,'15'),(30,'15')]")
 if p.name=='stage24.py':s=s.replace("*S.glob('take-*-r29')","*S.glob('take-*-r30')").replace("endswith('-r30')","endswith('-r31')").replace("['-r29/','-r30/']","['-r30/','-r31/']").replace("0 if '-r30/'","0 if '-r31/'")
 if p.name in ['resume26.py','deferred28.py']:s=s.replace('take-k123-r29/','take-k123-r30/').replace("'resume30'","'resume31'").replace("'deferred30'","'deferred31'")
 if p.name=='provenance24.py':s=s.replace('27|28|29|30','27|28|29|30|31')
 if p.name=='finish26.py':
  s=s.replace('report30.py','report31.py').replace('round30-section','round31-section').replace('## Round 30','## Round 31').replace('tools/k123/r30','tools/k123/r31').replace('k123-r30-2026-11-15','k123-r31-2026-11-16').replace('round 30 k123','round 31 k123')
 if p.name=='report30.py':
  s=s.replace('round 30','round 31').replace('Round 30','Round 31').replace('beyond_other_live_r30','beyond_other_live_r31').replace('round29 and round30','round30 and round31').replace('k123-r30-2026-11-15','k123-r31-2026-11-16').replace('tools/k123/r30','tools/k123/r31').replace('take-k123-r30/work','take-k123-r31/work').replace('round30-section','round31-section').replace('2026,11,15,17,55,1','2026,11,16,0,25,1');(W/'report31.py').write_text(s)
 (W/p.name).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv']:shutil.copy(O/name,W/name)
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('')
for name,m in [('deadline',15),('search-deadline',5)]: (W/name).write_text(str(datetime.datetime(2026,11,16,0,m,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round30-1115c/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round31-briefs/bar31.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
ends=[p for t in S.glob('take-*-r30') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r30/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*-threeway28-*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in oldnear+ends+rects]));(W/'next28.json').write_text(json.dumps(json.load(open(S/'round31-briefs/r30-results.json'))['k123']['next']));(W/'measurements28.json').write_text('[]')
(W/'owned-helpers26.json').write_text(json.dumps([p.name for p in W.glob('*.py')]))
print('round31 copied',len(list(W.glob('*.py'))), 'helpers; donors',len(oldnear),'ends',len(ends),'rects',len(rects))
