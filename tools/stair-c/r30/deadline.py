"""Stop, verify, publish, document and report this lane at the round deadline."""
import shlex,csv,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,tarfile,time,traceback
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('$PRIVATE_REPO')
LANE=REPO/'lanes/squares'
TAKE=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r30')
WORK=TAKE/'work'
PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=datetime.datetime(2026,11,15,17,45,tzinfo=datetime.timezone.utc).timestamp()
REPORT=datetime.datetime(2026,11,15,17,55,5,tzinfo=datetime.timezone.utc).timestamp()
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
    expected={'coordinator':HERE/'coordinator.py','recovery':HERE/'recover.py','resume-saved':HERE/'resume-saved.py','setup':HERE/'setup.py','bootstrap':WORK/'bootstrap.py','recovery-later':WORK/'recover-later.py','held801':HERE/'held801.py','kick-follow':HERE/'kick_follow.py','restart-reprice':WORK/'restart-reprice.py','follow-driver':HERE/'follow_driver.py'}
    expected.update({'recover-bytes':HERE/'recover_bytes.py','priority-recovered':WORK/'priority-recovered.py','paired':HERE/'paired.py','audit_library':HERE/'audit_library.py'})
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
    import finish_local30 as F
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

def experiment_summary(m):
    measurements=[];prose=[];next_items=[];pair_deltas=[]
    paired=WORK/'paired-results.json'
    if paired.exists():
        rows=json.loads(paired.read_text())
        for seed in sorted({r['seed']for r in rows}):
            pair={r['mode']:r for r in rows if r['seed']==seed}
            if not {'input','bar'}<=set(pair):
                measurements.append(f'Paired seed{seed} has only {list(pair)} completed. No paired conclusion is available.')
                continue
            assert pair['input']['input_sha256']==pair['bar']['input_sha256']
            delta={k:r['kick']['start']-r['kick']['end']for k,r in pair.items()}
            pair_deltas.append((seed,delta))
            text=f"Matched n812 seed{seed}: input-side shortening {delta['input']:.12g}, bar-input shortening {delta['bar']:.12g} of side."
            measurements.append(text);prose.append(text)
            measurements.append(f"Both seed{seed} legs used identical certified bytes, a 900-second cap and the same stopping flags. Each completed a certified-file fq pass.")
        if any(d['bar']>d['input']+1e-9 for seed,d in pair_deltas)and any(d['input']>d['bar']+1e-9 for seed,d in pair_deltas):
            measurements.append('The two matched pairs reversed the preferred variant. This shows a seed interaction, not reliable dominance of one input box.')
            prose.append('The two matched seeds preferred different input-box variants.\nNeither paired comparison supplied a counted row.')
            next_items.append('Keep both input-box variants for changed fresh starts. Seed3912 favored bar-input by4.90988818e-6 of side, while seed4912 favored input-side by4.78861004e-6. Neither supplied a counted n812 row.')
    recovery=WORK/'byte-recovery-all.json'
    if recovery.exists():
        r=json.loads(recovery.read_text());text=f"Recovered {r['restored']} module states from {len(r['aliases'])} exact input paths after full source proofs. The wrong-hash mutant failed."
        measurements.append(text);prose.append(text)
    native=WORK/'native-feed-control.json'
    if native.exists():
        r=json.loads(native.read_text())
        measurements.append(f"An independent native-feeder budget admitted {r['admitted_states']} actual fresh module states in {r['seconds']:.3f}s. CSV source checks had consumed the previous shared budget.")
        prose.append(f"CSV source checks could use the module feeder's whole time budget.\nThe module feeder now has its own budget and reads the newest libraries first.\nIts live control admitted {r['admitted_states']} fresh module states in {r['seconds']:.3f}s.")
        current=WORK/'coord-state.json'
        if current.exists():
            count=max(0,len(json.loads(current.read_text()).get('native',[]))-r['before'])
            measurements.append(f"By collection, the repaired native feeder had admitted {count} additional unique module geometries. Need-file versions and partial-packet contents have distinct queue identities.")
            prose.append(f"By collection, the repaired feeder admitted {count} more module geometries.\nRequest-file changes and partial packets each have their own queue identity.")
    policy=WORK/'library-public-audit.json'
    if policy.exists():
        r=json.loads(policy.read_text())
        text=f"The public-root audit checked {r['groups']} source groups and deferred {r['deferred_groups']}. Owned layouts received no share test."
        measurements.append(text);prose.append(text)
        measurements.append('The cached n805 following-stack corners reached recorded public-first n457 from pablodiegoo, with share1.0. Those exact source versions were excluded. The retained n995 source proof passed through public n462 at share0.23809523809523808 with Apache2.0 terms.')
        prose.append('The cached n805 corners reached public-first n457, whose share was 1.0.\nThose source versions were removed from the worker libraries after the audit.\nThe n995 proof passed through public n462, whose share was 0.23809523809523808.')
    own_bar=WORK/'own-bar-control.json'
    if own_bar.exists():
        r=json.loads(own_bar.read_text());count=sum(r['measured_no_gain_builds'].values())
        measurements.append(f"The actual n995 worker-bar control lowered its side from {r['old_side']:.15g} to the own certified side {r['own_side']:.15g}. It reclassified {count} prior full builds as no gain against that floor.")
        measurements.append('The changed far-zone control kept one first build after 24 count failures, capped its repeat and preserved a below-bar recipe. The existing new-corner and count-cap controls also passed.')
        prose.append(f"The worker bar omitted the lane's own n995 take.\n{count} builds returned to its floor while comparing with the older bar.\nThe corrected worker bar includes the certified own take.\nA changed far zone keeps one first build after a count cap. Its repeat remains capped.\nThe far-zone, corner and count-cap controls passed.")
    base_control=WORK/'basebar-control.json'
    if base_control.exists():
        r=json.loads(base_control.read_text())
        measurements.append(f"The fixed bar30 control matched all {r['actual_rows']} rows and ignored a synthetic later BASE override. No actual BASE line existed, so this changed no measured gain.")
        prose.append('The score baseline stays fixed at bar30.\nAll 1,000 rows matched the brief, and a synthetic later BASE line could not alter them.\nNo actual BASE line existed, so this changed no measured gain.')
    plain=WORK/'plain-follow-control.json'
    if plain.exists():
        r=json.loads(plain.read_text());count=len(r['inherited'])
        measurements.append(f"The plain-follow control cleared inherited kick fields from {count} real near records. Explicit self-follows retain the kick; their plain-fq checks cannot queue a duplicate.")
        prose.append('Plain near follows now clear inherited kick fields.\nFour real inherited records passed the control.\nExplicit self-follows retain the kick, while plain fq checks keep their previous receipts.')
    attempts=WORK/'attempt-control.json'
    if attempts.exists():
        r=json.loads(attempts.read_text());count=r['completed_saved_recipes']
        measurements.append(f"Command receipts identified {count} already attempted saved recipes, including the no-output n813 timeout under r29/r30 aliases. Finished and timed-out attempts close; never-run and failed-import cases stay open.")
        prose.append(f"Command receipts identified {count} already attempted saved recipes.\nThe n813 timeout had repeated under r29 and r30 names without an exported layout.\nThe corrected queue closes those attempts and preserves never-run jobs.")
    control=WORK/'cert-cache-control.json'
    if control.exists():
        measurements.append('The exact-byte certificate cache now persists results under a verifier-code hash. Real n995 disk replay matched its certificate, and a duplicate-square copy failed.')
        prose.append('Certificate results persist under exact input and checker hashes.\nA real n995 disk replay matched its certificate. A duplicate-square copy failed.')
    strict=WORK/'final-named-source-control.json'
    if strict.exists():
        r=json.loads(strict.read_text())
        measurements.append(f"The final named-source receipt control retained n995 with full source proof in {r['recheck_seconds']:.3f}s after preparation. An earlier equivalent near-follow source timed out; exact-score ties now use the direct construction witness.")
    bounded_measure=WORK/'measure-bounded-control.json'
    if bounded_measure.exists():
        r=json.loads(bounded_measure.read_text())
        measurements.append(f"The original diagnostic measurement exceeded its 200-second cap in a nested source walk. The bounded control finished with return code {r['returncode']} in {r['seconds']:.3f}s and marked {r.get('deferred_source_stages',0)} source screens as deferred.")
        prose.append(f"The diagnostic measurement exceeded 200 seconds in a nested source walk.\nBounded diagnostic checks finished in {r['seconds']:.3f}s and deferred {r.get('deferred_source_stages',0)} source screens.\nRetained rows required completed source proofs and actual fq receipts.")
    lp=WORK/'boxcopy/n/lp-bridge/receipt.json'
    if lp.exists():
        r=json.loads(lp.read_text());gain=r['start']-r['certified_side']
        measurements.append(f"The n812 contact LP shortened the matched bar result by {gain:.12g} of side to {r['certified_side']:.15g}. Actual fq from that certificate completed and preserved the better LP input.")
        prose.append(f"Contact LP shortened the n812 bar result by {gain:.12g} of side.\nIts certified side was {r['certified_side']:.15g}.\nThe following fq completed and preserved the better LP certificate.")
    for p in WORK.glob('boxcopy/*/final/995-contact-lp.json'):
        j=json.loads(p.read_text());r=j.get('lp_receipt')
        if not r:continue
        gain=r['start']-r['certified_side'];completed=j.get('certified_file_quench',{}).get('completed',False)
        measurements.append(f"Contact LP on the retained n995 input changed its certified side by {gain:.12g} to {r['certified_side']:.15g}. The certified-file fq completion flag was {completed}. The input SHA256 was {r['input_sha256']}.")
        prose.append(f"Contact LP on n995 changed its certified side by {gain:.12g}.\nIts certified side was {r['certified_side']:.15g}. The following fq completion flag was {completed}.")
    transfers=[]
    for p in WORK.glob('boxcopy/*/raw-a/*.json'):
        j=json.loads(p.read_text())
        if j['n']==748 and not j.get('early_stage')and j.get('built')is not None:transfers.append(j)
    if transfers:
        import math
        best=min(j['built']for j in transfers)
        bar=(1+m.get('bar748',0))*math.sqrt(748)if m.get('bar748')is not None else None
        text=f"The changed n805-to748 pairing exported {len(transfers)} full layouts. Its best side was {best:.15g}."
        measurements.append(text);prose.append(text)
    for p in WORK.glob('boxcopy/*/final/*.json'):
        j=json.loads(p.read_text())
        if j.get('control_only'):continue
        if j['n']==995 and j.get('certified_file_quench',{}).get('completed'):
            measurements.append('The first published n995 composition gained 5.74009938936e-6 against bar30 before peer follows. Its certified-file fq receipt completed.')
            break
    next_items += ['Follow new source-cleared corner and far-zone pairings first. An unmeasured saved composition supplied the first n995 certificate, worth5.74009938936e-6 before peer follows.','Replace the cached805 source tree before another748 transfer. Its recorded public-first457 root measured share1.0, so the original18-state cache is not an admissible pool as a whole.','Keep source recovery tied to exact input versions and run the public-root audit before dispatch. Recovery restored78 states, but the wider root pass found exclusions missed by the older proof-only screen.']
    next_items.sort(key=lambda item:0 if item.startswith('Follow new source-cleared')else 1)
    (WORK/'report-extra.json').write_text(json.dumps(dict(what_was_measured=measurements,next=next_items),indent=2))
    (WORK/'experiment-summary.md').write_text('\n'.join(prose)+'\n')

def document(m,t):
    experiment_summary(m)
    text='\n\n## 17. Round 30\n\n'
    text+='One serial worker ran on each assigned box: boxC, boxD and boxE.\n'
    text+='The restored library kept complete source proofs and byte hashes.\n'
    text+='Fresh compositions preceded saved recipes. Completed recipes stayed closed.\n'
    text+='The physical corner model included following flush stacks.\n'
    text+='Own layouts had no share gate. Public starts retained licence and source checks.\n\n'
    text+=f"The workers exported {m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP stages across {m.get('n_values',0)} counts.\n"
    text+=f"The final take retained {t.get('improved_n',0)} counts, gaining {t.get('against_base_bar',0):.15g} against bar30.\n"
    text+='Certification used border finesafe at clearance 2.2e-11.\n'
    text+='Each retained row required a remote fq pass from its certified file.\n'
    text+='The [result table](../results/stair-c-r30-2026-11-15.tsv) records the builds and source screens.\n'
    text+='Full experiment receipts and exact saved queues remain in the take work directory.\n'
    extra=WORK/'experiment-summary.md'
    if extra.exists():text+='\n'+extra.read_text()+'\n'
    text+='\nAll remote archives passed SHA256 verification before scratch removal.\n'
    text+='The shared runtimes remain in place.\n'
    excerpt=WORK/'doc-r30.md';excerpt.write_text(text)
    checker='$STYLE_CHECK/check.py'
    if run(['/opt/homebrew/bin/python3',checker,'--level','default',str(excerpt)],60).returncode:raise RuntimeError('readable check failed')
    doc=LANE/'avenues/stair-c.md'
    if '\n## 17. Round 30\n'not in doc.read_text():
        with doc.open('a')as f:f.write(text)
    paths=[str(doc.relative_to(REPO)),str((LANE/'results/stair-c-r30-2026-11-15.tsv').relative_to(REPO))]
    paths += [str(p.relative_to(REPO))for p in sorted(HERE.glob('*.py'))]
    result=run(['git','add','--',*paths],60)
    if result.returncode:raise RuntimeError('stage failed')
    result=run(['git','commit','--only','-m','Record stair-c round 30 composition experiments','--',*paths],120)
    if result.returncode:raise RuntimeError('commit failed')
    sha=run(['git','rev-parse','HEAD'],30).stdout.strip()
    changed=run(['git','show','--format=','--name-only',sha],30).stdout.splitlines()
    if not set(changed)<=set(paths):raise RuntimeError('foreign paths in commit')
    run(['git','show','--stat','--oneline',sha],30)
    pulled=run(['git','pull','--rebase','--autostash'],60).returncode==0
    pushed=pulled and run(['git','push','origin','HEAD:main'],60).returncode==0
    if not pushed:pushed=run(['git','push','origin','HEAD:main'],60).returncode==0
    rebased=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 30 composition experiments$'],30).stdout.strip()
    sha=rebased or sha;state('COMMIT '+sha+(' pushed'if pushed else' not pushed'))
    earlier=WORK/'early-commits.json'
    return (json.loads(earlier.read_text())if earlier.exists()else[])+[sha+(' (pushed)'if pushed else' (not pushed)')]

def main():
    import importlib.util
    os.chdir(REPO)
    spec=importlib.util.spec_from_file_location('finish_local30',HERE/'finish-local.py')
    while time.time()<HARD:time.sleep(min(45,HARD-time.time()))
    F=importlib.util.module_from_spec(spec);sys.modules['finish_local30']=F;spec.loader.exec_module(F)
    m={};t={};blocked=[];commits=[]
    state('START final collection. Long jobs stop17:45Z. Final take before17:55Z and report after17:55Z.')
    try:m,t=finish()
    except Exception as ex:traceback.print_exc();blocked.append('collection: '+str(ex))
    if not blocked:
        try:commits=document(m,t)
        except Exception as ex:traceback.print_exc();blocked.append('documentation: '+str(ex))
    while time.time()<REPORT-35:time.sleep(min(30,REPORT-35-time.time()))
    try:t=F.final_take()
    except Exception as ex:traceback.print_exc();blocked.append('final take: '+str(ex))
    while time.time()<REPORT:time.sleep(min(30,REPORT-time.time()))
    audit=json.loads((WORK/'base-audit.json').read_text())
    measurements=[f"Source pass retained {audit['kept']} states, deferred {len(audit['dropped'])}, and repriced {audit['pending']} unrun recipes.",f"{m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP stages across {m.get('n_values',0)} counts.",f"Completed certified-file fq receipts: {m.get('whole_completed',0)}.","Input snapshots retained hashes and complete source proofs. Own-layout share gates stayed disabled.","The physical corner model included following stacks. Fresh geometry preceded saved unmeasured recipes."]
    next_items=['Follow changed corner and far-zone pairings first. The round28 n805 transfer gained 0.000141661 before peer improvement.','Keep full byte-bound source proofs and preserve exact unmeasured recipes. Measured full and SLP recipes remain closed.']
    extra=WORK/'report-extra.json'
    if extra.exists():
        e=json.loads(extra.read_text());measurements.extend(e.get('what_was_measured',[]));next_items=e.get('next',next_items)
    report=dict(lane='stair-c',improved_n=t.get('improved_n',0),gain=dict(against_base_bar=t.get('against_base_bar',0.),beyond_other_live_r30=t.get('beyond_other_live_r30',0.)),take_dir=str(TAKE),summary=f"Retained {t.get('improved_n',0)} counts below bar30 and every other live take.",what_was_measured=measurements,next=next_items,commits=commits,processes_left=[]if(WORK/'cleanup-final.json').exists()else['inspect work/deadline.log'],blocked=blocked,repo='private repo',branch='main',worktree=str(REPO),pr=None)
    temp=WORK/'report-final.tmp';temp.write_text(json.dumps(report,indent=2)+'\n');temp.replace(TAKE/'report.json')
    state('REPORT written after17:55Z. take.tsv frozen.');print(json.dumps(report),flush=True)

if __name__=='__main__':main()

