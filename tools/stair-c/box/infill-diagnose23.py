import glob,pickle,sys
sys.path.insert(0,'lane');import modules as M
for d in glob.glob('lib-zip51f*'):
 need=set(open(d+'/need.txt').read().split());lib=M.Library(d,only=M.usable)
 print('LIB',d,'need',len(need),'usable',sum(C['id'] in need for C in lib.corners),'far',[(c,len(F)) for c,F in lib.far.items()],flush=True)
 for n in [803,860,921,978,982,984,987]:
  rows=lib.best(n,top=1,below=1.,need=need,depth=.3)
  print('PRED',n,[(r[0],r[2]['id'],r[3]['id'],r[4]['id'],r[5],r[6]) for r in rows],flush=True)
