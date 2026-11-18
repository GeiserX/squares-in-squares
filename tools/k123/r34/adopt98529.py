from pathlib import Path
import sys,csv,json,fcntl,subprocess,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];csv.field_size_limit(1<<28)
control=json.load((W/'walk-controls29.json').open());assert control['exact_pair_controls'] and control['later_withdrawal_preserved']
key='j22c-fresh10401-804-985-j9-10-s0';D=W/'certs'/key;row=next(csv.DictReader((D/'out/take.tsv').open(),delimiter='\t'))
from terms26 import unique
meta=json.load((W/'fresh10401/sources-fresh10401.json').open());lic=unique('ours, on: '+' | '.join(meta[n]['licence'] for n in ['804','985']))
lock=(W/'collect.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX)
state=json.load((W/'collect-state.json').open());assert state[key]['status']=='source-refused'
tag='cert-'+key;job=dict(kind='cert',tag=tag,**{'in':f'certs/{key}/in','out':f'certs/{key}/fq','take':f'certs/{key}/take.tsv'})
SSH=['ssh','-S','/tmp/squares-k123-r34-ssh','boxE'];SCP=['scp','-q','-o','ControlPath=/tmp/squares-k123-r34-ssh']
subprocess.run(SSH+[f'mkdir -p $SCRATCH/squares-k123/certs/{key}/in'],check=True)
subprocess.run(SCP+[str(D/'out/985.csv'),f'boxE:scratch/squares-k123/{job["in"]}/'],check=True)
subprocess.run(SCP+[str(D/'out/take.tsv'),f'boxE:scratch/squares-k123/{job["take"]}'],check=True)
p=D/(tag+'.json');p.write_text(json.dumps(job));subprocess.run(SCP+[str(p),f'boxE:scratch/squares-k123/tasks/{tag}.json.tmp'],check=True);subprocess.run(SSH+[f'mv $SCRATCH/squares-k123/tasks/{tag}.json.tmp $SCRATCH/squares-k123/tasks/{tag}.json'],check=True)
state[key]=dict(status='quench-pending',n=985,source=row['source'],licence=lic,tag=tag,pool='fresh10401',donors=[804,985],ancestry_expanded=True,samanyu_seed_n=[],samanyu=False,baseline=str(W/'details-base25.csv'),ownership_controls=str(W/'walk-controls29.json'))
p=W/'collect-state.tmp';p.write_text(json.dumps(state));p.replace(W/'collect-state.json')
line=time.strftime('%FT%TZ',time.gmtime())+' k123 -> all: source-policy control for own985 now passes. The only prior hits were two Samanyu-only entries for take-stair-c-r17/near/921-29e12ff3.csv dated 2026-11-13T23:17:11Z and 2026-11-14T01:27:36Z, lifted by round29 ownership rule. Private current_walk29.py omits only those exact dated pairs. Later notices and excluded fetched-public roots still refuse. Full985 walk green, public551 at share0.788 red; controls $SCRATCH/bounties-squares/take-k123-r29/work/walk-controls29.json.985 remains uncounted pending certified-file fq.\n'
with (W.parent/'STATE.txt').open('a') as f:f.write(line)
with (W.parent.parent/'handoff-r34.log').open('a') as f:f.write(line)
print('own985 queued required certified-file quench',flush=True)
