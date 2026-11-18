from pathlib import Path
import subprocess,json,time,os
W=Path(__file__).resolve().parent;S=W.parent.parent
assert json.load((W/'controls29.json').open())['own756_accepted']
r=subprocess.run(['ssh','boxE','cat $SCRATCH/squares-k123/control444/turn-444.tsv'],check=True,text=True,capture_output=True);assert '21.564693167754' in r.stdout
(W/'numerical-control34.json').write_text(json.dumps({'side':21.564693167754,'reference':21.564693168782,'output':r.stdout}))
subprocess.run(['ssh','boxE','mkdir -p $SCRATCH/squares-k123/control580'],check=True)
for p,dest in [(S/'take-k123-r26/580.csv','control580/580.csv'),(S/'gate/cand-round25-1114b/details.csv','control-details.csv')]:subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/'+dest],check=True)
job=dict(kind='verify',tag='verify-control26-580',out='control-verify580',source='positive control held round25b 580',raws=['control580'],details='control-details.csv')
p=W/'verify-control26-580.json';p.write_text(json.dumps(job));subprocess.run(['scp','-q',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
subprocess.run(['ssh','boxE','cd $SCRATCH/squares-k123 && nohup nice -n 5 $SCRATCH/squares-base/venv/bin/python -I box_guard34.py > out/box-guard34.log 2>&1 < /dev/null &'],check=True)
# Controllers stay on collector, all numerical work stays on assigned boxes.
PY=str(S/'venv/bin/python');started=[]
for name,args in [('collect',['resident25.py','collect']),('stage',['resident25.py','stage']),('third',['background29.py','third']),('storage',['background29.py','storage'])]:
 with open(W/(name+'-resident29.log'),'a') as f:p=subprocess.Popen(['nohup','nice','-n','5',PY,str(W/args[0]),*args[1:]],stdout=f,stderr=f,stdin=subprocess.DEVNULL,start_new_session=True)
 (W/(name+'.pid')).write_text(str(p.pid));started.append(dict(name=name,pid=p.pid,args=args))
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: round34 fresh band joins START boxE4 after 444 positive control21.564693167754 and own756 source control. 19,209 completed signatures closed; fresh259/445/968/734 first, then valid non-winning donors. boxC+2 and boxD+5 prepared under load9; partitions disjoint. Search intake23:25, hard search/quench23:45Z. '+str(W.parent)+'\n'
for q in [W.parent/'STATE.txt',S/'handoff-r36.log']:
 with q.open('a') as f:f.write(line)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START '+json.dumps(started)+' logs work/*-resident29.log, deadline23:45Z.\n')
print(json.dumps(started))
