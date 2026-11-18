"""Prove restart limits and interrupted-file recovery without launching workers."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import W
import finish
import quick
import dispatch


def control():
    with tempfile.TemporaryDirectory(dir=W) as name:
        tmp=Path(name);(tmp/'driver.pid').write_text('42\n')
        with patch.object(finish,'W',tmp),patch.object(finish,'END',20000),patch.object(finish,'state',lambda msg:None):
            with (patch.object(finish.subprocess,'run',return_value=SimpleNamespace(stdout='/harvest37/driver.py')),
                  patch.object(finish.subprocess,'Popen') as spawn):
                finish.ensure_driver(10000);assert not spawn.called
            with (patch.object(finish.subprocess,'run',return_value=SimpleNamespace(stdout='')),
                  patch.object(finish.subprocess,'Popen',return_value=SimpleNamespace(pid=43)) as spawn):
                finish.ensure_driver(10000);assert spawn.call_count==1
                finish.ensure_driver(10010);assert spawn.call_count==1
                finish.ensure_driver(10070);finish.ensure_driver(10140)
                finish.ensure_driver(10210);assert spawn.call_count==3
                finish.ensure_driver(19900);assert spawn.call_count==3
        from driver import packing_csv
        probe=tmp/'unfamiliar.csv';probe.write_text('n,square_id,x,y,angle\n1,0,0,0,0\n');assert packing_csv(probe)
        probe.write_text('n,source,L\n1,source,1\n');assert not packing_csv(probe)
        probe.write_bytes(b'\xef\xbb\xbfn,square_id,x,y,angle\n1,0,0,0,0\n');assert packing_csv(probe)
        root=tmp/'screen';selected=root/'selected/nb/source';selected.mkdir(parents=True)
        (selected/'meta.json').write_text(json.dumps(dict(ref='example/source',license='Apache 2.0')))
        for item in ['a.csv','b.csv']:(selected/item).write_text('n,x,y,angle\n1,0,0,0\n')
        def first(path):
            if path.name=='b.csv':raise KeyboardInterrupt('forced screen interruption')
            return None,{1:(0.,1.,1)}
        def bar(path):return [dict(n='1',bar='0.0')] if 'bar37.tsv' in str(path) else []
        with patch.object(quick,'table',bar),patch.object(quick,'state',lambda msg:None),patch.object(dispatch,'drain',return_value=0):
            with patch.object(quick,'read',side_effect=first):
                try:quick.plan(root)
                except KeyboardInterrupt:pass
                else:raise AssertionError('forced interruption did not run')
            assert len(json.loads((root/'screen-progress.json').read_text())['completed'])==1
            with patch.object(quick,'read',return_value=(None,{1:(0.,1.,1)})) as read:
                quick.plan(root)
                assert read.call_count==1 and read.call_args.args[0].name=='b.csv'
            assert len(json.loads((root/'screen-progress.json').read_text())['completed'])==2
    print('CONTROL live driver is not duplicated; absent driver restarts with backoff and three-per-hour limit; deadline blocks restart',flush=True)
    print('CONTROL packing columns and UTF8 BOM accepted with unknown filename; credit-only CSV refused',flush=True)
    print('CONTROL forced public-screen interruption retains completed first file; recovery reads only the unfinished second file',flush=True)

if __name__=='__main__':control()
