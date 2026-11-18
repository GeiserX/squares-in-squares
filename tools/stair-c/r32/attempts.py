"""Close measured saved attempts across round-name aliases."""
import re
NAME=re.compile(r'^(\d+)-r\d+-([0-9a-f]{12})$')
COMMAND=re.compile(r' COMMAND (\S+) rc (0|124)(?:\s|$)')

def identity(name):
    match=NAME.fullmatch(name)
    return (int(match[1]),match[2])if match else None

def signature(job,by,fingerprint):
    if job.get('recipe')is not None:return tuple(job['recipe'])
    if not set(job['ids'])<=set(by):return None
    return(job['n'],*[fingerprint(by[k])for k in job['ids']],*job['stacks'])

def finished(jobs,lines):
    names={identity(j['name']):tuple(j['recipe'])for j in jobs if identity(j['name'])and j.get('recipe')is not None}
    result=set()
    for line in lines:
        match=COMMAND.search(line)
        if match and identity(match[1])in names:result.add(names[identity(match[1])])
    return result
