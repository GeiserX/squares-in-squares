"""Save round35 measured jobs and only the invent lane files."""
import pathlib,json,csv,math,subprocess,shutil,time,re
W=pathlib.Path(__file__).resolve().parent;T=W.parent;R=pathlib.Path('.');REPO=R.parents[1]
def run(args,timeout=120):
 r=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 if r.returncode and args[0]=='git'and 'index.lock'in r.stdout:
  time.sleep(3);r=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 print(r.stdout,flush=True);r.check_returncode();return r.stdout

def record(prepare=False):
 import finish35
 report=finish35.report();jobs=json.load(open(W/'jobs.json'));rows=[];trials=0;stats={}
 for j in jobs:
  if j['kind']in('control','early'):continue
  p=W/'boxE-raw'/j['id']/'done.json'
  if not p.exists():continue
  d=json.load(open(p));new=d.get('new');move=j['side']-(new+1)*math.sqrt(j['n'])if new is not None else None
  rows.append([j['id'],j['n'],j['kind'],j['seed'],j['side'],new,move,d.get('search_end',''),d.get('error',''),j['input_sha256'],j['ancestry']])
  s=stats.setdefault(j['kind'],[0,0]);s[0]+=1;s[1]+=int(move is not None and move>1e-8)
  for p in (W/'boxE-raw'/j['id']).glob('slide-*.tsv'):trials+=max(0,len(p.read_text().splitlines())-1)
 out=R/'results/invent-r35-2026-11-17.tsv'
 with out.open('w',newline='')as f:
  w=csv.writer(f,delimiter='\t');w.writerow(['job','n','kind','seed','start_side','new_score','side_reduction','search_end','error','input_sha256','source_graph']);w.writerows(rows)
 text='\n## Round 35 (2026-11-17)\n\n'
 text+='Fresh changed rectangles and joins received priority. Three boxE slots ran with a 120-second dry probe.\n'
 text+='Plain held kicks, unchanged539 and the completed broad-radius pilot stayed closed.\n'
 text+=f'The lane completed {len(rows)} production jobs and logged {trials} family-kick trials.\n'
 for kind,(count,moved)in stats.items():text+=f'The {kind} queue completed {count} jobs. {moved} shortened side by more than 1e-8.\n'
 text+='Movement compares each endpoint with its start. It is not additive score gain.\n'
 text+='Two finds certified below bar35 by more than 1e-10. Both lost to a lower live round 35 take at the same n.\n'
 text+='Our 746 row was 8.3e-10 below bar35. The classfill 746 row built from it was 3.05e-9 below bar35.\n'
 text+='Our 925 row was 4.8e-8 below bar35. The backlog 925 row was 1.98e-5 below bar35.\n'
 text+='The lane take holds 0 rows. Five fresh jobs queued after 15:25Z never started before the close.\n'
 text+='Each distinct certified candidate completed the full default and polish fq loop before comparison.\n'
 text+='Completed candidate checkpoints exported while the batch compared later candidates.\n'
 text+='Production required the pair and stopped907 controls, plus checkpoint controls that refused overlaps and wrong quench markers.\n'
 text+='The startup order ran control2 before the checkpoint control. Production waited for every control.\n'
 text+='Source controls accepted a submitted round34 row without a share call. They refused changed coordinates, wrong evidence and exact withdrawn bytes.\n'
 text+='A watchdog restarted dead boxE slots and released their job locks. Its control killed and restarted an idle slot.\n'
 text+='The watchdog also stopped a running job once a live peer row passed its dispatch bar by more than 1e-6.\n'
 trans=json.load(open(W/'transfer-check.json'))if(W/'transfer-check.json').exists()else{}
 if trans.get('boxE_scratch_removed'):text+=f'All {trans["csv_files_copied"]} archived CSV hashes matched before removing the owned boxE scratch.\n'
 text+='The [results table](../results/invent-r35-2026-11-17.tsv) records each completed job.\n'
 text+='The [saved tools](../tools/invent/round35) preserve the campaign and source checks.\n'
 prose=W/'round35-prose.md';prose.write_text(text)
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(prose)])
 doc=R/'avenues/invent.md';old=doc.read_text();mark='\n## Round 35 (2026-11-17)\n'
 if mark in old:old=old.split(mark)[0]
 doc.write_text(old+text)
 dest=R/'tools/invent/round35';dest.mkdir(exist_ok=True)
 files=['setup35.py', 'watchdog35.py', 'wd_remote35.py', 'controls35.py', 'campaign35.py', 'campaign35base.py', 'worker35.py', 'early32.py', 'certify31.py', 'invent_barretain_budget30.py', 'finesafe.py', 'ancestry28.py', 'source_gate28.py', 'public_branch30.py', 'public_roots29.py', 'owned30.py', 'scoped30.py', 'extend30.py', 'exact_root30.py', 'aliases29.py', 'archive28.py', 'archived_credit28.py', 'gather29.py', 'held32.py', 'held_geometry33.py', 'controls_geometry35.py', 'controls_r35rules.py', 'freeze_held32.py', 'historical756.py', 'implicit_public29.py', 'public_archive28.py', 'invent_shape22.py', 'direct814_control31.py', 'branch_controls30.py', 'remote_close35.py', 'finish35.py', 'record35.py', 'start_remote35.py']
 for name in files:shutil.copyfile(W/name,dest/name)
 paths=[str((dest/n).relative_to(REPO))for n in files]+[str(out.relative_to(REPO)),str(doc.relative_to(REPO))]
 if prepare:return dict(paths=paths,completed=len(rows),stats=stats)
 run(['git','add','--',*paths]);run(['git','commit','--only','-m','squares invent r35: measure fresh changed-geometry searches against bar35','--',*paths]);sha=run(['git','rev-parse','HEAD']).strip();run(['git','show','--stat','--oneline',sha]);actual=set(run(['git','diff-tree','--no-commit-id','--name-only','-r',sha]).splitlines());assert actual<=set(paths)
 run(['git','pull','--rebase','--autostash']);sha=run(['git','log','-1','--format=%H','--',*paths]).strip()
 try:run(['git','push','origin','HEAD:main'])
 except subprocess.CalledProcessError:time.sleep(4);run(['git','push','origin','HEAD:main'])
 previous=json.load(open(W/'commits.json'))if(W/'commits.json').exists()else[];previous.append(sha);(W/'commits.json').write_text(json.dumps(previous));return sha
if __name__=='__main__':record()
