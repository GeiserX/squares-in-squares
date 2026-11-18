from pathlib import Path
import json,subprocess,tarfile,shutil
W=Path(__file__).resolve().parent;S=W.parent.parent
shutil.copy(S/'take-k123-r33/work/fq-boxCD33',W/'fq')
configs={'boxE':json.load(open(W/'runtime33.json')),'boxD':{'python':'/Users/boxD/scratch/squares-quench/venv/bin/python','fq':'/Users/boxD/scratch/squares-k123/fq','partitions':list(range(10)),'slots':{s:['qrun22.py',s] for s in ['j22e','j22f','j22g']},'load_limit':9}}
for host,cfg in configs.items():
 D=W if host=='boxE' else W/host;D.mkdir(exist_ok=True);(D/'runtime33.json').write_text(json.dumps(cfg));(D/'box33').write_text('boxE' if host=='boxE' else host)
 archive=W/(host+'-boot36.tgz')
 with tarfile.open(archive,'w:gz') as t:
  for p in W.glob('*.py'):t.add(p,arcname=p.name)
  for n in ['deadline','search-deadline','details-base25.csv','completed-geometries26.json','queue.tsv','refused-inputs26.json','444-control.csv','board.tsv','enable-wide30','fq']:t.add(W/n,arcname=n)
  for n in ['runtime33.json','box33']:t.add(D/n,arcname=n)
  t.add(W/'lane',arcname='lane')
 subprocess.run(['ssh',host,'test ! -d $SCRATCH/squares-k123 && mkdir -p $SCRATCH/squares-k123/out $SCRATCH/squares-k123/claims $SCRATCH/squares-k123/tasks $SCRATCH/squares-k123/taskdone'],check=True)
 subprocess.run(['scp','-q',str(archive),host+':scratch/squares-k123/boot36.tgz'],check=True)
 subprocess.run(['ssh',host,'cd $SCRATCH/squares-k123 && tar xzf boot36.tgz && rm boot36.tgz && chmod +x fq'],check=True)
 cmd=f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I lane/k123_turn.py 444-control.csv 444 control444 {cfg["fq"]} --turns=0 --modes self --loosen 1.001 --bar 21.5647 --keep'
 r=subprocess.run(['ssh',host,cmd],check=True,text=True,capture_output=True);(D/'control444.log').write_text(r.stdout+r.stderr)
 out=subprocess.check_output(['ssh',host,'cat $SCRATCH/squares-k123/control444/turn-444.tsv'],text=True);assert '21.564693167754' in out,out
 (D/'control36.json').write_text(json.dumps({'side':21.564693167754,'output':out}));print(host,'control passed',flush=True)
