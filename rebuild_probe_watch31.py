"""probe_watch.py ROOT: the round 31 probe of the rebuild box worker, run beside it on each box (one light process).
Every 15 s it reads the running kick jobs (out/<key>/ with no done.json) whose queue mode is kick:SECONDS:PROBE. When a
job has run PROBE seconds (from the time its scan file header records) and no FIND line of its scan gained more than
MIN (1e-8) of side below the start, it kills the job's process group (midm_scan and its fq child). The worker then
reads raw/ as usual. Why: the worker's own probe passes on any raw file, and the first try of a held row is often an fq
polish that gains 1e-9 to 3e-9 of side (r30: 9 held kicks moved 1.2e-9 to 1.7e-9, under the 1e-10 score rule).
Log: ROOT/probe_watch.log. Ends at the deadline (ROOT/deadline)."""
import os, re, signal, subprocess, sys, time, calendar, pathlib
R = pathlib.Path(sys.argv[1]); MIN = float(os.environ.get('PROBE_MIN', '1e-8'))
log = open(R / 'probe_watch.log', 'a')
seen = {}
def say(s):
    log.write(time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + ' ' + s + '\n'); log.flush()
say('start MIN %g' % MIN)
while time.time() < float((R / 'deadline').read_text()):
    try:
        modes = {}
        for l in (R / 'queue.tsv').read_text().splitlines():
            f = l.split('\t')
            if len(f) > 4:
                modes[f[0]] = f[4].strip()
        for d in (R / 'out').iterdir():
            k = d.name
            if (d / 'done.json').exists() or k in seen:
                continue
            m = modes.get(k, '')
            if not m.startswith('kick:') or m.count(':') < 2:
                continue
            if re.match(r'^k[2-9]-', k):   # chain legs of our own fresh certs: any find counts (the worker's own probe);
                continue                    # backlog's 180 s lkick took our 910 by 7e-10 of score after our legs stopped
            probe = float(m.split(':')[2])
            sc = sorted(d.glob('scan-*.tsv'))
            if not sc:
                continue
            txt = sc[0].read_text(errors='replace')
            h = re.match(r'# n=\d+ held=([0-9.]+) .* (\d\d):(\d\d):(\d\d)', txt)
            if not h:
                continue
            held = float(h.group(1))
            # elapsed: the scan file's birth (creation) time, else its header time of day
            try:
                t0 = os.stat(sc[0]).st_birthtime
            except AttributeError:
                t0 = os.stat(sc[0]).st_ctime
            if time.time() - t0 < probe:
                continue
            gains = [held - float(x) for x in re.findall(r'^# FIND .* side ([0-9.]+) ', txt, re.M)]
            g = max(gains) if gains else 0.0
            if g > MIN:
                seen[k] = 'pass'; say('pass %s probe %g s best find %.3e of side' % (k, probe, g)); continue
            pids = subprocess.run(['pgrep', '-f', 'out/%s' % k], capture_output=True, text=True).stdout.split()
            killed = []
            for p in pids:
                try:
                    pg = os.getpgid(int(p))
                    if pg != os.getpgid(0):
                        os.killpg(pg, signal.SIGKILL); killed.append(pg)
                except (ProcessLookupError, PermissionError):
                    pass
            seen[k] = 'stop'; say('stop %s probe %g s best find %.3e of side (finds %d); killed groups %s' % (k, probe, g, len(gains), sorted(set(killed))))
    except Exception as e:
        say('error %r' % (e,))
    time.sleep(15)
say('end at the deadline')
