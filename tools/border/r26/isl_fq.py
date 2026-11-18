"""isl_fq.py START.txt (boxC, border r26): the fq chain of the worker (default then deep rounds, up to 6, until the side
stops falling; border_sweep.quench_one) on a soft-box island result that boxA rendered as an fq start file
(isl_prep.py). The record START->.k0.json names the best packing; isl_prep.py --back turns it into a csv."""
import sys,os
root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,root)
import border_sweep as bs
start=sys.argv[1]
END=float(open(os.path.join(root,'deadline')).read())
res=bs.quench_one((start,os.path.join(root,'fq'),600,6,.001,0,END))
print('fq chain',start,res['s_start'],'->',res['s_final'],'rounds',res['round'],'best',res['best'],flush=True)
