#!/bin/zsh
# walk each given start with forensics_walk36 (cap 100000), one at a time; output walks/<sha16>.out (never named in a sidecar)
cd .
for f in "$@"; do
  h=$(shasum -a 256 "$f" | cut -c1-16)
  [ -s $SCRATCH/bounties-squares/take-invent-r36/work/walks/$h.out ] && continue
  nice -n 5 $SCRATCH/bounties-squares/venv/bin/python forensics_walk36.py "$f" > $SCRATCH/bounties-squares/take-invent-r36/work/walks/$h.tmp 2>$SCRATCH/bounties-squares/take-invent-r36/work/walks/$h.err && mv $SCRATCH/bounties-squares/take-invent-r36/work/walks/$h.tmp $SCRATCH/bounties-squares/take-invent-r36/work/walks/$h.out
done
