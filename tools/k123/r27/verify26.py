"""Run the unchanged verifier in one boxE slot without an argv-size limit."""
import pathlib,sys,json
R=pathlib.Path.home()/'scratch/squares-k123';j=json.load(open(sys.argv[1]))
sys.path.insert(0,str(R/'lane'))
import methods_take
sys.argv=['methods_take.py',str(R/j.get('details','details-base25.csv')),str(R/j['out']),j['source'],*[str(R/p) for p in j['raws']]]
methods_take.main()
print('DIRECT_VERIFY26 complete',flush=True)
