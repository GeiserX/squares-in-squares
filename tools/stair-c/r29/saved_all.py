"""Keep source-held pending recipes open without replaying measured geometry."""
def gather(archives,fingerprint):
    completed=set();pending={};measured=set()
    for lib,state,history,records in archives:
        by={q['id']:q for q in lib['mods']};fps={k:fingerprint(q)for k,q in by.items()}
        completed.update(history);completed.update(state['recipes'])
        for j in state['build']+state.get('deferred',[]):
            if not set(j['ids'])<=set(by):continue
            recipe=(j['n'],*[fps[k]for k in j['ids']],*j['stacks'])
            pending[recipe]=dict(j,recipe=recipe,name=j['name'].replace('-r28-','-r29-'),patch='restored exact unrun '+j['patch'])
        for j in records:
            if j.get('built')is None or not j.get('modules'):continue
            ids=[q['id']for q in j['modules']]
            if len(ids)==3 and set(ids)<=set(by):measured.add((j['n'],*[fps[k]for k in ids],*j['stacks']))
    unrun=set(pending)-measured;completed.difference_update(unrun);completed.update(measured)
    return dict(jobs=[j for key,j in pending.items()if key in unrun],completed=completed)

def control():
    from saved import admit
    fps=lambda q:q['fp'];mods=[dict(id=k,fp=k)for k in['c','f1','f2']]
    def job(name,stacks):return dict(n=921,name=name,ids=['c','f1','f2'],stacks=stacks,predicted=30.001,patch='saved')
    unrun=job('unrun-r28-x',[1,2]);done=job('done-r28-y',[2,2]);ku=(921,'c','f1','f2',1,2);kd=(921,'c','f1','f2',2,2)
    archive=(dict(mods=mods),dict(recipes={ku,kd},build=[done],deferred=[unrun]),{ku,kd},[dict(n=921,built=30.01,modules=[dict(id=q['id'])for q in mods],stacks=[2,2])])
    result=gather([archive],fps);assert len(result['jobs'])==1 and result['jobs'][0]['recipe']==ku
    assert ku not in result['completed']and kd in result['completed']
    assert admit(result['jobs'],{'c':mods[0]},result['completed'],set(),0,{921:30.},fps)==[]
    assert len(admit(result['jobs'],{q['id']:q for q in mods},result['completed'],set(),0,{921:30.},fps))==1
    mutant=(archive[0],dict(archive[1],deferred=[]),archive[2],archive[3]);assert not gather([mutant],fps)['jobs']
    print('CONTROL all saved: deferred geometry stays unrun before source admission; missing modules defer; recovered modules admit once; measured geometry stays completed; dropping deferred jobs changes the result',flush=True)
if __name__=='__main__':control()
