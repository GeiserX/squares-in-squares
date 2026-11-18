"""Two-slot harvest driver: bounded fetching and source-checked fresh geometry."""
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import follow
from fetch import fetch
from quick import plan
from policy import control
from pins import control as pins_control
from walk import control as walk_control

CSV_NAMES={'submission.csv','submission_merged.csv','submission_ours.csv','effective_pandas_roundtrip.csv','improvements.csv','best_current.csv','c0.csv','best.csv'}

def packing_csv(path):
    if path.suffix.lower()!='.csv':return False
    try:
        with path.open(encoding='utf-8-sig',newline='') as stream:fields=next(csv.reader(stream),[])
        return {'n','x','y','angle'}.issubset(fields)
    except (OSError,UnicodeError,csv.Error):return False


def select(data,selected):
    count=0
    for src in data.glob('*/*/*.csv'):
        if not packing_csv(src):continue
        dst=selected/src.relative_to(data);dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():os.link(src,dst)
        (dst.parent/'meta.json').write_bytes((src.parent/'meta.json').read_bytes());count+=1
    return count


def credits(data,reprice=False):
    old=S/'take-quench-r37/work/harvest/work'
    roots=sorted((p for p in W.glob('public*/data') if p.resolve()!=data.resolve()),reverse=True)
    roots+=sorted(old.glob('public*/data'),reverse=True)+sorted((S/'take-harvest-r34/work').glob('public*/data'),reverse=True)
    roots += [S/'take-harvest-r26/work'/p for p in ['public3/data','public2/data','public/data']]
    for root in roots:
        for src in root.glob('*/*/meta.json'):
            dst=data/src.relative_to(root)
            if not dst.exists():
                dst.parent.mkdir(parents=True,exist_ok=True)
                meta=json.loads(src.read_text());meta['carried']=str(root)
                dst.write_text(json.dumps(meta)+'\n')
                # Reprice prior round34 data when a newly fetched source clears
                # its upstream chain. Preserve the exact output version.
                if not reprice or not root.is_relative_to(W):continue
                folder=src.parent;visited=set()
                while not any((folder/name).is_file() for name in CSV_NAMES):
                    if str(folder) in visited or not (folder/'meta.json').exists():break
                    visited.add(str(folder));carried=json.loads((folder/'meta.json').read_text()).get('carried')
                    if not carried:break
                    folder=Path(carried)/src.parent.parent.name/src.parent.name
                if not folder.is_relative_to(W):continue
                for name in CSV_NAMES:
                    source=folder/name;target=dst.parent/name
                    if source.is_file() and not target.exists():os.link(source,target)


def inventory():
    """Read live ledgers and near-file inventories without claiming solver work."""
    items=[]
    for directory in sorted(S.glob('take-*-r38')):
        ledger=directory/'take.tsv'
        try:
            raw=ledger.read_bytes() if ledger.exists() else b''
            rows=table(ledger)
            near=[dict(path=str(p),size=p.stat().st_size,mtime=p.stat().st_mtime)
                  for p in sorted((directory/'near').glob('*.csv')) if p.is_file()]
            items.append(dict(directory=str(directory),ledger_sha256=hashlib.sha256(raw).hexdigest(),rows=rows,near=near))
        except (OSError,ValueError,csv.Error) as exc:
            items.append(dict(directory=str(directory),deferred=type(exc).__name__))
    write_json(W/'live-inventory.json',dict(utc=time.time(),lanes=items))
    state(f'LIVE inventory lanes={len(items)} rows={sum(len(v.get("rows",[])) for v in items)} near={sum(len(v.get("near",[])) for v in items)}; follows stay with assigned lanes')


def main():
    setup()
    if not (W/"controls-passed").exists():control();pins_control();walk_control()
    from held_boundary import control as held_control
    if not (W/"controls-passed").exists():held_control()
    from dispatch import drain
    from restore import restore
    # Prior valid takes are already included in bar34. No historical replay.
    drain(limit=8)
    for prior in sorted(W.glob('public*')):
        if (prior/'selected').is_dir() and not (prior/'decisions.json').exists():
            state(f'RECOVER interrupted public screen {prior}')
            plan(prior)
    cachepath=W/'fetch-cache.json'
    if not cachepath.exists():cachepath.write_bytes((S/'take-quench-r37/work/harvest/work/fetch-cache.json').read_bytes())
    cache=json.loads(cachepath.read_text())
    next_path=W/'next-fetch.txt'
    next_fetch=float(next_path.read_text()) if next_path.exists() else 0;index=1
    last_output_audit=0
    last_inventory=0
    drain(limit=8)
    while (W/f'public{index:02d}').exists():index+=1
    while time.time()<END-300:
        if time.time()-last_inventory>=600:
            inventory();last_inventory=time.time()
        handoff=S/'handoff-r38.log'
        if handoff.exists():(W/'handoff-last-read.txt').write_text(handoff.read_text())
        revision=hashlib.sha256(Path(follow.__file__).read_bytes()+(Path(__file__).parent/'common.py').read_bytes()).hexdigest()
        if getattr(follow,'_loaded_revision',None)!=revision:
            import importlib
            import common
            importlib.reload(common)
            importlib.reload(follow);follow._loaded_revision=revision
        if time.time()>=next_fetch and time.time()<END-900:
            root=W/f'public{index:02d}';root.mkdir(exist_ok=True)
            state(f'START public delta pass={index} log={W}/driver.log deadline23:30Z')
            try:
                import fetch as fetch_module
                import importlib
                import rpc
                importlib.reload(rpc)
                importlib.reload(fetch_module)
                changes=fetch_module.fetch(root/'data',cache)
                if index%3==1:
                    import datasets
                    importlib.reload(datasets)
                    changes+=datasets.fetch(root/'data',cache)
                if index%3==1:
                    import github_delta
                    github_delta.control()
                    try:changes += ['github-delta'] if github_delta.fetch(root) else []
                    except Exception as exc:state('GITHUB optional delta deferred '+type(exc).__name__)
                write_json(cachepath,cache)
                credits(root/'data',reprice=bool(changes))
                count=select(root/'data',root/'selected')
                state(f'FINISH fetch changed={len(changes)} selected={count}')
                if count:plan(root)
                try:
                    import partial
                    partial.scan(root)
                except Exception as exc:state('PARTIAL diagnostic deferred '+type(exc).__name__)
            except Exception as e:state('ERROR public delta '+repr(e))
            index+=1;next_fetch=time.time()+2700  # round 38: every 45 minutes (quench brief 8)
            next_path.write_text(str(next_fetch)+'\n')
        drain(limit=8)
        if time.time()-last_output_audit>=600 and any((W/'jobs').glob('*.json')):
            try:
                import output_audit
                output_audit.ROOT.mkdir(exist_ok=True)
                output_audit.main()
            except Exception as exc:
                state('OUTPUT AUDIT deferred '+type(exc).__name__)
            last_output_audit=time.time()
        used=0  # Live certified follows belong to the assigned follow lanes.
        drain(limit=8)
        state(f'SCAN fresh and restored sources queued={used}; proof deadline13:45Z')
        time.sleep(20)
    state('STOP feed23:40Z; no more public or follow dispatches')

if __name__=='__main__':main()
