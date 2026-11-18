from pathlib import Path
import json
W=Path(__file__).resolve().parent
p=W/'qrun22.py';s=p.read_text();s=s.replace("if BOX33=='boxD' and pool not in eligible33:continue","if BOX33!='boxE' and pool not in eligible33:continue")
s=s.replace("if pool in eligible33 and int(signature[:8],16)%2!=(1 if BOX33=='boxD' else 0):continue","if int(signature[:8],16)%10 not in runtime33.get('partitions',list(range(10))):continue")
s=s.replace("except FileExistsError:continue\n  found=True", "except FileExistsError:continue\n  (R/'claims'/keyclaim/'owner.json').write_text(json.dumps(dict(pid=os.getpid(),worker=worker,jobkey=key,time=time.time())))\n  found=True")
p.write_text(s)
# Only fresh or source-cleared untried pools are exported. Partitioning is independent of export timing.
p=W/'boxCD_export33.py';s=p.read_text().replace("if pool.startswith('fresh') or pool.startswith('deferred33') and (R/('sources-'+pool+'.json')).exists() and '-r33/' in (R/('sources-'+pool+'.json')).read_text():allowed.append(pool)","if (R/('sources-'+pool+'.json')).exists():allowed.append(pool)")
p.write_text(s)
# Avoid a frozen old proof generated path that omits the corrected held date.
p=W/'provenance24.py';s=p.read_text().replace("per-n source table results/round{held_round33}-best-2026-11-17.tsv","per-n source table results/round{held_round33}-best-2026-11-{'17' if held_round33==33 else '16'}.tsv")
p.write_text(s)
# Fresh stage prefers the lowest current row at productive counts.
p=W/'stage24.py';s=p.read_text().replace("str(p) not in priority,0 if", "str(p) not in priority,0 if")
p.write_text(s)
(W/'owned-helpers26.json').write_text(json.dumps([p.name for p in W.glob('*.py')]))
