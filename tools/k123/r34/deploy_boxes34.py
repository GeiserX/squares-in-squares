from pathlib import Path
import json,subprocess,tarfile,shutil
W=Path(__file__).resolve().parent;S=W.parent.parent
shutil.copy(S/'take-k123-r33/work/fq-boxCD33',W/'fq')
for host,user,runtime,slots,parts in [('boxC','boxC','squares-corners',['j22i','j22j'],[3,4]),('boxD','boxD','squares-quench',['j22e','j22f','j22g','j22h','j22k'],[5,6,7,8,9])]:
 cfg={'python':f'/Users/{user}/scratch/{runtime}/venv/bin/python','fq':f'/Users/{user}/scratch/squares-k123/fq','partitions':parts,'slots':{s:['qrun22.py',s] for s in slots},'load_limit':9}
 root=W/host;root.mkdir(exist_ok=True);(root/'runtime33.json').write_text(json.dumps(cfg));(root/'box33').write_text(host)
 with tarfile.open(W/(host+'-boot34.tgz'),'w:gz') as t:
  for p in W.glob('*.py'):t.add(p,arcname=p.name)
  for name in ['deadline','search-deadline','details-base25.csv','completed-geometries26.json','queue.tsv','refused-inputs26.json','444-control.csv','board.tsv','enable-wide30','fq']:t.add(W/name,arcname=name)
  for name in ['runtime33.json','box33']:t.add(root/name,arcname=name)
  t.add(W/'lane',arcname='lane')
 subprocess.run(['ssh',host,'test ! -d $SCRATCH/squares-k123 && mkdir -p $SCRATCH/squares-k123/out $SCRATCH/squares-k123/claims $SCRATCH/squares-k123/tasks $SCRATCH/squares-k123/taskdone'],check=True)
 subprocess.run(['scp','-q',str(W/(host+'-boot34.tgz')),host+':scratch/squares-k123/boot34.tgz'],check=True)
 subprocess.run(['ssh',host,'cd $SCRATCH/squares-k123 && tar xzf boot34.tgz && rm boot34.tgz && chmod +x fq'],check=True)
 cmd=f'cd $SCRATCH/squares-k123 && {cfg["python"]} -I lane/k123_turn.py 444-control.csv 444 control444 {cfg["fq"]} --turns=0 --modes self --loosen 1.001 --bar 21.5647 --keep'
 result=subprocess.run(['ssh',host,cmd],check=True,text=True,capture_output=True);(root/'control444.log').write_text(result.stdout+result.stderr)
 text=subprocess.check_output(['ssh',host,'cat $SCRATCH/squares-k123/control444/turn-444.tsv'],text=True);assert '21.564693167754' in text
 (root/'control34.json').write_text(json.dumps({'side':21.564693167754,'output':text,'scipy':'1.18.1'}))
 print(host,'control passed',flush=True)
