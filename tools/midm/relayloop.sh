#!/bin/sh
# relayloop.sh: run mkrelay.sh once a minute until ./deadline passes or STOP exists.
cd "$(dirname "$0")"
while [ ! -e STOP ] && [ $(( $(cat deadline) - $(date +%s) )) -gt 120 ]; do /bin/sh mkrelay.sh; sleep 60; done
