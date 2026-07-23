# Simulated vulnerable IoT CCTV camera for EduVAPT-IoT.
# Import this image into GNS3 as a Docker container node template -
# see docs/gns3_setup.md.
FROM python:3.12-slim

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app/ /app/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 80  = intentionally weak web admin panel + live snapshot
# 23  = intentionally weak Telnet-style admin CLI
# 554 = unauthenticated RTSP-style banner (no real video)
EXPOSE 80 23 554

ENTRYPOINT ["/entrypoint.sh"]
