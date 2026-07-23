#!/bin/sh
set -e

python /app/telnet_stub.py &
python /app/rtsp_stub.py &
exec python /app/web_admin.py
