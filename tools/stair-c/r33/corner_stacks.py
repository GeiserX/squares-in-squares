"""Include following flush stacks in a tagged corner's local physical model."""
import math
import numpy as np
import modules as M
import corner_paths as C
ORIGINAL_STATE=M.corner_state
ORIGINAL_AT=M.corner_at
INSTALLED=False

def corner_state(mod,f,Pm,y0,x0):
    P,mode=ORIGINAL_STATE(mod,f,Pm,y0,x0)
    count=int(mod.get('extra_stacks',0))
    if not count:return P,mode
    parts=[P];modes=[mode]
    for arm in[1,2]:
        c=mod['c1'if arm==1 else'c2'];t=M.flush_tilt(c,f);pitch=1/math.cos(t);W=c-1+f
        angle=mod['lean1'if arm==1 else'lean2']*math.degrees(t)
        for j in range(1,count+1):
            Q=M.stack_squares(c,angle,W/2,y0+(j+.5)*pitch)if arm==1 else M.stack_squares(c,angle,x0+(j+.5)*pitch,W/2,along_x=False)
            Q[:,2]=np.radians(Q[:,2]);parts.append(Q);modes.append(np.full(c,arm,int))
    return np.vstack(parts),np.concatenate(modes)

def corner_at(mod,f,cap_y,cap_x):
    return C.corner_at(mod,f,cap_y,cap_x)if mod.get('extra_stacks')else ORIGINAL_AT(mod,f,cap_y,cap_x)

def install():
    global INSTALLED
    if INSTALLED:return
    M.corner_state=corner_state;M.corner_at=corner_at;INSTALLED=True
