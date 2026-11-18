"""Add the final measured bar-leg result after the deadline report is written."""
import datetime,json,math,os
from pathlib import Path
W=Path('$SCRATCH/bounties-squares/take-stair-c-r29/work')
def facts(m):
    row=next(x for x in m['whole_follows']if x.get('kick',{}).get('target_side')is not None)
    k=row['kick'];side=row['certified_side'];gain=(k['target_side']-side)/math.sqrt(row['n'])
    return dict(n=row['n'],seed=k['seed'],seconds=k['seconds'],shortening=k['start']-k['end'],side=side,side_below_bar=k['target_side']-side,score_below_bar=gain,record=row['path'])
def main():
    assert datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,11,15,11,55,tzinfo=datetime.timezone.utc)
    p=W.parent/'report.json';report=json.load(open(p));m=json.load(open(W/'measurements-final.json'));v=facts(m)
    sentence=f"The final n812 bar-input leg (seed {v['seed']}) shortened its input by {v['shortening']:.12g} of side in {v['seconds']:.3f}s. Its certified side was {v['side']:.15f}, only {v['side_below_bar']:.12g} below the queued live bar ({v['score_below_bar']:.12g} score), below the1e-10 gain requirement. The earlier input-side leg used seed3612 and shortened5.69085e-9 of side. These legs used different seeds."
    if sentence not in report['what_was_measured']:report['what_was_measured'].append(sentence)
    item='Run paired900s bar-input and input-side legs with identical seeds, starting earlier. The late n812 bar-input leg shortened4.90988818e-6 in333s and reached the held floor; the earlier input-side leg shortened5.69085e-9 in901s. Different seeds prevent isolating the cause. Cached18-state following-stack library: '+str(W/'following-stack-library')+'. Try changed805 corners at748 after installing corner_stacks.py.'
    if item not in report['next']:report['next'].insert(1,item)
    commit=json.load(open(W/'supplement-commit.json'))['commit']
    if commit not in report['commits']:report['commits'].append(commit)
    temp=W/'report-supplement.tmp';temp.write_text(json.dumps(report,indent=2)+'\n');os.replace(temp,p)
    (W/'report-supplemented.json').write_text(json.dumps(v,indent=2))
if __name__=='__main__':main()
