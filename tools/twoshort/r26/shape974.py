"""Recognize numerical copies of the 974 state after three dry scans."""
import csv, math
import numpy as np
from scipy.spatial import cKDTree

def load(path):
 a=np.array([[float(r[k]) for k in ('x','y','angle')] for r in csv.DictReader(open(path))])
 h=(np.abs(np.cos(a[:,2]))+np.abs(np.sin(a[:,2])))/2
 a[:,:2]-=(a[:,:2]-h[:,None]).min(0)
 return a,float((a[:,:2]+h[:,None]).max())

def distance(a,la,b):
 tree=cKDTree(np.c_[b[:,:2],np.cos(4*b[:,2]),np.sin(4*b[:,2])]);best=math.inf
 for reflect in (False,True):
  q=a.copy()
  if reflect:q[:,0]=la-q[:,0];q[:,2]=-q[:,2]
  for _ in range(4):
   best=min(best,float(tree.query(np.c_[q[:,:2],np.cos(4*q[:,2]),np.sin(4*q[:,2])])[0].max()))
   q[:,:2]=np.c_[la-q[:,1],q[:,0]];q[:,2]+=math.pi/2
 return best

def guard(root):
 a,la=load(root/'starts/h-corners-974-c7fd606f.csv')
 b,_=load(root/'starts/h-corners-974-3370274c.csv')
 positive=distance(a,la,b);b[0,0]+=1e-4;negative=distance(a,la,b)
 assert positive<2e-8 and negative>1e-6,(positive,negative)
 def same(path):
  p,side=load(path)
  return len(p)==974 and abs(side-la)<2e-8 and distance(p,side,a)<2e-8
 return same,dict(positive=positive,negative=negative,tolerance=2e-8)
