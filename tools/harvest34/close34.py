"""Freeze the assigned lane's records and push its exact paths before the deadline."""
import datetime as dt
import json
import re
import time
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import L,T,W,END,state,table,write_json


def run(args,timeout=35):
    result=subprocess.run(args,cwd=L.parents[1],capture_output=True,text=True,timeout=max(.01,min(timeout,END-time.time()-5)))
    if result.returncode and ('index.lock' in result.stderr or 'index lock' in result.stderr) and time.time()<END-10:
        time.sleep(2)
        result=subprocess.run(args,cwd=L.parents[1],capture_output=True,text=True,timeout=max(.01,min(timeout,END-time.time()-5)))
    return result


def close():
    outcomes=[json.loads(p.read_text()) for p in (W/'outcomes').glob('*.json')]
    decisions=[r for p in W.glob('public*/decisions.json') for r in json.loads(p.read_text())]
    handed=[r for r in outcomes if r.get('outcome')=='certified handoff; offbox fq required' and Path(r.get('path','')).is_file()]
    best={}
    for r in handed:best[r['n']]=min(best.get(r['n'],float('inf')),r['input_score'])
    bars={int(r['n']):float(r['bar']) for r in table(T.parent/'round34-briefs/bar34.tsv')}
    margin=sum(max(0.,bars[n]-v) for n,v in best.items())
    info=json.loads((W/'final-run-info.json').read_text())
    info['summary']=f'Source-cleared certificates for {len(best)} counts total {margin:.12g} below bar34 before offbox follows. Finished peer rows count in their own lanes. Harvest retains {len(table(T / "take.tsv"))} rows.'
    info['measurements'] += [f'Closed {len(decisions)} public reader decisions and {len(outcomes)} dispatch outcomes. Certified handoffs cover {len(best)} distinct counts with a fixed-bar margin of {margin:.17g} before offbox follows. These handoffs are not harvest take gains.']
    info['next']=[
        f'Fetch changed licensed public final CSVs first. Round32 supplied7 source-cleared counts with margin0.000416088218, round33 supplied2 with margin1.12670012e-06, and round34 supplied{len(best)} with margin{margin:.9g}, all before follows.',
        'Keep the GitHub delta on every third pass. In round34 it read the jlevy register and kenaznia n292. Only n305 fell below bar34, by 3.05e-05, and its share against the prvsiyan 1105 row was 0.564 at1e-2, so it stays out. The n292 side 17.590104218681835 sits above bar34.',
        'Keep the frozen assembler share check on every public-first certificate and fq output. Real controls reject851 at0.464159811986 and972 at0.452674897119. Owned layouts keep their exemption.',
        'Expect little from public intake now. Round34 ran about18 passes, and every changed Kaggle file stayed at or above bar34 or failed the share gate. The public pool tracks the board top, and our held file already holds its licensed rows.',
        'Keep the harvest lane to two light local processes. Its fetch and screen pass takes under a minute when nothing changed.'
    ]
    info['processes_left']='none'
    if table(T/'take.tsv'):
        from finalize import prepare_take
        prepare_take()
    else:
        (L/'results/harvest-r34-2026-11-17.tsv').write_bytes((T/'take.tsv').read_bytes())
        write_json(W/'final-source-audit.json',[])
    doc=L/'avenues/harvest.md'
    heading='### Round 34 close\n'
    if heading not in doc.read_text():
        text=f'\n{heading}\nThe screen recorded {len(decisions)} candidate decisions and {len(outcomes)} dispatch outcomes.\nCertified handoffs cover {len(best)} distinct counts before other lanes follow them.\nTheir fixed-bar margin totals {margin:.17g}.\nThe harvest take retains {len(table(T/"take.tsv"))} rows after the required quench and live comparison.\nUnquenched handoffs do not count as harvest gains.\n'
        fragment=W/'doc-r34-close.md';fragment.write_text(text)
        checker=next(c for c in [Path('$STYLE_CHECK/check.py'),Path('$STYLE_CHECK/check.py')] if c.exists())
        checked=run(['/opt/homebrew/bin/python3',str(checker),'--level','default',str(fragment)])
        if checked.returncode:raise ValueError('closing prose did not pass readable checker')
        with doc.open('a') as stream:stream.write(text)
    paths=[str(p.relative_to(L.parents[1])) for p in sorted((L/'tools/harvest34').glob('*.py'))]
    paths += ['lanes/squares/avenues/harvest.md','lanes/squares/results/harvest-r34-2026-11-17.tsv']
    status=run(['git','status','--porcelain','--',*paths])
    if status.returncode:raise ValueError('cannot inspect own git paths')
    if status.stdout.strip():
        staged=run(['git','add','--',*paths])
        if staged.returncode:raise ValueError('cannot stage own git paths')
        committed=run(['git','commit','--only','-m','squares: record round 34 harvest close','--',*paths])
        if committed.returncode:raise ValueError('cannot commit own git paths')
        match=re.search(r'\[\S+ ([0-9a-f]{7,40})\]',committed.stdout)
        if not match:raise ValueError('cannot identify own closing commit')
        sha=run(['git','rev-parse',match[1]]).stdout.strip()
        stat=run(['git','show','--stat','--oneline',sha])
        (W/'closing-commit-stat.txt').write_text(stat.stdout)
        changed=run(['git','show','--format=','--name-only',sha]).stdout.splitlines()
        if any(name not in paths for name in changed):raise ValueError('commit includes an unexpected path')
        info['commits'].append(sha)
        state('COMMIT closing own paths '+sha)
    write_json(W/'final-run-info.json',info)
    for attempt in range(2):
        try:
            pulled=run(['git','pull','--rebase','--autostash'])
            pushed=run(['git','push','origin','HEAD:main']) if not pulled.returncode else pulled
            if not pushed.returncode:
                state('PUSH closing records to origin/main succeeded');break
        except subprocess.TimeoutExpired:
            pass
    else:
        info['blocked']='not pushed: two bounded closing push attempts failed'
        write_json(W/'final-run-info.json',info)
        state('not pushed: closing commit retained on local main')
    write_json(W/'closed.json',dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),decisions=len(decisions),outcomes=len(outcomes),distinct_handoffs=len(best)))

if __name__=='__main__':close()
