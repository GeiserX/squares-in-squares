"""Stage exact unrun recipes after frozen source bytes become usable again."""
import datetime,hashlib,json,pickle,subprocess,sys,tarfile
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path[:0]=[str(H),str(H.parents[2])]
from prepare import fingerprint
from saved_all import gather,control
R=Path('$SCRATCH/bounties-squares');W=R/'take-stair-c-r33/work'
control();archives=[]
for key in['n','m','s']:
    with tarfile.open(R/f'take-stair-c-r28/work/archive/{key}/final-copy.tar.gz')as tf:
        read=lambda name:pickle.loads(tf.extractfile(name).read())
        records=[json.loads(tf.extractfile(m).read())for m in tf.getmembers()if m.name.startswith('raw-a/')and m.name.endswith('.json')]
        archives.append((read('libbase/library.pkl'),read('state.pkl'),read('prior-recipes.pkl'),records))
data=gather(archives,fingerprint);raw=pickle.dumps(data);digest=hashlib.sha256(raw).hexdigest();out=W/'saved-jobs.pkl';out.write_bytes(raw)
marker=W/'donors'/('r33-priority-saved-resume-'+digest[:12]+'.pkl');pickle.dump(dict(mods=[],lens={},origin='restore exact unrun after source recovery'),open(marker,'wb'))
for host in['boxC','boxD','boxE']:
    subprocess.run(['rsync','-a',str(out),host+':scratch/squares-stair-c/'],check=True,timeout=40)
    subprocess.run(['rsync','-a',str(marker),host+':scratch/squares-stair-c/inbox/'],check=True,timeout=40)
recovered=set(json.load(open(W/'byte-recovery-all.json'))['modules'])
summary=dict(unrun=len(data['jobs']),completed=len(data['completed']),sha256=digest,source_held_jobs=sum(any(q in recovered for q in j['ids'])for j in data['jobs']))
(W/'saved-all-receipt.json').write_text(json.dumps(summary,indent=2))
with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+' boxA RESTORE SAVED ALL '+str(summary)+'; derive unrun status before filtering for source-held modules; full/SLP outputs stay measured and completed. Source admission and live-bar filters still run in saved.admit. Empty import marker makes workers load this data without restart; log work/restore-saved-all.log, deadline00:15Z on November16.\n')
print(json.dumps(summary),flush=True)
