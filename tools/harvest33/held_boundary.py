"""Extend the verified held catalog with the round33 brief's exact held file."""
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,W,write_json
from forensics_public30 import is_held_node as previous_held_node
HELD=S/'gather/round32-2026-11-16a.csv'
MANIFEST=W/'held32-boundary.json'
PRIOR_MANIFEST=S/'take-harvest-r32/work/held31-boundary.json'
PRIOR_HELD=S/'gather/round31-2026-11-16b.csv'


def manifest():
    if not MANIFEST.exists():
        raw=HELD.read_bytes()
        write_json(MANIFEST,dict(path=str(HELD),sha256=hashlib.sha256(raw).hexdigest(),authority=str(S/'round33-briefs/harvest.txt')))
    return json.loads(MANIFEST.read_text())


@lru_cache(maxsize=2)
def current_sha(path,size,stamp):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def is_held_node(value):
    if previous_held_node(value):return True
    if not isinstance(value,dict) or not isinstance(value.get('n'),int):return False
    if value.get('path')==str(PRIOR_HELD):
        record=json.loads(PRIOR_MANIFEST.read_text());st=PRIOR_HELD.stat()
        return record['path']==str(PRIOR_HELD) and current_sha(str(PRIOR_HELD),st.st_size,st.st_mtime_ns)==record['sha256']
    if value.get('path')!=str(HELD):return False
    record=manifest();st=HELD.stat()
    return record['path']==str(HELD) and current_sha(str(HELD),st.st_size,st.st_mtime_ns)==record['sha256']


def control():
    assert is_held_node(dict(path=str(HELD),n=588))
    assert is_held_node(dict(path=str(PRIOR_HELD),n=588))
    assert not is_held_node(dict(path=str(W/'unregistered-held.csv'),n=588))
    assert not is_held_node(dict(path=str(HELD),n='588'))
    print('CONTROL exact held32a and prior held31b nodes accepted; unregistered path and untyped row refused; sha256='+manifest()['sha256'],flush=True)

if __name__=='__main__':control()
