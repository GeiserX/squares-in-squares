from pathlib import Path
import shutil,csv,json,datetime,re
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r32/work';W=Path(__file__).resolve().parent;T=W.parent
for p in O.glob('*.py'):
 if p.name.startswith('setup'):continue
 s=p.read_text().replace('/tmp/squares-k123-r32-ssh','/tmp/squares-k123-r33-ssh').replace('handoff-r32.log','handoff-r33.log').replace('round32-briefs/bar32.tsv','round33-briefs/bar33.tsv').replace('17:15','00:15').replace('17:05','00:05').replace('17:25','00:25').replace('17:30','00:30')
 if p.name=='base25.py':
  s=s.replace('gather/round31-2026-11-16b.csv','gather/round32-2026-11-16a.csv').replace('gate/cand-round31-1116b','gate/cand-round32-1116a').replace("take-*-r31/take.tsv","take-*-r32/take.tsv").replace("take-*-r32/take.tsv')]):","take-*-r33/take.tsv')]):").replace("(31,'16')]","(31,'16'),(32,'16')]")
 if p.name=='stage24.py':
  s=s.replace('take-*-r31','take-*-r32').replace("*S.glob('take-*-r32')]:","*S.glob('take-*-r33')]:").replace("endswith('-r32')","endswith('-r33')").replace("['-r31/','-r32/']","['-r32/','-r33/']").replace("0 if '-r32/'","0 if '-r33/'")
 if p.name in ['collect22.py','report32.py']:s=s.replace('take-*-r32/take.tsv','take-*-r33/take.tsv')
 if p.name in ['resume26.py','deferred28.py']:
  s=s.replace('take-k123-r31/','take-k123-r32/').replace("'resume32'","'resume33'").replace("'deferred32'","'deferred33'")
 if p.name=='provenance24.py':s=s.replace('29|30|31|32','29|30|31|32|33')
 if p.name=='walker30.py':s=s.replace("'QUENCH_LIVE_ROUND', '32'","'QUENCH_LIVE_ROUND', '33'")
 if p.name=='admission32.py':
  s=s.replace("['round31-2026-11-16b.csv'","['round32-2026-11-16a.csv','round31-2026-11-16b.csv'").replace("[(31,'round31-2026-11-16b.csv')","[(32,'round32-2026-11-16a.csv'),(31,'round31-2026-11-16b.csv')")
 if p.name=='background29.py':s=s.replace("['feedstrip32.py',script,'prejoin31.py']","[script,'prejoin31.py']")
 if p.name=='finish26.py':
  s=s.replace('report32.py','report33.py').replace('round32-section','round33-section').replace('## Round 32','## Round 33').replace('tools/k123/r32','tools/k123/r33').replace('k123-r32-2026-11-16','k123-r33-2026-11-17').replace('round 32 k123','round 33 k123')
 if p.name=='report32.py':
  s=s.replace('round 32','round 33').replace('Round 32','Round 33').replace('beyond_other_live_r32','beyond_other_live_r33').replace('k123-r32-2026-11-16','k123-r33-2026-11-17').replace('tools/k123/r32','tools/k123/r33').replace('take-k123-r32/work','take-k123-r33/work').replace('round32-section','round33-section').replace('2026,11,16,17,25,0','2026,11,17,0,25,0')
 (W/('report33.py' if p.name=='report32.py' else p.name)).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv','fivebins30-control-passed','enable-wide30']:
 if (O/name).exists():shutil.copy(O/name,W/name)
for name in ['out','tasks','taskdone','certs']:(W/name).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('')
for name,m in [('deadline',15),('search-deadline',5)]:(W/name).write_text(str(datetime.datetime(2026,11,17,0,m,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round32-1116a/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round33-briefs/bar33.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
ends=[p for t in S.glob('take-*-r32') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r32/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*-threeway28-*.csv'))+list((O.parent/'near').glob('*-heldreturn31-*.csv'))+list((O.parent/'near').glob('*-prejoin31-*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in ends+rects+oldnear]));(W/'next28.json').write_text(json.dumps(json.load(open(S/'round33-briefs/r32-results.json'))['k123']['next']));(W/'measurements28.json').write_text('[]')
hist={tuple(x) for x in json.load(open(W/'completed-geometries26.json'))};old=len(hist);missing=[]
for line in (O/'records.jsonl').read_text().splitlines():
 r=json.loads(line);m=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if not m:continue
 p=O/r['pool']/('sources-'+r['pool']+'.json')
 if not p.exists():p=O/'boxE-final'/('sources-'+r['pool']+'.json')
 if not p.exists():missing.append(str(p));continue
 meta=json.load(open(p));hist.add((r['tag'],*(meta[n]['sha256_geometry'] for n in m.groups()),*([r['mechanism']] if r.get('mechanism') else [])))
assert not missing,missing
(W/'completed-geometries26.json').write_text(json.dumps(sorted(hist)));r={'old':old,'new':len(hist)-old,'total':len(hist),'missing':missing};(W/'history-rebuilt33.json').write_text(json.dumps(r));print(r)
with (T/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+f' boxA CLOSED prior geometry history {r}. START changed endpoint joins first, including valid non-winning returned bands. Preserved measured1.005 branch. Held kicks, dry1.010,1.003 and unchanged slide masks stay closed. Common deadline2026-11-17T00:15Z.\n')
print('helpers',len(list(W.glob('*.py'))),'forced',len(ends+rects+oldnear))
