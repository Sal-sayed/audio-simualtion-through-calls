import os
import csv
import uuid
import json
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory

app = Flask(__name__)

DB_FILE = "tracking.json"
CONTACTS_FILE = "contacts.csv"

# ─── Helpers ───────────────────────────────────────────────────────────────────

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {}

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_contacts():
    contacts = []
    if os.path.exists(CONTACTS_FILE):
        with open(CONTACTS_FILE, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                contacts.append(row)
    return contacts

# ─── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    user_id = request.args.get("user", "guest")
    name    = request.args.get("name", "")
    db = load_db()

    # Register user on first visit
    if user_id not in db:
        db[user_id] = {
            "name": name,
            "phone": user_id,
            "clicked": False,
            "audio_played": False,
            "visited_at": datetime.now().isoformat(),
            "audio_at": None,
        }
        save_db(db)
    elif not db[user_id]["clicked"]:
        db[user_id]["clicked"] = True
        db[user_id]["visited_at"] = datetime.now().isoformat()
        save_db(db)

    display_name = db[user_id].get("name") or name or "Friend"
    return render_template("index.html", user_id=user_id, name=display_name)


@app.route("/track", methods=["POST"])
def track():
    """Called by JS when audio starts playing."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id", "guest")
    event   = data.get("event", "")

    db = load_db()
    if user_id not in db:
        db[user_id] = {
            "name": "", "phone": user_id,
            "clicked": True, "audio_played": False,
            "visited_at": datetime.now().isoformat(), "audio_at": None,
        }

    if event == "audio_played":
        db[user_id]["audio_played"] = True
        db[user_id]["audio_at"] = datetime.now().isoformat()

    save_db(db)
    return jsonify({"status": "ok"})


@app.route("/dashboard")
def dashboard():
    db = load_db()
    contacts = load_contacts()

    rows = []
    for c in contacts:
        phone = c.get("Phone", c.get("phone", ""))
        name  = c.get("Name",  c.get("name",  ""))
        info  = db.get(phone, {})
        rows.append({
            "name":         name,
            "phone":        phone,
            "clicked":      info.get("clicked", False),
            "audio_played": info.get("audio_played", False),
            "visited_at":   info.get("visited_at", "—"),
            "audio_at":     info.get("audio_at",   "—"),
        })

    total        = len(rows)
    clicked      = sum(1 for r in rows if r["clicked"])
    audio_played = sum(1 for r in rows if r["audio_played"])
    return render_template("dashboard.html",
                           rows=rows, total=total,
                           clicked=clicked, audio_played=audio_played)


@app.route("/contacts")
def get_contacts():
    """Returns contact list with unique links — used by sender script."""
    contacts = load_contacts()
    base_url = request.host_url.rstrip("/")
    result = []
    for c in contacts:
        phone = c.get("Phone", c.get("phone", ""))
        name  = c.get("Name",  c.get("name",  ""))
        link  = f"{base_url}/?user={phone}&name={name.replace(' ', '%20')}"
        result.append({"name": name, "phone": phone, "link": link})
    return jsonify(result)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        f = request.files.get("csv_file")
        if f and f.filename.endswith(".csv"):
            f.save(CONTACTS_FILE)
            return jsonify({"status": "ok", "message": "CSV uploaded successfully."})
        return jsonify({"status": "error", "message": "Please upload a valid .csv file."}), 400
    return render_template("upload.html")


@app.route("/static/audio/<path:filename>")
def serve_audio(filename):
    return send_from_directory("static/audio", filename)


if __name__ == "__main__":
    os.makedirs("static/audio", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
