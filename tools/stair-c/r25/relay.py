"""Relay new independent tables across the two parity workers."""
import datetime,glob,hashlib,json,os,pickle,subprocess,time
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');T=S/'take-stair-c-r25';W=T/'work'
END=datetime.datetime(2026,11,14,2,15,tzinfo=datetime.timezone.utc).timestamp()
state=W/'relay-state.json';seen=set(json.load(open(state))) if state.exists() else set()
for d in [W/'relayed']:d.mkdir(exist_ok=True)
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
while time.time()<END and not (W/'STOP_RELAY').exists():
    for p in sorted(W.glob('boxcopy/*/tables/*.pkl')):
        if p.name.startswith('r25-live-cross-'):continue
        data=pickle.load(open(p,'rb'));origin=str(data.get('origin',''))
        if not origin.startswith(('independent core-step','new independent staircase')) or not data['mods']:continue
        raw=p.read_bytes();digest=hashlib.sha256(raw).hexdigest()
        if digest in seen:continue
        source=p.parent.parent.name;target='boxE' if source=='n' else 'boxC'
        out=W/'relayed'/('r25-live-cross-'+source+'-'+digest[:16]+'.pkl');out.write_bytes(raw)
        r=subprocess.run(['rsync','-az',str(out),target+':scratch/squares-stair-c/inbox/'],capture_output=True,text=True,timeout=50)
        if r.returncode:print(stamp(),'COPY FAILED',target,r.stderr,flush=True);continue
        lib=W/'relayed'/digest;lib.mkdir(exist_ok=True)
        pickle.dump(dict(mods=data['mods'],layouts=[]),open(lib/'library.pkl','wb'));pickle.dump(data['lens'],open(lib/'lens.pkl','wb'))
        (lib/'need.txt').write_text('\n'.join(q['id'] for q in data['mods'])+'\n')
        with (S/'handoff-r25.log').open('a') as h:h.write(stamp()+' stair-c -> all: independent table states='+str(len(data['mods']))+' relayed to both assigned parity workers; '+str(lib)+'\n')
        with (T/'STATE.txt').open('a') as h:h.write(stamp()+' RELAY '+str(p)+' to '+target+' one serial worker; source '+origin+'; '+str(lib)+'; search02:15Z hard02:45Z\n')
        seen.add(digest);state.write_text(json.dumps(sorted(seen)))
    time.sleep(30)
print(stamp(),'RELAY STOPPED',len(seen),flush=True)
