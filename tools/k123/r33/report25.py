"""Write the final report only after source, archive and cleanup verification."""
import json,pathlib,csv
from provenance24 import W
T=W.parent;j=json.load(open(W/'metrics25.json'));v=json.load(open(W/'validation25.json'));a=json.load(open(W/'copy-verified25.json'));c=json.load(open(W/'cleanup25.json'));g=json.load(open(W/'git-commit25.json'))
assert len(v)==j['source_rows'] and all(r['floatsafe'] and r['source_clean'] for r in v)
assert not a['checksum_differences'] and c['remote_removed'] and not c['processes_left']
scans=[];recovered={f'licensed2000{i}' for i in range(1,6)}|{'saved00001'}
for p in (W/'taskdone').glob('*.json'):
 r=json.load(open(p))
 if r.get('kind')=='scan' and (r.get('rc')==0 or r.get('tag') in recovered):scans.append(r)
pending=len(list((W/'boxE-final/tasks').glob('*.json')))
summary=f"{j['source_rows']} clean certified source layouts; {len(j['lowest_n'])} remain below the other live takes at {j['measured_at']}. Lower descendants remain in follower lanes. All workers stopped and boxE archive verified."
report=dict(lane='k123',improved_n=len(j['lowest_n']),gain={'against_base_bar':j['gain_against_base'],'beyond_other_live_r25':j['gain_beyond_others']},take_dir=str(T),summary=summary,what_was_measured=[
 f"{j['attempts']} join attempts on {j['counts']} counts; groups {j['attempt_groups']}; {len(j['errors'])} rebuild errors/refusals; {j['timeouts']} time-limited attempts.",
 f"{len(scans)} completed or selector-recovered scans over {sum(r.get('pairs',0) for r in scans)} pairs. {pending} scan tasks remain preserved in the stopped archive.",
 f"Source rows {[r['n'] for r in j['rows']]} passed floatsafe at 2.2e-11 and certified-file boxE quenches. Final verification kept every coordinate unchanged.",
 "The initial 172-derived 534 was withdrawn for an untraceable generic seed source. Its files are quarantined. New 534 uses the rebuilt licensed 735/968 parents. Frozen border 735/790 and provisional k123 489/968 were excluded as donors.",
 "The near 45-degree reader fallback restored 30 chains in both rebuilt parents without changing side. The 444 quench printed 21.564693167754 before and after the change, reference 21.564693168782.",
 "Clean 968 broad replay reached 31.604245473120. The historical rotated seam on different normalized ends ended 31.840227744147. Exact 489 indices rebuilt 492 squares and were refused; its broad scan supplied no 489.",
 "Source controls accepted clean replacements and rejected the old 534, frozen 735 and an unlicensed seed hidden in nested JSON. Cached withdrawal paths matched the log; 1000 checks took 0.0603s.",
 "Metadata admission was the limiting step late in the round: saved/deferred passes reached671s and953s. The final helpers cache packing reads and bound old-queue candidate loops. Fresh receipts and complete input/source snapshots remain preserved.",
 f"Verified archive: {a['files']} files, {a['bytes']} bytes, zero checksum differences. boxE scratch removed after verification; shared base preserved."
],next=[
 "Join changed licensed ends and fresh follower returns first. Rebuilt 735/790 and clean 968 supplied 228, 365 and 534, and fresh 747/921 supplied 982. Midm and soft then lowered source descendants.",
 f"Resume the preserved fresh queue against the next bar with its exact input and source snapshots. This round measured {j['attempt_groups'].get('fresh',0)} fresh attempts; unused starts remain in boxE-final/queue.tsv and tasks/.",
 "Keep admission incremental before expanding saved queues. Late saved/deferred metadata took671s/953s and stalled fresh staging despite cheap numerical scans. Reuse resident packing arrays and reserve collection time.",
 "Revisit 489 only with a changed orientation or seam. Its old indices produced 492 on the clean normalized parents; the unchanged broad pair scan had no 489 start.",
 "Keep generic seed fallbacks and withdrawn source trees closed. The negative controls exposed a false 534 gain before replacement, and every accepted replacement now binds source identity as well as CSV bytes."
],commits=g.get('commits',[g['sha']]),processes_left='none; boxE and boxA lane workers stopped; verified boxE scratch removed; other boxes were not used',blocked='none' if g['pushed'] else 'not pushed: git push failed after retry',repo='$PRIVATE_REPO (private repo)',branch='main',worktree='$PRIVATE_REPO',pr='')
(T/'report.json.tmp').write_text(json.dumps(report,indent=2));(T/'report.json.tmp').replace(T/'report.json');print(json.dumps(report,indent=2))
