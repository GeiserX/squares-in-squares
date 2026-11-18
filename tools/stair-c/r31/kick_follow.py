"""Give close whole-layout starts one kick leg, then follow changed better inputs."""
import csv,datetime,hashlib,json,math,os,shutil,subprocess,time
from pathlib import Path
S=Path('$SCRATCH/bounties-squares');W=S/'take-stair-c-r31/work';H=Path(__file__).resolve().parent
END=datetime.datetime(2026,11,15,23,50,tzinfo=datetime.timezone.utc).timestamp();STATE=W/'kick-follow-state.json'
csv.field_size_limit(1<<26)
def stamp():return datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')
def run():
    seen=json.loads(STATE.read_text())if STATE.exists()else{}
    bar={int(r['n']):float(r['bar'])for r in csv.DictReader(open(S/'round31-briefs/bar31.tsv'),delimiter='\t')}
    for p in S.glob('take-*-r31/take.tsv'):
        for r in csv.DictReader(open(p),delimiter='\t'):
            try:n=int(r['n']);bar[n]=min(bar[n],float(r['new']))
            except (ValueError,KeyError):pass
    handoff=(S/'handoff-r31.log').read_text();claims='\n'.join(line for line in handoff.splitlines()if 'claims' in line)
    for meta in sorted((W/'cert-in').glob('*.json')):
        j=json.loads(meta.read_text())
        if not j.get('whole_layout_follow') or j.get('whole_kick') or j.get('control_only')or j.get('after_kick'):continue
        n=j['n'];path=meta.with_suffix('.csv');payload=path.read_bytes();digest=hashlib.sha256(payload).hexdigest()
        paired=W/'paired-results.json'
        if n%3==0 and (not paired.exists()or len(json.loads(paired.read_text()))<4):continue
        key=str(n)+':'+digest
        if key in seen:continue
        source_hash=j.get('source_sha256','')
        if source_hash and source_hash[:12] in claims:
            seen[key]=dict(status='backlog claimed source');continue
        side=j['built']
        if side>(1+bar[n])*math.sqrt(n)+.0002:
            seen[key]=dict(status='outside .0002 side kick screen',side=side);continue
        prior=[v['side']for v in seen.values()if v.get('n')==n and v.get('status')=='queued']
        dest=W/'cert-in'/(path.stem+'-kick900.csv');dest.write_bytes(payload)
        j.update(whole_kick=True,kick_parent=str(path),kick_parent_sha256=digest)
        # The matched n812 pair changed only fq's starting box. --ref is a
        # diagnostic counter in midm_scan, not a search or acceptance parameter.
        host=['boxC','boxD','boxE'][n%3]
        control=W/'bar-controls'/(host+'.json')
        if not control.exists():continue
        assert json.loads(control.read_text())['passed']
        j.update(kick_target_side=(1+bar[n])*math.sqrt(n),bar_input_follow=True)
        dest.with_suffix('.json').write_text(json.dumps(j))
        result=subprocess.run(['rsync','-a',str(dest),str(dest.with_suffix('.json')),host+':scratch/squares-stair-c/cert-in/'],capture_output=True,timeout=40)
        if result.returncode:continue
        seen[key]=dict(status='queued',n=n,side=side,input_sha256=digest,host=host,source=str(path))
        with (W.parent/'STATE.txt').open('a')as f:f.write(stamp()+' boxA KICK whole n='+str(n)+' one900s sixty-try sigma0.02 kick/lkick leg on '+host+'; source '+str(path)+' sha256 '+digest+'; final fq from certified kick result, hard deadline00:15Z on November16.\n')
        print(stamp(),'KICK QUEUED',n,host,path.name,flush=True)
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(seen,indent=2));tmp.replace(STATE)
while time.time()<END:
    try:run()
    except Exception:
        import traceback;traceback.print_exc()
    time.sleep(45)
print(stamp(),'STOP kick feed',flush=True)
