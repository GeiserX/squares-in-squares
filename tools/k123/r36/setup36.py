from pathlib import Path
import shutil,csv,json,re,datetime
S=Path('$SCRATCH/bounties-squares');O=S/'take-k123-r35/work';W=Path(__file__).resolve().parent;T=W.parent
for p in O.glob('*.py'):
 if p.name.startswith('setup'):continue
 s=p.read_text().replace('/tmp/squares-k123-r35','/tmp/squares-k123-r36').replace('handoff-r35.log','handoff-r36.log').replace('round35-briefs/bar35.tsv','round36-briefs/bar36.tsv')
 s=s.replace('16:25','23:45').replace('15:55','23:25').replace('16:35','23:55')
 if p.name=='base25.py':
  s=s.replace('round34-2026-11-17a.csv','round35-2026-11-17a.csv').replace('cand-round34-1117a','cand-round35-1117a').replace('take-*-r35','take-*-r36').replace("(34,'17')]","(34,'17'),(35,'17')]").replace('held round34','held round35').replace('of round 34','of round 35').replace('round34-best','round35-best')
 if p.name in ['stage24.py','collect22.py','peer33.py','retention32.py','validate25.py','independent33.py']:s=s.replace('take-*-r35','take-*-r36')
 if p.name=='stage24.py':s=s.replace('take-*-r34','take-*-r35').replace("endswith('-r35')","endswith('-r36')").replace("['-r34/','-r35/']","['-r35/','-r36/']").replace("0 if '-r35/'","0 if '-r36/'")
 if p.name in ['resume26.py','deferred28.py']:s=s.replace('take-k123-r34/','take-k123-r35/').replace("'resume35'","'resume36'").replace("'deferred35'","'deferred36'")
 if p.name=='provenance24.py':s=s.replace('|33|34|35)/','|33|34|35|36)/').replace('in (33,34)','in (33,34,35)')
 if p.name=='admission32.py':s=s.replace("['round34-2026-11-17a.csv'","['round35-2026-11-17a.csv','round34-2026-11-17a.csv'").replace("[(34,'round34-2026-11-17a.csv')","[(35,'round35-2026-11-17a.csv'),(34,'round34-2026-11-17a.csv')")
 if p.name=='walker30.py':
  s=s.replace("'QUENCH_LIVE_ROUND', '35'","'QUENCH_LIVE_ROUND', '36'").replace('def walk(start, n, cap=3000):','def walk(start, n, cap=100000):').replace("'clean': not hits, 'hits'","'clean': not hits, 'capped': len(seen)>=100000, 'hits'")
 if p.name=='bridge34.py':s=s.replace("boxes={'boxC':['j22i','j22j'],'boxD':['j22e','j22f','j22g','j22h','j22k']}","boxes={'boxD':['j22e','j22f','j22g']}").replace("for host in ['boxC','boxD','boxE']:","for host in ['boxD','boxE']:")
 (W/p.name).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','completed-geometries26.json','444-control.csv','board.tsv','fivebins30-control-passed','enable-wide30','runtime33.json','box33']:
 if (O/name).exists():shutil.copy(O/name,W/name)
for n in ['out','tasks','taskdone','certs','boxD']:(W/n).mkdir(exist_ok=True)
(T/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n');(W/'records.jsonl').write_text('');(W/'queue.tsv').write_text('');(W/'refused-inputs26.json').write_text('{}');(W/'measurements28.json').write_text('[]')
for name,hm in [('deadline',(23,45)),('search-deadline',(23,25)),('finalize-at32',(23,40))]:(W/name).write_text(str(datetime.datetime(2026,11,17,*hm,tzinfo=datetime.timezone.utc).timestamp()))
rows=list(csv.DictReader(open(S/'gate/cand-round35-1117a/details.csv')));bars={int(r['n']):r['bar'] for r in csv.DictReader(open(S/'round36-briefs/bar36.tsv'),delimiter='\t')}
for r in rows:r['score']=bars[int(r['n'])]
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
shutil.copy(S/'take-backlog-r35/work/share/zips.json',W/'share/zips.json')
ends=[p for t in S.glob('take-*-r35') for p in t.glob('*.csv')];rects=list((S/'take-forensics-r35/near').glob('*-rect.csv'));oldnear=list((O.parent/'near').glob('*.csv'))
(W/'force-fresh28.json').write_text(json.dumps([str(p) for p in ends+rects+oldnear]));(W/'priority-inputs31.json').write_text(json.dumps([str(p) for p in ends]));(W/'next28.json').write_text(json.dumps(json.load(open(S/'round36-briefs/r35-results.json'))['k123']['next']))
hist={tuple(x) for x in json.load(open(W/'completed-geometries26.json'))};old=len(hist);missing=[]
for line in (O/'records.jsonl').read_text().splitlines():
 r=json.loads(line);m=re.match(r'(\d+)r?-(\d+)r?-j',r['tag'])
 if not m:continue
 ps=[O/r['pool']/('sources-'+r['pool']+'.json'),O/'boxE-final'/('sources-'+r['pool']+'.json')];p=next((p for p in ps if p.exists()),None)
 if p is None:missing.append(r['pool']);continue
 meta=json.load(open(p));hist.add((r['tag'],*(meta[n]['sha256_geometry'] for n in m.groups()),*([r['mechanism']] if r.get('mechanism') else [])))
(W/'completed-geometries26.json').write_text(json.dumps(sorted(hist)));r={'old':old,'new':len(hist)-old,'total':len(hist),'missing':len(missing),'missing_first':missing[:5]};(W/'history-rebuilt36.json').write_text(json.dumps(r));print(r)
cfg=json.load(open(W/'runtime33.json'));cfg.update(partitions=list(range(10)),slots={'j22a':['qrun22.py','j22a'],'j22d':['qrun22.py','j22d'],'third':['third22.py']});(W/'runtime33.json').write_text(json.dumps(cfg))
with (T/'STATE.txt').open('a') as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA SETUP36: r35 next item 1 first, changed held sources then valid near donors, because they fed 693 and 803 last round. Fresh input or finish mechanism required to reopen history. boxE3 and boxD:3 slots only. Deadline23:45Z. Closed history '+json.dumps(r)+'\n')
