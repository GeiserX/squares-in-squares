import pathlib,subprocess,json,shutil,time
W=pathlib.Path(__file__).resolve().parent;SSH=['ssh','-S','/tmp/squares-k123-r29-ssh','boxE']
p=W/'verify26.py';s=p.read_text().replace("str(R/'details-base25.csv')", "str(R/j.get('details','details-base25.csv'))");p.write_text(s)
subprocess.run(SSH+['mkdir -p $SCRATCH/squares-k123/control580'],check=True)
for path,dest in [(W/'verify26.py','verify26.py'),(W.parent.parent/'take-k123-r26/580.csv','control580/580.csv'),(W.parent.parent/'gate/cand-round25-1114b/details.csv','control-details.csv')]:
 subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r29-ssh',str(path),'boxE:scratch/squares-k123/'+dest],check=True)
job=dict(kind='verify',tag='verify-control26-580',out='control-verify580',source='positive control held round25b 580',raws=['control580'],details='control-details.csv')
p=W/'verify-control26-580.json';p.write_text(json.dumps(job));subprocess.run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r29-ssh',str(p),'boxE:scratch/squares-k123/tasks/'],check=True)
cmd="cd $SCRATCH/squares-k123 && nohup nice -n 5 $SCRATCH/squares-base/venv/bin/python -I third22.py > out/third.log 2>&1 < /dev/null &"
subprocess.run(SSH+[cmd],check=True)
# Three join slots stay separate from the scan/certification slot.
for worker in ['j22a','j22b','j22d']:
 subprocess.run(SSH+[f'cd $SCRATCH/squares-k123 && nohup nice -n 5 $SCRATCH/squares-base/venv/bin/python -I qrun22.py {worker} > out/{worker}.log 2>&1 < /dev/null &'],check=True)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxE START four numerical slots qrun22.py j22a,j22b,j22d and third22.py after ps ownership check. 444 control21.564693167754 vs21.564693168782. Verification control580 queued with older bar. Logs out/j22*.log,out/third.log. Search cutoff11:35, common hard11:45Z.\n')
print('four boxE slots launched',flush=True)
