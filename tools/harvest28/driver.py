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


def select(data,selected):
    names={'submission.csv','submission_merged.csv','submission_ours.csv','effective_pandas_roundtrip.csv','improvements.csv','best_current.csv','c0.csv','best.csv'}
    count=0
    for src in data.glob('*/*/*.csv'):
        if src.name not in names:continue
        dst=selected/src.relative_to(data);dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists():os.link(src,dst)
        (dst.parent/'meta.json').write_bytes((src.parent/'meta.json').read_bytes());count+=1
    return count


def credits(data):
    old=S/'take-harvest-r27/work'
    roots=sorted(old.glob('public*/data'),reverse=True)
    roots += [S/'take-harvest-r26/work'/p for p in ['public3/data','public2/data','public/data']]
    for root in roots:
        for src in root.glob('*/*/meta.json'):
            dst=data/src.relative_to(root)
            if not dst.exists():
                dst.parent.mkdir(parents=True,exist_ok=True)
                meta=json.loads(src.read_text());meta['carried']=str(root)
                dst.write_text(json.dumps(meta)+'\n')


def main():
    setup();control();pins_control();walk_control()
    from restore import restore
    restore()
    cachepath=W/'fetch-cache.json'
    if not cachepath.exists():cachepath.write_bytes((S/'take-harvest-r27/work/fetch-cache.json').read_bytes())
    cache=json.loads(cachepath.read_text())
    next_fetch=0;index=1
    while (W/f'public{index:02d}').exists():index+=1
    while time.time()<END-300:
        handoff=S/'handoff-r28.log'
        if handoff.exists():(W/'handoff-last-read.txt').write_text(handoff.read_text())
        revision=hashlib.sha256(Path(follow.__file__).read_bytes()+(Path(__file__).parent/'common.py').read_bytes()).hexdigest()
        if getattr(follow,'_loaded_revision',None)!=revision:
            import importlib
            import common
            importlib.reload(common)
            importlib.reload(follow);follow._loaded_revision=revision
        used=follow.scan(max_items=8)
        state(f'SCAN fresh and restored sources queued={used}; proof deadline05:45Z')
        if time.time()>=next_fetch and time.time()<END-900:
            root=W/f'public{index:02d}';root.mkdir(exist_ok=True)
            state(f'START public delta pass={index} log={W}/driver.log deadline05:30Z')
            try:
                import fetch as fetch_module
                import importlib
                importlib.reload(fetch_module)
                changes=fetch_module.fetch(root/'data',cache)
                if index%3==1:
                    from datasets import fetch as datasets_fetch
                    changes+=datasets_fetch(root/'data',cache)
                write_json(cachepath,cache)
                credits(root/'data')
                count=select(root/'data',root/'selected')
                state(f'FINISH fetch changed={len(changes)} selected={count}')
                if count:plan(root)
            except Exception as e:state('ERROR public delta '+repr(e))
            index+=1;next_fetch=time.time()+1200
        time.sleep(30)
    state('STOP feed05:40Z; no more public or follow dispatches')

if __name__=='__main__':main()
