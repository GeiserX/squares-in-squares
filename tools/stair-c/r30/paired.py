"""Compare source-side and bar-side kicks with identical bytes, seeds and budget."""
import csv,datetime,hashlib,json,math,pathlib,subprocess,sys,time,traceback
H=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import coordinator as C
W=pathlib.Path(C.WORK);OLD=pathlib.Path(C.ROOT)/'take-stair-c-r29/work'
STOP=datetime.datetime(2026,11,15,17,20,tzinfo=datetime.timezone.utc).timestamp()
def run(args):return subprocess.run(args,capture_output=True,text=True,timeout=40)
def copy(path,host='boxC'):
    r=run(['rsync','-a',*[str(x)for x in path],host+':scratch/squares-stair-c/cert-in/'])
    assert r.returncode==0,r.stderr
def main():
    while not(W/'coordinator.pid').exists():time.sleep(10)
    # A real binary control must finish before production at-bar dispatch.
    p=W/'cert-in/975-000-bar-control.csv';p.parent.mkdir(exist_ok=True)
    p.write_bytes((W/'box/cert-in/975-control-real.csv').read_bytes())
    j=dict(n=975,control_only=True,whole_kick=True,kick_bar_control=True,modules=[],built=31.7141)
    p.with_suffix('.json').write_text(json.dumps(j));copy([p,p.with_suffix('.json')])
    while time.time()<STOP:
        r=run(['rsync','-a','boxC:scratch/squares-stair-c/bar-kick-control.json',str(W)+'/'])
        if r.returncode==0:break
        time.sleep(20)
    assert json.load(open(W/'bar-kick-control.json'))['passed']
    print('CONTROL real975 bar-input passed before production',flush=True)
    source=OLD/'cert-in/812-own-near-8a380cee054d.csv'
    j=json.load(open(source.with_suffix('.json')));meta=C.manifest(j)
    assert C.full_admission(str(source),812,meta)is not None,'unresolved source proof'
    _,rows,score,why=C.floatsafe.work((812,C.rows(str(source))));assert rows is not None,why
    target=(1+C.bar()[812])*math.sqrt(812);receipts=[]
    for seed in [3912,4912]:
        # Alternate order across pairs. The stopping rule and maximum effort match.
        for mode in (['input','bar']if seed==3912 else['bar','input']):
            name=f'812-pair-{seed}-{mode}'
            p=W/'cert-in'/(name+'.csv');C.write(str(p),rows)
            digest=hashlib.sha256(p.read_bytes()).hexdigest()
            record=dict(j,source=str(source)+' immutable sha256 '+hashlib.sha256(source.read_bytes()).hexdigest()+'; '+meta['source'],whole_layout_follow=True,whole_kick=True,kick_seed=seed,paired_experiment=True,pair_seed=seed,pair_mode=mode,pair_input_sha256=digest,built=(1+score)*math.sqrt(812))
            record.pop('source_kick',None)
            if mode=='bar':record['kick_target_side']=target
            else:record.pop('kick_target_side',None)
            p.with_suffix('.json').write_text(json.dumps(record));copy([p,p.with_suffix('.json')])
            C.state(f'PAIRED n812 {mode} seed{seed} input sha256 {digest} target {target}; serial boxC, budget900s and certified-file fq. Source proof passed. Deadline17:45Z.')
            out=W/(name+'-receipt.json')
            while time.time()<STOP:
                r=run(['rsync','-a','boxC:scratch/squares-stair-c/final/'+name+'.json',str(out)])
                if r.returncode==0:break
                time.sleep(30)
            result=json.loads(out.read_text());kick=result.get('source_kick',{});q=result.get('certified_file_quench',{})
            assert kick.get('invoked')and q.get('completed'),result
            receipts.append(dict(seed=seed,mode=mode,input_sha256=digest,target=target,kick=kick,quench=q))
            (W/'paired-results.json').write_text(json.dumps(receipts,indent=2))
            print('PAIRED RESULT',seed,mode,'shortening',kick['start']-kick['end'],'seconds',kick['seconds'],flush=True)
    for seed in[3912,4912]:
        pair=[r for r in receipts if r['seed']==seed]
        assert len(pair)==2 and pair[0]['input_sha256']==pair[1]['input_sha256']
    C.state('PAIRED complete: four matched-seed legs and final certified-file quenches. Receipts work/paired-results.json.')
if __name__=='__main__':main()
