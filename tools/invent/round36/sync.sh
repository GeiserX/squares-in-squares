#!/bin/zsh
# push starts then queue (in that order), pull runs back
cd $SCRATCH/bounties-squares/take-invent-r36/work/boxE
rsync -a starts boxE:scratch/squares-invent-r36/ && rsync -a queue.json boxE:scratch/squares-invent-r36/
rsync -a boxE:scratch/squares-invent-r36/runs boxE:scratch/squares-invent-r36/pipe.log ./ 2>/dev/null
