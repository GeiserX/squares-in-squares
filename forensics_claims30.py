"""Reserve an unclaimed exact-input kick so another lane can finish that input."""
from pathlib import Path
import hashlib,json,os,re,sys


def skip(root,key,expected):
    root=Path(root)
    if not re.fullmatch(r'kick-[a-f0-9]{24}',key):raise ValueError('invalid kick key')
    path=root/'tasks'/(key+'.json')
    if not path.exists():return 'missing task'
    record=json.loads(path.read_text());packing=root/'inputs'/(key+'.csv')
    if record.get('input_sha256')!=expected or key!='kick-'+expected[:24] or not packing.exists() or hashlib.sha256(packing.read_bytes()).hexdigest()!=expected:
        return 'different input'
    try:(root/'claims'/key).mkdir()
    except FileExistsError:return 'already claimed'
    result=dict(record,end=None,seconds=0.,cancelled=True,error='exact input assigned to backlog before kick dispatch')
    output=root/'results'/(key+'.json');temporary=output.with_suffix('.tmp-'+str(os.getpid()));temporary.write_text(json.dumps(result));os.replace(temporary,output)
    return 'skipped'


if __name__=='__main__':
    root=Path(sys.argv[1]);assert str(root)=='$SCRATCH/squares-forensics-r30'
    requests=json.loads(Path(sys.argv[2]).read_text());print(json.dumps({r['key']:skip(root,r['key'],r['sha256']) for r in requests}),flush=True)
