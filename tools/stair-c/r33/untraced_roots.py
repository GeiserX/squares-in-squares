"""Exclude source versions whose direct graph reaches a known untraced input."""
import datetime,hashlib,json,pickle,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import public_roots as P
from prepare import fingerprint
W=P.ROOT
BAD='take-twoshort-r27/work/boxE27/runs/modules-997-eeb926e0-s825/raw/997-sl825-2.csv'
def denied(source):
    graph,_=P.direct_graph(dict(source=source))
    return BAD in json.dumps(graph)
def main():
    # A real rejected 813 descendant must fail. A submitted boundary stops its tree.
    fixture=W.parent/'near/813-r33-42b84e688c67-n.csv.json'
    if fixture.exists():
        modules=json.loads(fixture.read_text())['modules']
        assert any(denied(q['source'])for q in modules),'real untraced descendant missed'
    assert not denied('independent staircase construction')
    graph,boundaries=P.direct_graph(dict(path=str(W.parents[1]/'gather/round32-2026-11-16a.csv'),n=997,source=BAD))
    assert boundaries and BAD not in json.dumps(graph)
    (W/'untraced-root-control.json').write_text(json.dumps(dict(passed=True,real813_rejected=fixture.exists(),held_boundary_stops_walk=True)))
    print('CONTROL known untraced813 source refused; independent source allowed; held boundary stops walk',flush=True)
    seen={};end=float((W/'box/search-deadline').read_text())
    while time.time()<end:
        lib=pickle.load(open(W/'box/libbase/library.pkl','rb'));mods=lib['mods'][:]
        for path in (W/'donors').glob('*.pkl'):
            try:mods.extend(pickle.load(open(path,'rb')).get('mods',[]))
            except(OSError,ValueError,EOFError):continue
        records=json.loads((W/'denied-module-sources.json').read_text());keys={(r['fingerprint'],r['source_sha256'])for r in records};changed=0
        for q in mods:
            source=q['src'];sha=hashlib.sha256((source+'\0'+q['licence']).encode()).hexdigest()
            if sha not in seen:
                try:seen[sha]=denied(source)
                except(OSError,ValueError,RecursionError):continue
            if not seen[sha]:continue
            key=(fingerprint(q),sha)
            if key in keys:continue
            records.append(dict(fingerprint=key[0],source_sha256=sha,id=q['id'],reason='direct source graph reaches known missing source record '+BAD));keys.add(key);changed+=1
        if changed:
            p=W/'denied-module-sources.json';temp=p.with_suffix('.tmp');temp.write_text(json.dumps(records,indent=2));temp.replace(p)
            for host in ['boxC','boxD','boxE']:
                subprocess.run(['rsync','-a',str(p),host+':scratch/squares-stair-c/denied-module-sources.json'],capture_output=True,timeout=40,check=True)
            with(W.parent/'STATE.txt').open('a')as f:f.write(datetime.datetime.now(datetime.timezone.utc).strftime('%FT%TZ')+f' boxA DEFER {changed} module source versions whose direct graph reaches known untraced997 raw bytes. Held boundaries stayed closed to the walk. Worker source filters updated; no counted row used these versions.\n')
        (W/'untraced-root-screen.json').write_text(json.dumps(dict(groups=len(seen),denied_groups=sum(seen.values()),denied_versions=len(records)),indent=2))
        print('SOURCE SCREEN',len(seen),'groups',sum(seen.values()),'denied;',changed,'new module versions',flush=True)
        time.sleep(min(300,max(0,end-time.time())))
if __name__=='__main__':main()
