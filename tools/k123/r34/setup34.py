from pathlib import Path
import shutil,csv,json,datetime,re
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r33/work';W=Path(__file__).resolve().parent;T=W.parent
for p in O.glob('*.py'):
 if p.name.startswith('setup'):continue
 s=p.read_text().replace('/tmp/squares-k123-r33','/tmp/squares-k123-r34').replace('handoff-r33.log','handoff-r34.log').replace('round33-briefs/bar33.tsv','round34-briefs/bar34.tsv')
 s=s.replace('00:15','07:25').replace('00:05','07:05').replace('00:25','07:35').replace('00:30','07:40').replace('23:45','06:55').replace('23:55','07:05')
 if p.name=='base25.py':
  s=s.replace('gather/round32-2026-11-16a.csv','gather/round33-2026-11-17a.csv').replace('gate/cand-round32-1116a','gate/cand-round33-1117a').replace('take-*-r32/take.tsv','take-*-r33/take.tsv').replace("*S.glob('take-*-r33/take.tsv')]):","*S.glob('take-*-r34/take.tsv')]):").replace("(32,'16')]","(32,'16'),(33,'17')]").replace('held round32','held round33').replace('held n = {n} of round 32','held n = {n} of round 33').replace('results/round32-best-2026-11-16.tsv','results/round33-best-2026-11-17.tsv')
 if p.name=='stage24.py':
  s=s.replace('take-*-r32','take-*-r33').replace("*S.glob('take-*-r33')]:","*S.glob('take-*-r34')]:").replace("endswith('-r33')","endswith('-r34')").replace("['-r32/','-r33/']","['-r33/','-r34/']").replace("0 if '-r33/'","0 if '-r34/'")
 if p.name in ['collect22.py','report33.py','peer33.py','independent33.py']:s=s.replace('take-*-r33/take.tsv','take-*-r34/take.tsv')
 if p.name in ['resume26.py','deferred28.py']:
  s=s.replace('take-k123-r32/','take-k123-r33/').replace("'resume33'","'resume34'").replace("'deferred33'","'deferred34'")
 if p.name=='provenance24.py':s=s.replace('29|30|31|32|33','29|30|31|32|33|34').replace('best-2026-11-16.tsv','best-2026-11-17.tsv')
 if p.name=='walker30.py':s=s.replace("'QUENCH_LIVE_ROUND', '33'","'QUENCH_LIVE_ROUND', '34'")
 if p.name=='admission32.py':
  s=s.replace("['round32-2026-11-16a.csv'","['round33-2026-11-17a.csv','round32-2026-11-16a.csv'").replace("[(32,'round32-2026-11-16a.csv')","[(33,'round33-2026-11-17a.csv'),(32,'round32-2026-11-16a.csv')")
 if p.name=='finish26.py':
  s=s.replace('report33.py','report34.py').replace('round33-section','round34-section').replace('## Round 33','## Round 34').replace('tools/k123/r33','tools/k123/r34').replace('k123-r33-2026-11-17','k123-r34-2026-11-17').replace('round 33 k123','round 34 k123')
 if p.name=='report33.py':
  s=s.replace('round 33','round 34').replace('Round 33','Round 34').replace('beyond_other_live_r33','beyond_other_live_r34').replace('k123-r33-2026-11-17','k123-r34-2026-11-17').replace('tools/k123/r33','tools/k123/r34').replace('take-k123-r33/work','take-k123-r34/work').replace('round33-section','round34-section').replace('2026,11,17,0,25,0','2026,11,17,7,35,0')
 (W/('report34.py' if p.name=='report33.py' else p.name)).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv','fivebins30-control-passed','enable-wide30']:
 if (O/name).exists():shutil.copy(O/name,W/name)
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('')
for name,hm in [('deadline',(7,25)),('search-deadline',(6,55)),('finalize-at32',(7,5))]:(W/name).write_text(str(datetime.datetime(2026,11,17,*hm,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round33-1117a/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round34-briefs/bar34.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
ends=[p for t in S.glob('take-*-r33') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r33/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in ends+rects+oldnear]));(W/'next28.json').write_text(json.dumps(json.load(open(S/'round34-briefs/r33-results.json'))['k123']['next']));(W/'measurements28.json').write_text('[]')
priority=[str(p) for p in ends if p.stem in ['259','445','968','734']]
(W/'priority-inputs31.json').write_text(json.dumps(priority))
hist={tuple(x) for x in json.load(open(W/'completed-geometries26.json'))};old=len(hist);missing=[]
for line in (O/'records.jsonl').read_text().splitlines():
 r=json.loads(line);m=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if not m:continue
 p=O/r['pool']/('sources-'+r['pool']+'.json')
 if not p.exists():p=O/'boxE-final'/('sources-'+r['pool']+'.json')
 if not p.exists():missing.append(str(p));continue
 meta=json.load(open(p));hist.add((r['tag'],*(meta[n]['sha256_geometry'] for n in m.groups()),*([r['mechanism']] if r.get('mechanism') else [])))
assert not missing,missing
(W/'completed-geometries26.json').write_text(json.dumps(sorted(hist)));r={'old':old,'new':len(hist)-old,'total':len(hist),'missing':missing};(W/'history-rebuilt34.json').write_text(json.dumps(r));print(r)
with (T/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+f' boxA CLOSED prior geometry history {r}. Fresh joins then non-winning bands, measured1.005 branch only. Common deadline2026-11-17T07:25Z.\n')
print('helpers',len(list(W.glob('*.py'))),'forced',len(ends+rects+oldnear))
