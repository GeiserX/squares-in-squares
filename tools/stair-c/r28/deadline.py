"""Stop, verify, publish, document and report this lane at the round deadline."""
import shlex,csv,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,tarfile,time,traceback
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('$PRIVATE_REPO')
LANE=REPO/'lanes/squares'
TAKE=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r28')
WORK=TAKE/'work'
PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=datetime.datetime(2026,11,15,5,35,tzinfo=datetime.timezone.utc).timestamp()
REPORT=datetime.datetime(2026,11,15,5,55,5,tzinfo=datetime.timezone.utc).timestamp()
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
    expected={'coordinator':HERE/'coordinator.py','recovery':HERE/'recover.py','resume-saved':HERE/'resume-saved.py','setup':HERE/'setup.py','bootstrap':WORK/'bootstrap.py','recovery-later':WORK/'recover-later.py','held801':HERE/'held801.py','kick-follow':HERE/'kick_follow.py','restart-reprice':WORK/'restart-reprice.py'}
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
    import finish_local28 as F
    stop_coordinator()
    verified=[]
    for host,key,python in HOSTS:
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
        verified.append((host,key,python,receipt['receipt_sha256']))
        state('VERIFIED '+host+' archive '+str(receipt['files'])+' payload files; receipt '+receipt['receipt_sha256'])
    F.C.publish();F.C.save()
    measurement=F.measure();take=F.final_take()
    for host,key,python,digest in verified:
        result=run(['ssh','-o','ConnectTimeout=15',host,'cd $SCRATCH/squares-stair-c && '+python+' finish-box.py --remove '+digest],60)
        if result.returncode:raise RuntimeError(host+' scratch removal failed')
    (WORK/'cleanup-final.json').write_text(json.dumps(dict(verified=[dict(host=h,receipt=d) for h,k,p,d in verified],processes_left=[]),indent=2))
    state('FINISH remote payloads verified and own scratch removed on all three boxes. Shared runtimes kept. take retained'+str(take['improved_n']))
    return measurement,take

def document(m,t):
    doc=LANE/'avenues/stair-c.md'
    audit=json.loads((WORK/'base-audit.json').read_text())
    text="\n\n## 15. Round 28\n\n"
    text+="The lane used bar28 and the live round 28 takes.\n"
    text+="One serial worker ran on each of boxC, boxD and boxE.\n"
    text+="Search ended at 05:25 UTC on November 15. All long jobs had a 05:45 UTC deadline.\n\n"
    text+=f"The initial source pass kept {audit['kept']} states and deferred or rejected {len(audit['dropped'])}.\n"
    text+="RULE001903 then reopened own geometry matches and their descendants.\n"
    text+=f"The first pass repriced {audit['pending']} admitted unrun recipes.\n"
    text+="The saved queue keeps all 1,426 unrun recipes separate from 2,923 completed recipes.\n"
    text+="Each input kept its byte snapshot and SHA256 before dispatch.\n"
    text+="At 00:19 UTC the main handoff relayed the new source rule. Own layouts and their descendants do not fail on geometry share.\n"
    text+="The updated controls admitted own construction, held 801, seeds 503/983 and the own n684 tree. Recorded excluded-file ancestry still fails.\n"
    text+="The fresh import, count cap, live cadence and new corner controls passed.\n\n"
    text+="A real certified-975 fq control completed with return code 0 in 6.81 seconds.\n"
    text+="Its output worsened the input, so the wrapper preserved the better certified input.\n"
    text+="Close whole rectangles without two flush arms also received one certified-file fq pass. A dry plain probe then qualified for one bounded kick leg.\n"
    text+="The inflated-975 kick control recovered 0.00770 side in 60.07 seconds, then completed certified-file fq in 5.05 seconds.\n"
    text+="The first n918 kick shortened side by 0.00000450 and still missed the bar. A new seed supplied one continuation.\n"
    text+="The first n871 kick shortened side by 0.0000023945 and still missed the bar.\n"
    text+="Its continuation reached bar28 side to within 0.000000000054, with no counted gain.\n"
    text+="Own near compositions within 0.00002 side of the live bar also received a follow.\n"
    text+="Full CSV source controls admitted n805 and n812. The n871 follow also passed its full walk.\n"
    text+="Module records missed unresolved parents in n804, n995 and n997 follows. Those follows remained uncounted.\n"
    text+="Publication now requires a full CSV source walk for every score candidate.\n"
    text+="Pending jobs now use the latest live bar before each build.\n"
    text+="When a bar falls, the cap counts completed recipes against that bar.\n"
    text+="The queue control repriced old n805 to +0.000325 side and gave n812 priority.\n"
    text+="SLP and full stages count as one recipe. Unfinished recipes do not count toward the cap.\n"
    text+="The live-bar cache invalidated a lower replacement. The certificate cache rejected a changed overlapping CSV.\n"
    text+=f"The final archive holds {len(m.get('whole_follows',[]))} whole-layout receipts.\n\n"
    text+=f"Of these, {m.get('whole_completed',0)} completed the final certified-file fq invocation.\n\n"
    text+="Fresh layouts and rectangle handoffs preceded the saved queue.\n"
    text+="Each readable fresh layout supplied a corner and far zones to all three workers.\n"
    text+="A new corner received one full build after the count cap. Repeated corners kept the cap.\n"
    text+="The unchanged exact-f seed and hop campaigns stayed closed because round 27 reached the same loss floors.\n\n"
    text+="An n805 composition reached score 0.0164302490798085, gaining 0.000141661374949642 against bar28.\n"
    text+="Rebuild later improved a pinned copy of an earlier stair-c n805 composition.\n"
    text+="The final take removed any row beaten by another live take.\n\n"
    text+=f"The workers exported {m['full_builds']} full builds and {m['slp_exports']} SLP stages across {m['n_values']} counts.\n"
    text+=f"At archive time the take retained {t['improved_n']} counts, gaining {t['against_base_bar']:.15g} against bar28.\n"
    text+=f"The gain beyond the other live takes was {t['beyond_other_live_r28']:.15g}.\n"
    text+="Every retained row required a completed fq invocation from its certified file and a fresh floatsafe check at 2.2e-11.\n"
    text+="The [result table](../results/stair-c-r28-2026-11-14.tsv) lists measured builds and their source screens.\n\n"
    text+="All remote copies passed SHA256 verification before scratch removal.\n"
    text+="The shared runtimes remain in place. No lane worker remains.\n"
    excerpt=WORK/'doc-r28.md';excerpt.write_text(text)
    checker='$STYLE_CHECK/check.py'
    if not pathlib.Path(checker).exists():checker='$STYLE_CHECK/check.py'
    result=run(['/opt/homebrew/bin/python3',checker,'--level','default',str(excerpt)],60)
    if result.returncode:raise RuntimeError('new documentation failed readable')
    if '## 15. Round 28' not in doc.read_text():
        with doc.open('a') as f:f.write(text)
    paths=[str(doc.relative_to(REPO)),str((LANE/'results/stair-c-r28-2026-11-14.tsv').relative_to(REPO))]
    paths += [str(p.relative_to(REPO)) for p in sorted(HERE.glob('*.py'))]
    result=run(['git','add','--',*paths],60)
    if result.returncode:raise RuntimeError('stage failed')
    result=run(['git','commit','--only','-m','Record stair-c round 28 ancestor checks and fresh composition measurements','--',*paths],120)
    if result.returncode:raise RuntimeError('lane commit failed')
    match=re.search(r'^\[[^\n]*\s([0-9a-f]{7,40})\]',result.stdout,re.M)
    if not match:raise RuntimeError('cannot identify the lane commit')
    sha=run(['git','rev-parse',match.group(1)],30).stdout.strip()
    changed=run(['git','show','--format=','--name-only',sha],30).stdout.splitlines()
    if not set(changed)<=set(paths):raise RuntimeError('commit contains foreign paths')
    run(['git','show','--stat','--oneline',sha],30)
    result=run(['git','pull','--rebase','--autostash'],120)
    pushed=False
    if result.returncode==0:
        result=run(['git','push','origin','HEAD:main'],120);pushed=result.returncode==0
        if not pushed:pushed=run(['git','push','origin','HEAD:main'],120).returncode==0
    # A successful rebase can change the commit ID. Other lanes can also
    # advance HEAD, so locate this unique subject instead of reporting HEAD.
    rebased=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 28 ancestor checks and fresh composition measurements$'],30).stdout.strip()
    if rebased:sha=rebased
    state('COMMIT '+sha+(' pushed to origin/main' if pushed else ' not pushed'))
    return [sha+(' (pushed)' if pushed else ' (not pushed)')]

def main():
    os.chdir(REPO)
    # Import by path because the original filename contains a hyphen.
    import importlib.util
    spec=importlib.util.spec_from_file_location('finish_local28',HERE/'finish-local.py')
    while time.time()<HARD:time.sleep(min(45,HARD-time.time()))
    mod=importlib.util.module_from_spec(spec);sys.modules['finish_local28']=mod;spec.loader.exec_module(mod)
    state('START deadline finalizer. Long-job deadline05:45Z, report after05:55Z. Log work/deadline.log')
    blocked=[];commits=[];m={};t={}
    try:
        m,t=finish()
        commits=document(m,t)
    except Exception as e:
        traceback.print_exc();blocked.append(str(e));state('FINALIZER BLOCK '+str(e))
        if (WORK/'measurements-final.json').exists():m=json.loads((WORK/'measurements-final.json').read_text())
        if (WORK/'final-take-check.json').exists():t=json.loads((WORK/'final-take-check.json').read_text())
    freeze=REPORT-20
    while time.time()<freeze:time.sleep(min(45,freeze-time.time()))
    # Revalidate before 05:55, then write only the report after the deadline.
    if not blocked:
        t=mod.final_take()
    while time.time()<REPORT:time.sleep(min(45,REPORT-time.time()))
    audit=json.loads((WORK/'base-audit.json').read_text())
    closest=', '.join(str(v['n'])+' ('+format(v['side_margin'],'+.6g')+' side)' for v in m.get('closest_full',[])[:3])
    pending=sum(q.get('pending_builds',0)for q in m.get('queues',{}).values())
    report=dict(lane='stair-c',improved_n=t.get('improved_n',0),gain=dict(against_base_bar=t.get('against_base_bar',0.),beyond_other_live_r28=t.get('beyond_other_live_r28',0.)),take_dir=str(TAKE),summary='Retained '+str(t.get('improved_n',0))+' counts below the live takes. N805 compositions gained 0.000141661 on bar28 before rebuild improved a pinned copy.',what_was_measured=['The live-queue control repriced an old n805 job to +0.000325 side and gave n812 priority. Completed SLP/full stages count once. All three workers adopted the update after their current job.','Full CSV source controls admitted n805, n812 and n871. The n804, n995 and n997 follows have unresolved parents and remain uncounted. Publication requires a full source walk for each score candidate.','The first n871 kick shortened side by 0.0000023945. Its continuation reached bar28 side to within 5.4e-11, with no counted gain.','Our n805 composition reached score 0.0164302490798085, gaining 0.000141661374949642 on bar28. Rebuild later improved a pinned earlier stair-c composition. Final retained gains use the current live takes.',f"{m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP exports across {m.get('n_values',0)} counts.",f"Initial source pass: {audit['kept']} module states. {len(audit['dropped'])} deferred or rejected. Repriced {audit['pending']} unrun recipes.",'RULE001903 controls admitted own construction, held n801, seeds 503/983 and own n684 descendants. Direct public starts keep the share test. Recorded excluded-file ancestry still fails. Fresh import, cap, cadence and saved-recipe controls passed.','Fresh full layouts and rectangle cuts ran before the saved queue. Unchanged exact-f seed and hop campaigns stayed closed.',f"Whole-layout follow receipts: {len(m.get('whole_follows',[]))}, including {m.get('whole_completed',0)} completed certified-file fq runs. The certified n975 control completed rc0 in 6.81 s and kept the better input.",'The kick control recovered 0.00770 side from an inflated n975 in 60.07 s. Fq from its certified result completed rc0 in 5.05 s.','Each retained row requires fq from the certified file, floatsafe clearance 2.2e-11 and score gain above 1e-10.','Exact per-stage measurements and saved queues are in work/measurements-final.json.','All three remote archives passed SHA256 verification before own scratch removal. Shared runtimes were kept.' if not blocked else 'Cleanup needs inspection: '+str(blocked)],next=["Follow fresh changed compositions and source-cleared rectangle cuts first. N805 compositions gained 0.000141661 on bar28 before rebuild improved a pinned copy.",'Change the corner/far-zone pairing before retrying full builds above the 1e-8 side screen: '+(closest or 'none above the final bar')+'. Their measured margins remain above the bar.','Repair the source records for n804, n995 and n997 before reusing those follows. The full walks found missing backlog source metadata and the frozen n814 donor.',f"Reprice the {pending} archived pending builds against the next bar. The 1426 saved recipes were separated from 2923 completed recipes before dispatch.",'Change topology or count class before another exact-f seed campaign. Round 27 hops of 16 minutes returned loss floors near 3.5130 and 3.5109 without a certified full row.'],commits=commits,processes_left=[] if not blocked else ['inspect work/deadline.log'],blocked=blocked,repo='private repo',branch='main',worktree=str(REPO),pr=None)
    tmp=TAKE/'work/report-final.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,TAKE/'report.json')
    state('REPORT report.json written after05:55Z. Final take frozen.');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
