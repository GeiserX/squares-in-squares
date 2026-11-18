# twoshort round 33 tools

These are the round 33 tools as they ran, kept so the next round can port from git.

- `manage33.py` is the collector on boxA. It follows fresh certified rows of other lanes when no lane claims them within 10 minutes. It also queues first lkicks of held rows and the 900 s deep kicks of the shared queue. It mirrors boxE, certifies each quenched find with the pinned `finesafe.py`, runs `share31.py` on each output and writes the take.
- `worker33.py` runs on boxE. It is `worker32.py` with a new stop file (`STOP33`).
- `sel33.py` screens held rows n 1 to 399 for a first lkick. `sel33b.py` does the same for n 400 to 1000.
- `sel33c.py` screens the shared deep-kick queue from border's `held33/info.json`. `sel33d.py` adds the held rows that changed in round 32 and have had no unprobed 900 s kick since that change.
- `table33.py` writes the results table. `final33.py` is the last prune before the assembler copies.
- `finesafe.sha256` pins the copy of border's `finesafe.py` we certify with.
