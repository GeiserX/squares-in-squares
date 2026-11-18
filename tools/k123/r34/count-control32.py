from pathlib import Path
import sys,json,csv,time
W=Path(__file__).resolve().parent;sys.path[:0]=[str(W),str(W/'lane')];sys.dont_write_bytecode=True
import walker30
from publicshare31 import file_measure
p='$SCRATCH/bounties-squares/take-harvest-r32/work/public16/data/gh/kenaznia-doga__s292-upper-bound/n-292-candidate.yaml.csv'
a=walker30.prv_share(p,292);b=walker30.prv_share(p,488);assert b[1]==0 and b[3]==0,(a,b)
full=file_measure(p,292);assert max(full[1],full[3])<.4,full
saved=json.load((W/'certs/j22w-fresh10084-292-292-j14-7-s5/out/source-walk26.json').open());q=saved['start'];r=walker30.check(q);assert r['clean'],r['hits']
row={'count_cache_control':True,'root292_measure':a,'absent488_measure':b,'full_292_measure':full,'child488_full_source_clean':True,'files':r['files'],'output488_measure':r.get('prv_share')};(W/'count-control32.json').write_text(json.dumps(row));print(json.dumps(row),flush=True)
