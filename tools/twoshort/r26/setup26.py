"""Port the round 25 twoshort tools to round 26 paths, base and seeds."""
from pathlib import Path
import shutil,datetime,json,csv,re
B=Path('$SCRATCH/bounties-squares');W=B/'take-twoshort-r26/work';O=B/'take-twoshort-r25/work'
for x in ['lane','starts','jobs','locks','runs','done','q','tmp','designs','stage','reference','boxE26','intake','proofs','libraries','empty-old/jobs','empty-old/locks']:(W/x).mkdir(parents=True,exist_ok=True)
for p in Path('.').glob('*.py'):shutil.copy2(p,W/'lane'/p.name)
for name in ['shape974.py','control22.py','cornerhot22.py','cornerlk22.py']:shutil.copy2(O/name,W/name)
MODS=['admit','ancestry_index','bar','source','certify','prune_take','prioritize','worker','manage','design','specs','union','family_targets','results','copy','status','audit_near','promote_legs','prune_remote']
for name in MODS:
 s=(O/(name+'25.py')).read_text()
 for m in MODS:s=re.sub(r'\b'+m+r'25\b',m+'26',s)
 s=s.replace('take-twoshort-r25','take-twoshort-r26').replace('handoff-r25.log','handoff-r26.log').replace('boxE25','boxE26').replace('STOP25','STOP26')
 s=s.replace('deadline02:45UTC','deadline17:15UTC').replace("'02:45UTC'","'17:15UTC'")
 s=s.replace('seed=625','seed=725').replace('-625.json','-725.json').replace("'-s625'","'-s725'").replace('-s625','-s725')
 s=s.replace('v25q','v26q').replace('twoshort round25','twoshort round26')
 if name=='manage':
  s=s.replace('gate/cand-round23-1113b/details.csv','gate/cand-round25-1114b/details.csv')
 (W/(name+'26.py')).write_text(s)
end=int(datetime.datetime(2026,11,14,17,15,tzinfo=datetime.timezone.utc).timestamp())
(W/'deadline').write_text(str(end));(W/'search-deadline').write_text(str(end-12*60))
if not (W.parent/'take.tsv').exists():(W.parent/'take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n')
shutil.copy2(O/'starts/control793.csv',W/'starts/control793.csv') if (O/'starts/control793.csv').exists() else None
print('setup complete',end)
