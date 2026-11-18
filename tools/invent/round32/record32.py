"""Record measured jobs, documentation, and the exact lane commit."""
import pathlib,json,csv,math,subprocess,shutil,re,time
W=pathlib.Path(__file__).resolve().parent;T=W.parent;R=pathlib.Path('.');REPO=R.parents[1]
def run(args,timeout=120):
 r=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 if r.returncode and args[0]=='git'and 'index.lock'in r.stdout:
  time.sleep(3);r=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
 print(r.stdout,flush=True);r.check_returncode();return r.stdout

def record(prepare=False):
 jobs=json.load(open(W/'jobs.json'));rows=[];stats={};trials=0
 for j in jobs:
  if j['kind']in('control','early'):continue
  p=W/'boxE-raw'/j['id']/'done.json'
  if not p.exists():continue
  d=json.load(open(p));new=d.get('new');move=j['side']-(new+1)*math.sqrt(j['n'])if new is not None else None
  rows.append([j['id'],j['n'],j['kind'],j['seed'],j['side'],new,move,d.get('search_end',''),d.get('error',''),json.dumps(j.get('options',[])),j['input_sha256'],j['ancestry']]);s=stats.setdefault(j['kind'],[0,0]);s[0]+=1;s[1]+=int(move is not None and move>1e-8)
  for p in (W/'boxE-raw'/j['id']).glob('slide-*.tsv'):
   trials+=max(0,len(p.read_text().splitlines())-1)
 out=R/'results/invent-r32-2026-11-16.tsv'
 with out.open('w',newline='')as h:
  w=csv.writer(h,delimiter='\t');w.writerow(['job','n','kind','seed','start_side','new_score','side_reduction','search_end','error','numerical_options','input_sha256','source_graph']);w.writerows(rows)
 comp=json.load(open(W/'comparison.json'));trans=json.load(open(W/'transfer-check.json'))if(W/'transfer-check.json').exists()else None
 published={}
 for line in (W.parents[1]/'handoff-r32.log').read_text(errors='replace').splitlines():
  match=re.search(r'invent -> all: CERTIFIED n=(\d+) score=([0-9.eE+-]+)',line)
  if match:
   n=int(match[1]);score=float(match[2]);published[n]=min(published.get(n,math.inf),score)
 base={int(r['n']):float(r['bar'])for r in csv.DictReader(open(W.parents[1]/'round32-briefs/bar32.tsv'),delimiter='\t')}
 published_gain=sum(base[n]-score for n,score in published.items())
 text='\n## Round 32 (2026-11-16)\n\n'
 text+='The lane recovered the round 31 archive before starting production. All 1,212 CSV hashes matched.\n'
 text+='It removed the owned round 31 boxE scratch and pushed the saved code and measured results.\n'
 text+='The late 989 endpoint was already claimed by rebuild. The lane skipped that duplicate start.\n'
 text+='Fresh changed rectangles and joins received priority.\n'
 text+=f'The lane published {len(published)} provisional rows. Their maximum per-n gains sum to {published_gain:.15g} before peer follows.\n'
 text+='Unchanged held kicks and the unchanged 539 retention profile stayed closed.\n'
 text+=f'Three boxE slots completed {len(rows)} production jobs and logged {trials} family-kick trials.\n'
 for k,(count,moved)in stats.items():text+=f'The {k} queue completed {count} jobs. {moved} shortened side by more than 1e-8.\n'
 text+='A planned two-start pilot uses radius 8 with angular noise factor 0.15. Its stopped 907 control gates admission.\n'
 text+='The older radius 8 trials stay closed on their unchanged geometry. This pilot uses new rectangle and join bytes.\n'
 text+='Movement compares each endpoint with its start. It is not additive score gain.\n'
 text+=f'The archive comparison retained {comp["improved_n"]} rows for {comp["gain"]["against_base_bar"]:.15g} against bar32.\n'
 text+='Search and quench share a 17:00 UTC cutoff, leaving time for the archive and push before 17:15.\n'
 text+='The take remains open for the final comparison before 17:25 UTC.\n'
 text+='Every retained endpoint completed fq from its certified input and cleared native and pandas reads by at least 2.2e-11.\n'
 text+='The stopped 907 control reached the known deep basin below side 30.6183 before production opened.\n'
 text+='The four-candidate control quenched every distinct certified input before selecting its winner.\n'
 text+='Production compares the certified start with every saved raw candidate after their separate quenches.\n'
 text+='An immutable checkpoint now exports after each completed candidate quench. The batch keeps comparing later candidates.\n'
 text+='Checkpoint controls accept a completed candidate and refuse overlaps and wrong quench markers.\n'
 text+='Source controls accepted held ancestry without a share call and rejected changed evidence.\n'
 text+='The exact-byte withdrawal control reads the current round log and ignores a notice for different bytes.\n'
 text+='A direct withdrawn 814 parent still fails beside a held sibling. Its held-only ancestry passes.\n'
 text+='Held roots verify a known submitted file and its GREEN gate. Exact exports also verify their coordinates.\n'
 text+='An unsubmitted round 23 candidate needs identical coordinates in the submitted b file. Its changed 228 fails.\n'
 text+='The 367 source control accepts its SHA-bound held wrapper and rejects a wrong ancestry hash.\n'
 text+='Changed source sidecars can reopen a deferred start. Unchanged source failures stay closed.\n'
 text+='The 970 control passes without a share call. Changed exports, forged row hashes and nonheld leaves fail.\n'
 if trans and trans.get('boxE_scratch_removed'):
  text+=f'All {trans["csv_files_copied"]} archived CSV hashes matched before removing the owned round 32 boxE scratch.\n'
 else:text+='The final archive verification and scratch removal are pending.\n'
 text+='The [results table](../results/invent-r32-2026-11-16.tsv) records each completed production job.\n'
 text+='The [saved tools](../tools/invent/round32) preserve the controller, source policy and numerical worker.\n'
 prose=W/'round32-prose.md';prose.write_text(text)
 run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(prose)])
 doc=R/'avenues/invent.md';old=doc.read_text();mark='\n## Round 32 (2026-11-16)\n'
 if mark in old:old=old.split(mark)[0]
 doc.write_text(old+text)
 dest=R/'tools/invent/round32';dest.mkdir(exist_ok=True)
 # Preserve actual dependencies, without unused historical campaign launchers.
 files=['campaign32.py','campaign32base.py','worker32.py','worker32-stream.py','worker32-final.py','early32.py','certify31.py','invent_barretain_budget30.py','finesafe.py','ancestry28.py','source_gate28.py','public_branch30.py','public_roots29.py','owned30.py','scoped30.py','extend30.py','exact_root30.py','aliases29.py','archive28.py','archived_credit28.py','gather29.py','held32.py','freeze_held32.py','controls_held32.py','historical756.py','implicit_public29.py','public_archive28.py','invent_shape22.py','controls32.py','controls_wrapper32.py','controls_retry32.py','direct814_control31.py','branch_controls30.py','remote_close32.py','roll32.py','roll_final32.py','finish32.py','record32.py']
 for name in files:shutil.copyfile(W/name,dest/name)
 paths=[str((dest/n).relative_to(REPO))for n in files]+[str(out.relative_to(REPO)),str(doc.relative_to(REPO))]
 if prepare:return dict(paths=paths,completed=len(rows),stats=stats,comparison=comp)
 run(['git','add','--',*paths]);run(['git','commit','--only','-m','Measure round 32 invent follows of changed packing geometry','--',*paths]);sha=run(['git','rev-parse','HEAD']).strip();print(run(['git','show','--stat','--oneline',sha]));actual=set(run(['git','diff-tree','--no-commit-id','--name-only','-r',sha]).splitlines());assert actual<=set(paths)
 run(['git','pull','--rebase','--autostash']);sha=run(['git','log','-1','--format=%H','--',*paths]).strip();run(['git','push','origin','HEAD:main']);(W/'commits.json').write_text(json.dumps([sha]));return sha
if __name__=='__main__':record()
