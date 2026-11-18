# twoshort round 30 tools

`setup30.py` writes every `*30` tool of this folder from the round 29 tools in `take-twoshort-r29/work`.
The other files here are its output, with the round 30 changes, kept so the next round can port from git.

- `manage30.py` is the collector on boxA. It reads the live take dirs, walks each input, queues kicks and stages quenched results.
- `worker30.py` runs on boxE. It runs one kick job at a time, then one fq quench near the bar, then a contact LP polish of the quenched file.
- `admit30.py` and `qgate30.py` are the two ancestry gates. `qwalk30.py` runs the quench lane's `quench_walk.py`.
- `certify30.py` certifies with border's `finesafe.py`. `finesafe.sha256` pins the copy we use.
- `bar30.py` is the bar: the lower of `round30-briefs/bar30.tsv` and the round 29 b file.
- `handq30.py` queues a whole layout by hand, with a byte snapshot and an intake record.
- `reorder30.py` renames pending jobs to change their order. `unqueue30.py` drops jobs whose input was withdrawn.
- `kicks30.py`, `stats30.py`, `results30.py` and `final30.py` write the counts, the results table and the report numbers.
- `mon30.sh` and `tick30.sh` are monitor passes.
