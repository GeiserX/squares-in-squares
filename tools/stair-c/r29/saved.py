"""Keep unrun recipes separate from completed geometry when source groups reopen."""
def admit(jobs,by,completed,queued,part,bar,fingerprint):
    out=[];known=set(queued);fps={}
    for j in jobs:
        if j['n']%3!=part or not set(j['ids'])<=set(by):continue
        for k in j['ids']:
            if k not in fps:fps[k]=fingerprint(by[k])
        recipe=(j['n'],*[fps[k] for k in j['ids']],*j['stacks'])
        if recipe!=j['recipe'] or recipe in completed or recipe in known:continue
        side=bar[j['n']]
        if j['predicted']>side+.003:continue
        known.add(recipe);out.append(dict(j,bar=side))
    return out
if __name__=='__main__':
    f=lambda q:q['fp'];by={k:dict(fp=k)for k in ['c','f1','f2']};r=(921,'c','f1','f2',1,2)
    j=dict(n=921,ids=list(by),stacks=[1,2],predicted=30.001,recipe=r)
    assert len(admit([j,j],by,set(),set(),0,{921:30.},f))==1
    assert admit([j],by,{r},set(),0,{921:30.},f)==[]
    assert admit([j],dict(c=by['c']),set(),set(),0,{921:30.},f)==[]
    assert admit([dict(j,recipe=('wrong',))],by,set(),set(),0,{921:30.},f)==[]
    print('CONTROL saved queue: eligible unrun recipe admitted once; completed, missing module and changed geometry refused')
