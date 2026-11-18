"""Keep metadata imports warm on the loaded collector box."""
import pathlib,os,sys,time,runpy,traceback,resource
W=pathlib.Path(__file__).resolve().parent;os.chdir(W);sys.path.insert(0,str(W));sys.path.insert(0,str(W/'lane'))
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
import faulthandler,signal
_debug=open(W/('stack-'+sys.argv[1]+'.log'),'a')
faulthandler.register(signal.SIGUSR1,file=_debug,all_threads=True)
end=float((W/'deadline').read_text());search=float((W/'search-deadline').read_text());mode=sys.argv[1]
while time.time()<end:
 scripts=['collect22.py'] if mode=='collect' else ['stage24.py','deferred28.py','resume26.py']
 for name in scripts:
  # Refresh source dependencies together so warm controllers use tested code.
  import importlib
  modules=['current_walk29','policy27','policy_walk27','provenance24','seed_notice24','ancestry24','terms26','bare26','held26','source25','base25']
  changed=any(name in sys.modules and getattr(sys.modules[name],'_code_stamp',None)!=(W/(name+'.py')).stat().st_mtime_ns for name in modules)
  if changed:
   for module_name in modules:
    if module_name in sys.modules:
     mod=importlib.reload(sys.modules[module_name]);mod._code_stamp=(W/(module_name+'.py')).stat().st_mtime_ns
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
 if mode=='stage' and (W/'restart-stage28').exists():
  (W/'restart-stage28').unlink();os.execv(sys.executable,[sys.executable,str(W/'resident25.py'),mode])
 time.sleep(min(30,max(0,end-time.time())))
