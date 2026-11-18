"""Stop, verify, publish, document and report this lane at the round deadline."""
import csv,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,tarfile,time,traceback
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('$PRIVATE_REPO')
LANE=REPO/'lanes/squares'
TAKE=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r27')
WORK=TAKE/'work'
PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=datetime.datetime(2026,11,14,23,45,tzinfo=datetime.timezone.utc).timestamp()
REPORT=datetime.datetime(2026,11,14,23,55,5,tzinfo=datetime.timezone.utc).timestamp()
HOSTS=[('boxC','n','venv/bin/python'),('boxD','m','venv/bin/python'),('boxE','s','$SCRATCH/squares-base/venv/bin/python')]

def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def state(s):
    with (TAKE/'STATE.txt').open('a') as f:f.write(stamp()+' boxA '+s+'\n')
def run(args,limit=90):
    p=subprocess.run(args,cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=limit)
    print(stamp(),args[0],p.returncode,p.stdout[-5000:],flush=True)
    return p

def stop_coordinator():
    pid=int((WORK/'coordinator.pid').read_text())
    # Confirm the saved PID before signalling. Include its own transport children.
    lines=subprocess.check_output(['ps','-axo','pid=,ppid=,command='],text=True).splitlines()
    rows=[line.split(None,2) for line in lines if len(line.split(None,2))==3]
    cmd=next((r[2] for r in rows if int(r[0])==pid),'')
    if not cmd:return
    if not any(name in cmd for name in ['coordinator.py','coordinator2.py']):raise RuntimeError('coordinator PID identity changed')
    own={pid}
    while True:
        more={int(r[0]) for r in rows if int(r[1]) in own}
        if more<=own:break
        own.update(more)
    for p in sorted(own-{os.getpid()},reverse=True):
        try:os.kill(p,signal.SIGTERM)
        except ProcessLookupError:pass
    state('STOP coordinator pid'+str(pid)+' and its transports before final receipt snapshots')

def finish():
    sys.path[:0]=[str(HERE),str(LANE)]
    import finish_local27 as F
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
    text='''\n\n## 14. Round 27\n\nThe lane used the round 27 bar and compared every candidate with the live round 27 takes.\nOne serial worker ran on each of boxC, boxD and boxE.\nSearch ended at 23:15 UTC and all long jobs ended by 23:45 UTC on November 14.\n\nThe source gate reopened the Samanyu seed tree under the round 27 override.\nIt restored 106 of the 110 states removed in round 26.\nThe library held 2,567 states after 350 source or share refusals.\nThe prvsiyan share test and the other excluded sources stayed in force.\nThe source control accepted the reopened seed and rejected the excluded public roots.\nThe share control rejected 818, 706 and 971, and accepted the independent 921 and 860 designs.\nEvery new donor was copied with its SHA256 before dispatch.

The coordinator now reads the current rectangle part records.
Both the producer and assembler walkers must pass.
Each accepted rectangle keeps its full walk snapshot and source notices.
The 863 positive control passed, and a missing-part copy failed.\n\nAt adoption, live packets had waited up to 54 minutes behind reopened packets and close builds.\nThe replacement worker reserved every third turn for a live import.\nEvery twelfth turn chose the oldest live packet.\nThe existing import and build-cap controls passed.\nFour new cadence cases passed, and always-import and never-import mutants failed.\nThe workers resumed their saved queues after their current jobs finished.

Each new live corner gets one build after the count cap.
Repeats of that corner keep the cap.
The control built the first new corner and skipped its repeated build.
The 871 and 932 certified-file probes both worsened their inputs.
The wrapper kept each better input, and neither probe entered the take.\n\nExact-f runs added new seeds and longer hops near f 0.80.\nSeed 28 at 860 lowered corner loss to 3.5132, against 3.5150 in round 26.\nThe 920 seed-28 corner reached 3.5109.\nNew requests then tried seeds 30 and 31 with 16-minute hops at the live fraction.\nThese losses describe modules. Only certified full layouts count in the take.\n\n'''
    text+=f'The workers exported {m["full_builds"]} full builds and {m["slp_exports"]} SLP stages across {m["n_values"]} counts.\n'
    text+=f'The final take retained {t["improved_n"]} counts, with score gain {t["against_base_bar"]:.15g} against the round 27 bar.\n'
    text+=f'The gain beyond the other live takes was {t["beyond_other_live_r27"]:.15g}.\n'
    text+='The [result table](../results/stair-c-r27-2026-11-14.tsv) records each exported stage and its source screen.\n\n'
    text+='All three remote receipts passed SHA256 verification before scratch removal.\nChanged-byte controls failed, and the sibling scratch control passed.\nThe local coordinator stopped before the final snapshots.\nNo lane process remains on the worker boxes.\n'
    excerpt=WORK/'doc-r27.md';excerpt.write_text(text)
    checker='$STYLE_CHECK/check.py'
    if not pathlib.Path(checker).exists():checker='$STYLE_CHECK/check.py'
    result=run(['/opt/homebrew/bin/python3',checker,'--level','default',str(excerpt)],60)
    if result.returncode:raise RuntimeError('new documentation failed readable')
    if '## 14. Round 27' not in doc.read_text():
        with doc.open('a') as f:f.write(text)
    paths=[str(doc.relative_to(REPO)),str((LANE/'results/stair-c-r27-2026-11-14.tsv').relative_to(REPO))]
    paths += [str(p.relative_to(REPO)) for p in sorted(HERE.glob('*.py'))]
    result=run(['git','add','--',*paths],60)
    if result.returncode:raise RuntimeError('stage failed')
    result=run(['git','commit','--only','-m','Record stair-c round 27 measurements and bounded live imports','--',*paths],120)
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
    rebased=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 27 measurements and bounded live imports$'],30).stdout.strip()
    if rebased:sha=rebased
    state('COMMIT '+sha+(' pushed to origin/main' if pushed else ' not pushed'))
    return [sha+(' (pushed)' if pushed else ' (not pushed)')]

def main():
    os.chdir(REPO)
    # Import by path because the original filename contains a hyphen.
    import importlib.util
    spec=importlib.util.spec_from_file_location('finish_local27',HERE/'finish-local.py')
    while time.time()<HARD:time.sleep(min(45,HARD-time.time()))
    mod=importlib.util.module_from_spec(spec);sys.modules['finish_local27']=mod;spec.loader.exec_module(mod)
    state('START deadline finalizer. Long-job deadline23:45Z, report after23:55Z. Log work/deadline.log')
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
    # Revalidate before 23:55, then write only the report after the deadline.
    if not blocked:
        t=mod.final_take()
    while time.time()<REPORT:time.sleep(min(45,REPORT-time.time()))
    report=dict(lane='stair-c',improved_n=t.get('improved_n',0),gain=dict(against_base_bar=t.get('against_base_bar',0.),beyond_other_live_r27=t.get('beyond_other_live_r27',0.)),take_dir=str(TAKE),summary='Round 27 stair-c retained '+str(t.get('improved_n',0))+' counts after the source, share, certified-file quench and live-take checks.',what_was_measured=[f'{m.get("full_builds",0)} full builds and {m.get("slp_exports",0)} SLP exports across {m.get("n_values",0)} counts.', 'Reopened 106 of 110 round 26 removed states. The 2567-state library kept the prvsiyan share test and other excluded roots.', 'Live packets waited54m before the reserved third-turn import fix. Four new cadence controls passed and two mutants failed.', 'Exact-f seed28: 860 corner loss3.5132 and 920 loss3.5109. New seeds30/31 used16m hops.', 'The 871 and 932 certified-file probes completed with fq rc0 in71.98s and48.43s. Both worsened their inputs, so neither counted.', 'Current rectangle part records pass both the producer and assembler source walks. The actual863 positive control passed; a missing-part copy failed.', 'Full measurements and saved queues: work/measurements-final.json. Per-stage results: lanes/squares/results/stair-c-r27-2026-11-14.tsv.'],next=['Follow fresh changed corners before repeated near-floor compositions. Live packets waited54m under the former queue order.', 'Reprice the saved queues against the next bar and skip completed geometry. Their exact states and recipes remain in the three verified archives.', 'Use the new corner and full-layout measurements together before choosing further exact-f seeds. Scalar loss improvements alone did not certify a full layout.'],commits=commits,processes_left=[] if not blocked else ['check work/deadline.log'],blocked=blocked,repo='private repo',branch='main',worktree=str(REPO),pr=None)
    tmp=TAKE/'work/report-final.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,TAKE/'report.json')
    state('REPORT report.json written after23:55Z. Final take frozen.');print(json.dumps(report,indent=2),flush=True)

if __name__=='__main__':main()
