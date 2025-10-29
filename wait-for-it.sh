#!/bin/sh
# Minimal wait-for-it replacement using python3 to test TCP connectivity to 'db:5432'
# Exits 0 when the host:port is reachable.

HOST=${1:-db}
PORT=${2:-5432}
RETRIES=${3:-60}
SLEEP=${4:-1}

i=0
while [ $i -lt "$RETRIES" ]; do
    if python3 - <<PY >/dev/null 2>&1
import socket
try:
    s=socket.create_connection(("$HOST", int($PORT)), timeout=1)
    s.close()
    print('ok')
except Exception:
    raise SystemExit(1)
PY
    then
        echo "Connection to $HOST:$PORT successful"
        exit 0
    fi
    i=$((i+1))
    echo "Waiting for $HOST:$PORT... ($i/$RETRIES)"
    sleep $SLEEP
done

echo "Timed out waiting for $HOST:$PORT"
exit 1
