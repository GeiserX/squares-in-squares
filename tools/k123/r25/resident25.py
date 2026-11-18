"""Keep metadata imports warm on the loaded collector box."""
import pathlib,os,sys,time,runpy,traceback,resource
W=pathlib.Path(__file__).resolve().parent;os.chdir(W);sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'))
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
end=float((W/'deadline').read_text());search=float((W/'search-deadline').read_text());mode=sys.argv[1]
while time.time()<end:
 scripts=['collect22.py'] if mode=='collect' else ['rebuild25.py','stage24.py','saved25.py','deferred25.py']
 for name in scripts:
  # Reload the base reader when the source file changes, retaining other warm imports.
  import importlib
  if 'base25' in sys.modules:
   mod=sys.modules['base25'];stamp=(W/'base25.py').stat().st_mtime_ns
   if getattr(mod,'_code_stamp',None)!=stamp:importlib.reload(mod);mod._code_stamp=stamp
  if mode!='collect' and time.time()>=search:break
  args=sys.argv;sys.argv=[str(W/name)]
  t=time.time()
  with open(W/(name+'.log'),'a',buffering=1) as f:
   oldout,olderr=sys.stdout,sys.stderr;sys.stdout=sys.stderr=f
   try:
    result=runpy.run_path(str(W/name),run_name='__main__')
    if result.get('lock'):result['lock'].close()
    del result
    rc=0
   except SystemExit as e:rc=e.code
   except BaseException:traceback.print_exc();rc=1
   finally:
    sys.stdout,sys.stderr=oldout,olderr;sys.argv=args
    import gc;gc.collect()
  with open(W/'resident25.log','a') as f:f.write(time.strftime('%FT%TZ',time.gmtime())+f' {mode} {name} rc={rc} seconds={time.time()-t:.3f} rss={resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}\n')
 time.sleep(min(30,max(0,end-time.time())))
