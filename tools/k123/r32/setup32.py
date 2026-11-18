from pathlib import Path
import shutil,csv,json,datetime,re
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r31/work';W=Path(__file__).resolve().parent;T=W.parent
for p in O.glob('*.py'):
 if p.name.startswith('setup'):continue
 s=p.read_text().replace('/tmp/squares-k123-r31-ssh','/tmp/squares-k123-r32-ssh').replace('handoff-r31.log','handoff-r32.log').replace('round31-briefs/bar31.tsv','round32-briefs/bar32.tsv').replace('00:15','17:15').replace('00:05','17:05').replace('00:25','17:25').replace('00:30','17:30')
 if p.name=='base25.py':
  s=s.replace('gather/round30-2026-11-15c.csv','gather/round31-2026-11-16b.csv').replace('gate/cand-round30-1115c','gate/cand-round31-1116b').replace("take-*-r30/take.tsv","take-*-r31/take.tsv").replace("take-*-r31/take.tsv')]):","take-*-r32/take.tsv')]):").replace("(30,'15')]","(30,'15'),(31,'16')]")
 if p.name=='stage24.py':
  s=s.replace('take-*-r30','take-*-r31').replace("*S.glob('take-*-r31')]:","*S.glob('take-*-r32')]:").replace("endswith('-r31')","endswith('-r32')").replace("['-r30/','-r31/']","['-r31/','-r32/']").replace("0 if '-r31/'","0 if '-r32/'")
 if p.name in ['collect22.py','report31.py']:s=s.replace('take-*-r31/take.tsv','take-*-r32/take.tsv')
 if p.name in ['resume26.py','deferred28.py']:
  s=s.replace('take-k123-r30/','take-k123-r31/').replace("'resume31'","'resume32'").replace("'deferred31'","'deferred32'")
 if p.name=='provenance24.py':s=s.replace('29|30|31','29|30|31|32')
 if p.name=='walker30.py':s=s.replace("'QUENCH_LIVE_ROUND', '31'","'QUENCH_LIVE_ROUND', '32'")
 if p.name=='resident25.py':s=s.replace("['feedheld31.py','stage24.py','feedkick30.py','deferred28.py','resume26.py']","['stage24.py','deferred28.py','resume26.py']")
 if p.name=='finish26.py':
  s=s.replace('report31.py','report32.py').replace('round31-section','round32-section').replace('## Round 31','## Round 32').replace('tools/k123/r31','tools/k123/r32').replace('k123-r31-2026-11-16','k123-r32-2026-11-16').replace('round 31 k123','round 32 k123')
 if p.name=='report31.py':s=s.replace('round 31','round 32').replace('Round 31','Round 32').replace('beyond_other_live_r31','beyond_other_live_r32').replace('k123-r31-2026-11-16','k123-r32-2026-11-16').replace('tools/k123/r31','tools/k123/r32').replace('take-k123-r31/work','take-k123-r32/work').replace('round31-section','round32-section').replace('2026,11,16,0,25,0','2026,11,16,17,25,0')
 (W/('report32.py' if p.name=='report31.py' else p.name)).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv','fivebins30-control-passed']: 
 if (O/name).exists():shutil.copy(O/name,W/name)
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('')
for name,m in [('deadline',15),('search-deadline',5)]: (W/name).write_text(str(datetime.datetime(2026,11,16,17,m,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round31-1116b/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round32-briefs/bar32.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
ends=[p for t in S.glob('take-*-r31') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r31/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*-threeway28-*.csv'))+list((O.parent/'near').glob('*-heldreturn31-*.csv'))+list((O.parent/'near').glob('*-prejoin31-*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in ends+rects+oldnear]));(W/'next28.json').write_text(json.dumps(json.load(open(S/'round32-briefs/r31-results.json'))['k123']['next']));(W/'measurements28.json').write_text('[]')
(W/'owned-helpers26.json').write_text(json.dumps([p.name for p in W.glob('*.py')]))
# Rebuild the final prior-round index from immutable manifests before admitting work.
hist={tuple(x) for x in json.load(open(W/'completed-geometries26.json'))};old=len(hist);missing=[]
for line in (O/'records.jsonl').read_text().splitlines():
 r=json.loads(line);m=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if not m:continue
 p=O/r['pool']/('sources-'+r['pool']+'.json')
 if not p.exists():p=O/'boxE-final'/('sources-'+r['pool']+'.json')
 if not p.exists():missing.append(str(p));continue
 meta=json.load(open(p));hist.add((r['tag'],*(meta[n]['sha256_geometry'] for n in m.groups()),*([r['mechanism']] if r.get('mechanism') else [])))
assert not missing,missing
(W/'completed-geometries26.json').write_text(json.dumps(sorted(hist)))
r={'old':old,'new':len(hist)-old,'total':len(hist),'missing':missing};(W/'history-rebuilt32.json').write_text(json.dumps(r));print(r)
with (T/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+f' boxA CLOSED prior geometry history {r}. START changed endpoint joins first, including valid non-winning held returns. Preserved 1.005 branch. Plain held kicks and 1.010 intake remain closed. Common deadline17:15Z.\n')
print('helpers',len(list(W.glob('*.py'))),'forced',len(ends+rects+oldnear))
