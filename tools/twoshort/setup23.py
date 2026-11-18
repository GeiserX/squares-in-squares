from pathlib import Path
import csv,json,math,shutil,datetime
B=Path('$SCRATCH/bounties-squares');T=B/'take-twoshort-r23';W=T/'work';OLD=B/'take-twoshort-r22/work'
for x in ['lane','starts','jobs','locks','runs','done','q','tmp','designs','stage','reference']:(W/x).mkdir(exist_ok=True)
for p in Path('.').glob('*.py'):shutil.copy2(p,W/'lane'/p.name)
shutil.copy2(OLD/'shape974.py',W/'shape974.py')
for name in ['control22.py','cornerhot22.py','cornerlk22.py']:shutil.copy2(OLD/name,W/name)
s=(OLD/'worker22.py').read_text().replace('STOP22','STOP23').replace('design22.py','design23.py')
s=s.replace("if tag=='control793':return","if tag=='control793':return")
s=s.replace("if cur!=j['start'] and best<bar+0.00015", "if (cur!=j['start'] or j.get('force_quench')) and best<bar+0.0007")
s=s.replace("shutil.copy2(cur,qfile)","shutil.copy2(cur,qfile)\n  sys.path.insert(0,str(R/'lane'));import floatsafe\n  fr=floatsafe.work((n,[{k:r[k] for k in ('n','square_id','x','y','angle')} for r in csv.DictReader(open(qfile))]))[1]\n  if fr is None:raise RuntimeError('cannot certify quench input')\n  with open(qfile,'w',newline='') as f:\n   cw=csv.DictWriter(f,fieldnames=['n','square_id','x','y','angle']);cw.writeheader();cw.writerows(fr)")
s=s.replace("if j['remaining']>1 and miss<3", "if j['remaining']>1 and miss<2")
# Fork only raw finds that moved at least 1e-7; first passes outrank dry continuations.
s=s.replace("jj.update(start=cur,seed=seed+1,remaining=j['remaining']-1,miss=miss,priority=2 if improved else 8)","jj.update(start=cur,seed=seed+1,remaining=j['remaining']-1,miss=miss,priority=2 if start-best>1e-7 else 8)")
(W/'worker23.py').write_text(s)
s=(OLD/'certify22.py').read_text().replace('r22','r23').replace('r21','r22').replace('round20','round21')
# r22 and r23, exactly the two reference rounds.
s=s.replace("'take-*-r23/take.tsv'))+list(B.glob('take-*-r23/take.tsv'", "'take-*-r22/take.tsv'))+list(B.glob('take-*-r23/take.tsv'")
(W/'certify23.py').write_text(s)
held={int(r['n']):float(r['score']) for r in csv.DictReader(open(B/'gate/cand-round21-1113a/details.csv'))};bar=dict(held)
for p in list(B.glob('take-*-r22/take.tsv'))+list(B.glob('take-*-r23/take.tsv')):
 for r in csv.DictReader(open(p),delimiter='\t'):bar[int(r['n'])]=min(bar[int(r['n'])],float(r['new']))
(W/'bar.json').write_text(json.dumps({str(n):(1+s)*math.sqrt(n) for n,s in bar.items()}))
(W/'deadline').write_text(str(int(datetime.datetime(2026,11,13,18,30,tzinfo=datetime.timezone.utc).timestamp())))
shutil.copy2(OLD/'starts/control793.csv',W/'starts/control793.csv')
j=dict(tag='control793',n=793,start='starts/control793.csv',seed=21,remaining=1,seconds=60,miss=0,priority=0,source='twoshort positive control, own staircase family build',licence='our own design')
(W/'jobs/000-control793-21.json').write_text(json.dumps(j))
with open(T/'take.tsv.tmp','w') as f:f.write('n\theld\tnew\tgain\tsource\tlicence\n')
(T/'take.tsv.tmp').replace(T/'take.tsv')
print('setup complete')
