"""Commit the measured final table and close the doc after the report deadline."""
import datetime as dt
import json
import re
from pathlib import Path
import subprocess
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,T,W,L,state,write_json


def run(args,timeout=60):
    return subprocess.run(args,cwd=L.parents[1],check=True,capture_output=True,text=True,timeout=timeout)


def section(report,metrics):
    gain=report['gain'];ns=report['improved_n']
    return ('\n### Round29 close\n\n'
        +f'The final take retains {ns} rows. Its gain against the round bar is {gain["vs_base_bar"]:.16g}.\n'
        +f'The gain beyond the other live takes is {gain["beyond_other_live_r29_takes"]:.16g}.\n'
        +f'The queue recorded {metrics["completed"]} outcomes and {metrics["admissions"]} provisional admission events.\n'
        +f'It recorded {metrics["errors"]} errors or pre-search refusals.\n'
        +'Every retained row passed the final source, receipt, byte and live-bar checks.\n'
        +'Search stopped by 11:45 UTC. The final report followed 11:55 UTC.\n')


def close():
    end=dt.datetime(2026,11,15,11,55,tzinfo=dt.timezone.utc).timestamp()
    if time.time()<=end:raise RuntimeError('close must follow the take deadline')
    report=json.loads((T/'report.json').read_text())
    metrics=json.loads((W/'final-metrics.json').read_text())
    doc=L/'avenues/harvest.md';table=L/'results/harvest-r29-2026-11-15.tsv'
    text=doc.read_text().split('\n### Round29 close\n',1)[0]
    doc.write_text(text+section(report,metrics))
    table.write_bytes((T/'take.tsv').read_bytes())
    report['what_was_measured']=[x for x in report['what_was_measured'] if not x.startswith('Final queue: ')]
    report['what_was_measured'].append(f'Final queue: {metrics["completed"]} outcomes, {metrics["errors"]} errors or pre-search refusals, {metrics["admissions"]} provisional admissions. Final retained rows: {report["improved_n"]}.')
    try:
        run(['/opt/homebrew/bin/python3','$STYLE_CHECK/check.py','--level','default',str(doc)])
        paths=[str(doc.relative_to(L.parents[1])),str(table.relative_to(L.parents[1]))]
        changed=run(['git','diff','--name-only','HEAD','--']+paths).stdout.strip()
        if changed:
            run(['git','add','--']+paths)
            committed=run(['git','commit','--only','-m','squares: record final round29 harvest measurements','--']+paths)
            match=re.search(r'^\[[^ ]+ ([0-9a-f]+)\]',committed.stdout,re.M)
            if not match:raise RuntimeError('cannot identify close commit from git output')
            sha=run(['git','rev-parse',match[1]]).stdout.strip()
            actual=run(['git','diff-tree','--no-commit-id','--name-only','-r',sha]).stdout.splitlines()
            if not set(actual)<=set(paths):raise RuntimeError('unexpected paths in close commit: '+repr(actual))
            state('CLOSE commit stat '+run(['git','show','--stat','--oneline',sha]).stdout.strip().replace('\n',' | '))
            report['commits'].append(sha)
            run(['git','pull','--rebase','--autostash'])
            # A rebase can change our commit hash; this lane owns both paths.
            final_sha=run(['git','log','-1','--format=%H','--']+paths).stdout.strip()
            report['commits'][-1]=final_sha
            try:run(['git','push','origin','HEAD:main'])
            except subprocess.SubprocessError:run(['git','push','origin','HEAD:main'])
            state('CLOSE final doc/table committed and pushed '+final_sha)
        else:state('CLOSE doc/table already committed')
    except Exception as exc:
        report['blocked']=str(report.get('blocked','none'))+'; final doc/table not pushed: '+repr(exc)
        state('CLOSE ERROR '+repr(exc))
    write_json(T/'report.json',report)
    return report


if __name__=='__main__':print(json.dumps(close(),indent=2))
