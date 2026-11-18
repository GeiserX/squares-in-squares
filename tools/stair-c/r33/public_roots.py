"""Check direct public roots at both tolerances and stop at held boundaries."""
import csv,functools,hashlib,importlib.util,json,os,re,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import numpy as np
from scipy.spatial import cKDTree
LANE=Path('.');sys.path.insert(0,str(LANE))
import forensics_public29 as prior
import forensics_public30 as held_reader
ROOT=Path('$SCRATCH/bounties-squares/take-stair-c-r33/work')
REF=re.compile(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.(?:json|txt))')
CREF=re.compile(r'($DATA/[^\s,;<>"\\()|\[\]{}]+\.csv)')
@functools.lru_cache(None)
def held_catalog():
    result=dict(held_reader.held_paths())
    p=ROOT.parents[1]/'gather/round30-2026-11-15c.csv'
    result[str(p)]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    p=ROOT.parents[1]/'gather/round31-2026-11-16b.csv'
    result[str(p)]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    p=ROOT.parents[1]/'gather/round32-2026-11-16a.csv'
    result[str(p)]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    return result
@functools.lru_cache(maxsize=128)
def file_sha(path,size,stamp):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def held(path):
    p=Path(path);entry=held_catalog().get(str(p))
    if not entry or not p.is_file():return False
    st=p.stat();return file_sha(str(p),st.st_size,st.st_mtime_ns)==entry['sha256']
def direct_graph(proof):
    seen=set();boundaries=[]
    def expand(value):
        if isinstance(value,list):return [expand(v)for v in value]
        if isinstance(value,dict):
            path=value.get('path')
            if isinstance(path,str)and isinstance(value.get('n'),int)and held(path):
                boundaries.append(dict(path=path,n=value['n']));return dict(submitted_held_boundary=path,held_n=value['n'])
            if isinstance(path,str)and isinstance(value.get('n'),int)and value.get('source')and 'licence'in value and 'record'not in value:
                value=dict(value,record={k:value[k]for k in ['source','licence','public_first']if k in value})
            return {k:(v if k in {'licence','licence_text','record'}else expand(v))for k,v in value.items()if k not in {'public_root_proof','public_roots'}}
        if not isinstance(value,str):return value
        extras=[]
        for path in REF.findall(value):
            if path in seen:continue
            p=Path(path)
            if not p.is_file():continue
            if len(seen)>=2048:raise ValueError('direct public graph exceeds2048 proof files')
            seen.add(path)
            try:extras.append(expand(json.loads(p.read_text())))
            except (UnicodeDecodeError,json.JSONDecodeError):continue
        return dict(text=value,referenced_direct_proofs=extras)if extras else value
    return expand(proof),boundaries
@functools.lru_cache(None)
def geometry_policy():
    # Load the current harvest lane's policy privately, without changing it or
    # colliding with older producers' modules named policy.
    sp=importlib.util.spec_from_file_location('stair31_harvest_geometry',Path(__file__).resolve().parent/'geometry_policy.py')
    module=importlib.util.module_from_spec(sp);sp.loader.exec_module(module)
    module.references();module.own_seeds();return module
@functools.lru_cache(maxsize=4096)
def compare(n,sha,coords_tuple):
    policy=geometry_policy();a=np.asarray(coords_tuple,float).copy();a[:,:2]-=(a[:,:2].min(0)+a[:,:2].max(0))/2
    best=[0.,0.,0.]
    for label,target in policy.excluded(n):
        measured=policy.share(a,target)
        best=[max(x,y)for x,y in zip(best,measured[:3])]
    return tuple(best)
@functools.lru_cache(maxsize=1000)
def own_comparator(n):
    policy=geometry_policy();refs=[v[n]for _,v in policy.references()if n in v]
    return bool(refs)and all(policy.is_own_reference(n,b)for b in refs)
@functools.lru_cache(maxsize=128)
def held_coordinates(path,n,sha):
    from held_proof import HELD,held_rows,coords
    if path==str(HELD):return coords(held_rows()[n])
    rows=[]
    with open(path)as f:
        for r in csv.DictReader(f):
            if int(r['n'])==n:rows.append(r)
    return coords(rows)
def owned_transport(original,path,n,sha,texts,files):
    for name in [original+'.json',original+'.origin.json',original[:-4]+'.json']:
        try:data=json.loads(texts[name])if name in texts else json.loads(Path(files.get(name,name)).read_text())
        except(OSError,ValueError,TypeError):continue
        if not isinstance(data,dict):continue
        parent=data.get('path');count=data.get('n',n)
        if not isinstance(parent,str):continue
        parent=str(Path('$SCRATCH/bounties-squares')/parent)if not parent.startswith('/')else parent
        if not isinstance(count,(int,str))or not str(count).isdigit():continue
        if not held(parent)or int(count)!=n:continue
        wanted=data.get('row_sha256',data.get('snapshot_sha256'))
        if wanted!=sha:continue
        expected=held_catalog()[parent]['sha256']
        if data.get('row_sha256')and data.get('sha256')!=expected:continue
        try:
            from held_proof import coords
            actual=coords(list(csv.DictReader(open(path))))
            if actual==held_coordinates(parent,n,expected):return True
        except(OSError,ValueError,KeyError):continue
    return False
class Public:
    def __init__(self):
        prior.reader()
        spec=importlib.util.spec_from_file_location('stair31_public_classifier',LANE/'tools/harvest29/public_sources.py')
        base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
        original_record=base.source_record_public;original_node=base.public_node
        def record(data,n):
            if isinstance(data,dict)and isinstance(data.get('n'),int)and data.get('path')and held(data['path']):return False
            return original_record(data,n)
        def node(original,n,texts,files,seen=None):
            path=Path(files.get(original,original))
            if path.is_file():
                sha=hashlib.sha256(path.read_bytes()).hexdigest()
                if owned_transport(original,str(path),n,sha,texts,files):return False
                for name in [original+'.json',original+'.origin.json',original[:-4]+'.json']:
                    try:data=json.loads(texts[name])if name in texts else json.loads(Path(files.get(name,name)).read_text())
                    except(OSError,ValueError,TypeError):continue
                    if not isinstance(data,dict)or not data.get('path')or not held(data['path']):continue
                    want=data.get('row_sha256',data.get('snapshot_sha256'))
                    if want and want!=sha:raise ValueError('changed held transport row hash: '+original)
            return original_node(original,n,texts,files,seen)
        base.source_record_public=record;base.public_node=node;self.base=base
    def __getattr__(self,key):return getattr(self.base,key)
    def audit_nodes(self,nodes,texts,files):
        out=[]
        for original,path,sha in nodes:
            if not original.endswith('.csv'):continue
            data=self.base.packing(path)
            if data is None:continue
            n,a=data
            full=geometry_policy().A.read(path,[n]).get(n)
            if full is not None:a=np.array([[float(r[k]) for k in ('x','y','angle')]for r in full])
            if owned_transport(original,path,n,sha,texts,files):continue
            if not self.base.public_node(original,n,texts,files):continue
            # Every harvested1105 version at228 equals our seed under the brief.
            owned=own_comparator(n)
            measured=(0.,0.,0.)if owned else compare(n,sha,tuple(map(tuple,a)))
            declared=None
            for name in [original+'.json',original+'.source.json',original[:-4]+'.json',original+'.origin.json']:
                try:data=json.loads(texts[name])if name in texts else json.loads(Path(files.get(name,name)).read_text())
                except(OSError,ValueError,TypeError):continue
                if isinstance(data,dict)and('licence'in data or'licence_text'in data):
                    declared=str(data.get('licence',data.get('licence_text','')));break
            label=re.search(r'\b(?:Apache(?:(?: License)?[- ]?[0-9]+(?:\.[0-9]+)?)?|CC0|CC BY 4\.0|Attribution 4\.0|Other|CC BY-SA|MIT|BSD|GPL|proprietary|unknown|custom terms|unlicensed|no licen[cs]e)\b',declared or'',re.I)
            licensed=bool(label and(re.fullmatch(r'Apache(?: License)?[- ]?2\.0',label[0],re.I)or re.match(r'CC0|CC BY 4\.0|Attribution 4\.0',label[0],re.I)))
            out.append(dict(original=original,snapshot=str(path),sha256=sha,n=n,share1e6=measured[0],share1e3=measured[1],share1e2=measured[2],owned_comparison=owned,declared_licence=declared,declared_licence_allowed=licensed,allowed=licensed and max(measured[1:])<.4))
        return out
@functools.lru_cache(None)
def reader():return Public()
def warm():geometry_policy();return reader()
# A private imported copy retains the producer's parsing without changing its globals.
sp=importlib.util.spec_from_file_location('stair31_public_parser',LANE/'forensics_public29.py');parser=importlib.util.module_from_spec(sp);sp.loader.exec_module(parser);parser.reader=reader

def audit(proof,folder=ROOT):
    folder=Path(folder);folder.mkdir(exist_ok=True)
    graph,boundaries=direct_graph(proof)
    # These exact public transport files were never held. A held sibling does not exempt them.
    raw=json.dumps(graph)
    for p in set(CREF.findall(raw)):
        q=Path(p)
        import withdrawals
        if q.is_file()and not withdrawals.allowed_bytes(q,ROOT.parents[1]):raise ValueError('withdrawn direct ancestor bytes: '+p)
        prohibited=(p.endswith('/take-harvest-r26/695.csv')and not q.is_file())or(p.endswith('/take-harvest-r26/814.csv')and((q.is_file()and hashlib.sha256(q.read_bytes()).hexdigest().startswith('5a4c0cdb'))or(not q.is_file()and '5a4c0cdb'in raw)))or(p.endswith('/take-forensics-r22/work/donors/799-986b3b6daebce05b9257.csv')and q.is_file()and hashlib.sha256(q.read_bytes()).hexdigest()=='94740134aabf0aeed3e34e7f743a44ca68b5f9be4d6e3d3b1d49a694fbb2d8fe')
        if prohibited:raise ValueError('direct withdrawn public transport '+p)
    rows=parser.audit(graph,[],folder,[],gather=lambda parts:[])
    bad=[r for r in rows if not r['allowed']]
    if bad:raise ValueError('excluded direct public root: '+json.dumps(bad[:2],sort_keys=True))
    owned=bool(boundaries)or bool(re.search(r'Samanyu-dev/squares_in_squares|seed merged0|own construction|own design|independent staircase|submitted_held_boundary',json.dumps(graph),re.I))
    raw=json.dumps(dict(public_roots=rows,held_boundaries=boundaries,owned_ancestry=owned),sort_keys=True,separators=(',',':')).encode()
    out=folder/'public-root-proofs';out.mkdir(exist_ok=True);digest=hashlib.sha256(raw).hexdigest();p=out/(digest+'.json')
    if not p.exists():
        temp=p.with_name(p.name+'.tmp-'+str(os.getpid()));temp.write_bytes(raw);temp.replace(p)
    return dict(public_roots=rows,held_boundaries=boundaries,owned_ancestry=owned,public_root_proof=str(p),public_root_sha256=digest)
def control():
    import tempfile,share27
    with tempfile.TemporaryDirectory(dir=ROOT)as d:
        folder=Path(d);p=folder/'972.csv';a=share27.prv_rows()[972][-1]
        with p.open('w')as f:
            w=csv.writer(f);w.writerow(['n','x','y']);w.writerows((972,*q)for q in a)
        bad=dict(path=str(p),n=972,record=dict(public_first=True,source='example/public :: submission.csv',licence='CC0'))
        try:audit(bad,folder)
        except ValueError:pass
        else:raise AssertionError('direct public match admitted')
        owned=dict(path=next(iter(held_catalog())),n=4,parent=bad)
        assert audit(owned,folder)['public_roots']==[]
        try:audit(dict(parent=owned,direct=bad),folder)
        except ValueError:pass
        else:raise AssertionError('held sibling suppressed direct root')
        a=a+.004
        s=compare(972,'shift-control',tuple(map(tuple,a)))
        assert s[2]==1
        assert audit(dict(path='/owned/503.csv',n=503,record=dict(source='Samanyu-dev/squares_in_squares',licence='our own')),folder)['public_roots']==[]
    print('CONTROL direct public match refused; held path and seed exempt; direct sibling refused; translated1e-2 match detected',flush=True)
if __name__=='__main__':control()
