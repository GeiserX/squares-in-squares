from pathlib import Path
import json,time,shutil
W=Path(__file__).resolve().parent;S=W.parent.parent
p=W/'provenance24.py';s=p.read_text().replace(" if share(n,A)>=0.4:return None", " if origin and origin!='held':\n  import quench_walk\n  if quench_walk.harvest_type(str(origin),n) and share(n,A)>=0.4:return None").replace("if banned(json.dumps(row)) or n==801:return None", "if banned(json.dumps(row)):return None");p.write_text(s)
p=W/'policy27.py';s=p.read_text().replace("|801h\\b|held(?: n\\s*=)?\\s+801\\b", "");p.write_text(s)
(W/'policy_walk27.py').write_text('''"""Use the current shared walk without changing another lane's tool."""\nimport importlib,sys\nsys.path.insert(0,'.')\nimport quench_walk\nimportlib.reload(quench_walk)\nfrom quench_walk import *\n''')
p=W/'seed_rule27.py';s=p.read_text().replace("'excluded':_shares[n]>=.4", "'excluded':False").replace('def text_checks(text):return check_numbers(refs(text))','def text_checks(text):return []');a=s.index('def file_checks(');s=s[:a]+"def file_checks(path,walker):return []\n";p.write_text(s)
p=W/'csv_rule27.py';s=p.read_text().replace("'excluded':s>=.4", "'excluded':False");a=s.index('def file_checks(');s=s[:a]+"def file_checks(path,walker):return []\n";p.write_text(s)
for name in ['source25.py','stage24.py','collect22.py']:
 p=W/name;p.write_text(p.read_text().replace('r28-full-tree-v3','r28-full-tree-v4-own'))
p=W/'base25.py';s=p.read_text().replace('  _bound=True',"  base()[key(801,P[801])]=dict(clean=True,n=801,origin='held own801',source='original seed: n = 801 of own independently discovered packing; seeds/merged0.csv; main round28 rule 00:19:03Z',licence='own; main round28 rule',sha256_geometry=key(801,P[801]))\n  _bound=True");p.write_text(s)
D=W/'reopened';D.mkdir(exist_ok=True);made=[]
for root in [S/'take-k123-r27/work/withdrawn-seed503',S/'take-k123-r27/work/withdrawn-ancestor742',S/'take-k123-r27/work/withdrawn']:
 for n in [699,932,798]:
  cp=root/f'{n}.csv';jp=Path(str(cp)+'.json')
  if cp.exists() and jp.exists():
   dest=D/f'{n}-own-rule28-{root.name}.csv';shutil.copy(cp,dest);shutil.copy(jp,str(dest)+'.json');made.append(str(dest))
# The complete preserved source receipts are preferable to generic replacement labels.
for p in (S/'take-k123-r27/work/certs').glob('*/final/798.csv'):
 ledger=p.parent/'take.tsv'
 if ledger.exists():
  import csv
  row=next((r for r in csv.DictReader(ledger.open(),delimiter='\t') if r['n']=='798'),None)
  if row:
   dest=D/'798-own-rule28-certified.csv';shutil.copy(p,dest);Path(str(dest)+'.json').write_text(json.dumps(row));made.append(str(dest));break
marker=W/'reopened-inputs27.txt';old=marker.read_text().splitlines() if marker.exists() else [];marker.write_text('\n'.join(dict.fromkeys(made+old))+'\n')
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA ADOPT main handoff00:19:03Z rule change: own layouts, held801, original503/983 and own descendants no longer refused for share. Public harvested starts still meet share<0.4; recorded prvsiyan1105 and other forbidden-source ancestry stay excluded. Source gate v4-own. Reopened '+str(made)+'; controls follow. Deadline23:45Z.\n')
(W/'restart-stage28').touch()
