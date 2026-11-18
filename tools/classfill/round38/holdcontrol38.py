"""Positive and negative control of the r38 hold-before-certify logic in cf38.collect (no ssh, no file writes)."""
import sys, time
sys.dont_write_bytecode = True
sys.path.insert(0, '$SCRATCH/bounties-squares/take-classfill-r38/work')
import cf38 as C
notes = []
C.note = lambda x: notes.append(x)
C.save = lambda: None
C.HOSTS = []
C.own = lambda: {}
C.bars = lambda: ({900: 0.02}, {900: 0.02}, {})
cand = dict(n=900, near='/x/900-a.csv', sha='a' * 64, score=0.0199, tag='ta', pubfirst=False, seed=1, licence='l', source='s', input_path='/x')
# case 1: a held find with a follow still running stays held
C.state.clear(); C.state.update(jobs={'tf': dict(n=900, kind='own-family-follow')}, collected=[], done_keys=[], chain=[], pending=[], hold={'900': dict(cands=[cand], rounds=1, best=0.0199)}, endpoints={})
C.collect(); assert C.state['pending'] == [] and '900' in C.state['hold'], 'held find released while its follow runs'
# case 2: a held find with a queued chain entry stays held
C.state['jobs'] = {}; C.state['chain'] = [dict(n=900)]
C.collect(); assert C.state['pending'] == [] and '900' in C.state['hold'], 'held find released while its chain waits'
# case 3: follows done -> best candidate released
c2 = dict(cand, near='/x/900-b.csv', score=0.01985, tag='tb')
C.state['chain'] = []; C.state['hold']['900']['cands'].append(c2)
C.collect(); assert [p['tag'] for p in C.state['pending']] == ['tb'] and C.state['hold'] == {}, C.state
print('HOLD38_CONTROL_PASS running follow holds, queued chain holds, release picks the best (tb)')
