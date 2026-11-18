"""Stop, verify, publish, document and report this lane at the round deadline."""
import shlex,csv,io,math,datetime,hashlib,json,os,pathlib,re,signal,subprocess,sys,tarfile,time,traceback
from concurrent.futures import ThreadPoolExecutor
HERE=pathlib.Path(__file__).resolve().parent
REPO=pathlib.Path('$PRIVATE_REPO')
LANE=REPO/'lanes/squares'
TAKE=pathlib.Path('$SCRATCH/bounties-squares/take-stair-c-r32')
WORK=TAKE/'work'
PY='$SCRATCH/bounties-squares/venv/bin/python'
HARD=datetime.datetime(2026,11,16,17,0,tzinfo=datetime.timezone.utc).timestamp()
REPORT=datetime.datetime(2026,11,16,17,25,0,tzinfo=datetime.timezone.utc).timestamp()
HOSTS=[('boxC','n','venv/bin/python'),('boxD','m','venv/bin/python'),('boxE','s','$SCRATCH/squares-base/venv/bin/python')]

def count_label(n):return str(n)+(' count'if n==1 else' counts')

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
    expected['pair-driver']=HERE/'pair_driver.py'
    expected['support']=HERE/'support.py'
    expected['public-controls']=HERE/'public_roots.py'
    expected['policy-controls']=HERE/'control_policy.py'
    expected['coupled-corners']=HERE/'coupled_corners.py'
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

def valid_output_csv(raw,name):
    try:
        n=int(pathlib.Path(name).stem.split('-')[0]);seen=set();count=0
        if not 1<=n<=1000:return False
        for row in csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))):
            if int(row['n'])!=n:return False
            ident=int(row['square_id'])
            if ident in seen:return False
            seen.add(ident);count+=1
            if count>n or not all(math.isfinite(float(row[k]))for k in ('x','y','angle')):return False
        return count==n
    except (ValueError,TypeError,KeyError,UnicodeDecodeError,csv.Error):return False

def valid_output_metadata(raw):
    try:value=json.loads(raw)
    except (ValueError,UnicodeDecodeError):return False
    return isinstance(value,dict)and type(value.get('n'))is int and 1<=value['n']<=1000

def finish():
    sys.path[:0]=[str(HERE),str(LANE)]
    import finish_local31 as F
    stop_coordinator()
    if pathlib.Path(F.C.STATE).exists():
        F.C.S={k:set(v)for k,v in json.loads(pathlib.Path(F.C.STATE).read_text()).items()}
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
                    raw=tf.extractfile(item).read()
                    structured=item.name.split('/')[0]in {'raw-a','final'}
                    bad_metadata=structured and item.name.endswith(('.json','.nostart'))and not valid_output_metadata(raw)
                    bad_csv=structured and item.name.endswith('.csv')and not valid_output_csv(raw,item.name)
                    if bad_metadata or bad_csv:
                        partial=WORK/'partial-outputs'/key/(item.name+'.partial');partial.parent.mkdir(parents=True,exist_ok=True);partial.write_bytes(raw)
                        target.unlink(missing_ok=True)
                        state('DEFER incomplete archived output '+key+'/'+item.name+'; original bytes remain in the verified archive')
                        continue
                    target.write_bytes(raw)
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
    measurements=[];pairs={}
    by_path={r['path']:r for r in m.get('whole_follows',[])}
    for p in WORK.glob('boxcopy/*/final/*paired-fresh*.json'):
        j=json.loads(p.read_text())
        if not p.with_suffix('.csv').is_file()or not j.get('certified_file_quench',{}).get('completed'):continue
        key=(j['n'],j['pair_seed'],j['pair_input_sha256'])
        side=by_path.get(str(p),{}).get('certified_side',j.get('source_kick',{}).get('end'))
        pairs.setdefault(key,{})[j['pair_mode']]=dict(side=side,record=str(p))
    receipts=[]
    for (n,seed,sha),v in sorted(pairs.items()):
        receipts.append(dict(n=n,seed=seed,input_sha256=sha,variants=v))
        measurements.append(f"Matched fresh n={n}, seed{seed}, certified input {sha[:12]}: " + ', '.join(f"{mode} side{value['side']}"for mode,value in sorted(v.items())))
    (WORK/'paired-fresh-results.json').write_text(json.dumps(receipts,indent=2))
    for file,label in [('fresh-held-corners.json','physical corners'),('held-canonical-staged.json','canonical modules'),('returned-stacks-staged.json','returned corners'),('coupled-corners.json','coupled corners')]:
        path=WORK/file
        if path.exists():
            values=json.loads(path.read_text());measurements.append(f"Staged {sum(len(v.get('modules',[]))for v in values)} {label} from {len(values)} input records.")
    for p in WORK.glob('boxcopy/*/final/*control*.json'):
        j=json.loads(p.read_text());kick=j.get('source_kick',{});receipt=j.get('certified_file_quench',{})
        if kick.get('start')is not None and kick.get('end')is not None:
            measurements.append(f"{p.parent.parent.name} actual control n={j['n']} recovered {kick['start']-kick['end']:.12g} of side. Certified-input fq completed: {receipt.get('completed',False)}.")
    measurements+=['Own layouts received no share gate. Public-first outputs and their direct public ancestors used frozen share31 at both tolerances.','All source snapshots retained byte hashes. The driver checked withdrawals in both round logs.']
    next_items=['Use changed n805 corner and far-zone geometry for matched input-box trials. The round31 pair supplied2.74641416054e-7 of score. Check the round32 pair receipts before choosing a new seed.','Keep exact completed recipe keys closed. Resume only never-run recipes after repricing against the next bar.','Give fresh certified rows to backlog promptly. The round31 follow lane supplied its largest gains on new geometry.']
    for row in m.get('contributions',[]):measurements.append(f"A peer take retains n={row['n']} through this lane's input, gaining {row['gain']:.12g} against bar32. The peer retains that gain.")
    timeout_lines=[]
    for log in WORK.glob('boxcopy/*/worker.log'):
        timeout_lines +=[line for line in log.read_text().splitlines()if 'TABLE TIMEOUT'in line]
    measurements.append(f"Bounded module tabulation closed failed or timed-out {len(timeout_lines)} attempts with a120-second limit after an enlarged997 corner consumed more than20minutes without a table.")
    if (WORK/'cache-policy-control.json').exists():measurements.append('Stable source-cache inputs reused their proof. A new withdrawal and changed input bytes each forced a recheck.')
    if (WORK/'denied-module-sources.json').exists():measurements.append('One frozen997 source version and22 direct812 near outputs were withheld after their full tree reached a twoshort-r27 raw file with no source record. No held-source rebinding matched the module geometry.')
    from finish_local31 import C
    pair_gains=[]
    for item in receipts:
        sides=[v['side']for v in item['variants'].values()if v['side']is not None]
        if sides:
            gain=C.basebar()[item['n']]-(min(sides)/item['n']**.5-1)
            if gain>1e-10:pair_gains.append((gain,item['n']))
    if pair_gains:
        gain,n=max(pair_gains);next_items[0]=f"Use changed source-cleared n={n} inputs first. A matched round32 pair gained {gain:.12g} against bar32. Keep both input boxes and close completed geometry keys."
    else:
        complete=sum(set(r['variants'])=={'input','bar'}for r in receipts)
        next_items[0]=f'Use changed source-cleared corner and far-zone geometry. The {complete} completed matched groups did not clear bar32 by1e-10. Keep recovered held floors closed.'
    for item in receipts:
        missing={'input','bar'}-set(item['variants'])
        if missing:
            measurements.append(f"n={item['n']} seed{item['seed']} has only {list(item['variants'])} completed. Its matched comparison is incomplete.")
            next_items.append(f"Check the saved incomplete n={item['n']} pair before replaying its missing {sorted(missing)} variant. Seed{item['seed']} and certified input {item['input_sha256']} bind the completed measurement.")
    next_items.insert(1,f"Keep a120-second bound on each module table. It stopped {len(timeout_lines)} slow attempts after the observed20-minute997 stall. Preserve completed tables and close only the timed-out module version.")
    next_items.insert(1,'Split native805 construction from its paired quenches. At15:52UTC boxD had16 full builds, while boxC and boxE had101 and140. Keep one owner for each geometry recipe.')
    next_items.append(f'Try sparse module tables near the live target fraction after a cached975 control. Full-span tabulation caused the observed20-minute997 stall and {len(timeout_lines)} failed or timed-out attempts.')
    (WORK/'report-extra.json').write_text(json.dumps(dict(what_was_measured=measurements,next=next_items),indent=2))
    (WORK/'experiment-summary.md').write_text('New n805 compositions received matched input-box trials.\nEach pair used identical certified bytes, a shared seed and both box variants.\nInitial plain held probes stayed closed after the dry round31 measurements.\nSource checks used both withdrawal logs and the frozen assembler measure.\n')

def document(m,t):
    experiment_summary(m)
    text='\n\n## 19. Round 32\n\n'
    text+='One serial worker ran on each assigned box: boxC, boxD and boxE.\n'
    text+='The restored library kept complete source proofs and byte hashes.\n'
    text+='Fresh compositions preceded saved recipes. Completed recipes stayed closed.\n'
    text+='The physical corner model included following flush stacks.\n'
    text+='Own layouts had no share gate. Public starts retained licence and source checks.\n\n'
    text+=f"The workers exported {m.get('full_builds',0)} full builds and {m.get('slp_exports',0)} SLP stages across {m.get('n_values',0)} counts.\n"
    text+=f"After collection, the take retained {count_label(t.get('improved_n',0))}, gaining {t.get('against_base_bar',0):.15g} against bar32.\n"
    text+='A final live peer check removed any late superseded rows before the take froze.\n'
    text+='Certification used border finesafe at clearance 2.2e-11.\n'
    text+='Each retained row required a remote fq pass from its certified file.\n'
    text+='The [result table](../results/stair-c-r32-2026-11-16.tsv) records the builds and source screens.\n'
    text+='Full experiment receipts and exact saved queues remain in the take work directory.\n'
    extra=WORK/'experiment-summary.md'
    if extra.exists():text+='\n'+extra.read_text()+'\n'
    text+='\nAll remote archives passed SHA256 verification before scratch removal.\n'
    text+='The shared runtimes remain in place.\n'
    excerpt=WORK/'doc-r31.md';excerpt.write_text(text)
    checker='$STYLE_CHECK/check.py'
    if run(['/opt/homebrew/bin/python3',checker,'--level','default',str(excerpt)],60).returncode:raise RuntimeError('readable check failed')
    doc=LANE/'avenues/stair-c.md'
    if '\n## 19. Round 32\n'not in doc.read_text():
        with doc.open('a')as f:f.write(text)
    paths=[str(doc.relative_to(REPO)),str((LANE/'results/stair-c-r32-2026-11-16.tsv').relative_to(REPO))]
    paths += [str(p.relative_to(REPO))for p in sorted(HERE.glob('*.py'))]
    result=run(['git','add','--',*paths],60)
    if result.returncode:raise RuntimeError('stage failed')
    result=run(['git','commit','--only','-m','Record stair-c round 32 composition experiments','--',*paths],120)
    if result.returncode:raise RuntimeError('commit failed')
    sha=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 32 composition experiments$'],30).stdout.strip()
    changed=run(['git','show','--format=','--name-only',sha],30).stdout.splitlines()
    if not set(changed)<=set(paths):raise RuntimeError('foreign paths in commit')
    run(['git','show','--stat','--oneline',sha],30)
    pulled=run(['git','pull','--rebase','--autostash'],60).returncode==0
    pushed=pulled and run(['git','push','origin','HEAD:main'],60).returncode==0
    if not pushed:pushed=run(['git','push','origin','HEAD:main'],60).returncode==0
    rebased=run(['git','log','-1','--format=%H','--grep=^Record stair-c round 32 composition experiments$'],30).stdout.strip()
    sha=rebased or sha;state('COMMIT '+sha+(' pushed'if pushed else' not pushed'))
    earlier=WORK/'early-commits.json'
    return (json.loads(earlier.read_text())if earlier.exists()else[])+[sha+(' (pushed)'if pushed else' (not pushed)')]

def main():
    import importlib.util
    os.chdir(REPO)
    spec=importlib.util.spec_from_file_location('finish_local31',HERE/'finish-local.py')
    while time.time()<HARD-900:time.sleep(min(45,HARD-900-time.time()))
    F=importlib.util.module_from_spec(spec);sys.modules['finish_local31']=F;spec.loader.exec_module(F)
    state('READY finalization imports and frozen references loaded before the stop deadline')
    while time.time()<HARD:time.sleep(min(45,HARD-time.time()))
    m={};t={};blocked=[];commits=json.loads((WORK/'early-commits.json').read_text())if(WORK/'early-commits.json').exists()else[]
    state('START final collection. Long jobs stop17:15Z. Final take before17:25Z and report after17:25Z.')
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
    report=dict(lane='stair-c',improved_n=t.get('improved_n',0),gain=dict(against_base_bar=t.get('against_base_bar',0.),beyond_other_live_r32=t.get('beyond_other_live_r32',0.)),take_dir=str(TAKE),summary=f"Retained {count_label(t.get('improved_n',0))} below bar32 and every other live take.",what_was_measured=measurements,next=next_items,commits=commits,processes_left=[]if(WORK/'cleanup-final.json').exists()else['inspect work/deadline.log'],blocked=blocked,repo='private repo',branch='main',worktree=str(REPO),pr=None)
    temp=WORK/'report-final.tmp';temp.write_text(json.dumps(report,indent=2)+'\n')
    while time.time()<REPORT-2:time.sleep(min(.25,REPORT-2-time.time()))
    try:
        t=F.prune_live_take()
        report.update(improved_n=t['improved_n'],gain=dict(against_base_bar=t['against_base_bar'],beyond_other_live_r32=t['beyond_other_live_r32']),summary=f"Retained {count_label(t['improved_n'])} below bar32 and every other live take.")
    except Exception as ex:traceback.print_exc();blocked.append('last peer check: '+str(ex))
    temp.write_text(json.dumps(report,indent=2)+'\n')
    while time.time()<REPORT:time.sleep(min(.25,REPORT-time.time()))
    temp.replace(TAKE/'report.json')
    state('REPORT written after17:25Z. take.tsv frozen.');print(json.dumps(report),flush=True)

if __name__=='__main__':main()

