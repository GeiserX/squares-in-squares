"""Extend the verified held catalog with the round38 brief's exact held file (round37 a)."""
import hashlib
import json
import sys
from functools import lru_cache
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import S,W,write_json
from forensics_public30 import is_held_node as previous_held_node
HELD=S/'gather/round37-2026-11-18a.csv'
MANIFEST=W/'held37-boundary.json'
# Earlier held files, each pinned by the manifest its own round wrote.
PRIORS=[(S/'gather/round31-2026-11-16b.csv',S/'take-harvest-r32/work/held31-boundary.json'),
        (S/'gather/round32-2026-11-16a.csv',S/'take-harvest-r33/work/held32-boundary.json'),
        (S/'gather/round33-2026-11-17a.csv',S/'take-harvest-r34/work/held33-boundary.json'),
        (S/'gather/round34-2026-11-17a.csv',S/'take-quench-r35/work/harvest/work/held34-boundary.json'),
        (S/'gather/round35-2026-11-17a.csv',S/'take-quench-r36/work/harvest/work/held35-boundary.json'),
        (S/'gather/round36-2026-11-18b.csv',S/'take-quench-r37/work/harvest/work/held36-boundary.json')]


def manifest():
    if not MANIFEST.exists():
        raw=HELD.read_bytes()
        write_json(MANIFEST,dict(path=str(HELD),sha256=hashlib.sha256(raw).hexdigest(),authority=str(S/'round38-briefs/quench.txt')))
    return json.loads(MANIFEST.read_text())


@lru_cache(maxsize=4)
def current_sha(path,size,stamp):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pinned(path,record):
    st=path.stat()
    return record['path']==str(path) and current_sha(str(path),st.st_size,st.st_mtime_ns)==record['sha256']


def is_held_node(value):
    if previous_held_node(value):return True
    if not isinstance(value,dict) or not isinstance(value.get('n'),int):return False
    for held,record in PRIORS:
        if value.get('path')==str(held):return pinned(held,json.loads(record.read_text()))
    if value.get('path')!=str(HELD):return False
    return pinned(HELD,manifest())


def control():
    assert is_held_node(dict(path=str(HELD),n=588))
    for held,_ in PRIORS:assert is_held_node(dict(path=str(held),n=588))
    assert not is_held_node(dict(path=str(W/'unregistered-held.csv'),n=588))
    assert not is_held_node(dict(path=str(HELD),n='588'))
    print('CONTROL exact held37a and prior held36b/35a/34a/33a/32a/31b nodes accepted; unregistered path and untyped row refused; sha256='+manifest()['sha256'],flush=True)

if __name__=='__main__':control()
