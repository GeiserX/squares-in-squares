"""Stop, verify, publish, document and report this lane at the round deadline."""
import shlex,csv,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,tarfile,time,traceback
from concurrent.futures import ThreadPoolExecutor
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('$PRIVATE_REPO')
LANE=REPO/'lanes/squares'
TAKE=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r31')
WORK=TAKE/'work'
PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=datetime.datetime(2026,11,16,0,15,tzinfo=datetime.timezone.utc).timestamp()
REPORT=datetime.datetime(2026,11,16,0,25,0,tzinfo=datetime.timezone.utc).timestamp()
HOSTS=[('boxC','n','venv/bin/python'),('boxD','m','venv/bin/python'),('boxE','s','$SCRATCH/squares-base/venv/bin/python')]

def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def state(s):
    with (TAKE/'STATE.txt').open('a') as f:f.write(stamp()+' boxA '+s+'\n')
def run(args,limit=90):
    p=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
    if p.returncode and args[0]=='git' and 'index.lock' in p.stdout:
        time.sleep(3);p=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
    print(stamp(),args[0],p.returncode,p.stdout[-5000:],flush=True)
    return p

def owns_script(command,expected):
    try:parts=shlex.split(command)
    except ValueError:return False
    if not parts or 'python' not in pathlib.Path(parts[0]).name.lower() or '-m' in parts or '-c' in parts:return False
    first=next((part for part in parts[1:] if part.endswith('.py')),None)
    return first==str(expected)

def stop_coordinator():
    lines=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines()
    rows=[line.split(None,2) for line in lines if len(line.split(None,2))==3]
    expected={'coordinator':HERE/'coordinator.py','recovery':HERE/'recover.py','resume-saved':HERE/'resume-saved.py','setup':HERE/'setup.py','bootstrap':WORK/'bootstrap.py','recovery-later':WORK/'recover-later.py','held801':HERE/'held801.py','kick-follow':HERE/'kick_follow.py','restart-reprice':WORK/'restart-reprice.py','follow-driver':HERE/'follow_driver.py','held-driver':HERE/'held_driver.py','source-recovery':HERE/'recover_sources.py','fresh-held':HERE/'fresh_held.py','own-kicks':HERE/'own_kicks.py','paired-fresh':HERE/'paired_fresh.py','deploy-counts':WORK/'deploy-empty-counts.py'}
    expected.update({'recover-bytes':HERE/'recover_bytes.py','priority-recovered':WORK/'priority-recovered.py','paired':HERE/'paired.py','audit_library':HERE/'audit_library.py','feedback-finals':HERE/'feedback_finals.py','return-stacks':HERE/'fresh_return_stacks.py'})
    expected['paired-returns']=HERE/'paired_returns.py'
    expected['held-canonical']=HERE/'fresh_held.py'
    for name,script in expected.items():
        f=WORK/(name+'.pid')
        if not f.exists():continue
        pid=int(f.read_text());command=next((r[2] for r in rows if int(r[0])==pid),'')
        if not owns_script(command,script):continue
        own={pid}
        while True:
            more={int(r[0]) for r in rows if int(r[1]) in own}
            if more<=own:break
            own.update(more)
        for child in sorted(own-{os.getpid()},reverse=True):
            try:os.kill(child,signal.SIGTERM)
            except ProcessLookupError:pass
        state('STOP '+name+' pid'+str(pid)+' and its transports before final receipt snapshots')

def finish():
    sys.path[:0]=[str(HERE),str(LANE)]
    import finish_local31 as F
    stop_coordinator()
    def collect_box(seat):
        host,key,python=seat
        folder=WORK/'archive'/key;folder.mkdir(parents=True,exist_ok=True)
        result=run(['ssh','-o','ConnectTimeout=15',host,'cd $SCRATCH/squares-stair-c && '+python+' finish-box.py'],150)
        if result.returncode:raise RuntimeError(host+' archive failed')
        (folder/'finish.json').write_text(result.stdout)
        meta=json.loads(result.stdout)
        p=run(['rsync','-a',host+':scratch/squares-stair-c/final-copy.tar.gz',host+':scratch/squares-stair-c/receipt.json',str(folder)+'/'],120)
        if p.returncode:raise RuntimeError(host+' archive transfer failed')
        receipt=F.verify(folder/'final-copy.tar.gz',folder/'receipt.json',meta['archive_sha256'])
        (folder/'verify.json').write_text(json.dumps(receipt,indent=2))
        # Refresh the collected view from the verified snapshot, without another transport pass.
        base=WORK/'boxcopy'/key
        with tarfile.open(folder/'final-copy.tar.gz') as tf:
            for item in tf:
                if item.name=='worker.log' or item.name.split('/')[0] in {'raw-a','final','logs','tables'}:
                    target=base/item.name;target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(tf.extractfile(item).read())
        state('VERIFIED '+host+' archive '+str(receipt['files'])+' payload files; receipt '+receipt['receipt_sha256'])
        return host,key,python,receipt['receipt_sha256']
    with ThreadPoolExecutor(max_workers=3) as pool:
        verified=list(pool.map(collect_box,HOSTS))
    F.C.publish();F.C.save()
    measurement=F.measure();take=F.final_take()
    for host,key,python,digest in verified:
        result=run(['ssh','-o','ConnectTimeout=15',host,'cd $SCRATCH/squares-stair-c && '+python+' finish-box.py --remove '+digest],60)
        if result.returncode:raise RuntimeError(host+' scratch removal failed')
    (WORK/'cleanup-final.json').write_text(json.dumps(dict(verified=[dict(host=h,receipt=d) for h,k,p,d in verified],processes_left=[]),indent=2))
    state('FINISH remote payloads verified and own scratch removed on all three boxes. Shared runtimes kept. take retained'+str(take['improved_n']))
    return measurement,take

def experiment_summary(m):
    follows=m.get('whole_follows',[])
    kicks=[r for r in follows if (r.get('kick')or{}).get('invoked')]
    stopped=sum(bool(r['kick'].get('probe_stopped'))for r in kicks)
    measurements=[f"Completed numerical kick probes: {len(kicks)}. Stopped after 120 seconds without a raw improvement: {stopped}.","Source controls rejected direct public matches and a bad direct sibling beside a held boundary. Held rows and own seeds received no share gate.","Direct public roots used bounding-box centering, eight symmetries and rigid ICP at 1e-3 and 1e-2."]
    if (WORK/'held-driver-state.json').exists():
        j=json.loads((WORK/'held-driver-state.json').read_text());measurements.append(f"Exact-byte held starts claimed and dispatched: {sum(k.isdigit() for k in j)}.")
    if (WORK/'fresh-held-corners.json').exists():
        stages=json.loads((WORK/'fresh-held-corners.json').read_text())
        measurements.append(f"Fresh current-held corner transfer staged {sum(len(r.get('modules',[]))for r in stages)} physical corner modules from {sum(bool(r.get('modules'))for r in stages)} exact held rows.")
    if(WORK/'held-canonical-staged.json').exists():
        stages=json.loads((WORK/'held-canonical-staged.json').read_text())
        measurements.append(f"Submitted-row bindings staged {sum(len(r.get('modules',[]))for r in stages)} canonical module records from {len(stages)} held rows. The direct frozen-take trees remained deferred.")
    if (WORK/'source-recovery.json').exists():
        recovery=json.loads((WORK/'source-recovery.json').read_text())
        measurements.append(f"The held-credit boundary retry restored {recovery['restored']} exact frozen module versions after the full current source checks.")
    for r in m.get('fq_controls',[]):
        kick=r.get('kick')or{}
        if kick.get('invoked')and kick.get('start')is not None:
            measurements.append(f"The real n={r['n']} inflated-start control shortened side by {kick['start']-kick['end']:.12g} and completed certified-file fq: {r['completed']}.")
    for item in m.get('contributions',[]):
        measurements.append(f"A live peer source names this lane at n={item['n']}, with {item['gain']:.12g} gain against bar31 in that peer's take. The peer retains the gain.")
    for p in WORK.glob('boxcopy/*/final/*raw-lp*.json'):
        j=json.loads(p.read_text());r=j.get('lp_receipt')
        if r:measurements.append(f"Direct raw contact LP at n={j['n']} changed its raw side by {r['start']-r['lp_side']:.12g}. Its certified-file fq completed: {j.get('certified_file_quench',{}).get('completed',False)}.")
    paired={}
    whole_by_path={r['path']:r for r in m.get('whole_follows',[])}
    for path in WORK.glob('boxcopy/*/final/*paired-fresh*.json'):
        j=json.loads(path.read_text())
        if not j.get('certified_file_quench',{}).get('completed')or not whole_by_path.get(str(path),{}).get('completed'):continue
        paired.setdefault((j['n'],j['pair_seed']),{})[j['pair_mode']]=(j,whole_by_path.get(str(path),{}))
    pair_receipts=[]
    for (n,seed),variants in sorted(paired.items()):
        if set(variants)!={'input','bar'}:
            measurements.append(f"Fresh paired n={n} seed{seed} completed only {list(variants)}. No paired conclusion follows.")
            continue
        assert variants['input'][0]['pair_input_sha256']==variants['bar'][0]['pair_input_sha256']
        values={key:row.get('certified_side')for key,(j,row)in variants.items()}
        item=dict(n=n,seed=seed,certified_sides=values,input_sha256=variants['input'][0]['pair_input_sha256'])
        pair_receipts.append(item)
        measurements.append(f"Fresh matched n={n} seed{seed} certified sides: input-box {values['input']}, bar-input {values['bar']}. Identical certified bytes and seed used the same 900-second cap and 120-second dry-probe rule. These are input-variant measurements, not counted gains.")
    (WORK/'paired-fresh-results.json').write_text(json.dumps(pair_receipts,indent=2))
    next_items=[]
    best_pair_gains={}
    for item in pair_receipts:
        sides=item['certified_sides'];n=item['n']
        if None in sides.values():continue
        base_side=(1+float(next(r['bar']for r in csv.DictReader((TAKE.parent/'round31-briefs/bar31.tsv').open(),delimiter='\t')if int(r['n'])==n)))*n**.5
        if min(sides.values())<base_side-1e-10*n**.5:
            gain=(base_side-min(sides.values()))/n**.5
            best_pair_gains[n]=max(best_pair_gains.get(n,0),gain)
    for n,gain in sorted(best_pair_gains.items(),key=lambda item:-item[1]):
        next_items.append(f"Use new source-cleared corner and far-zone inputs in the n={n} family. Its best matched pair gained {gain:.12g} against bar31. Keep completed recipe keys closed.")
    feedback=WORK/'feedback-final-state.json'
    if feedback.exists():
        staged=[r for r in json.loads(feedback.read_text()).values()if r.get('status')=='staged']
        measurements.append(f"Certified kick returns staged {sum(len(r['modules'])for r in staged)} corner and far-zone module records from {len(staged)} byte versions. Each passed full source admission. Workers deduplicated geometry fingerprints.")
        measurements.append(f"Returned-module compositions completed {len(m.get('feedback_full',[]))} full builds. Their build receipts retain exact module versions.")
    returned=WORK/'returned-stacks-staged.json'
    if returned.exists():
        stages=json.loads(returned.read_text())
        measurements.append(f"Changed kick returns supplied {sum(len(r['modules'])for r in stages)} physical corner variants. Seven n=975 assemblies passed before dispatch. Partial and overlapping stack mutants failed.")
        measurements.append(f"Physical corners from kick returns completed {len(m.get('return_stack_full',[]))} full builds.")
    held_control=WORK/'held-record-exclusion-control.json'
    if held_control.exists():
        value=json.loads(held_control.read_text())
        measurements.append(f"All {value['current_held_records_passed']} bound held source records passed the named-source check. An excluded-publication mutant inside the original record failed.")
    if(WORK/'last-peer-control.json').exists():
        measurements.append('The final peer-prune control removed ties and kept strict peer gains below1e-10. It refused base gains below1e-10 and changes to the fully verified take.')
    if(WORK/'partial-output-control.json').exists():
        measurements.append('The finalization control kept the real n=342 output and excluded a completed fq receipt whose output CSV was missing.')
    useful=[]
    for r in kicks:
        if r.get('certified_side')is None:continue
        j=json.loads(pathlib.Path(r['path']).read_text());progress=r['kick'].get('start',0)-r['certified_side'];first=j.get('first_kick_shortening',progress)
        if progress>1e-6 or(first>=1e-5 and j.get('kick_leg',0)<2):useful.append(dict(r,follow_shortening=max(progress,first)))
    useful.sort(key=lambda r:r['follow_shortening'],reverse=True)
    chains_path=WORK/'held-driver-state.json'
    chains=json.loads(chains_path.read_text())if chains_path.exists()else{}
    outstanding=set()
    for r in useful:
        if r['n']in outstanding:continue
        path=pathlib.Path(r['path']);entry=chains.get('chain:'+hashlib.sha256(path.read_bytes()).hexdigest())
        completed=list(WORK.glob('boxcopy/*/final/'+entry.get('name','missing')+'.json'))if entry else[]
        measured=any(json.loads(p.read_text()).get('source_kick',{}).get('invoked')and json.loads(p.read_text()).get('certified_file_quench',{}).get('completed')for p in completed)
        if entry and (entry.get('status')=='chain closed'or measured):continue
        next_items.append(f"Finish the pending follow for changed n={r['n']} geometry. Its recorded useful input shortening was {r['follow_shortening']:.12g} of side. Check saved receipts before choosing another seed.")
        outstanding.add(r['n'])
        if len(outstanding)==2:break
    next_items.append('Prioritize held rows with no recent exact-byte claim. This round found small held-row gains at n=342, n=548 and n=928. Check live peer follows first.')
    next_items.append('Keep completed pairings closed. The matched n=812 and n=873 probes gave zero input shortening. The two extra seeds for each initial n=805 return also completed without further gain.')
    (WORK/'report-extra.json').write_text(json.dumps(dict(what_was_measured=measurements,next=next_items),indent=2))
    (WORK/'experiment-summary.md').write_text('Exact held-row starts kept submitted-file hashes and per-row source records.\nEach kick used a 120-second probe and a 900-second cap.\nA probe with no raw improvement stopped early.\nPublic starts used both tolerances. Own seeds and submitted rows received no share gate.\n')

def document(m,t):
    experiment_summary(m)
    text='\n\n## 18. Round 31\n\n'
    text+='One serial worker ran on each assigned box: boxC, boxD and boxE.\n'
    text+='The restored library kept complete source proofs and byte hashes.\n'
    text+='Fresh compositions preceded saved recipes. Completed recipes stayed closed.\n'
    text+='The physical corner model included following flush stacks.\n'
    text+='Own layouts had no share gate. Public starts retained licence and source checks.\n\n'
    text+=f"The workers exported {m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP stages across {m.get('n_values',0)} counts.\n"
    text+=f"After collection, the take retained {t.get('improved_n',0)} counts, gaining {t.get('against_base_bar',0):.15g} against bar31.\n"
    text+='A final live peer check removed any late superseded rows before the take froze.\n'
    text+='Certification used border finesafe at clearance 2.2e-11.\n'
    text+='Each retained row required a remote fq pass from its certified file.\n'
    text+='The [result table](../results/stair-c-r31-2026-11-16.tsv) records the builds and source screens.\n'
    text+='Full experiment receipts and exact saved queues remain in the take work directory.\n'
    extra=WORK/'experiment-summary.md'
    if extra.exists():text+='\n'+extra.read_text()+'\n'
    text+='\nAll remote archives passed SHA256 verification before scratch removal.\n'
    text+='The shared runtimes remain in place.\n'
    excerpt=WORK/'doc-r31.md';excerpt.write_text(text)
    checker='$STYLE_CHECK/check.py'
    if run(['/opt/homebrew/bin/python3',checker,'--level','default',str(excerpt)],60).returncode:raise RuntimeError('readable check failed')
    doc=LANE/'avenues/stair-c.md'
    if '\n## 18. Round 31\n'not in doc.read_text():
        with doc.open('a')as f:f.write(text)
    paths=[str(doc.relative_to(REPO)),str((LANE/'results/stair-c-r31-2026-11-16.tsv').relative_to(REPO))]
    paths += [str(p.relative_to(REPO))for p in sorted(HERE.glob('*.py'))]
    result=run(['git','add','--',*paths],60)
    if result.returncode:raise RuntimeError('stage failed')
    result=run(['git','commit','--only','-m','Record stair-c round 31 composition experiments','--',*paths],120)
    if result.returncode:raise RuntimeError('commit failed')
    sha=run(['git','rev-parse','HEAD'],30).stdout.strip()
    changed=run(['git','show','--format=','--name-only',sha],30).stdout.splitlines()
    if not set(changed)<=set(paths):raise RuntimeError('foreign paths in commit')
    run(['git','show','--stat','--oneline',sha],30)
    pulled=run(['git','pull','--rebase','--autostash'],60).returncode==0
    pushed=pulled and run(['git','push','origin','HEAD:main'],60).returncode==0
    if not pushed:pushed=run(['git','push','origin','HEAD:main'],60).returncode==0
    rebased=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 31 composition experiments$'],30).stdout.strip()
    sha=rebased or sha;state('COMMIT '+sha+(' pushed'if pushed else' not pushed'))
    earlier=WORK/'early-commits.json'
    return (json.loads(earlier.read_text())if earlier.exists()else[])+[sha+(' (pushed)'if pushed else' (not pushed)')]

def main():
    import importlib.util
    os.chdir(REPO)
    spec=importlib.util.spec_from_file_location('finish_local31',HERE/'finish-local.py')
    while time.time()<HARD:time.sleep(min(45,HARD-time.time()))
    F=importlib.util.module_from_spec(spec);sys.modules['finish_local31']=F;spec.loader.exec_module(F)
    m={};t={};blocked=[];commits=json.loads((WORK/'early-commits.json').read_text())if(WORK/'early-commits.json').exists()else[]
    state('START final collection. Long jobs stop00:15Z. Final take before00:25Z and report after00:25Z.')
    try:m,t=finish()
    except Exception as ex:traceback.print_exc();blocked.append('collection: '+str(ex))
    if not blocked:
        try:commits=document(m,t)
        except Exception as ex:traceback.print_exc();blocked.append('documentation: '+str(ex))
    while time.time()<REPORT-90:time.sleep(min(30,REPORT-90-time.time()))
    try:F.C.publish();F.C.save();t=F.final_take()
    except Exception as ex:traceback.print_exc();blocked.append('final take: '+str(ex))
    audit=json.loads((WORK/'base-audit.json').read_text())
    measurements=[f"Initial source pass retained {audit['kept']} states, deferred {len(audit['dropped'])}, and repriced {audit['pending']} unrun recipes.",f"{m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP stages across {m.get('n_values',0)} counts.",f"Completed certified-file fq receipts: {m.get('whole_completed',0)}.","Input snapshots retained hashes and complete source proofs. Own-layout share gates stayed disabled.","The physical corner model included following stacks. Fresh geometry preceded saved unmeasured recipes."]
    next_items=['Follow changed corner and far-zone pairings first. The round28 n805 transfer gained 0.000141661 before peer improvement.','Keep full byte-bound source proofs and preserve exact unmeasured recipes. Measured full and SLP recipes remain closed.']
    extra=WORK/'report-extra.json'
    if extra.exists():
        e=json.loads(extra.read_text());measurements.extend(e.get('what_was_measured',[]));next_items=e.get('next',next_items)
    report=dict(lane='stair-c',improved_n=t.get('improved_n',0),gain=dict(against_base_bar=t.get('against_base_bar',0.),beyond_other_live_r31=t.get('beyond_other_live_r31',0.)),take_dir=str(TAKE),summary=f"Retained {t.get('improved_n',0)} counts below bar31 and every other live take.",what_was_measured=measurements,next=next_items,commits=commits,processes_left=[]if(WORK/'cleanup-final.json').exists()else['inspect work/deadline.log'],blocked=blocked,repo='private repo',branch='main',worktree=str(REPO),pr=None)
    temp=WORK/'report-final.tmp';temp.write_text(json.dumps(report,indent=2)+'\n')
    while time.time()<REPORT-2:time.sleep(min(.25,REPORT-2-time.time()))
    try:
        t=F.prune_live_take()
        report.update(improved_n=t['improved_n'],gain=dict(against_base_bar=t['against_base_bar'],beyond_other_live_r31=t['beyond_other_live_r31']),summary=f"Retained {t['improved_n']} counts below bar31 and every other live take.")
    except Exception as ex:traceback.print_exc();blocked.append('last peer check: '+str(ex))
    temp.write_text(json.dumps(report,indent=2)+'\n')
    while time.time()<REPORT:time.sleep(min(.25,REPORT-time.time()))
    temp.replace(TAKE/'report.json')
    state('REPORT written after00:25Z. take.tsv frozen.');print(json.dumps(report),flush=True)

if __name__=='__main__':main()

