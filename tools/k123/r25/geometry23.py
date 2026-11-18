import hashlib
import numpy as np
def key(n,P,cross=False):
 Q=np.ascontiguousarray(P[np.lexsort((P[:,2],P[:,1],P[:,0]))],dtype=np.float64)
 return hashlib.sha256(f'{n}:{int(cross)}:'.encode()+Q.tobytes()).hexdigest()
