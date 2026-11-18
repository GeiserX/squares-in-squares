"""Save round33 measured jobs and only the invent lane files."""
import pathlib,json,csv,math,subprocess,shutil,time,re
W=pathlib.Path(__file__).resolve().parent;T=W.parent;R=pathlib.Path('.');REPO=R.parents[1]
def run(args,timeout=120):
 r=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 if r.returncode and args[0]=='git'and 'index.lock'in r.stdout:
  time.sleep(3);r=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 print(r.stdout,flush=True);r.check_returncode();return r.stdout

def record(prepare=False):
 import finish33
 report=finish33.report();jobs=json.load(open(W/'jobs.json'));rows=[];trials=0;stats={}
 for j in jobs:
  if j['kind']in('control','early'):continue
  p=W/'boxE-raw'/j['id']/'done.json'
  if not p.exists():continue
  d=json.load(open(p));new=d.get('new');move=j['side']-(new+1)*math.sqrt(j['n'])if new is not None else None
  rows.append([j['id'],j['n'],j['kind'],j['seed'],j['side'],new,move,d.get('search_end',''),d.get('error',''),j['input_sha256'],j['ancestry']])
  s=stats.setdefault(j['kind'],[0,0]);s[0]+=1;s[1]+=int(move is not None and move>1e-8)
  for p in (W/'boxE-raw'/j['id']).glob('slide-*.tsv'):trials+=max(0,len(p.read_text().splitlines())-1)
 out=R/'results/invent-r33-2026-11-17.tsv'
 with out.open('w',newline='')as f:
  w=csv.writer(f,delimiter='\t');w.writerow(['job','n','kind','seed','start_side','new_score','side_reduction','search_end','error','input_sha256','source_graph']);w.writerows(rows)
 text='\n## Round 33 (2026-11-16 to 2026-11-17)\n\n'
 text+='Fresh changed rectangles and joins received priority. Four boxE slots ran with a 120-second dry probe.\n'
 text+='Plain held kicks, unchanged539 and the completed broad-radius pilot stayed closed.\n'
 text+=f'The lane completed {len(rows)} production jobs and logged {trials} family-kick trials.\n'
 for kind,(count,moved)in stats.items():text+=f'The {kind} queue completed {count} jobs. {moved} shortened side by more than 1e-8.\n'
 text+='Movement compares each endpoint with its start. It is not additive score gain.\n'
 text+=report['summary']+'\n'
 text+=f'The archive comparison gain against bar33 is {report["gain"]["against_base_bar"]:.15g}. The take remains open for the final live comparison.\n'
 text+='Each distinct certified candidate completed the full default and polish fq loop before comparison.\n'
 text+='Completed candidate checkpoints exported while the batch compared later candidates.\n'
 text+='Production required the pair and stopped907 controls, plus checkpoint controls that refused overlaps and wrong quench markers.\n'
 text+='The startup order now waits for control2 before its checkpoint control. The initial workers exited before any search.\n'
 text+='Source controls accepted submitted round32 coordinates without a share call and refused changed coordinates or evidence.\n'
 text+='A k123 catalogue leaf now resolves held ownership through its accepted gate and exact float64 geometry hash.\n'
 text+='The actual789 mixed held and original-seed graph passed without a share call. A changed seed hash failed.\n'
 text+='The actual259 control passed. Wrong geometry hashes, wrong counts and mixed-parent records failed.\n'
 text+='The exact-byte withdrawal control selected the current log and ignored notices for different bytes.\n'
 text+='The historical970 source fixture failed closed because its forensics849 parent had been superseded. It supplied no production input.\n'
 trans=json.load(open(W/'transfer-check.json'))if(W/'transfer-check.json').exists()else{}
 if trans.get('boxE_scratch_removed'):text+=f'All {trans["csv_files_copied"]} archived CSV hashes matched before removing the owned boxE scratch.\n'
 text+='The [results table](../results/invent-r33-2026-11-17.tsv) records each completed job.\n'
 text+='The [saved tools](../tools/invent/round33) preserve the campaign and source checks.\n'
 prose=W/'round33-prose.md';prose.write_text(text)
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(prose)])
 doc=R/'avenues/invent.md';old=doc.read_text();mark='\n## Round 33 (2026-11-16 to 2026-11-17)\n'
 if mark in old:old=old.split(mark)[0]
 doc.write_text(old+text)
 dest=R/'tools/invent/round33';dest.mkdir(exist_ok=True)
 files=['campaign33.py','campaign33base.py','worker33.py','early32.py','certify31.py','invent_barretain_budget30.py','finesafe.py','ancestry28.py','source_gate28.py','public_branch30.py','public_roots29.py','owned30.py','scoped30.py','extend30.py','exact_root30.py','aliases29.py','archive28.py','archived_credit28.py','gather29.py','held32.py','held_geometry33.py','controls_geometry33.py','controls_freeze33.py','freeze_held32.py','historical756.py','implicit_public29.py','public_archive28.py','invent_shape22.py','controls33.py','direct814_control31.py','branch_controls30.py','remote_close33.py','finish33.py','record33.py','setup33.py','start_remote33.py']
 for name in files:shutil.copyfile(W/name,dest/name)
 paths=[str((dest/n).relative_to(REPO))for n in files]+[str(out.relative_to(REPO)),str(doc.relative_to(REPO))]
 if prepare:return dict(paths=paths,completed=len(rows),stats=stats)
 run(['git','add','--',*paths]);run(['git','commit','--only','-m','Measure round 33 invent searches on changed geometry','--',*paths]);sha=run(['git','rev-parse','HEAD']).strip();run(['git','show','--stat','--oneline',sha]);actual=set(run(['git','diff-tree','--no-commit-id','--name-only','-r',sha]).splitlines());assert actual<=set(paths)
 run(['git','pull','--rebase','--autostash']);sha=run(['git','log','-1','--format=%H','--',*paths]).strip()
 try:run(['git','push','origin','HEAD:main'])
 except subprocess.CalledProcessError:time.sleep(4);run(['git','push','origin','HEAD:main'])
 previous=json.load(open(W/'commits.json'))if(W/'commits.json').exists()else[];previous.append(sha);(W/'commits.json').write_text(json.dumps(previous));return sha
if __name__=='__main__':record()
