import os
import json
import logging
import time
from functools import wraps

from flask import (
    Flask, render_template, jsonify,
    request, Response, stream_with_context,
    session, redirect, url_for,
)

from database import init_db, fetch_recent_logs, fetch_all_logs, fetch_stats
import realtime as sim

# ---------------- APP SETUP ----------------
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.environ.get("FLASK_SECRET", "secret123")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

init_db()

# ---------------- LOGIN CONFIG ----------------
USERS = {
    os.environ.get("ADMIN_USER", "admin"): os.environ.get("ADMIN_PASS", "admin123")
}

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in USERS and USERS[username] == password:
            session["username"] = username
            return redirect(url_for("index"))
        else:
            error = "Invalid credentials"

    return render_template("login.html", error=error)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------------- DASHBOARD ----------------
@app.route("/")
@login_required
def index():
    try:
        stats = fetch_stats()
        recent = fetch_recent_logs(20)

        return render_template(
            "index.html",
            stats=stats,
            recent_logs=recent,
            sim_running=sim.is_running(),
            username=session.get("username")
        )
    except Exception as e:
        logger.error("Index error: %s", e)
        return render_template("index.html", stats={}, recent_logs=[])

# ---------------- LOGS PAGE ----------------
@app.route("/logs")
@login_required
def logs():
    logs = fetch_all_logs()
    return render_template("logs.html", logs=logs)

# ---------------- API ----------------
@app.route("/api/stats")
@login_required
def api_stats():
    return jsonify({
        "stats": fetch_stats(),
        "sim": sim.simulation_stats
    })

@app.route("/api/start_simulation", methods=["POST"])
@login_required
def start_sim():
    sim.start_simulation()
    return jsonify({"ok": True})

@app.route("/api/stop_simulation", methods=["POST"])
@login_required
def stop_sim():
    sim.stop_simulation()
    return jsonify({"ok": True})

# ---------------- LIVE STREAM ----------------
@app.route("/api/stream")
@login_required
def stream():

    def generate():
        while True:
            data = {
                "stats": sim.simulation_stats
            }
            yield f"data: {json.dumps(data)}\n\n"
            time.sleep(2)

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

# ---------------- MAIN ----------------
if __name__ == "__main__":
    logger.info("Starting server...")

    # 🔥 IMPORTANT: AUTO START SIMULATION
    sim.start_simulation()

    app.run(host="0.0.0.0", port=5000, debug=False)
