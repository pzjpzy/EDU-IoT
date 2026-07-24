# Partially-hardened variant of the EduVAPT-IoT simulated camera.
#
# Reuses the EXACT SAME app source as ../target (single source of truth for
# vulnerability logic - see target/app/vuln_config.py) so the two images
# never drift out of sync; only the environment variables set in this
# directory's docker-compose.yml differ.
#
# Must be built with the repo root as context, e.g.:
#   docker compose -f target-hardened/docker-compose.yml up --build -d
FROM python:3.12-slim

WORKDIR /app

COPY target/app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY target/app/ /app/
COPY target/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 80  = web admin panel (default creds FIXED, snapshot auth FIXED)
# 23  = Telnet-style admin CLI (still has default creds - left vulnerable)
# 554 = RTSP-style service DISABLED entirely in this variant
EXPOSE 80 23 554

ENTRYPOINT ["/entrypoint.sh"]
