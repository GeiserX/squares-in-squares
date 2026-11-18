import pathlib,subprocess,tarfile,json
W=pathlib.Path(__file__).resolve().parent
for d in ['out','tasks','taskdone','certs']:(W/d).mkdir(exist_ok=True)
(W/'queue.tsv').write_text('');(W/'refused-inputs26.json').write_text('{}')
# Round 34 lost enable-wide30 from the boot archive: carry runtime, box name and the wide flag explicitly.
with tarfile.open(W/'boot35.tgz','w:gz') as t:
 for p in W.glob('*.py'):t.add(p,arcname=p.name)
 for name in ['deadline','search-deadline','details-base25.csv','completed-geometries26.json','queue.tsv','refused-inputs26.json','444-control.csv','board.tsv','runtime33.json','box33','enable-wide30']:t.add(W/name,arcname=name)
 t.add(W/'lane',arcname='lane')
subprocess.run(['ssh','boxE','test ! -d $SCRATCH/squares-k123 && mkdir -p $SCRATCH/squares-k123/out $SCRATCH/squares-k123/tasks $SCRATCH/squares-k123/taskdone $SCRATCH/squares-k123/claims'],check=True)
subprocess.run(['scp','-q',str(W/'boot35.tgz'),'boxE:scratch/squares-k123/'],check=True)
subprocess.run(['ssh','boxE','cd $SCRATCH/squares-k123 && tar xzf boot35.tgz && rm boot35.tgz'],check=True)
cmd='cd $SCRATCH/squares-k123 && $SCRATCH/squares-base/venv/bin/python -I lane/k123_turn.py 444-control.csv 444 control444 $SCRATCH/squares-base/fq --turns=0 --modes self --loosen 1.001 --bar 21.5647 --keep'
r=subprocess.run(['ssh','boxE',cmd],check=True,text=True,capture_output=True);(W/'boxE-control444.log').write_text(r.stdout+r.stderr)
text=subprocess.check_output(['ssh','boxE','cat $SCRATCH/squares-k123/control444/turn-444.tsv'],text=True);assert '21.564693167754' in text,text
print('boxE control passed',text)
