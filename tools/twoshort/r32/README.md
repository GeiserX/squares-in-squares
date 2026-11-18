# twoshort round 32 tools

These are the round 32 tools as they ran, kept so the next round can port from git.

- `manage32.py` is the collector on boxA. It queues held-row lkicks with claims, mirrors boxE, certifies quenched finds with the pinned `finesafe.py` and writes the take. A plan row may carry its own kick steps (`sigs`). The source text names the tool of the job.
- `worker32.py` runs on boxE. It runs one job at a time (an `invent_rest.py` lkick, or a `midm_scan.py` kick with or without a probe), chains legs, then runs one fq quench. A leg starts from the quenched file when the quench went lower.
- `sel32.py` picks the held round 31 b rows (tiers 0 to 2). `sel32ext.py` adds the second-seed tiers 3a, 3b and 4. `elig32.py` counts the plan rows the collector would still queue.
- `queue_midm32.py` claims and queues 900 s `midm_scan.py` kicks with no probe on the held rows with the largest board gap that no other lane claimed, and their controls.
- `stats32.py` counts the runs by kind (`--md` for a table). `table32.py` writes the results table.
- `final32.py` is the last prune before the assembler copies. It drops a row from `take.tsv` and keeps its csv in place.
- `finesafe.sha256` pins the copy of border's `finesafe.py` we certify with.
