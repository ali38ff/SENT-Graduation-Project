import os
import json
import ssl
import smtplib
import requests

from pathlib import Path
from datetime import datetime
from email.message import EmailMessage

from flask import (
    Flask, request, jsonify, render_template_string,
    redirect, url_for, session, Response
)
from flask_cors import CORS
from twilio.rest import Client


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = Path(os.getenv("LOG_FILE", str(DATA_DIR / "notifications_log.json")))
CAPTURE_PATH = Path(os.getenv("CAPTURE_PATH", str(DATA_DIR / "latest_photo.jpg")))

SNAPSHOT_URL = os.getenv("SNAPSHOT_URL", "")          # e.g. http://127.0.0.1:8080/?action=snapshot
STREAM_INTERNAL = os.getenv("STREAM_INTERNAL", "")    # e.g. http://127.0.0.1:8080/?action=stream

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")              # Gmail App Password
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "")

TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM", "")        # e.g. whatsapp:+14155238886
WHATSAPP_TO = os.getenv("WHATSAPP_TO", "")            # e.g. whatsapp:+9665xxxxxxx

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "CHANGE_ME")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASS = os.getenv("ADMIN_PASS", "")
NORMAL_USER = os.getenv("NORMAL_USER", "user")
NORMAL_PASS = os.getenv("NORMAL_PASS", "")

USERS = {
    ADMIN_USER: {"password": ADMIN_PASS, "role": "admin"},
    NORMAL_USER: {"password": NORMAL_PASS, "role": "user"},
}

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
CORS(app)


def load_notifications():
    if LOG_FILE.exists():
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


notifications = load_notifications()


def save_notifications():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(notifications, f, ensure_ascii=False, indent=2)


def can_send_email():
    return all([EMAIL_SENDER, EMAIL_PASS, EMAIL_RECEIVER])


def send_email_with_photo(img_path: Path) -> bool:
    if not can_send_email() or not img_path.exists():
        return False
    try:
        msg = EmailMessage()
        msg["Subject"] = "SENT Robot Photo"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg.set_content("Attached photo captured by the robot.")

        with open(img_path, "rb") as f:
            data = f.read()
        msg.add_attachment(data, maintype="image", subtype="jpeg", filename="photo.jpg")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASS)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Email photo error:", e)
        return False


def send_email_alert(title: str, message: str, timestamp: str):
    if not can_send_email():
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = f"SENT Robot Alert: {title}"
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg.set_content(f"{message}\n\nTime: {timestamp}")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASS)
            smtp.send_message(msg)

        print(f"[+] Email alert sent: {title}")
    except Exception as e:
        print("Email error:", e)


def can_send_whatsapp():
    return all([TWILIO_SID, TWILIO_TOKEN, WHATSAPP_FROM, WHATSAPP_TO])


def send_whatsapp_alert(title: str, message: str, timestamp: str):
    if not can_send_whatsapp():
        return
    try:
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        body = f"SENT Robot Alert\n\nTitle: {title}\nMessage: {message}\nTime: {timestamp}"
        client.messages.create(from_=WHATSAPP_FROM, body=body, to=WHATSAPP_TO)
        print(f"[+] WhatsApp alert sent: {title}")
    except Exception as e:
        print("WhatsApp error:", e)


def require_login():
    return "user" in session


def require_admin():
    return session.get("role") == "admin"


@app.route("/", methods=["GET", "POST"])
def login_page():
    if request.method == "POST":
        user = (request.form.get("username") or "").strip()
        pwd = (request.form.get("password") or "").strip()

        if user in USERS and USERS[user]["password"] == pwd:
            session["user"] = user
            session["role"] = USERS[user]["role"]
            return redirect(url_for("dashboard"))
        return render_template_string(LOGIN_HTML, error="Invalid username or password")

    return render_template_string(LOGIN_HTML, error=None)


@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("login_page"))
    role = session.get("role", "user")
    return render_template_string(
        DASH_HTML,
        role=role,
        datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if username in USERS and USERS[username]["password"] == password:
        return jsonify({"status": "ok", "role": USERS[username]["role"]})
    return jsonify({"status": "error"}), 401


@app.route("/notify", methods=["POST"])
def receive_notification():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "Unknown").strip()
    message = (data.get("message") or "").strip()
    timestamp = (data.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")).strip()

    notifications.append({"title": title, "message": message, "time": timestamp})
    save_notifications()

    send_email_alert(title, message, timestamp)
    send_whatsapp_alert(title, message, timestamp)

    print(f"[+] New notification: {title}")
    return jsonify({"status": "ok"})


@app.route("/notify", methods=["GET"])
def list_notifications():
    return jsonify(notifications)


@app.route("/clear", methods=["POST"])
def clear_notifications():
    if not require_admin():
        return jsonify({"error": "unauthorized"}), 403

    notifications.clear()
    save_notifications()
    return jsonify({"status": "cleared"})


@app.route("/take_photo", methods=["POST"])
def take_photo():
    if not require_admin():
        return jsonify({"error": "unauthorized"}), 403

    if not SNAPSHOT_URL:
        return jsonify({"success": False, "error": "SNAPSHOT_URL not configured"}), 500

    try:
        r = requests.get(SNAPSHOT_URL, timeout=8)
        if r.status_code == 200 and r.content:
            CAPTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(CAPTURE_PATH, "wb") as f:
                f.write(r.content)

            ok = send_email_with_photo(CAPTURE_PATH)
            return jsonify({"success": bool(ok)})

        return jsonify({"success": False, "error": f"Snapshot HTTP {r.status_code}"}), 500
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/stream")
def stream_proxy():
    if not STREAM_INTERNAL:
        return "STREAM_INTERNAL not configured", 500

    try:
        r = requests.get(STREAM_INTERNAL, stream=True, timeout=8)
    except Exception as e:
        print("Stream error:", e)
        return "Stream error", 502

    def generate():
        try:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        except Exception as e:
            print("Stream client disconnected:", e)

    return Response(generate(), content_type=r.headers.get("Content-Type", "multipart/x-mixed-replace"))


LOGIN_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Login</title>
<style>
body{font-family:Poppins,sans-serif;background:#eef2f7;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.card{width:350px;background:white;padding:30px;border-radius:15px;box-shadow:0 6px 20px rgba(0,0,0,0.1)}
h2{text-align:center;color:#2563eb;margin-bottom:25px}
input{width:100%;padding:10px;margin-top:12px;border:1px solid #ccc;border-radius:8px;font-size:15px}
button{width:100%;padding:12px;margin-top:20px;background:#2563eb;color:white;border:none;border-radius:8px;font-weight:bold;cursor:pointer}
.error{color:red;text-align:center;margin-top:10px}
</style></head><body>
<form class="card" method="post" onkeypress="if(event.key==='Enter'){this.submit();}">
<h2>Robot Dashboard</h2>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
<input name="username" placeholder="Username" required>
<input name="password" type="password" placeholder="Password" required>
<button type="submit">Login</button>
</form></body></html>
"""

DASH_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Dashboard</title>
<style>
body{font-family:Poppins,sans-serif;background:#f5f7fa;margin:0}
.header{background:#2563eb;color:white;padding:16px;display:flex;justify-content:space-between;align-items:center}
.container{max-width:1000px;margin:20px auto;padding:0 16px}
button{padding:10px 14px;border:none;border-radius:8px;font-weight:bold;margin-right:8px;cursor:pointer}
.btn-primary{background:#1e40af;color:white}
.btn-danger{background:#ef4444;color:white}
.btn-logout{background:#facc15;color:black}
.table{width:100%;border-collapse:collapse;background:white;border-radius:10px;overflow:hidden;box-shadow:0 4px 10px rgba(0,0,0,0.05)}
th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}
th{background:#f0f0f0}
.small{color:#666;font-size:13px}
.video-box{
  background:#000;border-radius:12px;overflow:hidden;
  box-shadow:0 4px 10px rgba(0,0,0,0.2);
  margin-bottom:14px;max-width:600px;height:260px;margin-left:auto;margin-right:auto;
}
.video-box img{width:100%;height:100%;object-fit:cover;display:block;}
.controls{margin:10px 0;display:flex;flex-wrap:wrap;gap:8px}
</style></head><body>
<div class="header">
<h2>Robot Dashboard</h2>
<div>
<span style="margin-right:12px;">Role: {{ role.upper() }}</span>
<a href="/logout"><button class="btn-logout">Logout</button></a>
</div></div>

<div class="container">
<div class="video-box"><img src="/stream" alt="Robot Live Stream"></div>

{% if role == 'admin' %}
<div class="controls">
  <button class="btn-primary" onclick="takePhoto()">Take Photo & Send Mail</button>
  <button class="btn-danger" onclick="clearLog()">Clear Notifications</button>
</div>
{% endif %}

<table class="table" id="notifTable">
<thead><tr><th>Type</th><th>Message</th><th>Time</th></tr></thead>
<tbody><tr><td colspan="3" class="small">Loading...</td></tr></tbody>
</table></div>

<script>
const role="{{ role }}";let lastCount=0;
async function fetchData(){
  const r=await fetch('/notify');const data=await r.json();
  const tb=document.querySelector('#notifTable tbody');tb.innerHTML='';
  if(!data.length){tb.innerHTML='<tr><td colspan="3" class="small">No notifications</td></tr>';}
  else{
    data.slice().reverse().forEach(n=>{
      tb.innerHTML+=`<tr><td>${n.title}</td><td>${n.message}</td><td>${n.time}</td></tr>`;
    });
  }
  if(data.length>lastCount){
    new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg').play().catch(()=>{});
  }
  lastCount=data.length;
}
async function takePhoto(){
  if(role!=='admin')return;
  const r=await fetch('/take_photo',{method:'POST'});const d=await r.json();
  alert(d.success?'Photo sent!':'Failed');
}
async function clearLog(){
  if(role!=='admin')return;
  if(!confirm('Clear all notifications?'))return;
  await fetch('/clear',{method:'POST'});
  fetchData();
}
window.onload=()=>{fetchData();setInterval(fetchData,3000);}
</script></body></html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
