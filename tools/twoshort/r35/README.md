# twoshort round 35 tools

These are the round 35 tools as they ran. The lane owns the deep kicks of class n mod 4 = 1.

- `sel35.py` screens the held round 34 a rows of the class. It joins `sel34.py` and the byte check of `sel34b.py` in one script. A line that names several seeds now counts each seed. Our own round 34 kicks come from the DONE lines of our STATE.txt that ran to the end. List A holds the rows with one unprobed 900 s kick since their geometry, so they need their second seed. List B holds the rows with none. Each list runs largest board gap first.
- `worker35.py` runs on boxE. It is `worker34.py` with the stop file `STOP35`. A job with `noleg` queues no legs, so a find goes to backlog at once.
- `manage35.py` is the collector on boxA. It is `manage34.py` with 3 workers, load guard 16 and the last start at 15:30Z. It walks each start with `quench_walk.py` before the claim. The start gets a sidecar that names its held row.
