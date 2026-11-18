"""Read source withdrawals through the live round, using the existing parser."""
import glob,os,re
from quench_walk import S,withdraw_time,RETAIN,share_only
import quench_walk as Q
WITHDRAWN_LINES=Q.WITHDRAWN_LINES
_wl_key=[None]
_raw_lines=[]
def samanyu_only(line):return Q.samanyu_only(line)

def load_withdrawn():
    """The WITHDRAW, WITHHOLD and reclassify lines of the handoff logs, read again when a log changes
    (a long follow must see the withdrawals of its own round)."""
    logs = sorted(p for p in glob.glob(S + 'handoff-r*.log') if int(re.search(r'handoff-r(\d+)\.log$', p)[1]) >= 22)
    key = tuple((h, os.path.getmtime(h)) for h in logs)
    if key == _wl_key[0]:
        WITHDRAWN_LINES[:]=_raw_lines
        return
    out, back = [], []
    for _h in logs:
        rnd = re.search(r'handoff-(r\d+)\.log$', _h).group(1)
        for _l in open(_h, errors='replace'):
            if re.search(r'REINSTATE|reinstat|withdrawal (?:is )?lifted', _l, re.I):
                # classfill 20:06:05Z: REINSTATE n982 ... prior temporary withdrawal lifted (harvest saw the walk
                # refuse 982 on that line): a reinstatement cancels the earlier withdrawals of what it names
                back.append((_l.strip(), withdraw_time(_l), set(re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)', _l)),
                             re.match(r'\S+\s+([a-z0-9-]+)\s+->', _l), set(re.findall(r'\bn\s*=?\s*(\d{1,4})\b', _l))))
                continue
            # round 28: a retention note is not a withdrawal. modules 13:12:57Z of round 26 wrote 'certified n=975 ...
            # (own turned corner from twoshort-r24 973, not the withheld twoshort-r25/975.csv)', and the old read withdrew
            # the certified take-modules-r26/975.csv the line announces. The phrase 'not the withheld X' (or withdrawn,
            # refused) is cut before the test, so only a line that still says withdraw or withhold withdraws.
            _l = RETAIN.sub(' ', _l)
            if share_only(_l):
                continue
            # case-insensitive since round 27: harvest wrote 'withdrawn near file 988-pubfq-...' in lower case
            if re.search(r'withdr|withh[eo]ld|reclassif', _l, re.I) and not samanyu_only(_l):
                for _f in re.findall(r'(take-[a-z0-9-]+-r\d+/[^\s,;]+?\.csv)', _l):
                    out.append((_f, _l.strip()))
                # a line that names counts and no paths: 'harvest -> ...: harvest withdrew 416 499 646 654 695 814
                # from its take', 'midm -> all: withdrew 546 642 694 684 from the midm take', 'WITHDRAW n982'
                lm = re.match(r'\S+\s+([a-z0-9-]+)\s+->', _l)
                mm = re.search(r'withdr\w*\s+(?:n\s*=?\s*)?((?:\d{1,4}(?:\s*,\s*|\s+and\s+|\s+)?)+)', _l, re.I)
                if lm and mm:
                    for nn in re.findall(r'\d{1,4}', mm.group(1)):
                        out.append(('take-%s-%s/%s.csv' % (lm.group(1), rnd, nn), _l.strip()))
    keep = []
    for f, l in out:
        tw = withdraw_time(l)
        lane_n = re.match(r'take-([a-z0-9-]+)-r\d+/(\d+)\.csv$', f)
        cancelled = False
        for bl, tb, paths, blm, bns in back:
            if tb <= tw:
                continue
            if f in paths or (lane_n and blm and blm.group(1) == lane_n.group(1) and lane_n.group(2) in bns):
                cancelled = True
        if not cancelled:
            keep.append((f, l))
    WITHDRAWN_LINES[:] = keep
    _raw_lines[:]=keep
    _wl_key[0] = key
