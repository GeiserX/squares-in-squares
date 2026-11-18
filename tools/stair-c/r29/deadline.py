"""Stop, verify, publish, document and report this lane at the round deadline."""
import shlex,csv,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,tarfile,time,traceback
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('$PRIVATE_REPO')
LANE=REPO/'lanes/squares'
TAKE=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r29')
WORK=TAKE/'work'
PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=datetime.datetime(2026,11,15,11,42,tzinfo=datetime.timezone.utc).timestamp()
REPORT=datetime.datetime(2026,11,15,11,55,5,tzinfo=datetime.timezone.utc).timestamp()
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
    expected.update({'recover-bytes':HERE/'recover_bytes.py','priority-recovered':WORK/'priority-recovered.py'})
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
    import finish_local29 as F
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
    text='\n\n## 16. Round 29\n\n'
    text+='One serial worker ran on each of boxC, boxD and boxE.\n'
    text+='Fresh compositions and changed rectangle inputs preceded saved recipes.\n'
    text+='The source pass retained 3002 module states and repriced 97 pending recipes against bar29.\n'
    text+='The unchanged exact-f hop campaign stayed closed after its round 27 loss floors.\n\n'
    text+='Each queued input kept its byte snapshot and SHA256.\n'
    text+='Own layouts and their descendants had no share or ancestor-share test.\n'
    text+='Direct public starts retained the licence and share checks.\n'
    text+='Recorded excluded-file ancestry stayed out.\n\n'
    text+='The import, count-cap, new-corner, live-bar and saved-recipe controls passed.\n'
    text+='The controls now account for the queue sort before checking which build runs.\n'
    text+='The certified n975 control passed, and a duplicate-square copy failed.\n'
    text+='The larger-corner control moved complete flush stacks into the corner before tabulation.\n'
    text+='Four n975 assemblies kept side 31.714095652247682, with worst gap about -2.6e-12.\n'
    text+='A partial-stack mutant failed. The experiment used admitted inputs at n805, n812, n871 and n997.\n'
    text+='The bar-probe control rejected a false low prediction, then built n975 at side 31.714095650717713.\n'
    text+='Failed starts could then probe near the live bar. Four failed probes cap one count and corner.\n'
    text+='The cap preserves a first fresh corner, and a changed-cap mutant failed.\n'
    text+='One n997 corner failed 23 cross-count bar probes.\n'
    text+='Five corner paths still refused two measured n882 recipes.\n'
    text+='A table-knot replay at n945 and fraction .995 explained the false prediction.\n'
    text+='Its corner escaped beyond the declared cut, producing a full-layout gap of -1.0948843355167908.\n'
    text+='That exact corner closed for cross-count builds. Native n997 recipes remained open.\n'
    text+='Skipped recipes moved into the deferred queue. A control preserved both deferred and pending recipes.\n\n'
    text+='A new guard checked corner supports against their original cut allowances.\n'
    text+='All four n975 assemblies passed, and the observed escaped corner failed the guard.\n'
    text+='Three new guarded corner IDs from n997 then ran through the serial workers.\n'
    text+='The guarded n945 replay had no table fit and refused the physical corner in 25.103 seconds.\n'
    text+=f"Guarded corners produced {len(m.get('guarded_corner_full',[]))} full layouts.\n"
    text+='A physical replay identified the collision between corner square 65 and later run square 180.\n'
    text+='The next model included three following flush stacks in each local arm.\n'
    text+='Four n975 source assemblies passed at side 31.714095652247682.\n'
    text+='A duplicate of a free square in the following run failed the local legality check.\n'
    text+='The changed n945 replay refused the corner in 16.357 seconds.\n'
    text+='New corner IDs from n871 and n997 then ran through the workers.\n'
    text+=f"Corners with following stacks produced {len(m.get('following_stacks_full',[]))} full layouts.\n"
    text+='Three further n975 controls moved two whole stacks into the free corner.\n'
    text+='They preserved side 31.714095652247682. An incomplete-stack mutant failed.\n'
    text+=f"Two-stack transfers produced {len(m.get('two_stack_transfer_full',[]))} full layouts.\n"
    text+='Known native recipes also ran directly from their module geometry, without tables used only for ranking.\n'
    text+='The direct n975 control passed at side 31.714095650716718 and positive gap.\n'
    text+='A corner-path control found later feasible paths after the original first path refused.\n'
    text+='It preserved fixed source geometry before trying rotation.\n'
    text+=f"Direct native recipes produced {len(m.get('native_direct_full',[]))} full layouts.\n\n"
    text+=f"Expanded corners produced {len(m.get('expanded_corner_full',[]))} full layouts.\n"
    text+=f"Bar probes produced {len(m.get('bar_probe_full',[]))} full layouts and {m.get('bar_probe_failed',0)} failed starts.\n"
    text+='Certification used border\'s bisected dilation at clearance 2.2e-11.\n'
    text+='Each published row required a completed fq invocation from its certified file.\n\n'
    text+='Whole-layout follows included 900-second kicks on the three workers.\n'
    text+='One n986 kick shortened its input by 6.81061522e-6 of side, then reached the existing bar.\n'
    text+='A proposed source-locator repair failed the full n986 proof control and was reverted.\n'
    text+='Withdrawals named pinned bytes. Controls kept replacement bytes at a reused path eligible.\n\n'
    recovered=m.get('byte_recovery',{})
    text+=f"A later byte recovery restored {recovered.get('restored',0)} states held by the initial path checks.\n"
    text+=f"It recovered {recovered.get('approved_versions',0)} exact input versions from {recovered.get('paths',0)} original paths.\n"
    text+='Each version passed the full source proof. A wrong expected hash failed.\n'
    text+='Copied source records kept content hashes, and the frozen files stayed unchanged.\n'
    text+='One original path needed two byte versions, so rebinding selected the recorded hash.\n'
    text+='A bounded first build for each changed physical corner preceded the normal live-bar order.\n'
    text+='The priority control passed. A mutant with priority disabled failed.\n'
    text+='Repeated corners returned to the count caps.\n'
    text+=f"Recovered modules appeared in {len(m.get('recovered_module_full',[]))} full builds.\n\n"
    saved=m.get('saved_recovery',{})
    text+=f"The saved queue contained {saved.get('unrun',0)} exact unrun recipes.\n"
    text+=f"Of these, {saved.get('source_held_jobs',0)} named recovered module states.\n"
    text+='The queue builder derived unrun status before source admission and included deferred jobs.\n'
    text+='Recorded full layouts and SLP stages remained completed.\n'
    text+='Controls deferred missing modules, admitted recovered geometry once and kept measured recipes closed.\n\n'
    text+='A late audit found failed follow offers from before the certificate directory existed.\n'
    text+='The directory writer now creates the parent and resumes an identical certified input.\n'
    text+='Controls reject changed input hashes and coordinates.\n'
    text+='Failed offers now retry, and an untraced best row can yield to a source-admitted row.\n'
    text+='The retry and fallback controls passed.\n'
    text+='The real n812 offer passed its full source proof and queued a 900-second kick.\n'
    text+=f"The repair admitted {len(m.get('follow_repair',{}).get('new_offers',[]))} new offers.\n\n"
    text+='Table search ended at 11:25 UTC. Queued kicks could run until 11:38 UTC.\n'
    text+='The deadline control reserved 150 seconds for their final certified-file quench.\n'
    text+='Collection began at 11:42 UTC. Each worker stopped before its archive.\n'
    text+='The archive deadline was 11:45 UTC.\n\n'
    if m.get('bar_input_control',{}).get('passed'):
        v=m['bar_input_control']
        text+='A final variant capped the box side sent to fq at the live bar.\n'
        text+=f"The n975 control requested {v['requested_side']:.15f} instead of {v['uncapped_side']:.15f}.\n"
        text+=f"Its returned geometry had side {v['actual_side']:.15f} and gap {v['gap']:.6g}.\n"
        text+='Returned sides stayed unmodified. A duplicate-square mutant failed.\n'
        if m.get('bar_input_leg'):text+='The n812 variant then ran with the remaining kick window through 11:38 UTC.\n'
        text+='\n'
    text+=f"The workers exported {m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP stages across {m.get('n_values',0)} counts.\n"
    text+=f"At collection, the take retained {t['improved_n']} counts, gaining {t['against_base_bar']:.15g} against bar29.\n"
    text+=f"The gain beyond other live takes was {t['beyond_other_live_r29']:.15g}.\n"
    text+='The [result table](../results/stair-c-r29-2026-11-15.tsv) records measured stages and their source screens.\n'
    text+='The detailed follow receipts and saved queues remain in the take work directory.\n\n'
    text+='All three remote archives passed SHA256 verification before own scratch removal.\n'
    text+='The shared runtimes remain in place. No lane worker remains.\n'
    excerpt=WORK/'doc-r29.md';excerpt.write_text(text)
    checker='$STYLE_CHECK/check.py'
    result=run(['/opt/homebrew/bin/python3',checker,'--level','default',str(excerpt)],60)
    if result.returncode:raise RuntimeError('readable checker failed')
    doc=LANE/'avenues/stair-c.md'
    if '\n## 16. Round 29\n' not in doc.read_text():
        with doc.open('a')as f:f.write(text)
    paths=[str(doc.relative_to(REPO)),str((LANE/'results/stair-c-r29-2026-11-15.tsv').relative_to(REPO))]
    paths += [str(p.relative_to(REPO))for p in sorted(HERE.glob('*.py'))]
    result=run(['git','add','--',*paths],60)
    if result.returncode:raise RuntimeError('stage failed')
    result=run(['git','commit','--only','-m','Record stair-c round 29 fresh composition measurements','--',*paths],120)
    if result.returncode:raise RuntimeError('lane commit failed')
    match=re.search(r'^\[[^\n]*\s([0-9a-f]{7,40})\]',result.stdout,re.M)
    if not match:raise RuntimeError('commit ID missing')
    sha=run(['git','rev-parse',match.group(1)],30).stdout.strip()
    changed=run(['git','show','--format=','--name-only',sha],30).stdout.splitlines()
    if not set(changed)<=set(paths):raise RuntimeError('commit contains foreign paths')
    run(['git','show','--stat','--oneline',sha],30)
    result=run(['git','pull','--rebase','--autostash'],60);pushed=False
    if not result.returncode:
        pushed=run(['git','push','origin','HEAD:main'],60).returncode==0
        if not pushed:pushed=run(['git','push','origin','HEAD:main'],60).returncode==0
    rebased=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 29 fresh composition measurements$'],30).stdout.strip()
    if rebased:sha=rebased
    state('COMMIT '+sha+(' pushed'if pushed else' not pushed'))
    return [sha+(' (pushed)'if pushed else' (not pushed)')]

def main():
    os.chdir(REPO)
    import importlib.util
    spec=importlib.util.spec_from_file_location('finish_local29',HERE/'finish-local.py')
    while time.time()<HARD:time.sleep(min(45,HARD-time.time()))
    F=importlib.util.module_from_spec(spec);sys.modules['finish_local29']=F;spec.loader.exec_module(F)
    state('START finalizer; numerical and archive deadline11:45Z; take final11:55Z; report after11:55Z.')
    m={};t={};blocked=[];commits=[]
    try:m,t=finish()
    except Exception as ex:
        traceback.print_exc();blocked.append('collection: '+str(ex));state('FINALIZER BLOCK '+str(ex))
    if not blocked:
        try:commits=document(m,t)
        except Exception as ex:traceback.print_exc();blocked.append('documentation: '+str(ex))
    while time.time()<REPORT-125:time.sleep(min(45,REPORT-125-time.time()))
    try:t=F.final_take()
    except Exception as ex:traceback.print_exc();blocked.append('final take: '+str(ex))
    while time.time()<REPORT:time.sleep(min(45,REPORT-time.time()))
    audit=json.loads((WORK/'base-audit.json').read_text())
    closest=', '.join(str(x['n'])+' ('+format(x['side_margin'],'+.6g')+' side)'for x in m.get('closest_full',[])[:3])
    pending=sum(x.get('pending_builds',0)+x.get('deferred_builds',0)for x in m.get('queues',{}).values())
    report=dict(lane='stair-c',improved_n=t.get('improved_n',0),gain=dict(against_base_bar=t.get('against_base_bar',0.),beyond_other_live_r29=t.get('beyond_other_live_r29',0.)),take_dir=str(TAKE),summary=f"Retained {t.get('improved_n',0)} counts below bar29 and the other live takes.",what_was_measured=[f"Initial source pass retained {audit['kept']} states, deferred or refused {len(audit['dropped'])}, and repriced {audit['pending']} unrun recipes.",f"{m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP exports across {m.get('n_values',0)} counts.",'Fresh composition inputs and rectangle cuts ran before saved recipes. Unchanged exact-f hop campaigns stayed closed.','Input bytes and source records were pinned at queue time. Own-layout share gates stayed disabled. Direct public starts kept licence and share checks.','Fresh-import, count-cap, new-corner, live-bar and saved-recipe controls passed after the control fixtures accounted for queue sorting.','The n975 certificate passed; its duplicate-square copy failed. Each retained result requires real remote fq from the certified file and clearance 2.2e-11.',f"Whole-layout receipts: {len(m.get('whole_follows',[]))}; completed certified-file fq: {m.get('whole_completed',0)}.",'Border finesafe.py provided bisected dilation for certification.','All three archives were hash-verified before cleanup.'if(WORK/'cleanup-final.json').exists()else'Cleanup needs inspection.'],next=['Follow fresh changed corner/far-zone pairings first. The round 28 n805 composition gained 0.000141661 before a peer improved it.','Change the pairing before retrying the closest measured builds: '+(closest or'no admitted above-bar build recorded')+'.',f'Reprice the {pending} archived pending builds against the next bar. Completed recipes remain closed.','Repair unresolved source records before reuse. Frozen n804/n995/n997 follows were held in round 28 for missing parents.','Change topology or count class before exact-f hops. Round 27 losses reached 3.5130 and 3.5109 without a full certificate.'],commits=commits,processes_left=[]if(WORK/'cleanup-final.json').exists()else['inspect work/deadline.log'],blocked=blocked,repo='private repo',branch='main',worktree=str(REPO),pr=None)
    report['what_was_measured'] += ['Four expanded-corner n975 controls kept side 31.714095652247682, worst gap about -2.6e-12. A partial-stack mutant failed.',f"Expanded corners from admitted n805/n812/n871/n997 inputs produced {len(m.get('expanded_corner_full',[]))} full layouts.",'The bar-probe control first failed a false prediction, then built n975 to side 31.714095650717713 with positive gap.',f"Production bar probes produced {len(m.get('bar_probe_full',[]))} full layouts; {m.get('bar_probe_failed',0)} probes still had no legal start.",'Four failed probes cap one count/corner. The first fresh corner remains eligible. A cap4000 mutant failed the control.']
    report['what_was_measured'] += ['Withdrawal controls bound exclusions to old pinned bytes, admitted replacement bytes and ignored retention notes.','Five corner paths preserved all four n975 source layouts. Two real n882 failed recipes still had no fit, so the change did not reopen the broad queue.',f"Direct native recipes used physical module geometry without unused rank tables. The n975 control passed at side 31.714095650716718 with positive gap. Production exported {len(m.get('native_direct_full',[]))} full layouts.",'The n945 .995 table-knot replay exposed a corner that escaped its declared cut. The assembled gap was -1.0948843355167908. That exact corner closed for cross-count builds after 23 failed bar probes. Native n997 and other corners stayed open.','Deferred recipes remained in state.pkl. The restored-queue control kept pending and deferred recipes uncompleted.',f"The cut guard preserved four n975 assemblies and rejected the observed escaped state. Three new guarded n997 corner IDs exported {len(m.get('guarded_corner_full',[]))} full layouts.",'A 900-second n986 kick shortened its input by 6.81061522e-6 of side, then reached the existing bar. A proposed source-locator repair failed the real n986 proof control and was reverted.']
    report['what_was_measured'] += ['The guarded n945 .995 replay removed the table fit and refused the physical corner in 25.103 seconds. Direct native n812 recipes finished about 4.96e-6 above the bar; n871 about 2.39e-6 above. Native n997 stayed within 1.55e-9 below the bar before certification, short of the required score gain.']
    report['what_was_measured'] += [f"The physical n945 replay traced its -1.0948843355167908 gap to corner square 65 and later run1 square 180. Adding three following stacks made the local solver refuse both-arm caps in 16.357 seconds. Four n975 source assemblies passed unchanged side 31.714095652247682; the duplicate-ghost mutant failed. New n871/n997 corner IDs exported {len(m.get('following_stacks_full',[]))} full layouts."]
    recovered=m.get('byte_recovery',{})
    report['what_was_measured'] += [f"Byte recovery restored {recovered.get('restored',0)} initially deferred states from {recovered.get('approved_versions',0)} exact frozen input versions at {recovered.get('paths',0)} paths. Each approved version passed the full source proof. A wrong expected hash failed. One reused path required two versions, selected by its recorded hash. Source gates and frozen files stayed unchanged. Recovered modules appeared in {len(m.get('recovered_module_full',[]))} full builds.",'Each changed physical-model corner received one early build per box. The priority control passed, and disabling priority made it fail. Subsequent builds returned to live-bar order and existing caps.']
    saved=m.get('saved_recovery',{})
    report['what_was_measured'] += [f"The saved-queue pass staged {saved.get('unrun',0)} exact unrun recipes, including {saved.get('source_held_jobs',0)} with recovered states. It derives unrun status before source admission and includes deferred jobs. Actual full/SLP records stay completed. Controls defer missing modules, admit recovered geometry once and reject measured repeats.",f"Three two-stack n975 controls preserved side 31.714095652247682. The incomplete-stack mutant failed. Two-stack transfers produced {len(m.get('two_stack_transfer_full',[]))} full layouts."]
    report['what_was_measured'] += [f"A late audit repaired follow offers that failed before cert-in existed and were never retried. Controls reproduce that failure, create parents, resume identical certified inputs and refuse changed hashes/coordinates. Failed offers now retry, and an untraced closest row does not hide an admitted fallback. The n812 re-offer passed its full proof and certificate at side 28.92308837221382, margin +4.90841879e-6, and queued its 900-second kick. The repair admitted {len(m.get('follow_repair',{}).get('new_offers',[]))} new offers."]
    report['what_was_measured'] += ['Table search ended11:25Z. Queued kicks could run until11:38Z with150s reserved for certified-file fq. Collection began11:42Z, before the11:45Z archive limit. Workers stop before their payloads are archived. Deadline controls tested the900s cap, phase cap, final-quench reserve and expired phase.']
    if m.get('bar_input_control',{}).get('passed'):
        v=m['bar_input_control'];report['what_was_measured'] += [f"The bar-input variant capped only fq's requested input box. The n975 control requested {v['requested_side']:.15f} instead of {v['uncapped_side']:.15f}. Its actual returned geometry had side {v['actual_side']:.15f} and gap {v['gap']:.6g}. Binary returns and geometry measurements stayed unchanged. The duplicate-square mutant failed. A source-admitted n812 leg used the remaining window through11:38Z."if m.get('bar_input_leg')else'The bar-input control passed. No bar-input production leg was staged.']
    report['next'] = ['Follow fresh changed corner/far-zone pairings first. The round 28 n805 composition gained 0.000141661 before a peer improved it.','Continue cut-constrained corners with changed geometry. The n945 table-knot replay measured gap -1.0948843355167908 from an escaped corner. The new guard rejects it while preserving four n975 controls.','Change the pairing before retrying the closest measured builds: '+(closest or'no admitted above-bar build recorded')+'. Direct native recipes now avoid table work when the recipe is already known.',f'Reprice the {pending} archived pending and deferred builds against the next bar. Preserve their unrun status. Completed recipes remain closed.','Keep full source proofs bound to immutable snapshots. A proposed cycle-locator repair failed the real n986 control and was reverted.','Change topology or count class before exact-f hops. Round 27 losses reached 3.5130 and 3.5109 without a full certificate.']
    report['next'][0]+=' The recovered 90-state library and 194 saved recipes that name those states are available.'
    report['next'].insert(2,'Start the repaired own-near queue earlier. Four missed inputs were admitted after11:08Z. The input-side n812 kick shortened only5.69085e-9 of side. The bar-input variant passed a real975 input-box control, but its production leg had only the final window through11:38Z.')
    report['next'][1]='Use the physical model with following stacks for changed corners. The n945 false fit overlapped a later run1 stack by 1.0948843355167908. Adding three following stacks rejects it and preserves four n975 source assemblies.'
    tmp=WORK/'report-final.tmp';tmp.write_text(json.dumps(report,indent=2)+'\n');os.replace(tmp,TAKE/'report.json')
    state('REPORT report.json written after11:55Z; take frozen.');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
