#!/bin/sh
set -e

if [ "${EDUVAPT_TELNET_ENABLED:-true}" = "true" ]; then
  python /app/telnet_stub.py &
fi

if [ "${EDUVAPT_RTSP_ENABLED:-true}" = "true" ]; then
  python /app/rtsp_stub.py &
fi

exec python /app/web_admin.py
