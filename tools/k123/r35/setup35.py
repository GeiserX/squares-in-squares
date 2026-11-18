from pathlib import Path
import shutil,csv,json,datetime,re
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r34/work';W=Path(__file__).resolve().parent;T=W.parent
TIMES=[('07:25','16:25'),('07:05','16:05'),('07:35','16:35'),('07:40','16:40'),('06:55','15:55'),('07:15','16:15'),('06:25','15:25'),('06:40','15:40')]
for p in O.glob('*.py'):
 if p.name.startswith('setup'):continue
 s=p.read_text().replace('/tmp/squares-k123-r34','/tmp/squares-k123-r35').replace('handoff-r34.log','handoff-r35.log').replace('round34-briefs/bar34.tsv','round35-briefs/bar35.tsv')
 for a,b in TIMES:s=s.replace(a,b)
 if p.name=='base25.py':
  s=s.replace('gather/round33-2026-11-17a.csv','gather/round34-2026-11-17a.csv').replace('gate/cand-round33-1117a','gate/cand-round34-1117a').replace("*S.glob('take-*-r34/take.tsv')","*S.glob('take-*-r35/take.tsv')").replace("*S.glob('take-*-r33/take.tsv')","*S.glob('take-*-r34/take.tsv')").replace("(33,'17')]","(33,'17'),(34,'17')]").replace('held round33','held round34').replace('of round 33','of round 34').replace('results/round33-best-2026-11-17.tsv','results/round34-best-2026-11-17.tsv')
 if p.name in ['stage24.py','collect22.py','report34.py','peer33.py','independent33.py','base25.py','retention32.py','validate25.py']:
  s=s.replace('take-*-r34','take-*-r35').replace("*S.glob('take-*-r33')","*S.glob('take-*-r34')")
 if p.name=='stage24.py':
  s=s.replace("endswith('-r34')","endswith('-r35')").replace("['-r33/','-r34/']","['-r34/','-r35/']").replace("0 if '-r34/'","0 if '-r35/'")
 if p.name in ['resume26.py','deferred28.py']:
  s=s.replace('take-k123-r33/','take-k123-r34/').replace("'resume34'","'resume35'").replace("'deferred34'","'deferred35'")
 if p.name=='provenance24.py':s=s.replace('|32|33|34)/','|32|33|34|35)/').replace("'17' if held_round33==33","'17' if held_round33 in (33,34)")
 if p.name=='walker30.py':s=s.replace("'QUENCH_LIVE_ROUND', '34'","'QUENCH_LIVE_ROUND', '35'")
 if p.name=='admission32.py':
  s=s.replace("['round33-2026-11-17a.csv'","['round34-2026-11-17a.csv','round33-2026-11-17a.csv'").replace("[(33,'round33-2026-11-17a.csv')","[(34,'round34-2026-11-17a.csv'),(33,'round33-2026-11-17a.csv')")
 if p.name=='guardian34.py':s=s.replace('(2026,11,17,6,55,','(2026,11,17,15,55,')
 if p.name=='finish26.py':
  s=s.replace('report34.py','report35.py').replace('round34-section','round35-section').replace('## Round 34','## Round 35').replace('tools/k123/r34','tools/k123/r35').replace('k123-r34-2026-11-17','k123-r35-2026-11-17').replace('round 34 k123','round 35 k123')
 if p.name=='report34.py':
  s=s.replace('round 34','round 35').replace('Round 34','Round 35').replace('beyond_other_live_r34','beyond_other_live_r35').replace('bar34','bar35').replace('k123-r34-2026-11-17','k123-r35-2026-11-17').replace('tools/k123/r34','tools/k123/r35').replace('take-k123-r34/work','take-k123-r35/work').replace('round34-section','round35-section')
 if p.name=='finalize34.py':
  s=s.replace('report34.py','report35.py').replace('round34-section','round35-section').replace('## Round 34','## Round 35').replace('tools/k123/r34','tools/k123/r35').replace('k123-r34-2026-11-17','k123-r35-2026-11-17').replace('round 34 k123','round 35 k123').replace('FINAL34','FINAL35').replace('round34','round35')
  s=s.replace('$STYLE_CHECK/check.py','$STYLE_CHECK/check.py')
  for a,b in [('waitat(6,25)','waitat(15,25)'),('waitat(6,40)','waitat(15,40)'),('waitat(6,58)','waitat(15,58)'),('waitat(7,15)','waitat(16,15)'),('waitat(7,25)','waitat(16,25)'),('(2026,11,17,7,34,30,','(2026,11,17,16,34,30,')]:
   assert a in s,a;s=s.replace(a,b)
  # round 34 died here: the ps header line is not a pid.
  old="for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines():"
  assert old in s;s=s.replace(old,"for line in subprocess.check_output(['ps','-axo','pid,command'],text=True).splitlines()[1:]:")
 name={'report34.py':'report35.py','finalize34.py':'finalize35.py'}.get(p.name,p.name)
 (W/name).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv','fivebins30-control-passed','enable-wide30','runtime33.json']:
 if (O/name).exists():shutil.copy(O/name,W/name)
for host in ['boxC','boxD']:
 (W/host).mkdir(exist_ok=True)
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('')
for name,hm in [('deadline',(16,25)),('search-deadline',(15,55)),('finalize-at32',(16,5))]:(W/name).write_text(str(datetime.datetime(2026,11,17,*hm,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round34-1117a/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round35-briefs/bar35.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
ends=[p for t in S.glob('take-*-r34') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r34/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in ends+rects+oldnear]));(W/'next28.json').write_text(json.dumps(json.load(open(S/'round35-briefs/r34-results.json'))['k123']['next']));(W/'measurements28.json').write_text('[]')
CHANGED=[790,808,735,683,640,582,489,653,998,928,995,811,753,687,925]
priority=[str(p) for p in ends if p.stem.isdigit() and int(p.stem) in CHANGED]
(W/'priority-inputs31.json').write_text(json.dumps(priority))
hist={tuple(x) for x in json.load(open(W/'completed-geometries26.json'))};old=len(hist);missing=[]
for line in (O/'records.jsonl').read_text().splitlines():
 r=json.loads(line);m=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if not m:continue
 p=O/r['pool']/('sources-'+r['pool']+'.json')
 if not p.exists():p=O/'boxE-final'/('sources-'+r['pool']+'.json')
 if not p.exists():missing.append(str(p));continue
 meta=json.load(open(p));hist.add((r['tag'],*(meta[n]['sha256_geometry'] for n in m.groups()),*([r['mechanism']] if r.get('mechanism') else [])))
(W/'completed-geometries26.json').write_text(json.dumps(sorted(hist)));r={'old':old,'new':len(hist)-old,'total':len(hist),'missing':len(missing),'missing_first':missing[:5]};(W/'history-rebuilt35.json').write_text(json.dumps(r));print(r)
with (T/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+f' boxA SETUP35 helpers copied from take-k123-r34/work with round35 paths, bar35, times shifted to the 16:25Z deadline (search intake 15:55Z) and the finalizer ps-header fix. Closed geometry history {r}. Priority: changed held rows {CHANGED}.\n')
print('helpers',len(list(W.glob('*.py'))),'forced',len(ends+rects+oldnear),'priority',len(priority))
