import pathlib,os,signal
R=pathlib.Path.home()/'scratch/squares-k123';producer=int((R/'worker.pids').read_text().splitlines()[3]);os.kill(producer,signal.SIGSTOP)
try:
 old=(R/'queue.tsv').read_text();new=(R/'queue-send.tsv').read_text();(R/'queue-append.tmp').write_text(old+new);(R/'queue-append.tmp').replace(R/'queue.tsv')
finally:os.kill(producer,signal.SIGCONT)
