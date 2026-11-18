#!/bin/sh
cd $SCRATCH/bounties-squares/take-border-r35/work
date -u +%T; echo "final jobs $(ls final/*.job.json 2>/dev/null | wc -l) done $(ls final/*.job.done 2>/dev/null | wc -l); q jobs $(ls q/*.job.json 2>/dev/null | wc -l) done $(ls q/*.job.done 2>/dev/null | wc -l); lp jobs $(ls lp/jobs | wc -l)"
echo "take rows: $(tail -n +2 ../take.tsv | wc -l)"; tail -n +2 ../take.tsv | cut -f1-4
grep -E 'certified |direct |window |LP |REJECT|near ' ../STATE.txt | tail -8 | cut -c1-260
