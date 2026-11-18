import pathlib,subprocess,tarfile,json,shutil
W=pathlib.Path(__file__).resolve().parent
for d in ['out','tasks','taskdone','certs']:(W/d).mkdir(exist_ok=True)
(W/'queue.tsv').write_text('');(W/'refused-inputs26.json').write_text('{}')
# The old file is a real input to a numerical control, not a copied success marker.
with tarfile.open(W/'boot27.tgz','w:gz') as t:
 for p in W.glob('*.py'):t.add(p,arcname=p.name)
 for name in ['deadline','search-deadline','details-base25.csv','completed-geometries26.json','queue.tsv','refused-inputs26.json','444-control.csv','board.tsv']:t.add(W/name,arcname=name)
 t.add(W/'lane',arcname='lane')
subprocess.run(['ssh','boxE','test ! -d $SCRATCH/squares-k123 && mkdir -p $SCRATCH/squares-k123/out $SCRATCH/squares-k123/tasks $SCRATCH/squares-k123/taskdone'],check=True)
subprocess.run(['scp','-q',str(W/'boot27.tgz'),'boxE:scratch/squares-k123/'],check=True)
subprocess.run(['ssh','boxE','cd $SCRATCH/squares-k123 && tar xzf boot27.tgz && rm boot27.tgz'],check=True)
