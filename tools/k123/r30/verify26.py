"""Run the unchanged verifier in one boxE slot without an argv-size limit."""
import pathlib,sys,json
R=pathlib.Path.home()/'scratch/squares-k123';j=json.load(open(sys.argv[1]))
sys.path.insert(0,str(R/'lane'))
if j.get('diversity_scan'):
 import runpy
 runpy.run_path(str(R/'diversity29.py'),run_name='__main__');raise SystemExit
if j.get('kick_control') or j.get('kick_leg'):
 import runpy
 runpy.run_path(str(R/'kickcert30.py'),run_name='__main__');raise SystemExit
if j.get('variant_control'):
 import subprocess,time
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');FQ=str(pathlib.Path.home()/'scratch/squares-base/fq')
 d=R/'control444-wide30';d.mkdir(exist_ok=True)
 subprocess.run([PY,'-I','lane/k123_turn.py','444-control.csv','444',str(d),FQ,'--turns=0','--modes','self','--loosen','1.005','--keep'],cwd=R,check=True,timeout=180)
 rows=[l for l in (d/'turn-444.tsv').read_text().splitlines() if not l.startswith('#')];side=float(rows[-1].split('\t')[3]);assert abs(side-21.564693167754)<1e-7,side
 result={'n':444,'loosen':1.005,'side':side,'reference':21.564693167754};(R/'variant-control30.json').write_text(json.dumps(result));print(json.dumps(result),flush=True);raise SystemExit
if j.get('fine_control'):
 import csv,math,floatsafe,finesafe
 p=R/'control444/turn/444-self-+0.000-1.001.csv'
 rows=list(csv.DictReader(p.open()));a=floatsafe.work((444,rows));b=finesafe.work((444,rows))
 assert a[1] is not None and b[1] is not None
 assert b[2]<=a[2] and floatsafe.clearance(b[1])>=floatsafe.MIN_CLEARANCE
 assert floatsafe.check(444,floatsafe.via_pandas(b[1]))[1]=='ok'
 result={'n':444,'ladder_side':(a[2]+1)*math.sqrt(444),'fine_side':(b[2]+1)*math.sqrt(444),'ladder_e':a[3],'fine_e':b[3],'clearance':floatsafe.clearance(b[1])}
 (R/'control-finesafe29.json').write_text(json.dumps(result));print(json.dumps(result),flush=True);raise SystemExit
import methods_take
sys.argv=['methods_take.py',str(R/j.get('details','details-base25.csv')),str(R/j['out']),j['source'],*[str(R/p) for p in j['raws']]]
methods_take.main()
print('DIRECT_VERIFY26 complete',flush=True)
