#!/bin/bash
# quench: run queued jobs one at a time on one box, then collect them.
# Usage: quench_drive.sh BOX BOXDIR FQ QUEUE DEADLINE_EPOCH STATE [TAKEPY BAR]
#   BOX     ssh host (boxB, boxD)
#   BOXDIR  scratch dir on the box (holds quench_box.sh and jobs/)
#   FQ      fq binary path on the box
#   QUEUE   file of local job dirs, one per line; the driver reads new lines as they come
#   STATE   the lane STATE.txt (lines appended with >>)
#   TAKEPY  (round 27) python on the box: the certification (quench_once.py take) runs there in the same
#           slot right after fq, against a copy of BAR, and result.json and final.csv come back. boxA
#           was paging at load 100 on 2026-11-14 and one local take took 4.4 minutes for 5 s of CPU.
# A job dir is ready when it has in.txt (quench_once.py prep). Each job writes
# JOBDIR/done locally after its out.txt and box.log are copied back.
# Round 28: a job that holds kick.json is a kick job (quench_kick.sh: one invent_rest.py lkick leg, then the fq loop).
# It runs only on a box with TAKEPY, and only when no plain quench job is waiting in the queue.
BOX=$1; BD=$2; FQ=$3; Q=$4; DL=$5; ST=$6; TPY=$7; BAR=$8
LANE=$(cd "$(dirname "$0")" && pwd)
# Round 28 trap: a box script copied in place over a running job kills that job (sh reads the file as it runs;
# fo-860 at 00:26Z). Copy to a temporary name and rename, so a running job keeps its old file.
ssh "$BOX" "mkdir -p $BD/jobs $BD/lane" && scp -q "$LANE/quench_box.sh" "${BOX}:$BD/quench_box.sh.$$" && ssh "$BOX" "mv $BD/quench_box.sh.$$ $BD/quench_box.sh"
[ -n "$TPY" ] && scp -q "$LANE/quench_kick.sh" "${BOX}:$BD/quench_kick.sh.$$" && ssh "$BOX" "mv $BD/quench_kick.sh.$$ $BD/quench_kick.sh"
scp -q "$LANE/quench_fqkick.sh" "${BOX}:$BD/quench_fqkick.sh.$$" && ssh "$BOX" "mv $BD/quench_fqkick.sh.$$ $BD/quench_fqkick.sh"
[ -n "$TPY" ] && scp -q "$LANE/quench_once.py" "$LANE/floatsafe.py" "$LANE/methods_lp.py" "$LANE/midm_scan.py" "$LANE/kaggle_metric.py" "$LANE/tools/border/r28/finesafe.py" "${BOX}:$BD/lane/"
# round 29: the kick tools (klane) and the border finesafe go to every box with python (boxD has a venv copy now)
# one tar stream (harvest r28: per-file scp of ~400 files took minutes to boxD)
[ -n "$TPY" ] && ssh "$BOX" "mkdir -p $BD/klane" && (cd "$LANE" && COPYFILE_DISABLE=1 tar cf - *.py -C tools/border/r28 finesafe.py) | ssh "$BOX" "tar xf - -C $BD/klane"
while [ "$(date +%s)" -lt $((DL - 30)) ]; do
  job=""
  while read -r j; do
    [ -n "$j" ] && [ -s "$j/in.txt" ] && [ ! -e "$j/done" ] && [ ! -e "$j/claimed" ] && [ ! -e "$j/kick.json" ] && [ ! -e "$j/fqkick.txt" ] && { job=$j; break; }
  done < "$Q"
  if [ -z "$job" ]; then
    while read -r j; do
      [ -n "$j" ] && [ -s "$j/in.txt" ] && [ ! -e "$j/done" ] && [ ! -e "$j/claimed" ] || continue
      { [ -e "$j/kick.json" ] && [ -n "$TPY" ]; } || [ -e "$j/fqkick.txt" ] || continue
      job=$j; break
    done < "$Q"
  fi
  if [ -z "$job" ]; then sleep 20; continue; fi
  echo "$BOX" > "$job/claimed"
  id=$(basename "$job")
  ssh "$BOX" "mkdir -p $BD/jobs/$id" && scp -q "$job/in.txt" "${BOX}:$BD/jobs/$id/in.txt"
  if [ -e "$job/fqkick.txt" ]; then
    scp -q "$job/fqkick.txt" "${BOX}:$BD/jobs/$id/"
    echo "$(date -u +%FT%TZ) $BOX START fqkick $id: nice -n 5 quench_fqkick.sh $BD/jobs/$id (fq kicks and polish), log $BD/jobs/$id/box.log, deadline $DL" >> "$ST"
    ssh "$BOX" "cd $BD && nohup nice -n 5 sh quench_fqkick.sh $BD/jobs/$id $FQ $DL > /dev/null 2>&1 &"
  elif [ -e "$job/kick.json" ]; then
    scp -q "$job/kick.json" "$job/cert.csv" "$job/meta.json" "${BOX}:$BD/jobs/$id/"
    echo "$(date -u +%FT%TZ) $BOX START kick $id: nice -n 5 quench_kick.sh $BD/jobs/$id (lkick then the fq loop), log $BD/jobs/$id/box.log, deadline $DL" >> "$ST"
    ssh "$BOX" "cd $BD && nohup nice -n 5 sh quench_kick.sh $BD/jobs/$id $FQ $DL $TPY $BD/klane > /dev/null 2>&1 &"
  else
  echo "$(date -u +%FT%TZ) $BOX START fq once $id: nice -n 5 quench_box.sh $BD/jobs/$id, log $BD/jobs/$id/box.log, deadline $DL" >> "$ST"
  ssh "$BOX" "cd $BD && nohup nice -n 5 sh quench_box.sh $BD/jobs/$id $FQ $DL > /dev/null 2>&1 &"
  fi
  while ! ssh "$BOX" "test -e $BD/jobs/$id/done"; do
    sleep 15
    [ "$(date +%s)" -gt $((DL + 240)) ] && break
  done
  if [ -n "$TPY" ] && [ -s "$BAR" ]; then
    scp -q "$job/meta.json" "$job/cert.csv" "${BOX}:$BD/jobs/$id/" && scp -q "$BAR" "${BOX}:$BD/jobs/$id/bar.tsv" \
      && ssh "$BOX" "cd $BD/jobs/$id && nice -n 5 $TPY -I $BD/lane/quench_once.py take $BD/jobs/$id $BD/jobs/$id/bar.tsv > take.out 2>&1" \
      && scp -q "${BOX}:$BD/jobs/$id/final.csv" "$job/final.csv.tmp" && mv "$job/final.csv.tmp" "$job/final.csv" \
      && scp -q "${BOX}:$BD/jobs/$id/result.json" "$job/result.json.tmp"
  fi
  scp -q "${BOX}:$BD/jobs/$id/out.txt" "${BOX}:$BD/jobs/$id/box.log" "${BOX}:$BD/jobs/$id/done" "$job/" 2>/dev/null
  scp -q "${BOX}:$BD/jobs/$id/best.txt" "$job/" 2>/dev/null  # round 29: the lowest raw try (quench_box.sh)
  [ -e "$job/result.json.tmp" ] && mv "$job/result.json.tmp" "$job/result.json"
  echo "$(date -u +%FT%TZ) $BOX FINISH fq once $id: $(tail -1 "$job/box.log" 2>/dev/null) $(cat "$job/done" 2>/dev/null)$([ -e "$job/result.json" ] && echo ' (certified on the box)')" >> "$ST"
done
echo "$(date -u +%FT%TZ) $BOX driver stopped at deadline" >> "$ST"
