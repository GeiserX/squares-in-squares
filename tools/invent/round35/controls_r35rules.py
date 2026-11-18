"""Round 35 rule controls: producer_certified (lesson 6e), leg bar rule (6h), worker load guard (6d)."""
import pathlib,sys,tempfile,json,os,re
W=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(W))
import campaign35base as C
out={}
with tempfile.TemporaryDirectory() as tmp:
 real=C.S;C.S=pathlib.Path(tmp);(C.S/'take-k123-r35').mkdir();(C.S/'take-k123-r35/take.tsv').write_text('n\theld\tnew\tgain\tsource\tlicence\n790\t1\t0.5\t1\tx\ty\n')
 out['k123_certified_790_true']=C.producer_certified('/a/take-k123-r35/near/790-j.csv',790)
 out['k123_791_false']=not C.producer_certified('/a/take-k123-r35/near/791-j.csv',791)
 out['invent_self_false']=not C.producer_certified('/a/take-invent-r35/near/790-j.csv',790)
 out['r34_path_false']=not C.producer_certified('/a/take-k123-r34/near/790-j.csv',790)
 out['forensics_no_take_false']=not C.producer_certified('/a/take-forensics-r35/near/790-j.csv',790)
 C.S=real
src=(W/'campaign35.py').read_text();assert "C.BASE[n]-d['new']>1e-10" in src
leg=lambda base,new:base-new>1e-10
out['leg_far_below_true']=leg(0.02,0.02-1e-9);out['leg_within_1e-10_false']=not leg(0.02,0.02-5e-11)
wk=(W/'worker35.py').read_text();m=re.search(r"if os.getloadavg\(\)\[0\]>16 and all\(j\['kind'\]!='control'for j in queue\)",wk)
g=lambda load,queue:load>16 and all(j['kind']!='control'for j in queue)
out['guard_present']=bool(m);out['guard_high_load_waits']=g(17,[{'kind':'fresh'}]);out['guard_low_load_runs']=not g(3,[{'kind':'fresh'}]);out['guard_controls_run']=not g(17,[{'kind':'control'}])
print(json.dumps(out));assert all(out.values())
