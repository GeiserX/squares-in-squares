#!/bin/bash
set -e
cd "$(dirname "$0")"
./py -I lane/zone_corner.py zbase external/zip77-hop.pkl z-zip51f0.77/zones --max-loss 8 > logs/zip77-hop-source.log 2>&1
./py -I - <<'PY'
import pickle,sys
sys.path.insert(0,'lane');import zone_corner as Z
p='external/zip77-hop.pkl';a=pickle.load(open(p,'rb'));a=[b for b in a if b['count']==51];b=min(a,key=lambda b:Z.loss_of(Z.cmod(b['c1'],b['c2'],b['lean1'],b['lean2']),b['f'],51,b['y0'],b['x0']));pickle.dump([b],open(p,'wb'));print('SOURCE',b['id'],b['f'],b['count'],flush=True)
PY
ZIP_SOURCE=external/zip77-hop.pkl ./infill23.sh 0.7558
