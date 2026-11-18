import pathlib,shutil,datetime,csv,json
S=pathlib.Path('$SCRATCH/bounties-squares');W=S/'take-k123-r28/work';O=S/'take-k123-r27/work'
for p in O.glob('*.py'):
 s=p.read_text().replace('/tmp/squares-k123-r27-ssh','/tmp/squares-k123-r29-ssh').replace('handoff-r27.log','handoff-r29.log').replace("take-*-r27/", "take-*-r29/").replace("glob('take-*-r27')","glob('take-*-r29')").replace('round27-briefs/bar27.tsv','round29-briefs/bar29.tsv').replace('r27-full-tree-v6','r28-full-tree-v1').replace('23:45','05:45').replace('23:35','05:35').replace('23:55','05:55').replace('00:00Z','06:00Z')
 (W/p.name).write_text(s)
shutil.copytree(O/'lane',W/'lane',ignore=shutil.ignore_patterns('__pycache__'),dirs_exist_ok=True)
for name in ['base-credit24.json','seed-origin24.json','clean-replacements25.json','completed-geometries26.json','board.tsv','444-control.csv']:
 if (O/name).exists():shutil.copy(O/name,W/name)
for name,minute in [('deadline',45),('search-deadline',35)]: (W/name).write_text(str(datetime.datetime(2026,11,15,5,minute,tzinfo=datetime.timezone.utc).timestamp()))
(W.parent/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
bars={int(r['n']):float(r['bar']) for r in csv.DictReader(open(S/'round29-briefs/bar29.tsv'),delimiter='\t')}
rows=list(csv.DictReader(open(S/'gate/cand-round26-1114b/details.csv')))
for r in rows:r['score']=repr(bars[int(r['n'])])
with open(W/'details-base25.csv','w') as f:
 wr=csv.DictWriter(f,rows[0].keys());wr.writeheader();wr.writerows(rows)
p=W/'base25.py';s=p.read_text().replace('round25-2026-11-14b','round26-2026-11-14b').replace('cand-round25-1114b','cand-round26-1114b').replace('round25-best-2026-11-14','round26-best-2026-11-14').replace("[*S.glob('take-*-r26/take.tsv'),*S.glob('take-*-r29/take.tsv')]","[*S.glob('take-*-r27/take.tsv'),*S.glob('take-*-r29/take.tsv')]");s=s.replace('if abs(s-scores[n])>1e-8:continue',"if abs(s-float(rows[n]['score']))>1e-8:continue");p.write_text(s)
p=W/'provenance24.py';s=p.read_text().replace('23|24|25|26|27','23|24|25|26|27|28');p.write_text(s)
# Resume r27 exact unrun arrays. Older pending recipes are nested in its queue.
p=W/'resume26.py';s=p.read_text().replace("O=S/'take-k123-r26/work'","O=S/'take-k123-r27/work'").replace("tag='resume27'","tag='resume28'").replace("'take-k123-r26/'","'take-k123-r27/'");p.write_text(s)
# Do not reopen previously measured history blindly. Fresh r27 ends precede r28 near files.
p=W/'stage24.py';s=p.read_text().replace("for t in S.glob('take-*-r29'):","for t in [*S.glob('take-*-r29'),*S.glob('take-*-r27')]:");s=s.replace("if '-r26/' in p", "if any(r in p for r in ['-r27/','-r28/'])");p.write_text(s)
p=W/'resident25.py';s=p.read_text().replace("['reopen27.py','stage24.py','resume26.py','storage26.py']","['stage24.py','resume26.py','storage26.py']");p.write_text(s)
# Boot is inputs only, with existing concrete 444 control.
p=W/'boot27.py';s=p.read_text();a=s.index('O=W.parent.parent');b=s.index('with tarfile.open',a);s=s[:a]+s[b:];s=s.replace("'444-control.csv']","'444-control.csv','board.tsv']");p.write_text(s)
p=W/'finish26.py';s=p.read_text().replace("report27.py","report28.py").replace("round27-section.md","round28-section.md").replace("Round 27","Round 28").replace("k123-r27-2026-11-14","k123-r28-2026-11-15").replace("tools/k123/r27","tools/k123/r28").replace("round 27 k123","round 28 k123").replace("23:55Z","05:55Z");p.write_text(s)
