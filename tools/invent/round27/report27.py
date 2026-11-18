"""Write the round report from final comparisons, measurements and cleanup receipts."""
import json,pathlib,time,datetime
W=pathlib.Path(__file__).resolve().parent;T=W.parent
assert time.time()>=datetime.datetime(2026,11,14,23,55,tzinfo=datetime.timezone.utc).timestamp(),'report must follow take deadline'
f=json.load(open(W/'final-comparison.json'));m=json.load(open(W/'measurement.json'))
v=json.load(open(W/'boxE-raw/verification26.json'));x=json.load(open(W/'transfer-check.json'))
c=json.load(open(W/'boxE-raw/cleanup-processes.json'));removed=json.load(open(W/'remote-removal.json'))
assert not v['errors'] and all(v['controls'].values()) and not x['mismatches'] and not c['after']['owned']
assert removed['removed']=='$SCRATCH/squares-invent-r27' and (W/'local-controller-stopped.json').exists()
s=m['summary'];rows=m['rows'];selected=f['selected']
measure=[f'{sum(a["attempts"] for a in s.values())} completed production jobs and {sum(a["tries"] for a in s.values())} kick trials.']
for kind,a in s.items():
 measure.append(f'{kind}: {a["clean_normal"]} locally admitted normal ends, {a["clean_moved"]} side {'reduction' if a['clean_moved']==1 else 'reductions'} above 1e-8, summed side reduction {a["clean_side_gain"]:.12g}.')
measure.append('Movement totals use the initial local source admission. The independent full walk can later exclude those provisional results.')
measure+=json.load(open(W/'report-notes.json')) if (W/'report-notes.json').exists() else []
measure += [f'Uncached boxE checks accepted {len(v["verified"])} final {'file' if len(v['verified'])==1 else 'files'} with native and pandas reads and clearance at least 2.2e-11. Separated squares passed. Overlap and wrong hashes failed.',f'Final comparison at {f["time"]} used the round27 bar and every live r27 take. All {x["files"]} boxE CSV copies matched their hashes before cleanup.']
nexts=json.load(open(W/'next.json'))
report=dict(lane='invent',improved_n=f['improved_n'],gain=f['gain'],take_dir=str(T),summary=f'Retained {len(selected)} {'row' if len(selected)==1 else 'rows'} after source, certified-file quench and final live-peer checks. Owned workers stopped and boxE scratch removed after verified transfer.',what_was_measured=measure,next=nexts,commits=list(dict.fromkeys((W/'commits.txt').read_text().split())),processes_left={'boxA':[],'boxE':[],'boxE_scratch_removed':True,'csv_files_copied':x['files']},blocked='none',repo='private repo',branch='main',worktree='$PRIVATE_REPO',pr='none')
assert set(report)=={'lane','improved_n','gain','take_dir','summary','what_was_measured','next','commits','processes_left','blocked','repo','branch','worktree','pr'}
p=T/'report.json';q=p.with_suffix('.tmp');q.write_text(json.dumps(report,indent=2)+'\n');q.replace(p)
print(json.dumps(report,indent=2))
