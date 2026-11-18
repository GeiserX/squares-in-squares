import contextlib,glob,io,os,sys
sys.path.insert(0,'lane');import importlib.util
spec=importlib.util.spec_from_file_location('runner','lane/stair-c_run.py');R=importlib.util.module_from_spec(spec);spec.loader.exec_module(R)
added=0
for pool in sorted(glob.glob('lib-don-*')+glob.glob('lib-mod-*')+glob.glob('lib-ext-*')+glob.glob('lib-base-*')):
 if not os.path.exists(pool+'/library.pkl'):continue
 tag=pool[4:]
 for rows in [f'q-{tag}.tsv',f'q-{tag}-resume.tsv']:
  if not os.path.exists(rows):continue
  h=io.StringIO()
  with contextlib.redirect_stdout(h):R.cmd_jobs([pool,rows,'raw-a','details-r21.csv','gap.tsv','./fq','--max','.008','--per','1','--done','blog','--source-key',pool,'--py','./py','--lane','lane'])
  text=h.getvalue()
  with open('q.txt','a') as f:f.write(text)
  added+=len(text.splitlines())
print('REGEN',added,'pending job lines from retained tables; immutable library identity preserved',flush=True)
