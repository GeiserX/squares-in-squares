"""Check exact frozen roots, anchored history and scoped reader records."""
import pathlib,sys,json,hashlib
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import ancestry28 as A,scoped30 as C
from exact_root30 import resolve,unanchored_cycles
p=A.S/'take-forensics-r27/work/501-reopened-own.csv';good=dict(path=str(p),n=501)
assert resolve(good,'',A.metadata)
assert resolve(dict(good,n=500),'',A.metadata)is None
assert resolve(dict(good,sha256='0'*64),'',A.metadata)is None
assert resolve(dict(path=str(W/'starts/recover641.csv'),n=641),'',A.metadata)is None
cycle=[dict(node='a')];nodes={'a':dict(source='a',licence='own',parents=['b']),'b':dict(source='b',licence='own',parents=['a'])}
assert unanchored_cycles(nodes,cycle)
nodes['b']['parents'].append('r');nodes['r']=dict(source='own construction',licence='own',parents=[])
assert not unanchored_cycles(nodes,cycle)
nodes['r']['refused']='forbidden source';assert unanchored_cycles(nodes,cycle)
M=C.reader_records();d=W/'reader-controls';d.mkdir(exist_ok=True)
p=d/'2.csv';p.write_text('n,square_id,x,y,angle\n2,0,0.5,0.5,0\n2,1,1.5,0.5,0\n')
sha=hashlib.sha256(p.read_bytes()).hexdigest();source=['own construction control','our own construction'];credit=hashlib.sha256(json.dumps(source,sort_keys=True).encode()).hexdigest()
state=d/'follow.json';state.write_text(json.dumps(dict(sources={'2-control':source,'9-unrelated':['unresolved source','none']},seen={sha:dict(donor='2-control',path=str(p)),'f'*64:dict(donor='9-unrelated',path='missing-unrelated.csv')})))
node=dict(path=str(state),donor='2-control',snapshot=str(p),sha256=credit)
a=M.resolve(node);value=json.load(open(a['source_record']))
assert value['source']==source[0]and value['sha256']==sha and value['reader_state_sha256']==hashlib.sha256(state.read_bytes()).hexdigest()
assert 'unrelated'not in json.dumps(a)
for bad in [dict(node,sha256='0'*64),dict(node,snapshot=str(state))]:
 try:M.resolve(bad);raise AssertionError('bad reader accepted')
 except ValueError:pass
print('CONTROL exact frozen parent accepted; wrong count/hash/current-round root refused; anchored history retained; unanchored and refused-anchor cycles refused; reader donor bound to full-state pin; wrong credit and packing refused')
