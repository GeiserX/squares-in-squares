import sys
sys.path.insert(0,'lane');import modules as M
ids={'975tw17.C','975tw17.F1','975tw17.F2','975tw17.C~','975tw17.F1~','975tw17.F2~'}
l=M.Library('libbase',only=lambda q:q['id'] in ids)
a=l.best(975,top=2,below=.73,depth=.08,above=.70)
b=l.best(975,top=2,below=.73,depth=.025,above=.70)
def key(x):return [(round(r[0],10),r[2]['id'],r[3]['id'],r[4]['id'],r[5],r[6]) for r in x]
print('CONTROL rank depth .08',key(a),'.025',key(b),flush=True)
assert a and key(a)==key(b)
