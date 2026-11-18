#!/bin/sh
# gate.sh QUEUE OUT [LOAD]: start the queue when the 1-minute load of the box is under LOAD (default 16)
cd "$(dirname "$0")"; lim=${3:-16}
while [ "$(sysctl -n vm.loadavg | awk -v l=$lim '{print ($2 < l) ? 1 : 0}')" != 1 ]; do sleep 20; done
exec /bin/sh worker.sh "$1" "$2"
