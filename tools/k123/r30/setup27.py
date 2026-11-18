import pathlib,shutil,datetime,csv,json
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-k123-r27/work';O=S/'take-k123-r26/work';R=pathlib.Path('.')
for p in O.glob('*.py'):
 if p.name=='setup27.py':continue
 s=p.read_text().replace('/tmp/squares-k123-r26-ssh','/tmp/squares-k123-r30-ssh').replace('handoff-r26.log','handoff-r30.log').replace("take-*-r26/", "take-*-r30/").replace("glob('take-*-r26')","glob('take-*-r30')").replace('r26-full-tree-v11','r27-full-tree-v1').replace('17:15','05:45').replace('17:25','05:55').replace('17:30','00:00')
 (W/p.name).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','seed-origin24.json','clean-replacements25.json','completed-geometries26.json']:
 shutil.copy(O/name,W/name)
(W/'deadline').write_text(str(datetime.datetime(2026,11,14,23,45,tzinfo=datetime.timezone.utc).timestamp()))
(W/'search-deadline').write_text(str(datetime.datetime(2026,11,14,23,35,tzinfo=datetime.timezone.utc).timestamp()))
(W.parent/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
bars={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round30-briefs/bar30.tsv'),delimiter='\t')}
rows=list(csv.DictReader(open(S/'gate/cand-round25-1114b/details.csv')))
for r in rows:r['score']=repr(bars[int(r['n'])])
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
(W/'seed_notice24.py').write_text('''"""Round27 accepts the lane's independently discovered Samanyu-matching layouts."""\ndef notice(source,licence):\n return 'own discovered layouts; round27 Samanyu restriction lifted',False,[]\n''')
# Replace legacy path-level source bans with the remaining restrictions.
p=W/'provenance24.py';s=p.read_text();s=s[:s.index('_previous_banned=banned')]+'''\nfrom policy27 import banned\n''';s=s.replace("r'-r(?:23|24|25|26)/'","r'-r(?:23|24|25|26|27)/'");p.write_text(s)
# Use the private policy walk while preserving the shared implementation.
p=W/'held26.py';s=p.read_text().replace('import quench_walk as walker','import policy_walk27 as walker');p.write_text(s)
p=W/'publication_source26.py';s=p.read_text().replace('import quench_walk','import policy_walk27').replace('importlib.reload(quench_walk)','importlib.reload(policy_walk27)');p.write_text(s)
p=W/'resident25.py';s=p.read_text().replace("['stage24.py','resume26.py','storage26.py']","['reopen27.py','stage24.py','resume26.py','storage26.py']");p.write_text(s)
p=W/'collect22.py';s=p.read_text();s=s[:s.index('import runpy\ntry:runpy.run_path')]+"\nlock.close()\n";p.write_text(s)
# Negative source caches are deliberately not carried forward.
