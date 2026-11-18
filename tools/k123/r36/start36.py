from pathlib import Path
import subprocess,json,time,os,csv
W=Path(__file__).resolve().parent;S=W.parent.parent;PY=str(S/'venv/bin/python')
assert json.load(open(W/'controls29.json'))['own756_accepted']
for host in ['boxE','boxD']:
 for name in ['boxCD_import33.py','qrun22.py','box_guard34.py']:subprocess.run(['scp','-q',str(W/name),host+':scratch/squares-k123/'],check=True)
# A valid old held improvement must pass the unchanged boxE verifier before new rows can publish.
subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-k123/control580'],check=True)
for p,dest in [(S/'take-k123-r26/580.csv','control580/580.csv'),(S/'gate/cand-round25-1114b/details.csv','control-details.csv')]:subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/'+dest],check=True)
job=dict(kind='verify',tag='verify-control26-580',out='control-verify580',source='positive control held round25b 580',raws=['control580'],details='control-details.csv');p=W/'verify-control26-580.json';p.write_text(json.dumps(job));subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
for host in ['boxE','boxD']:
 cfg=json.load(open(W/('runtime33.json' if host=='boxE' else host+'/runtime33.json')))
 subprocess.run(['ssh',host,f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {cfg["python"]} -I box_guard34.py > out/box-guard34.log 2>&1 < /dev/null &'],check=True)
started=[]
for name,args in [('collect',['resident25.py','collect']),('stage',['resident25.py','stage']),('third',['background29.py','third']),('storage',['background29.py','storage']),('bridge34',['bridge34.py'])]:
 with open(W/(name+'-r36.log'),'a') as f:p=subprocess.Popen(['nohup','nice','-n','5',PY,str(W/args[0]),*args[1:]],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
 (W/(name+'.pid')).write_text(str(p.pid));started.append(dict(name=name,pid=p.pid))
# Feed lowest live changed held geometry first, before stale copies of prior takes.
rows=list(csv.DictReader(open('results/round35-best-2026-11-17.tsv'),delimiter='\t'));ns=[int(r['n']) for r in rows]
s=(W/'seed35.py').read_text();a=s.index('for n in [');b=s.index(':',a);s=s[:a]+'for n in '+repr(ns)+s[b:];s=s.replace('licensed35','licensed36').replace('round 34','round 35').replace('round35 lowest','round36 lowest');(W/'seed36.py').write_text(s)
with open(W/'seed36.log','a') as f:p=subprocess.Popen(['nohup','nice','-n','5',PY,str(W/'seed36.py')],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
(W/'seed36.pid').write_text(str(p.pid));started.append(dict(name='seed36',pid=p.pid))
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: round36 band joins START. Controls reproduce side21.564693167754 on boxE and boxD. Own756 source and changed-producer controls pass. boxE3 and boxD:3 slots, one central per-recipe claim queue, no fixed box partitions. Changed lowest live r35 geometries first, then valid near donors. 28114 completed geometry signatures closed. New walk cap100000 with explicit capped flag. Hard search/quench23:45Z. '+str(W.parent)+'\n'
for p in [W.parent/'STATE.txt',S/'handoff-r36.log']:
 with p.open('a') as f:f.write(line)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START '+json.dumps(started)+' logs work/*-r36.log and seed36.log, deadline23:45Z. Final walk starts23:05Z.\n')
print(json.dumps(started))
