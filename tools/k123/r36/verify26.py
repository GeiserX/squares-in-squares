"""Run the unchanged verifier in one boxE slot without an argv-size limit."""
import pathlib,sys,json
R=pathlib.Path.home()/'scratch/squares-k123';j=json.load(open(sys.argv[1]))
sys.path.insert(0,str(R/'lane'))
if j.get('near_donor36'):
 import runpy
 runpy.run_path(str(R/'near_numeric36.py'),run_name='__main__');raise SystemExit
if j.get('general_mask34'):
 import runpy
 runpy.run_path(str(R/'general_mask34.py'),run_name='__main__');raise SystemExit
if j.get('mask_exchange34'):
 import runpy
 runpy.run_path(str(R/'mask_exchange34.py'),run_name='__main__');raise SystemExit
if j.get('joint_phase34'):
 import runpy
 runpy.run_path(str(R/'joint_phase34.py'),run_name='__main__');raise SystemExit
if j.get('phase_physical34'):
 import runpy
 runpy.run_path(str(R/'phase_physical34.py'),run_name='__main__');raise SystemExit
if j.get('whole_crossover34'):
 import runpy
 runpy.run_path(str(R/'whole_crossover34.py'),run_name='__main__');raise SystemExit
if j.get('whole_crossover33'):
 import runpy
 runpy.run_path(str(R/'whole_crossover33.py'),run_name='__main__');raise SystemExit
if j.get('phase_matching33'):
 import runpy
 runpy.run_path(str(R/('phase_matching_resume33.py' if j.get('matching_resume33') else 'phase_matching_seed33.py' if j.get('matching_seed33') else 'phase_matching33c.py' if j.get('matching_uprights33') else 'phase_matching33b.py' if j.get('matching_signed33') else 'phase_matching33.py')),run_name='__main__');raise SystemExit
if j.get('phase_fullgrid33'):
 import runpy
 runpy.run_path(str(R/'phase_fullgrid33.py'),run_name='__main__');raise SystemExit
if j.get('phase_lattice33'):
 import runpy
 runpy.run_path(str(R/'phase_lattice33.py'),run_name='__main__');raise SystemExit
if j.get('phase_mask_strip33'):
 import runpy
 runpy.run_path(str(R/'phase_mask_strip33.py'),run_name='__main__');raise SystemExit
if j.get('phase_mask_bar33'):
 import runpy
 runpy.run_path(str(R/'phase_mask_bar33.py'),run_name='__main__');raise SystemExit
if j.get('phase_finish33'):
 import runpy
 runpy.run_path(str(R/'phase_finish33.py'),run_name='__main__');raise SystemExit
if j.get('phase_mask_fixed33'):
 import runpy
 runpy.run_path(str(R/('phase_mask_fixed33b.py' if j.get('phase_mask_refit33') else 'phase_mask_fixed33.py')),run_name='__main__');raise SystemExit
if j.get('phase_prefix_exact33'):
 import runpy
 runpy.run_path(str(R/'phase_prefix_exact33.py'),run_name='__main__');raise SystemExit
if j.get('phase_sweep33'):
 import runpy
 runpy.run_path(str(R/'phase_sweep33.py'),run_name='__main__');raise SystemExit
if j.get('phase_witness33'):
 import runpy
 runpy.run_path(str(R/'phase_witness33.py'),run_name='__main__');raise SystemExit
if j.get('slide_phase33'):
 import runpy
 runpy.run_path(str(R/'slide_phase33.py'),run_name='__main__');raise SystemExit
if j.get('slide_strip32'):
 import runpy
 runpy.run_path(str(R/'slide_strip32.py'),run_name='__main__');raise SystemExit
if j.get('slide_control31') or j.get('slide_milp31'):
 import runpy
 runpy.run_path(str(R/'slide_milp31.py'),run_name='__main__');raise SystemExit
if j.get('geometry_audit31'):
 import runpy
 runpy.run_path(str(R/'geometry_audit31.py'),run_name='__main__');raise SystemExit
if j.get('held_probe31') or j.get('held_control31'):
 import runpy
 runpy.run_path(str(R/'heldprobe31.py'),run_name='__main__');raise SystemExit
if j.get('diversity_scan'):
 import runpy
 runpy.run_path(str(R/'diversity29.py'),run_name='__main__');raise SystemExit
if j.get('kick_control') or j.get('kick_leg'):
 import runpy
 runpy.run_path(str(R/'kickcert30.py'),run_name='__main__');raise SystemExit
if j.get('variant_control'):
 import subprocess,time
 PY=str(pathlib.Path.home()/'scratch/squares-base/venv/bin/python');FQ=str(pathlib.Path.home()/'scratch/squares-base/fq')
 loosen=j.get('loosen',1.005);d=R/('control444-wide-'+format(loosen,'.3f'));d.mkdir(exist_ok=True)
 subprocess.run([PY,'-I','lane/k123_turn.py','444-control.csv','444',str(d),FQ,'--turns=0','--modes','self','--loosen',str(loosen),'--keep'],cwd=R,check=True,timeout=180)
 rows=[l for l in (d/'turn-444.tsv').read_text().splitlines() if not l.startswith('#')];side=float(rows[-1].split('\t')[3]);assert abs(side-21.564693167754)<1e-7,side
 result={'n':444,'loosen':loosen,'side':side,'reference':21.564693167754};(R/('variant-control-'+j['tag']+'.json')).write_text(json.dumps(result));print(json.dumps(result),flush=True);raise SystemExit
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
