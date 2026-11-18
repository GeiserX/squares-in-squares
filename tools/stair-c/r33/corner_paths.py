"""Try every existing corner path before refusing a rotating corner."""
import modules as M
ORIGINAL=M.corner_at

def rotating(mod,f,cap_y,cap_x):
    steps=M.path(mod['f0'],f)
    strategies=[(0,(1.,.02)),(1,(.02,1.)),(None,(1.,1.)),(None,(1.,.5)),(None,(.5,1.))]
    for first,cost in strategies:
        at=M.corner_len(mod,mod['f0'],mod['P'],mod['y0']+1e-6,mod['x0']+1e-6,cost)
        for g in steps:
            if at is None:break
            at=M.corner_len(mod,float(g),at[2],at[0]+.02,at[1]+.02,cost)
        if at is None:continue
        if at[0]<=cap_y+1e-9 and at[1]<=cap_x+1e-9:return at
        if first is None:
            r=M.corner_len(mod,f,at[2],at[0],at[1],caps=(cap_y-at[0],cap_x-at[1]))
        elif first==0:
            if at[0]>cap_y+1e-9:continue
            r=M.corner_len(mod,f,at[2],at[0],at[1],cost=(1e-3,1.),caps=(cap_y-at[0],None))
        else:
            if at[1]>cap_x+1e-9:continue
            r=M.corner_len(mod,f,at[2],at[0],at[1],cost=(1.,1e-3),caps=(None,cap_x-at[1]))
        if r is not None and r[0]<=cap_y+1e-9 and r[1]<=cap_x+1e-9:return r
    return None

def corner_at(mod,f,cap_y,cap_x):
    if not mod.get('turn'):return ORIGINAL(mod,f,cap_y,cap_x)
    fixed=dict(mod,turn=False,P=mod['P'].copy())
    at=ORIGINAL(fixed,f,cap_y,cap_x)
    return at if at is not None else rotating(mod,f,cap_y,cap_x)

def install():M.corner_at=corner_at

def branch_control():
    old_len,old_path=M.corner_len,M.path;seen=[];dummy=M.np.zeros((1,3))
    q=dict(turn=True,f0=.8,P=dummy,y0=1.,x0=1.)
    def fake(mod,f,P,y,x,cost=(1.,1.),caps=(None,None)):
        seen.append(cost)
        return (2.,1.,dummy)if cost==(1.,.02)else(1.,2.,dummy)if cost==(.02,1.)else(1.4,1.4,dummy)
    M.corner_len=fake;M.path=lambda *a:[]
    try:
        assert ORIGINAL(q,.8,1.5,1.5)is None
        assert rotating(q,.8,1.5,1.5)is not None and(.02,1.)in seen and(1.,1.)in seen
        assert rotating(q,.8,.5,.5)is None
        M.corner_len=lambda mod,f,P,y,x,cost=(1.,1.),caps=(None,None):(1.4,1.4,dummy)if cost==(1.,.5)and caps==(None,None)else(2.,2.,dummy)
        assert rotating(q,.8,1.5,1.5)is not None,'table intermediate cost path was skipped'
    finally:M.corner_len,M.path=old_len,old_path
    print('CONTROL corner paths: original first-path refusal reproduced; later balanced and intermediate table paths found; impossible caps refused',flush=True)
