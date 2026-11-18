# twoshort round 29 tools

`setup29.py` writes every `*29` tool of this folder from the round 28 tools in `take-twoshort-r28/work`.
The other files here are its output, with the round 29 changes, kept so the next round can port from git.

- `manage29.py` is the collector on boxA. It reads the live take dirs, walks each input, queues kicks and stages quenched results.
- `worker29.py` runs on boxE. It runs one `invent_rest.py` lkick job at a time, then one fq quench near the bar.
- `admit29.py` and `qgate29.py` are the two ancestry gates. `qwalk29.py` runs the quench lane's `quench_walk.py`.
- `certify29.py` certifies with border's `finesafe.py`. `finesafe.sha256` pins the copy we use.
- `kicks29.py` lists every finished kick with its gap to the bar.
- `worker29.py` runs `midm_scan.py --modes lkick,kick` for 900 s on a job with `tool: midm` (fresh take rows, bar-side forensics rectangles, held27 seed rows).
- `unqueue29.py` drops pending jobs and legs whose intake input has its sha256 in a WITHDRAW handoff line, and stops a running kick of one.
- `demote29.py` moves a pending job to priority 20 while another lane kicks the same n with `midm_scan.py` on boxE.
- `reorder29.py` renames pending jobs to change their order: the old name is locked on boxE, the new one is pushed.
- `qwalker29p.py` walks the take rows first, then the forensics and k123 near files.
- `mon29.sh` is one monitor pass. `stats29.py` and `fill_doc29.py` write the counts and the doc section.
