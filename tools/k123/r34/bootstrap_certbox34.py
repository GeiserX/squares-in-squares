from pathlib import Path
import subprocess,json,time,os,signal
W=Path(__file__).resolve().parent;S=W.parent.parent;gid=int((W/'guardian34.pid').read_text());os.kill(gid,signal.SIGSTOP)
def run(a):return subprocess.run(a,check=True,timeout=45)
try:
 for host in ['boxE','boxC']:
  for name in ['third22.py','verify26.py','cert_once22.py']:
   run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-'+host,str(W/name),host+':scratch/squares-k123/'])
  cfg=json.load((W/'runtime33.json' if host=='boxE' else W/host/'runtime33.json').open())
  run(['ssh','-S','/tmp/squares-k123-r34-'+host,host,f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I stop_remote25.py'])
  if host=='boxC':
   cfg['slots']={'j22i':['qrun22.py','j22i'],'third':['third22.py']};cfg['spare_join']='j22l';(W/host/'runtime33.json').write_text(json.dumps(cfg));run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-boxC',str(W/host/'runtime33.json'),'boxC:scratch/squares-k123/'])
   run(['ssh','-S','/tmp/squares-k123-r34-boxC','boxC','mkdir -p $SCRATCH/squares-k123/proxy-control580'])
   for p,dest in [(S/'take-k123-r26/580.csv','proxy-control580/580.csv'),(S/'gate/cand-round25-1114b/details.csv','proxy-control-details.csv')]:run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-boxC',str(p),'boxC:scratch/squares-k123/'+dest])
   j=dict(kind='verify',tag='verify-proxy-control580',out='proxy-control580-out',raws=['proxy-control580'],details='proxy-control-details.csv',source='positive certification control from held25b580',cert_box34='boxC');p=W/(j['tag']+'.json');p.write_text(json.dumps(j));run(['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-boxC',str(p),'boxC:scratch/squares-k123/tasks/'])
  run(['ssh','-S','/tmp/squares-k123-r34-'+host,host,f'cd $SCRATCH/squares-k123 && nohup nice -n 5 {cfg["python"]} -I box_guard34.py > out/box-guard34-certbox.log 2>&1 < /dev/null &'])
finally:os.kill(gid,signal.SIGCONT)
with (W.parent/'STATE.txt').open('a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+' boxA START boxC certification fallback inside its two-slot budget: one join plus a cert/scanner slot with spare joinj22l. boxE remains under load16; no process of another lane changed. Third-worker tasks now atomically claim files and restore interrupted claims on restart. Real580 finesafe control queued on boxC before live certificates. Logs work/cert-proxy34.log, cutoff07:25Z.\n')
print('certbox bootstrapped',flush=True)
