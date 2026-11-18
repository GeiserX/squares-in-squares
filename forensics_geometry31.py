"""Deduplicate numerical follows while retaining changed geometry and kick legs."""
import hashlib
import numpy as np
import forensics_compose as fc
import forensics_rect as rect


def key(squares):
    side,q=fc.frame(squares)
    keys=[]
    for _,a in rect.sym8(q,side):
        canonical=np.column_stack([a[:,:2],np.cos(4*a[:,2]),np.sin(4*a[:,2])])
        canonical=np.round(canonical,5)
        canonical[canonical==0]=0.
        canonical=canonical[np.lexsort(tuple(canonical[:,i] for i in range(3,-1,-1)))]
        keys.append(hashlib.sha256(canonical.tobytes()).hexdigest())
    return min(keys)


def control():
    q=np.array([[.5,.5,0.],[1.5,.5,0.]])
    shifted=q.copy();shifted[:,:2]+=[13.,-5.]
    assert key(q)==key(shifted)
    turned=q.copy();turned[:,:2]=q[:,1::-1];turned[:,2]=np.pi/2-q[:,2]
    assert key(q)==key(turned)
    noisy=q.copy();noisy[0,0]+=1e-9
    assert key(q)==key(noisy)
    changed=q.copy();changed[1,0]+=.02
    assert key(q)!=key(changed)
    print('CONTROL translation, quarter turn and 1e-9 noise deduplicate; changed spacing remains distinct',flush=True)


if __name__=='__main__':control()
