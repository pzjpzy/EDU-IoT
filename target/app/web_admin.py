"""Camera web admin panel - vulnerable by default, but see vuln_config.py
for how each weakness can be individually toggled off to build a
partially-hardened variant of the same image (target-hardened/).

Possible weaknesses (each independently toggleable):
  - default, unchangeable credentials (OWASP I1)
  - a static, unsigned session cookie with no expiry (OWASP I1 / weak session mgmt)
  - the live snapshot is reachable with NO authentication at all (OWASP I3)

Also self-reports which weaknesses exist at all (GET /eduvapt/profile) and
which have actually been triggered by a student (GET /eduvapt/status), so
the EduVAPT-IoT backend's task board can adapt to whatever this specific
target instance has enabled - see backend/app/services/task_engine.py.
"""
import os

from flask import Flask, Response, jsonify, redirect, request, send_file

import events
import vuln_config

app = Flask(__name__)

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Intentionally weak defaults when HTTP_DEFAULT_CREDS_VULNERABLE is on; a
# single fixed strong credential (still usable, just not guessable) when off.
VALID_CREDENTIALS = (
    {("admin", "admin"), ("admin", "1234"), ("admin", "password")}
    if vuln_config.HTTP_DEFAULT_CREDS_VULNERABLE
    else {vuln_config.HARDENED_HTTP_CREDENTIAL}
)

FLAG_HTTP_LOGIN = "EDUVAPT{d3f4ult_cr3d5_4r3_d4ng3r0us}"

LOGIN_PAGE = """<!doctype html>
<html><head><title>IoT-Cam Admin</title></head>
<body style="font-family:sans-serif;background:#1e1e23;color:#eee;padding:2rem">
<h2>IoT-Cam Admin Login</h2>
<form method="POST" action="/login">
  <label>Username: <input name="username" autofocus></label><br><br>
  <label>Password: <input name="password" type="password"></label><br><br>
  <button type="submit">Login</button>
</form>
</body></html>"""

LIVE_PAGE = f"""<!doctype html>
<html><head><title>IoT-Cam Live</title></head>
<body style="font-family:sans-serif;background:#1e1e23;color:#eee;padding:2rem">
<h2>Live Camera Feed - CAM-01</h2>
<img src="/snapshot.jpg" style="max-width:100%;border:2px solid #444">
<p>FLAG: {FLAG_HTTP_LOGIN}</p>
</body></html>"""


@app.route("/")
def index():
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return LOGIN_PAGE
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if (username, password) in VALID_CREDENTIALS:
        if vuln_config.HTTP_DEFAULT_CREDS_VULNERABLE:
            events.mark("http_default_login")
        resp = redirect("/live")
        # Intentionally weak: static, unsigned token, no expiry (independent
        # of the default-credentials toggle - this project doesn't offer a
        # hardened session-management variant).
        resp.set_cookie("session", "authenticated")
        return resp
    return Response("Invalid credentials", status=401)


@app.route("/live")
def live():
    if request.cookies.get("session") != "authenticated":
        return redirect("/login")
    return LIVE_PAGE


@app.route("/snapshot.jpg")
def snapshot():
    authenticated = request.cookies.get("session") == "authenticated"
    if vuln_config.SNAPSHOT_UNAUTH_VULNERABLE:
        # Intentional vulnerability: no auth check here at all, even though
        # the /live page it's embedded in does check for a session cookie.
        if not authenticated:
            events.mark("unauth_snapshot_access")
    elif not authenticated:
        return Response("Unauthorized", status=401)
    return send_file(os.path.join(ASSET_DIR, "cctv_snapshot.jpg"), mimetype="image/jpeg")


@app.route("/eduvapt/status")
def status():
    """Internal-use only: polled by the EduVAPT-IoT backend, not linked from any student-facing page."""
    return jsonify(events.get_all())


@app.route("/eduvapt/reset", methods=["POST"])
def reset():
    events.reset()
    return jsonify({"ok": True})


@app.route("/eduvapt/profile")
def profile():
    """Internal-use only: declares which weaknesses THIS build has enabled,
    so the backend can generate a challenge list and report matching this
    specific target instance instead of assuming every weakness is present."""
    return jsonify(vuln_config.profile())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
