import cv2
import sqlite3
import threading
import winsound
import os
from datetime import datetime
from flask import Flask, render_template_string, jsonify
from ultralytics import YOLO

app = Flask(__name__)
model = YOLO('yolov8n.pt') 

DB_NAME = 'sentinel.db'

# --- 1. DATABASE INIT ---
def init_db():
    if os.path.exists(DB_NAME):
        try: os.remove(DB_NAME) 
        except: pass
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''CREATE TABLE IF NOT EXISTS logs 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    obj TEXT, 
                    conf REAL, 
                    log_date TEXT,
                    log_time TEXT)''') 
    conn.close()
    print("✅ SENTINEL-AI Database Ready!")

def save_to_db(obj_name, conf):
    try:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        conn.execute('INSERT INTO logs (obj, conf, log_date, log_time) VALUES (?, ?, ?, ?)', 
                     (obj_name, conf, date_str, time_str))
        conn.commit()
        conn.close()
    except: pass

# --- 2. DETECTION ENGINE ---
def start_detection():
    cap = cv2.VideoCapture(0)
    print("🛡️ SENTINEL-AI Scanning Active...")
    while True:
        ret, frame = cap.read()
        if not ret: break
        results = model(frame, conf=0.4)
        for r in results:
            for box in r.boxes:
                name = model.names[int(box.cls[0])].upper()
                rating = round(float(box.conf[0]) * 100, 2)
                winsound.Beep(1000, 100) 
                save_to_db(name, rating)
                
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
                cv2.putText(frame, f"{name}: {rating}%", (x1, y1-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
        cv2.imshow('SENTINEL-AI MONITOR', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break
    cap.release()
    cv2.destroyAllWindows()

# --- 3. UI DESIGN (Universal Surveillance Mode) ---
HTML_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>SENTINEL AI | B. Lakshmi Kranthi</title>
    <style>
        :root { --primary: #00f2ff; --bg: #010810; --accent: #00ff88; }
        body { background: var(--bg); color: var(--primary); font-family: 'Segoe UI', sans-serif; margin: 0; text-align: center; }
        .header { background: #001a33; padding: 15px; border-bottom: 3px solid var(--primary); }
        .ticker { background: rgba(0, 242, 255, 0.1); padding: 8px; overflow: hidden; white-space: nowrap; color: #fff; border-bottom: 1px solid rgba(0,242,255,0.2); }
        .marquee { display: inline-block; animation: scroll 20s linear infinite; font-weight: bold; }
        @keyframes scroll { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
        .container { width: 90%; max-width: 850px; margin: 20px auto; }
        .day-section { margin-bottom: 25px; border: 1px solid rgba(0, 242, 255, 0.2); border-radius: 10px; overflow: hidden; background: rgba(255,255,255,0.02); }
        .day-header { background: rgba(0, 242, 255, 0.2); padding: 10px; font-weight: bold; color: #fff; border-bottom: 1px solid var(--primary); text-transform: uppercase; }
        .log-entry { display: flex; justify-content: space-between; padding: 12px 25px; border-bottom: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
        .log-entry:hover { background: rgba(0, 242, 255, 0.05); }
        .badge { border: 1px solid var(--primary); padding: 6px 25px; border-radius: 30px; color: #fff; display: inline-block; margin-top: 15px; background: rgba(0, 242, 255, 0.05); }
    </style>
</head>
<body>
    <div class="header">
        <h2 style="margin:0; letter-spacing: 1px;">VIGNAN'S NIRULA INSTITUTE OF TECHNOLOGY & SCIENCE FOR WOMAN (VNITSW)</h2>
        <p style="margin:5px 0 0 0; color:#8892b0; font-weight: bold;">GUNTUR, ANDHRA PRADESH</p>
    </div>
    <div class="ticker"><div class="marquee">SYSTEM STATUS: ACTIVE || MODE: UNIVERSAL SURVEILLANCE || AI ENGINE: YOLOv8 || LOGGING REAL-TIME DATA...</div></div>
    
    <div style="margin-top: 30px;">
        <h1 style="font-size: 4em; margin:0; text-shadow: 0 0 20px var(--primary); letter-spacing: 5px;">SENTINEL-AI</h1>
        <p style="color: #fff; font-size: 1.2em; margin: 5px 0;">Intelligent Surveillance & Activity Logger</p>
        <div class="badge">Designed & Developed by: <b>B. LAKSHMI KRANTHI</b></div>
    </div>

    <div class="container" id="logs">
        <h3 style="color:#8892b0; margin-top: 50px;">📡 Waiting for AI Input...</h3>
    </div>

    <script>
        async function fetchLogs() {
            try {
                const res = await fetch('/api/data');
                const data = await res.json();
                let html = '';
                if (Object.keys(data).length === 0) {
                    html = '<h3 style="color:#8892b0; margin-top: 50px;">No Detections Recorded.</h3>';
                } else {
                    for (const date in data) {
                        html += `<div class="day-section">
                                    <div class="day-header">📅 LOG DATE: ${date}</div>`;
                        data[date].forEach(item => {
                            html += `<div class="log-entry">
                                        <span style="color:#8892b0">🕒 ${item.time}</span>
                                        <span style="color:#fff; font-weight:bold;">${item.obj}</span>
                                        <span style="color:var(--accent)">${item.conf}% MATCH</span>
                                    </div>`;
                        });
                        html += `</div>`;
                    }
                }
                document.getElementById('logs').innerHTML = html;
            } catch(e) { console.log(e); }
        }
        setInterval(fetchLogs, 1500);
    </script>
</body>
</html>
"""

# --- 4. ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_UI)

@app.route('/api/data')
def get_data():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.execute('SELECT obj, conf, log_date, log_time FROM logs ORDER BY id DESC LIMIT 50')
        rows = cursor.fetchall()
        conn.close()
        history = {}
        for r in rows:
            date = r[2]
            if date not in history: history[date] = []
            history[date].append({"obj": r[0], "conf": r[1], "time": r[3]})
        return jsonify(history)
    except: return jsonify({})

if __name__ == "__main__":
    init_db()
    threading.Thread(target=start_detection, daemon=True).start()
    app.run(host='127.0.0.1', port=5000)