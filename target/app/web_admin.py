"""Intentionally vulnerable camera web admin panel.

This is the teaching target for EduVAPT-IoT, NOT a real product. Every
weakness below is deliberate and documented in target/README.md:
  - default, unchangeable credentials (OWASP I1)
  - a static, unsigned session cookie with no expiry (OWASP I1 / weak session mgmt)
  - the live snapshot is reachable with NO authentication at all (OWASP I3)
"""
import os

from flask import Flask, Response, redirect, request, send_file

app = Flask(__name__)

ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

# Intentionally weak: a small set of well-known default credentials.
VALID_CREDENTIALS = {
    ("admin", "admin"),
    ("admin", "1234"),
    ("admin", "password"),
}

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

LIVE_PAGE = """<!doctype html>
<html><head><title>IoT-Cam Live</title></head>
<body style="font-family:sans-serif;background:#1e1e23;color:#eee;padding:2rem">
<h2>Live Camera Feed - CAM-01</h2>
<img src="/snapshot.jpg" style="max-width:100%;border:2px solid #444">
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
        resp = redirect("/live")
        # Intentionally weak: static, unsigned token, no expiry.
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
    # Intentional vulnerability: no auth check here at all, even though the
    # /live page it's embedded in does check for a session cookie.
    return send_file(os.path.join(ASSET_DIR, "cctv_snapshot.jpg"), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
