# twoshort round 34 tools

These are the round 34 tools as they ran. The lane owns the deep kicks of class n mod 4 = 1.

- `sel34.py` screens the held round 33 a rows of the class. It skips rigid closed forms, lattice rows and out sources. It counts the unprobed 900 s kick lines since each row's current geometry. List A holds the rows that changed in round 33 a and had only probed kicks since. List B holds the rest, largest board gap first.
- `sel34b.py` recounts those lines by bytes. A line counts only when a csv it names holds the held geometry of n, or when it names no readable csv.
- `worker34.py` runs on boxE. It is `worker33.py` with the stop file `STOP34`. It also has a per-n stop file `stopn/<n>` and pid and current-job files for the liveness check.
- `manage34.py` is the collector on boxA. It claims a row, waits 5 s and re-reads the log before the row starts. It queues two unprobed 900 s seeds per row and keeps the load guard. It restarts dead workers and stops a kick when another lane posts a row more than 1e-6 lower. It certifies finds with the pinned `finesafe.py` and hands them to backlog.
