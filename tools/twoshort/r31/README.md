# twoshort round 31 tools

These are the round 31 tools as they ran, kept so the next round can port from git.

- `manage31.py` is the collector on boxA. It queues held-row kicks with claims, mirrors boxE, certifies quenched finds with the pinned `finesafe.py` and writes the take.
- `worker31.py` runs on boxE. It runs one kick job at a time (midm probe or `invent_rest.py` lkick), chains legs, then runs one fq quench.
- `sel31.py` and `sel31b.py` pick the held round 30 c rows to kick and rank them.
- `follow31.py` lists fresh certified rows of other lanes that no lane claimed. `waitfind.sh` waits for the next find.
- `stats31.py` counts the runs by kind. `table31.py` writes the results table.
- `final31.py` is the last prune before the assembler copies. It drops a row from `take.tsv` and keeps its csv in place.
- `finesafe.sha256` pins the copy of border's `finesafe.py` we certify with.

The prune in `manage31.py` moved a take csv to `near/` during the round. It was changed after the round to copy the file and keep it in place.
