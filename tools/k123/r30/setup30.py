from pathlib import Path
import shutil,csv,datetime,json
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r29/work';W=Path(__file__).resolve().parent;T=W.parent
for p in O.glob('*.py'):
 s=p.read_text()
 for a,b in [('/tmp/squares-k123-r29-ssh','/tmp/squares-k123-r30-ssh'),('handoff-r29.log','handoff-r30.log'),('round29-briefs/bar29.tsv','round30-briefs/bar30.tsv'),('take-*-r29','take-*-r30'),('11:45Z','17:45Z'),('11:55Z','17:55Z'),('11:56 UTC','17:56 UTC'),('12:00Z','18:00Z'),('11:35','17:35')]:s=s.replace(a,b)
 if p.name=='base25.py':
  s=s.replace('gather/round27-2026-11-15b.csv','gather/round28-2026-11-15b.csv').replace('gate/cand-round27-1115b','gate/cand-round28-1115b').replace("*S.glob('take-*-r28/take.tsv')","*S.glob('take-*-r29/take.tsv')")
 if p.name=='stage24.py':
  s=s.replace("*S.glob('take-*-r28')","*S.glob('take-*-r29')").replace("endswith('-r29')","endswith('-r30')").replace("['-r28/','-r29/']","['-r29/','-r30/']").replace("0 if '-r29/'","0 if '-r30/'")
 if p.name in ['resume26.py','deferred28.py']:
  s=s.replace('take-k123-r28/','take-k123-r29/').replace("'resume29'","'resume30'").replace("'deferred29'","'deferred30'")
 if p.name=='provenance24.py':s=s.replace('27|28|29|29','27|28|29|30')
 if p.name=='finish26.py':
  s=s.replace('report29.py','report30.py').replace('round29-section','round30-section').replace('## Round 29','## Round 30').replace('tools/k123/r29','tools/k123/r30').replace('k123-r29-2026','k123-r30-2026').replace('round 29 k123','round 30 k123')
 if p.name=='report29.py':
  s=s.replace('round 29','round 30').replace('Round 29','Round 30').replace('beyond_other_live_r29','beyond_other_live_r30').replace('round28 and round29','round29 and round30').replace('round28 00:19:03Z','round30 ownership').replace('k123-r29-2026','k123-r30-2026').replace('tools/k123/r29','tools/k123/r30').replace('take-k123-r29/work','take-k123-r30/work').replace('round29-section','round30-section').replace('2026,11,15,11,55,1','2026,11,15,17,55,1')
  (W/'report30.py').write_text(s)
 (W/p.name).write_text(s)
shutil.copytree(O/'lane',W/'lane',dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv']:
 shutil.copy(O/name,W/name)
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('')
for name,h,m in [('deadline',17,45),('search-deadline',17,35)]:
 (W/name).write_text(str(datetime.datetime(2026,11,15,h,m,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round28-1115b/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round30-briefs/bar30.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
ends=[p for t in S.glob('take-*-r29') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r29/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*-threeway28-*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in ends+rects+oldnear]))
(W/'next28.json').write_text(json.dumps(json.load(open(S/'round30-briefs/r29-results.json'))['k123']['next']))
(W/'measurements28.json').write_text('[]')
(W/'owned-helpers26.json').write_text(json.dumps([p.name for p in W.glob('*.py') if p.name!='setup30.py']))
print('round30 setup',len(list(W.glob('*.py'))),'helpers',len(ends),len(rects),len(oldnear))
